import logging
import uuid
from typing import List, Dict, Any, Optional
from neo4j import AsyncSession
from app.auth.password import hash_password, verify_password

logger = logging.getLogger("ridebuddy.service")

# --- USER AUTHENTICATION ---

async def register_user(
    session: AsyncSession,
    name: str,
    phone: str,
    password_plain: str,
    role: str
) -> Dict[str, Any]:
    """
    Registers a new user after checking if the phone number is already registered.
    Passwords are saved hashed.
    """
    # Check if user already exists
    check_query = "MATCH (u:User {phone: $phone}) RETURN u.phone AS phone"
    result = await session.run(check_query, {"phone": phone.strip()})
    record = await result.single()
    if record:
        raise RuntimeError("A user with this phone number is already registered.")

    hashed = hash_password(password_plain)
    user_id = f"user-{str(uuid.uuid4())[:8]}"
    
    create_query = """
    CREATE (u:User {
        id: $id,
        name: $name,
        phone: $phone,
        password: $password,
        role: $role
    })
    RETURN u.id AS id, u.name AS name, u.phone AS phone, u.role AS role
    """
    try:
        res = await session.run(create_query, {
            "id": user_id,
            "name": name.strip(),
            "phone": phone.strip(),
            "password": hashed,
            "role": role.strip().upper() # RIDER or DRIVER
        })
        created_record = await res.single()
        if created_record:
            return dict(created_record)
        raise RuntimeError("Failed to register user node.")
    except Exception as e:
        logger.error(f"Error in register_user: {e}")
        raise e

async def login_user(
    session: AsyncSession,
    phone: str,
    password_plain: str
) -> Optional[Dict[str, Any]]:
    """
    Finds user by phone and verifies the hashed password.
    Returns user details (sans password) if valid.
    """
    query = """
    MATCH (u:User {phone: $phone})
    RETURN u.id AS id, u.name AS name, u.phone AS phone, u.password AS password, u.role AS role
    """
    try:
        res = await session.run(query, {"phone": phone.strip()})
        record = await res.single()
        if not record:
            return None
        
        user_data = dict(record)
        if verify_password(password_plain, user_data["password"]):
            # Exclude password hash from response
            user_data.pop("password", None)
            return user_data
        return None
    except Exception as e:
        logger.error(f"Error in login_user: {e}")
        raise e


# --- RIDE SERVICE ---

async def create_ride_node(
    session: AsyncSession, 
    driver_id: str, 
    start_loc: str, 
    end_loc: str, 
    time: str,
    available_seats: int
) -> Dict[str, Any]:
    """
    Creates a Ride offered by a Driver, linking it to transit Locations.
    """
    # Check for duplicate ride: same driver/creator, start, end, time, and active status
    dup_query = """
    MATCH (driver:User {id: $driver_id})-[:OFFERS]->(r:Ride {status: "ACTIVE"})-[:STARTS_AT]->(s:Location {name: $start_loc})
    MATCH (r)-[:ENDS_AT]->(e:Location {name: $end_loc})
    WHERE r.departure_time = $time
    RETURN r.id AS ride_id
    """
    dup_res = await session.run(dup_query, {
        "driver_id": driver_id,
        "start_loc": start_loc.strip(),
        "end_loc": end_loc.strip(),
        "time": time.strip()
    })
    if await dup_res.single():
        raise RuntimeError("A duplicate active ride offer already exists for this driver, route, and time.")

    query = """
    MATCH (driver:User {id: $driver_id})
    MATCH (s:Location {name: $start_loc})
    MATCH (e:Location {name: $end_loc})
    
    CREATE (r:Ride {
        id: $ride_id, 
        departure_time: $time, 
        available_seats: toInteger($available_seats), 
        status: "ACTIVE"
    })
    CREATE (driver)-[:OFFERS]->(r)
    CREATE (r)-[:STARTS_AT]->(s)
    CREATE (r)-[:ENDS_AT]->(e)
    
    RETURN driver.name AS driver_name,
           r.id AS ride_id,
           r.departure_time AS ride_time,
           r.available_seats AS available_seats,
           r.status AS status,
           s.name AS ride_start,
           e.name AS ride_end
    """
    ride_id = f"ride-{str(uuid.uuid4())[:8]}"
    try:
        result = await session.run(query, {
            "driver_id": driver_id,
            "start_loc": start_loc.strip(),
            "end_loc": end_loc.strip(),
            "time": time.strip(),
            "available_seats": available_seats,
            "ride_id": ride_id
        })
        record = await result.single()
        if record:
            return dict(record)
        raise RuntimeError("Failed to create ride. Ensure Driver and Locations exist.")
    except Exception as e:
        logger.error(f"Error in create_ride_node: {e}")
        raise e

