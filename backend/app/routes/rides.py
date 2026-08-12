import logging
from typing import List, Dict, Any, Optional, Set
from fastapi import APIRouter, Depends, HTTPException, Query, Header, status, WebSocket, WebSocketDisconnect
from pydantic import BaseModel, Field
from neo4j import AsyncSession

from app.db import get_db_session
from app.services import graph_service

logger = logging.getLogger("ridebuddy.routes")
router = APIRouter()

# --- WEBSOCKET CONNECTION MANAGER ---
class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, Set[WebSocket]] = {}

    async def connect(self, user_id: str, websocket: WebSocket):
        await websocket.accept()
        if user_id not in self.active_connections:
            self.active_connections[user_id] = set()
        self.active_connections[user_id].add(websocket)
        logger.info(f"WebSocket connected for user: {user_id}")

    def disconnect(self, user_id: str, websocket: WebSocket):
        if user_id in self.active_connections:
            self.active_connections[user_id].discard(websocket)
            if not self.active_connections[user_id]:
                del self.active_connections[user_id]
        logger.info(f"WebSocket disconnected for user: {user_id}")

    async def send_personal_message(self, message: dict, user_id: str):
        if user_id in self.active_connections:
            for connection in list(self.active_connections[user_id]):
                try:
                    await connection.send_json(message)
                    logger.info(f"Sent message to user {user_id}: {message['type']}")
                except Exception as e:
                    logger.warning(f"Error sending message to user {user_id}, disconnecting: {e}")
                    self.disconnect(user_id, connection)

manager = ConnectionManager()

@router.websocket("/ws/{user_id}")
async def websocket_endpoint(websocket: WebSocket, user_id: str):
    await manager.connect(user_id, websocket)
    try:
        while True:
            # Wait for client input (e.g. keepalive/pings)
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(user_id, websocket)
    except Exception as e:
        logger.error(f"WebSocket error for user {user_id}: {e}")
        manager.disconnect(user_id, websocket)

# --- UTILS ---
def mask_phone(phone: str) -> str:
    """Masks a phone number, leaving only the last 4 digits visible."""
    cleaned = phone.strip()
    if len(cleaned) <= 4:
        return "****"
    return "*" * (len(cleaned) - 4) + cleaned[-4:]


# --- PYDANTIC SCHEMAS ---

class UserRegister(BaseModel):
    name: str = Field(..., min_length=2, max_length=50)
    phone: str = Field(..., min_length=10, max_length=15)
    password: str = Field(..., min_length=4)
    role: str = Field(..., pattern="^(RIDER|DRIVER)$")

class UserLogin(BaseModel):
    phone: str = Field(...)
    password: str = Field(...)

class UserResponse(BaseModel):
    id: str
    name: str
    phone: str
    role: str

class RideCreate(BaseModel):
    start: str = Field(..., min_length=1)
    end: str = Field(..., min_length=1)
    time: str = Field(..., min_length=4)
    available_seats: int = Field(..., gt=0)

class RideResponse(BaseModel):
    driver_name: str
    ride_id: str
    ride_time: str
    ride_start: str
    ride_end: str
    available_seats: int
    status: str

class MatchedRideResponse(BaseModel):
    driver_name: str
    driver_phone: str
    driver_id: str
    ride_id: str
    ride_time: str
    available_seats: int
    ride_start: str
    ride_end: str
    route_nodes: List[str]
    booking_status: Optional[str] = None
    booking_id: Optional[str] = None

class RideDetailsResponse(BaseModel):
    ride_id: str
    ride_time: str
    available_seats: int
    ride_status: str
    driver_name: str
    driver_phone: str
    driver_id: str
    ride_start: str
    ride_end: str
    booking_status: Optional[str] = None
    booking_id: Optional[str] = None
    route_nodes: List[str]

class BookingCreate(BaseModel):
    ride_id: str = Field(...)

class BookingResponse(BaseModel):
    booking_id: str
    booking_status: str
    created_at: int
    driver_name: str
    driver_phone: str
    driver_id: str
    ride_id: str
    ride_time: str
    ride_start: str
    ride_end: str
    ride_status: Optional[str] = None
    rider_name: Optional[str] = None
    rider_phone: Optional[str] = None
    rider_id: Optional[str] = None

class BookingRespond(BaseModel):
    action: str = Field(..., pattern="^(ACCEPT|REJECT)$")

