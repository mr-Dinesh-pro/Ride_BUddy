import os
import logging
from neo4j import GraphDatabase
from dotenv import load_dotenv
from app.auth.password import hash_password

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s]: %(message)s")
logger = logging.getLogger("seed")

# Load environment variables
current_dir = os.path.dirname(os.path.abspath(__file__))
dotenv_path = os.path.join(current_dir, ".env")
load_dotenv(dotenv_path)

URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
USER = os.getenv("NEO4J_USER", "neo4j")
PASSWORD = os.getenv("NEO4J_PASSWORD", "password123")

def seed_database():
    logger.info(f"Connecting to database at {URI}...")
    try:
        driver = GraphDatabase.driver(URI, auth=(USER, PASSWORD))
        with driver.session() as session:
            session.run("RETURN 1")
    except Exception as e:
        logger.error(f"Failed to connect to Neo4j/CognoDB: {e}")
        return

    with driver.session() as session:
        # 1. Clean Database
        logger.info("Cleaning existing database...")
        session.run("MATCH (n) DETACH DELETE n")

        # 2. Seed Locations with Coordinates
        logger.info("Seeding 30 Hyderabad locations...")
        locations = {
            "Miyapur": (17.4968, 78.3614),
            "Kukatpally": (17.4875, 78.3953),
            "Moosapet": (17.4690, 78.4190),
            "Ameerpet": (17.4374, 78.4482),
            "SR Nagar": (17.4429, 78.4414),
            "Begumpet": (17.4448, 78.4651),
            "Punjagutta": (17.4265, 78.4531),
            "Somajiguda": (17.4263, 78.4593),
            "Hitech City": (17.4483, 78.3741),
            "Madhapur": (17.4485, 78.3908),
            "Jubilee Hills": (17.4300, 78.4000),
            "Banjara Hills": (17.4165, 78.4200),
            "Gachibowli": (17.4401, 78.3489),
            "Kondapur": (17.4699, 78.3578),
            "Nanakramguda": (17.4172, 78.3473),
            "Financial District": (17.4180, 78.3375),
            "Manikonda": (17.4042, 78.3846),
            "Mehdipatnam": (17.3916, 78.4430),
            "Tolichowki": (17.3980, 78.4162),
            "Secunderabad": (17.4399, 78.4983),
            "Uppal": (17.4022, 78.5601),
            "LB Nagar": (17.3460, 78.5510),
            "Dilsukhnagar": (17.3688, 78.5247),
            "Kothapet": (17.3715, 78.5350),
            "Habsiguda": (17.4071, 78.5312),
            "Charminar": (17.3616, 78.4747),
            "Koti": (17.3824, 78.4842),
            "Tarnaka": (17.4277, 78.5385),
            "Yusufguda": (17.4367, 78.4239),
            "Khairatabad": (17.4124, 78.4608)
        }

        # Create Location nodes
        for name, coords in locations.items():
            session.run("""
                CREATE (:Location {
                    name: $name,
                    latitude: $lat,
                    longitude: $lng
                })
            """, name=name, lat=coords[0], lng=coords[1])

        # 3. Seed Connections (CONNECTED_TO Relationships)
        logger.info("Seeding transit network corridors (bidirectional)...")
        corridors = [
            ["Miyapur", "Kukatpally", "Moosapet", "Ameerpet", "SR Nagar", "Yusufguda", "Jubilee Hills", "Madhapur", "Hitech City", "Gachibowli", "Nanakramguda", "Financial District"],
            ["Secunderabad", "Begumpet", "Somajiguda", "Punjagutta", "Khairatabad", "Banjara Hills", "Jubilee Hills", "Madhapur", "Hitech City", "Gachibowli", "Nanakramguda", "Financial District"],
            ["Uppal", "Habsiguda", "Tarnaka", "Secunderabad", "Begumpet", "Ameerpet", "Yusufguda", "Madhapur", "Kondapur", "Gachibowli"],
            ["LB Nagar", "Kothapet", "Dilsukhnagar", "Koti", "Charminar", "Mehdipatnam", "Tolichowki", "Manikonda", "Gachibowli", "Financial District"]
        ]

        # Generate unique bidirectional connections
        unique_connections = set()
        for corr in corridors:
            for i in range(len(corr) - 1):
                loc1 = corr[i]
                loc2 = corr[i+1]
                pair = (min(loc1, loc2), max(loc1, loc2))
                unique_connections.add(pair)

        # Additional shortcut connections
        shortcuts = [
            ("Kondapur", "Miyapur"),
            ("Kondapur", "Madhapur"),
            ("Kondapur", "Hitech City"),
            ("Manikonda", "Gachibowli"),
            ("Tolichowki", "Mehdipatnam"),
            ("Banjara Hills", "Punjagutta"),
            ("Somajiguda", "Begumpet"),
            ("SR Nagar", "Ameerpet"),
            ("Ameerpet", "Punjagutta"),
            ("Punjagutta", "Banjara Hills"),
            ("Koti", "Dilsukhnagar"),
            ("Charminar", "Koti")
        ]
        for start, end in shortcuts:
            pair = (min(start, end), max(start, end))
            unique_connections.add(pair)

        # Create relationships in database (both directions)
        for loc1, loc2 in unique_connections:
            session.run("""
                MATCH (a:Location {name: $loc1})
                MATCH (b:Location {name: $loc2})
                MERGE (a)-[:CONNECTED_TO]->(b)
                MERGE (b)-[:CONNECTED_TO]->(a)
            """, loc1=loc1, loc2=loc2)

        # 4. Seed 400 Users (150 Drivers, 250 Riders)
        logger.info("Generating 400 Indian user accounts...")
        first_names = [
            "Amit", "Rahul", "Srinivas", "Ravi", "Sneha", "Sai", "Deepika", "Harish", "Karthik", "Priya",
            "Vikram", "Anjali", "Mahesh", "Swetha", "Vinay", "Kavitha", "Ananya", "Divya", "Manish", "Sandhya",
            "Pranay", "Shruti", "Kalyan", "Pooja", "Naresh", "Sunil", "Rajesh", "Suresh", "Ramesh", "Kiran",
            "Vijay", "Anil", "Arun", "Sanjay", "Ganesh", "Mohan", "Krishna", "Prasad", "Raju", "Venkatesh"
        ]
        last_names = [
            "Reddy", "Rao", "Sharma", "Verma", "Kumar", "Singh", "Patel", "Joshi", "Naidu", "Choudhary",
            "Gupta", "Mishra", "Pandey", "Yadav", "Tripathi", "Goud", "Murthy", "Babu", "Javed", "Iyer"
        ]

        # Precompute hashed password "password123" to make seeding extremely fast
        hashed_password = hash_password("password123")

        # Generate 400 unique users
        users_to_seed = []
        name_index = 0
        while len(users_to_seed) < 400:
            fn = first_names[name_index % len(first_names)]
            ln = last_names[(name_index // len(first_names)) % len(last_names)]
            name = f"{fn} {ln}"
            
            # Simple unique phone offset
            phone = f"+9198765{10000 + len(users_to_seed)}"
            
            role = "DRIVER" if len(users_to_seed) < 150 else "RIDER"
            user_id = f"driver-{len(users_to_seed) + 1}" if role == "DRIVER" else f"rider-{len(users_to_seed) - 149}"
            
            users_to_seed.append({
                "id": user_id,
                "name": name,
                "phone": phone,
                "role": role
            })
            name_index += 1

        # Seed users in a fast batch
        session.run("""
            UNWIND $users AS u
            CREATE (:User {
                id: u.id,
                name: u.name,
                phone: u.phone,
                password: $password,
                role: u.role
            })
        """, users=users_to_seed, password=hashed_password)

        # 5. Seed 200 Rides (100 Morning Commutes, 100 Evening Commutes)
        logger.info("Seeding 200 morning/evening rides...")
        residential = ["Miyapur", "Kukatpally", "Secunderabad", "Uppal", "LB Nagar", "Dilsukhnagar", "Kothapet", "Habsiguda", "Moosapet", "Begumpet"]
        office_hubs = ["Hitech City", "Madhapur", "Gachibowli", "Financial District", "Nanakramguda", "Kondapur"]
        morning_times = ["07:30", "08:00", "08:15", "08:30", "08:45", "09:00", "09:15", "09:30"]
        evening_times = ["17:00", "17:30", "18:00", "18:30", "19:00", "19:30"]

        rides_to_seed = []
        for i in range(200):
            ride_id = f"ride-{i+1}"
            driver_id = f"driver-{(i % 150) + 1}"
            
            if i < 100:
                # Morning: Residential -> Office
                start = residential[i % len(residential)]
                end = office_hubs[(i * 3) % len(office_hubs)]
                time = morning_times[i % len(morning_times)]
            else:
                # Evening: Office -> Residential
                start = office_hubs[i % len(office_hubs)]
                end = residential[(i * 3) % len(residential)]
                time = evening_times[i % len(evening_times)]
            
            seats = (i % 4) + 1  # 1 to 4 seats
            
            rides_to_seed.append({
                "ride_id": ride_id,
                "driver_id": driver_id,
                "start": start,
                "end": end,
                "time": time,
                "seats": seats
            })

        # Insert rides
        for r in rides_to_seed:
            session.run("""
                MATCH (d:User {id: $driver_id})
                MATCH (s:Location {name: $start})
                MATCH (e:Location {name: $end})
                CREATE (ride:Ride {
                    id: $ride_id,
                    departure_time: $time,
                    available_seats: toInteger($seats),
                    status: "ACTIVE"
                })
                CREATE (d)-[:OFFERS]->(ride)
                CREATE (ride)-[:STARTS_AT]->(s)
                CREATE (ride)-[:ENDS_AT]->(e)
            """, driver_id=r["driver_id"], start=r["start"], end=r["end"], ride_id=r["ride_id"], time=r["time"], seats=r["seats"])

        # 6. Seed 150 Bookings (60 Confirmed, 60 Pending, 30 Rejected)
        logger.info("Seeding 150 bookings in varying states...")
        bookings_created = 0
        trial_index = 0
        
        while bookings_created < 150:
            rider_num = (trial_index % 250) + 1
            rider_id = f"rider-{rider_num}"
            
            # Select a ride
            ride_num = ((trial_index * 7) % 200) + 1
            ride_id = f"ride-{ride_num}"
            
            # Decide booking status
            if bookings_created < 60:
                status = "CONFIRMED"
            elif bookings_created < 120:
                status = "PENDING"
            else:
                status = "REJECTED"
                
            # Verify driver ownership and duplicate check
            check = session.run("""
                MATCH (ride:Ride {id: $ride_id})<-[:OFFERS]-(driver:User)
                OPTIONAL MATCH (rider:User {id: $rider_id})-[:BOOKED]->(b:Booking)-[:FOR_RIDE]->(ride)
                RETURN driver.id = $rider_id AS is_driver, b IS NOT NULL AS exists, ride.available_seats AS seats
            """, ride_id=ride_id, rider_id=rider_id)
            
            record = check.single()
            if record and not record["is_driver"] and not record["exists"] and (status != "CONFIRMED" or record["seats"] > 0):
                booking_id = f"book-seed-{bookings_created+1}"
                
                # Create Booking
                session.run("""
                    CREATE (b:Booking {
                        id: $booking_id,
                        status: $status,
                        created_at: timestamp()
                    })
                    WITH b
                    MATCH (rider:User {id: $rider_id})
                    MATCH (ride:Ride {id: $ride_id})
                    CREATE (rider)-[:BOOKED]->(b)
                    CREATE (b)-[:FOR_RIDE]->(ride)
                    CREATE (rider)-[:REQUESTED]->(ride)
                """, booking_id=booking_id, status=status, rider_id=rider_id, ride_id=ride_id)
                
                # If confirmed, decrement seat
                if status == "CONFIRMED":
                    session.run("""
                        MATCH (r:Ride {id: $ride_id})
                        SET r.available_seats = r.available_seats - 1
                    """, ride_id=ride_id)
                    
                bookings_created += 1
            
            trial_index += 1

        logger.info(f"Database seeding completed successfully! {bookings_created} bookings created.")
        
        # Verify Relationship counts
        count_res = session.run("MATCH ()-[r]->() RETURN count(r) AS total_relationships")
        logger.info(f"Total graph relationships created: {count_res.single()['total_relationships']}")
        
    driver.close()

if __name__ == "__main__":
    seed_database()