async def query_matching_rides(
    session: AsyncSession, 
    start_name: str, 
    end_name: str,
    current_user_id: str
) -> List[Dict[str, Any]]:
    """
    Matches rides that pass through the requested start and destination in sequence.
    This uses the 'relationally awkward' overlap graph traversal.
    """
    query = """
    MATCH (start_loc:Location {name: $start_name})
    MATCH (end_loc:Location {name: $end_name})
    MATCH (u:User)-[:OFFERS]->(r:Ride {status: "ACTIVE"})
    MATCH (r)-[:STARTS_AT]->(r_start:Location)
    MATCH (r)-[:ENDS_AT]->(r_end:Location)
    
    // Traversal check: ride must cover passenger start and end in correct chronological order
    MATCH ride_path = (r_start)-[:CONNECTED_TO*0..4]->(start_loc)-[:CONNECTED_TO*1..4]->(end_loc)-[:CONNECTED_TO*0..4]->(r_end)
    
    // Check if current user has an existing booking
    OPTIONAL MATCH (current_user:User {id: $current_user_id})-[:BOOKED]->(b:Booking)-[:FOR_RIDE]->(r)
    
    // De-duplicate multiple traversal paths for the same ride by selecting the first matching path
    WITH u, r, r_start, r_end, b, collect(ride_path)[0] AS shortest_ride_path
    
    RETURN u.name AS driver_name,
           u.phone AS driver_phone,
           u.id AS driver_id,
           r.id AS ride_id,
           r.departure_time AS ride_time,
           r.available_seats AS available_seats,
           r_start.name AS ride_start,
           r_end.name AS ride_end,
           [n in nodes(shortest_ride_path) | n.name] AS route_nodes,
           b.status AS booking_status,
           b.id AS booking_id
    """
    try:
        result = await session.run(query, {
            "start_name": start_name.strip(),
            "end_name": end_name.strip(),
            "current_user_id": current_user_id
        })
        records = await result.data()
        return records
    except Exception as e:
        logger.error(f"Error in query_matching_rides: {e}")
        raise e

async def query_multi_hop_routes(
    session: AsyncSession, 
    start_name: str, 
    end_name: str
) -> List[List[str]]:
    """
    Finds all paths of length 2 to 4 CONNECTED_TO relationships.
    """
    query = """
    MATCH (a:Location {name: $start_name})
    MATCH (b:Location {name: $end_name})
    MATCH path = (a)-[:CONNECTED_TO*2..4]->(b)
    RETURN [n in nodes(path) | n.name] AS route_nodes, length(path) as path_len
    ORDER BY path_len ASC
    LIMIT 5
    """
    try:
        result = await session.run(query, {
            "start_name": start_name.strip(),
            "end_name": end_name.strip()
        })
        records = await result.data()
        return [record["route_nodes"] for record in records]
    except Exception as e:
        logger.error(f"Error in query_multi_hop_routes: {e}")
        raise e


# --- BOOKING WORKFLOW ---