class LocationResponse(BaseModel):
    name: str
    latitude: float
    longitude: float


# --- AUTHENTICATION ROUTES ---

@router.post("/register", status_code=status.HTTP_201_CREATED, response_model=UserResponse)
async def register(user: UserRegister, session: AsyncSession = Depends(get_db_session)):
    """Registers a new user (RIDER or DRIVER)."""
    try:
        new_user = await graph_service.register_user(
            session, user.name, user.phone, user.password, user.role
        )
        return new_user
    except RuntimeError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"Error in /register: {e}")
        raise HTTPException(status_code=500, detail="Internal server error during registration.")

@router.post("/login", response_model=UserResponse)
async def login(credentials: UserLogin, session: AsyncSession = Depends(get_db_session)):
    """Logs in an existing user."""
    try:
        user = await graph_service.login_user(
            session, credentials.phone, credentials.password
        )
        if not user:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid phone or password.")
        return user
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in /login: {e}")
        raise HTTPException(status_code=500, detail="Internal server error during login.")


# --- RIDE ROUTES ---

@router.post("/create-ride", status_code=status.HTTP_201_CREATED, response_model=RideResponse)
async def create_ride(
    ride: RideCreate,
    x_user_id: Optional[str] = Header(None),
    session: AsyncSession = Depends(get_db_session)
):
    """Offers a ride commute (Driver authentication required)."""
    if not x_user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authorization header X-User-Id is missing.")
    try:
        new_ride = await graph_service.create_ride_node(
            session, x_user_id, ride.start, ride.end, ride.time, ride.available_seats
        )
        return new_ride
    except RuntimeError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"Error in /create-ride: {e}")
        raise HTTPException(status_code=500, detail="Failed to create ride offer.")

@router.get("/find-rides", response_model=List[MatchedRideResponse])
async def find_rides(
    start: str = Query(...),
    end: str = Query(...),
    x_user_id: Optional[str] = Header(None),
    session: AsyncSession = Depends(get_db_session)
):
    """
    Rider searches matching commutes. 
    Enforces privacy by masking driver's phone unless booking is CONFIRMED or current user is the driver.
    """
    if not x_user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authorization header X-User-Id is missing.")
    try:
        rides = await graph_service.query_matching_rides(session, start, end, x_user_id)
        
        # Privacy validation
        for ride in rides:
            is_driver = ride["driver_id"] == x_user_id
            is_confirmed = ride["booking_status"] == "CONFIRMED"
            if not (is_driver or is_confirmed):
                ride["driver_phone"] = mask_phone(ride["driver_phone"])
                
        return rides
    except Exception as e:
        logger.error(f"Error in /find-rides: {e}")
        raise HTTPException(status_code=503, detail=f"Database lookup failed: {str(e)}")

@router.get("/ride/{ride_id}", response_model=RideDetailsResponse)
async def ride_details(
    ride_id: str,
    x_user_id: Optional[str] = Header(None),
    session: AsyncSession = Depends(get_db_session)
):
    """Retrieves full ride context. Masks phone number according to booking status privacy rules."""
    if not x_user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authorization header X-User-Id is missing.")
    try:
        ride = await graph_service.get_ride_details(session, ride_id, x_user_id)
        
        # Expose phone only to driver or confirmed riders
        if not ride["is_authorized"]:
            ride["driver_phone"] = mask_phone(ride["driver_phone"])
            
        return ride
    except RuntimeError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        logger.error(f"Error in /ride/{ride_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch ride details.")


# --- BOOKING ROUTES ---