async def create_booking_node(
    session: AsyncSession,
    ride_id: str,
    rider_id: str
) -> Dict[str, Any]:
    """
    Creates a PENDING booking node after checking business rules:
    - Driver cannot book own ride
    - Cannot book cancelled/inactive rides
    - Cannot book rides with 0 seats
    - Cannot duplicate booking
    """
    # 1. Validation check
    validation_query = """
    MATCH (r:Ride {id: $ride_id})<-[:OFFERS]-(driver:User)
    MATCH (rider:User {id: $rider_id})
    
    OPTIONAL MATCH (rider)-[:BOOKED]->(existing:Booking)-[:FOR_RIDE]->(r)
    
    RETURN (driver.id = rider.id) AS is_driver,
           (r.available_seats <= 0) AS no_seats,
           (r.status <> "ACTIVE") AS not_active,
           (existing IS NOT NULL) AS already_booked
    """
    res = await session.run(validation_query, {"ride_id": ride_id, "rider_id": rider_id})
    record = await res.single()
    if not record:
        raise RuntimeError("Specified ride or driver profile not found.")
        
    validation = dict(record)
    if validation["is_driver"]:
        raise RuntimeError("Drivers are not permitted to book their own offered commutes.")
    if validation["not_active"]:
        raise RuntimeError("This ride commute has been cancelled or is inactive.")
    if validation["no_seats"]:
        raise RuntimeError("No available seats remaining on this shared ride.")
    if validation["already_booked"]:
        raise RuntimeError("You have already booked or requested a seat on this ride.")
        
    # 2. Create the booking node and relationships
    booking_id = f"book-{str(uuid.uuid4())[:8]}"
    create_query = """
    CREATE (b:Booking {
        id: $booking_id,
        status: "PENDING",
        created_at: timestamp()
    })
    WITH b
    MATCH (rider:User {id: $rider_id})
    MATCH (r:Ride {id: $ride_id})
    CREATE (rider)-[:BOOKED]->(b)
    CREATE (b)-[:FOR_RIDE]->(r)
    CREATE (rider)-[:REQUESTED]->(r)
    RETURN b.id AS booking_id, b.status AS status
    """
    try:
        res = await session.run(create_query, {
            "booking_id": booking_id,
            "rider_id": rider_id,
            "ride_id": ride_id
        })
        booking_record = await res.single()
        if booking_record:
            return dict(booking_record)
        raise RuntimeError("Failed to build booking relationships in graph.")
    except Exception as e:
        logger.error(f"Error in create_booking_node: {e}")
        raise e

async def get_driver_booking_requests(
    session: AsyncSession,
    driver_id: str
) -> List[Dict[str, Any]]:
    """
    Retrieves all booking requests made for rides offered by the driver (Requirement D).
    """
    query = """
    MATCH (driver:User {id: $driver_id})-[:OFFERS]->(r:Ride)<-[:FOR_RIDE]-(b:Booking)<-[:BOOKED]-(rider:User)
    MATCH (r)-[:STARTS_AT]->(s:Location)
    MATCH (r)-[:ENDS_AT]->(e:Location)
    RETURN b.id AS booking_id,
           b.status AS booking_status,
           b.created_at AS created_at,
           rider.id AS rider_id,
           rider.name AS rider_name,
           rider.phone AS rider_phone,
           r.id AS ride_id,
           r.departure_time AS ride_time,
           s.name AS ride_start,
           e.name AS ride_end,
           r.available_seats AS available_seats,
           driver.id AS driver_id,
           driver.name AS driver_name,
           driver.phone AS driver_phone
    ORDER BY b.created_at DESC
    """
    try:
        result = await session.run(query, {"driver_id": driver_id})
        records = await result.data()
        return records
    except Exception as e:
        logger.error(f"Error in get_driver_booking_requests: {e}")
        raise e

async def get_rider_bookings(
    session: AsyncSession,
    rider_id: str
) -> List[Dict[str, Any]]:
    """
    Retrieves bookings created by a rider, checking driver relationship and context (Requirement E).
    """
    query = """
    MATCH (rider:User {id: $rider_id})-[:BOOKED]->(b:Booking)-[:FOR_RIDE]->(r:Ride)<-[:OFFERS]-(driver:User)
    MATCH (r)-[:STARTS_AT]->(s:Location)
    MATCH (r)-[:ENDS_AT]->(e:Location)
    RETURN b.id AS booking_id,
           b.status AS booking_status,
           b.created_at AS created_at,
           driver.id AS driver_id,
           driver.name AS driver_name,
           driver.phone AS driver_phone,
           r.id AS ride_id,
           r.departure_time AS ride_time,
           s.name AS ride_start,
           e.name AS ride_end,
           r.status AS ride_status
    ORDER BY b.created_at DESC
    """
    try:
        result = await session.run(query, {"rider_id": rider_id})
        records = await result.data()
        return records
    except Exception as e:
        logger.error(f"Error in get_rider_bookings: {e}")
        raise e

async def get_booking_details(
    session: AsyncSession,
    booking_id: str
) -> Optional[Dict[str, Any]]:
    """
    Retrieves full context details for a booking to send websocket notifications.
    """
    query = """
    MATCH (b:Booking {id: $booking_id})-[:FOR_RIDE]->(r:Ride)<-[:OFFERS]-(driver:User)
    MATCH (rider:User)-[:BOOKED]->(b)
    MATCH (r)-[:STARTS_AT]->(s:Location)
    MATCH (r)-[:ENDS_AT]->(e:Location)
    RETURN b.id AS booking_id,
           b.status AS booking_status,
           b.created_at AS created_at,
           rider.id AS rider_id,
           rider.name AS rider_name,
           rider.phone AS rider_phone,
           driver.id AS driver_id,
           driver.name AS driver_name,
           driver.phone AS driver_phone,
           r.id AS ride_id,
           r.departure_time AS ride_time,
           s.name AS ride_start,
           e.name AS ride_end
    """
    try:
        result = await session.run(query, {"booking_id": booking_id})
        record = await result.single()
        return dict(record) if record else None
    except Exception as e:
        logger.error(f"Error in get_booking_details: {e}")
        raise e

async def respond_to_booking(
    session: AsyncSession,
    booking_id: str,
    driver_id: str,
    action: str
) -> Dict[str, Any]:
    """
    Handles driver accepting or rejecting a pending booking.
    Accept action changes status to CONFIRMED and decrements seats.
    Reject action changes status to REJECTED.
    """
    if action.upper() == "ACCEPT":
        # Check seats remaining first
        check_seats_query = """
        MATCH (b:Booking {id: $booking_id})-[:FOR_RIDE]->(r:Ride)
        RETURN r.available_seats AS seats, b.status AS status
        """
        seats_res = await session.run(check_seats_query, {"booking_id": booking_id})
        record = await seats_res.single()
        if not record:
            raise RuntimeError("Booking request details not found.")
        seats_data = dict(record)
        if seats_data["status"] != "PENDING":
            raise RuntimeError(f"Cannot accept a request that is already {seats_data['status']}.")
        if seats_data["seats"] <= 0:
            raise RuntimeError("Cannot accept booking request: No seats available.")

        query = """
        MATCH (driver:User {id: $driver_id})-[:OFFERS]->(r:Ride)<-[:FOR_RIDE]-(b:Booking {id: $booking_id})
        WHERE b.status = "PENDING"
        SET b.status = "CONFIRMED"
        SET r.available_seats = r.available_seats - 1
        RETURN b.id AS booking_id, b.status AS status, r.available_seats AS available_seats
        """
    else:
        query = """
        MATCH (driver:User {id: $driver_id})-[:OFFERS]->(r:Ride)<-[:FOR_RIDE]-(b:Booking {id: $booking_id})
        WHERE b.status = "PENDING"
        SET b.status = "REJECTED"
        RETURN b.id AS booking_id, b.status AS status
        """
    try:
        result = await session.run(query, {"booking_id": booking_id, "driver_id": driver_id})
        record = await result.single()
        if not record:
            raise RuntimeError("Booking not found, not pending, or driver is unauthorized.")
        return dict(record)
    except Exception as e:
        logger.error(f"Error in respond_to_booking: {e}")
        raise e