@router.post("/book-ride", status_code=status.HTTP_201_CREATED)
async def book_ride(
    booking: BookingCreate,
    x_user_id: Optional[str] = Header(None),
    session: AsyncSession = Depends(get_db_session)
):
    """Creates a PENDING booking request for a ride."""
    if not x_user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authorization header X-User-Id is missing.")
    try:
        new_booking = await graph_service.create_booking_node(session, booking.ride_id, x_user_id)
        # Notify both users via WebSocket if details are available
        try:
            booking_id = new_booking["booking_id"]
            details = await graph_service.get_booking_details(session, booking_id)
            if details:
                # Notify Rider
                await manager.send_personal_message({
                    "type": "BOOKING_REQUESTED",
                    "message": f"Your request to book the ride with {details['driver_name']} from {details['ride_start']} to {details['ride_end']} is pending.",
                    "booking_id": booking_id,
                    "ride_id": details["ride_id"],
                    "status": "PENDING"
                }, x_user_id)
                # Notify Driver
                await manager.send_personal_message({
                    "type": "NEW_REQUEST",
                    "message": f"New ride request from {details['rider_name']} for your ride on {details['ride_time']} from {details['ride_start']} to {details['ride_end']}.",
                    "booking_id": booking_id,
                    "ride_id": details["ride_id"],
                    "status": "PENDING"
                }, details["driver_id"])

                # Log simulated SMS message database nodes
                rider_msg = f"RideBuddy: Your booking request for the ride with {details['driver_name']} from {details['ride_start']} to {details['ride_end']} on {details['ride_time']} is pending."
                driver_msg = f"RideBuddy: New ride request from {details['rider_name']} for your ride on {details['ride_time']} from {details['ride_start']} to {details['ride_end']}. Respond on RideBuddy."

                await graph_service.create_message_node(session, "RideBuddy", details['rider_phone'], rider_msg)
                await graph_service.create_message_node(session, "RideBuddy", details['driver_phone'], driver_msg)

                logger.info(f"MOCK SMS SENT TO {details['rider_phone']}: {rider_msg}")
                logger.info(f"MOCK SMS SENT TO {details['driver_phone']}: {driver_msg}")
        except Exception as ws_err:
            logger.error(f"Failed to send booking WebSocket notification: {ws_err}")
            
        return new_booking
    except RuntimeError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"Error in /book-ride: {e}")
        raise HTTPException(status_code=500, detail="Failed to request ride booking.")

@router.get("/bookings", response_model=List[BookingResponse])
async def get_bookings(
    x_user_id: Optional[str] = Header(None),
    session: AsyncSession = Depends(get_db_session)
):
    """Retrieves the bookings list for a rider."""
    if not x_user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authorization header X-User-Id is missing.")
    try:
        bookings = await graph_service.get_rider_bookings(session, x_user_id)
        # Apply privacy logic
        for b in bookings:
            is_confirmed = b["booking_status"] == "CONFIRMED"
            if not is_confirmed:
                b["driver_phone"] = mask_phone(b["driver_phone"])
        return bookings
    except Exception as e:
        logger.error(f"Error in GET /bookings: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve bookings.")

@router.get("/driver/bookings", response_model=List[BookingResponse])
async def get_driver_bookings(
    x_user_id: Optional[str] = Header(None),
    session: AsyncSession = Depends(get_db_session)
):
    """Retrieves incoming booking requests for rides offered by a driver."""
    if not x_user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authorization header X-User-Id is missing.")
    try:
        bookings = await graph_service.get_driver_booking_requests(session, x_user_id)
        # Apply privacy logic (driver gets to see rider contact only after confirmation)
        for b in bookings:
            is_confirmed = b["booking_status"] == "CONFIRMED"
            if not is_confirmed:
                b["rider_phone"] = mask_phone(b["rider_phone"])
        return bookings
    except Exception as e:
        logger.error(f"Error in GET /driver/bookings: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve booking requests.")