# --- RIDE DETAILS (WITH PRIVACY LOGIC) ---

async def get_ride_details(
    session: AsyncSession,
    ride_id: str,
    current_user_id: str
) -> Dict[str, Any]:
    """
    Retrieves ride details, driver name, route nodes, and coordinates.
    Also returns authorization flag indicating whether privacy rules allow exposing contact number.
    """
    query = """
    MATCH (r:Ride {id: $ride_id})<-[:OFFERS]-(driver:User)
    MATCH (r)-[:STARTS_AT]->(s:Location)
    MATCH (r)-[:ENDS_AT]->(e:Location)
    
    // Check if the current user is the driver or has a CONFIRMED booking
    OPTIONAL MATCH (curr_user:User {id: $current_user_id})-[:BOOKED]->(b:Booking)-[:FOR_RIDE]->(r)
    
    // Find transit path nodes
    OPTIONAL MATCH path = (s)-[:CONNECTED_TO*0..4]->(e)
    
    // Collect paths to avoid warning about multiple records when multiple routes connect them
    WITH r, driver, s, e, b, collect(path)[0] AS shortest_path
    
    RETURN r.id AS ride_id,
           r.departure_time AS ride_time,
           r.available_seats AS available_seats,
           r.status AS ride_status,
           driver.id AS driver_id,
           driver.name AS driver_name,
           driver.phone AS driver_phone,
           s.name AS ride_start,
           e.name AS ride_end,
           b.status AS booking_status,
           b.id AS booking_id,
           (driver.id = $current_user_id OR b.status = "CONFIRMED") AS is_authorized,
           [n in nodes(shortest_path) | n.name] AS route_nodes
    """
    try:
        result = await session.run(query, {
            "ride_id": ride_id,
            "current_user_id": current_user_id
        })
        record = await result.single()
        if not record:
            raise RuntimeError("Ride commute record not found.")
        return dict(record)
    except Exception as e:
        logger.error(f"Error in get_ride_details: {e}")
        raise e


# --- LOCATIONS SERVICE ---

async def get_all_locations(session: AsyncSession) -> List[Dict[str, Any]]:
    """
    Fetches all Location nodes from the database including their coordinates.
    """
    query = """
    MATCH (l:Location)
    RETURN l.name AS name, l.latitude AS latitude, l.longitude AS longitude
    ORDER BY l.name ASC
    """
    try:
        result = await session.run(query)
        records = await result.data()
        return records
    except Exception as e:
        logger.error(f"Error in get_all_locations: {e}")
        raise e

async def get_all_users(session: AsyncSession) -> List[Dict[str, Any]]:
    """
    Fetches all User nodes from the database.
    """
    query = """
    MATCH (u:User)
    RETURN u.id AS id, u.name AS name, u.phone AS phone, u.role AS role
    ORDER BY u.name ASC
    """
    try:
        result = await session.run(query)
        records = await result.data()
        return records
    except Exception as e:
        logger.error(f"Error in get_all_users: {e}")
        raise e

async def query_all_active_rides(
    session: AsyncSession,
    current_user_id: str
) -> List[Dict[str, Any]]:
    """
    Retrieves all active rides in the system for browsing by a rider when no search criteria are selected.
    """
    query = """
    MATCH (u:User)-[:OFFERS]->(r:Ride {status: "ACTIVE"})
    MATCH (r)-[:STARTS_AT]->(r_start:Location)
    MATCH (r)-[:ENDS_AT]->(r_end:Location)
    
    // Check if current user has an existing booking
    OPTIONAL MATCH (current_user:User {id: $current_user_id})-[:BOOKED]->(b:Booking)-[:FOR_RIDE]->(r)
    
    // Find transit path nodes
    OPTIONAL MATCH path = (r_start)-[:CONNECTED_TO*0..4]->(r_end)
    WITH u, r, r_start, r_end, b, collect(path)[0] AS shortest_path
    
    RETURN u.name AS driver_name,
           u.phone AS driver_phone,
           u.id AS driver_id,
           r.id AS ride_id,
           r.departure_time AS ride_time,
           r.available_seats AS available_seats,
           r_start.name AS ride_start,
           r_end.name AS ride_end,
           [n in nodes(shortest_path) | n.name] AS route_nodes,
           b.status AS booking_status,
           b.id AS booking_id
    ORDER BY r.departure_time ASC
    """
    try:
        result = await session.run(query, {"current_user_id": current_user_id})
        records = await result.data()
        return records
    except Exception as e:
        logger.error(f"Error in query_all_active_rides: {e}")
        raise e