@router.post("/bookings/{booking_id}/respond")
async def respond_booking(
    booking_id: str,
    response: BookingRespond,
    x_user_id: Optional[str] = Header(None),
    session: AsyncSession = Depends(get_db_session)
):
    """Allows driver to ACCEPT or REJECT booking request."""
    if not x_user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authorization header X-User-Id is missing.")
    try:
        res = await graph_service.respond_to_booking(
            session, booking_id, x_user_id, response.action
        )
        # Notify both users via WebSocket if details are available
        try:
            details = await graph_service.get_booking_details(session, booking_id)
            if details:
                status_upper = details["booking_status"].upper() # CONFIRMED or REJECTED
                if status_upper == "CONFIRMED":
                    # Notify Rider - include driver contact details
                    await manager.send_personal_message({
                        "type": "BOOKING_CONFIRMED",
                        "message": f"Ride confirmed! {details['driver_name']} has accepted your booking request.",
                        "booking_id": booking_id,
                        "ride_id": details["ride_id"],
                        "status": "CONFIRMED",
                        "contact_name": details["driver_name"],
                        "contact_phone": details["driver_phone"]
                    }, details["rider_id"])
                    # Notify Driver - include rider contact details
                    await manager.send_personal_message({
                        "type": "BOOKING_CONFIRMED",
                        "message": f"Booking confirmed! You have accepted {details['rider_name']}'s request.",
                        "booking_id": booking_id,
                        "ride_id": details["ride_id"],
                        "status": "CONFIRMED",
                        "contact_name": details["rider_name"],
                        "contact_phone": details["rider_phone"]
                    }, details["driver_id"])

                    # Log simulated SMS message database nodes
                    rider_msg = f"RideBuddy: Booking confirmed! {details['driver_name']} has accepted your booking request. Driver contact: {details['driver_phone']}."
                    driver_msg = f"RideBuddy: Booking confirmed! You accepted {details['rider_name']}'s request. Rider contact: {details['rider_phone']}."

                    await graph_service.create_message_node(session, "RideBuddy", details['rider_phone'], rider_msg)
                    await graph_service.create_message_node(session, "RideBuddy", details['driver_phone'], driver_msg)

                    logger.info(f"MOCK SMS SENT TO {details['rider_phone']}: {rider_msg}")
                    logger.info(f"MOCK SMS SENT TO {details['driver_phone']}: {driver_msg}")
                elif status_upper == "REJECTED":
                    # Notify Rider
                    await manager.send_personal_message({
                        "type": "BOOKING_REJECTED",
                        "message": f"Booking request for ride with {details['driver_name']} was rejected.",
                        "booking_id": booking_id,
                        "ride_id": details["ride_id"],
                        "status": "REJECTED"
                    }, details["rider_id"])

                    # Log simulated SMS message database nodes
                    rider_msg = f"RideBuddy: Booking request for ride with {details['driver_name']} from {details['ride_start']} to {details['ride_end']} was rejected."
                    await graph_service.create_message_node(session, "RideBuddy", details['rider_phone'], rider_msg)
                    logger.info(f"MOCK SMS SENT TO {details['rider_phone']}: {rider_msg}")
        except Exception as ws_err:
            logger.error(f"Failed to send booking response WebSocket notification: {ws_err}")
            
        return res
    except RuntimeError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"Error in respond_booking: {e}")
        raise HTTPException(status_code=500, detail="Failed to respond to booking request.")


# --- PATHS AND GENERAL ---

@router.get("/routes", response_model=List[List[str]])
async def get_routes(
    start: str = Query(...),
    end: str = Query(...),
    session: AsyncSession = Depends(get_db_session)
):
    """Traverses routes list using CONNECTED_TO*2..4 relationships (Multi-hop path)."""
    try:
        routes = await graph_service.query_multi_hop_routes(session, start, end)
        return routes
    except Exception as e:
        logger.error(f"Error in /routes: {e}")
        raise HTTPException(status_code=503, detail=f"Database path query failed: {str(e)}")

@router.get("/locations", response_model=List[LocationResponse])
async def get_locations(session: AsyncSession = Depends(get_db_session)):
    """Fetches all locations with coordinates (lat/lng) in the graph database."""
    try:
        locations = await graph_service.get_all_locations(session)
        return locations
    except Exception as e:
        logger.error(f"Error in /locations: {e}")
        raise HTTPException(status_code=503, detail=f"Failed to fetch locations: {str(e)}")

@router.get("/users", response_model=List[UserResponse])
async def get_users(session: AsyncSession = Depends(get_db_session)):
    """Fetches all registered users (for developer diagnostics/selection lists)."""
    try:
        users = await graph_service.get_all_users(session)
        return users
    except Exception as e:
        logger.error(f"Error in /users: {e}")
        raise HTTPException(status_code=503, detail=f"Failed to fetch users: {str(e)}")

@router.get("/messages")
async def get_messages(
    x_user_id: Optional[str] = Header(None),
    session: AsyncSession = Depends(get_db_session)
):
    """Retrieves simulated SMS messages for the currently logged in user's phone number."""
    if not x_user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authorization header X-User-Id is missing.")
    try:
        phone = await graph_service.get_user_phone(session, x_user_id)
        if not phone:
            raise HTTPException(status_code=404, detail="User profile not found.")
        messages = await graph_service.get_user_messages(session, phone)
        return messages
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in GET /messages: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch simulated messages.")