async def get_driver_offered_rides(
    session: AsyncSession,
    driver_id: str
) -> List[Dict[str, Any]]:
    """
    Retrieves all rides offered by a specific driver, whether active or cancelled.
    """
    query = """
    MATCH (driver:User {id: $driver_id})-[:OFFERS]->(r:Ride)
    MATCH (r)-[:STARTS_AT]->(s:Location)
    MATCH (r)-[:ENDS_AT]->(e:Location)
    
    OPTIONAL MATCH path = (s)-[:CONNECTED_TO*0..4]->(e)
    WITH r, s, e, collect(path)[0] AS shortest_path
    
    RETURN r.id AS ride_id,
           r.departure_time AS ride_time,
           r.available_seats AS available_seats,
           r.status AS ride_status,
           s.name AS ride_start,
           e.name AS ride_end,
           [n in nodes(shortest_path) | n.name] AS route_nodes
    ORDER BY r.departure_time ASC
    """
    try:
        result = await session.run(query, {"driver_id": driver_id})
        records = await result.data()
        return records
    except Exception as e:
        logger.error(f"Error in get_driver_offered_rides: {e}")
        raise e

# --- SIMULATED MESSAGE SERVICE ---

async def create_message_node(
    session: AsyncSession,
    from_phone: str,
    to_phone: str,
    body: str
) -> Dict[str, Any]:
    """
    Creates a simulated Message node in the database to log communications.
    """
    query = """
    CREATE (m:Message {
        id: $message_id,
        from_phone: $from_phone,
        to_phone: $to_phone,
        body: $body,
        timestamp: timestamp()
    })
    RETURN m.id AS message_id, m.from_phone AS from_phone, m.to_phone AS to_phone, m.body AS body, m.timestamp AS timestamp
    """
    message_id = f"msg-{str(uuid.uuid4())[:8]}"
    try:
        res = await session.run(query, {
            "message_id": message_id,
            "from_phone": from_phone,
            "to_phone": to_phone,
            "body": body
        })
        record = await res.single()
        if record:
            return dict(record)
        raise RuntimeError("Failed to create message node.")
    except Exception as e:
        logger.error(f"Error in create_message_node: {e}")
        raise e

async def get_user_messages(
    session: AsyncSession,
    phone: str
) -> List[Dict[str, Any]]:
    """
    Queries simulated Message nodes sent to or from a given phone number.
    """
    query = """
    MATCH (m:Message)
    WHERE m.to_phone = $phone OR m.from_phone = $phone
    RETURN m.id AS message_id, m.from_phone AS from_phone, m.to_phone AS to_phone, m.body AS body, m.timestamp AS timestamp
    ORDER BY m.timestamp DESC
    """
    try:
        res = await session.run(query, {"phone": phone})
        records = await res.data()
        return records
    except Exception as e:
        logger.error(f"Error in get_user_messages: {e}")
        raise e

async def get_user_phone(
    session: AsyncSession,
    user_id: str
) -> Optional[str]:
    """
    Helper to look up a user's phone number by ID.
    """
    query = "MATCH (u:User {id: $user_id}) RETURN u.phone AS phone"
    try:
        res = await session.run(query, {"user_id": user_id})
        record = await res.single()
        return record["phone"] if record else None
    except Exception as e:
        logger.error(f"Error in get_user_phone: {e}")
        raise e
