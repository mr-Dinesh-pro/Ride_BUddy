import pytest
import uuid
from fastapi.testclient import TestClient
from app.main import app

@pytest.fixture(scope="module")
def client():
    """Initializes the FastAPI TestClient within a context manager to run startup/shutdown events."""
    with TestClient(app) as c:
        yield c

# Helper function to generate unique phone numbers to avoid collision
def get_unique_phone():
    return f"+9199{str(uuid.uuid4().int)[:10]}"

def test_database_status(client):
    """Verify that root endpoint returns app status and DB connectivity check."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert data["status"] == "Running"
    assert "database_status" in data

def test_user_authentication(client):
    """Verify user registration, duplicate checking, and login verification."""
    phone = get_unique_phone()
    password = "secretpassword"
    
    # 1. Register Rider
    reg_response = client.post("/register", json={
        "name": "Test Rider",
        "phone": phone,
        "password": password,
        "role": "RIDER"
    })
    assert reg_response.status_code == 201
    rider_data = reg_response.json()
    assert "id" in rider_data
    assert rider_data["name"] == "Test Rider"
    assert rider_data["phone"] == phone
    assert rider_data["role"] == "RIDER"
    
    # 2. Register Duplicate Phone
    dup_response = client.post("/register", json={
        "name": "Another Name",
        "phone": phone,
        "password": "somepassword",
        "role": "RIDER"
    })
    assert dup_response.status_code == 400
    assert "detail" in dup_response.json()
    
    # 3. Login with Correct Password
    login_response = client.post("/login", json={
        "phone": phone,
        "password": password
    })
    assert login_response.status_code == 200
    login_data = login_response.json()
    assert login_data["id"] == rider_data["id"]
    
    # 4. Login with Incorrect Password
    login_wrong = client.post("/login", json={
        "phone": phone,
        "password": "wrongpassword"
    })
    assert login_wrong.status_code == 401

def test_booking_workflow_and_privacy(client):
    """
    Test E2E ride creation, search with phone masking, booking,
    driver acceptance, and unmasking.
    """
    driver_phone = get_unique_phone()
    rider_phone = get_unique_phone()
    
    # 1. Register Driver & Rider
    driver_reg = client.post("/register", json={
        "name": "Test Driver",
        "phone": driver_phone,
        "password": "password123",
        "role": "DRIVER"
    }).json()
    
    rider_reg = client.post("/register", json={
        "name": "Test Rider",
        "phone": rider_phone,
        "password": "password123",
        "role": "RIDER"
    }).json()
    
    driver_id = driver_reg["id"]
    rider_id = rider_reg["id"]
    
    # 2. Create Ride (Driver)
    # Using seeded locations: "Miyapur" and "Gachibowli"
    ride_res = client.post(
        "/create-ride",
        json={
            "start": "Miyapur",
            "end": "Gachibowli",
            "time": "08:30 AM",
            "available_seats": 2
        },
        headers={"X-User-Id": driver_id}
    )
    assert ride_res.status_code == 201
    ride_data = ride_res.json()
    ride_id = ride_data["ride_id"]
    
    # Verify unauthenticated create ride block
    bad_ride = client.post(
        "/create-ride",
        json={
            "start": "Miyapur",
            "end": "Gachibowli",
            "time": "08:30 AM",
            "available_seats": 2
        }
    )
    assert bad_ride.status_code == 401
    
    # 3. Search Ride (Rider) - check masking
    search_res = client.get(
        f"/find-rides?start=Miyapur&end=Gachibowli",
        headers={"X-User-Id": rider_id}
    )
    assert search_res.status_code == 200
    results = search_res.json()
    
    # Find our specific ride
    our_search_ride = next((r for r in results if r["ride_id"] == ride_id), None)
    assert our_search_ride is not None
    # Phone number MUST be masked before booking confirmation
    assert our_search_ride["driver_phone"] != driver_phone
    assert "*" in our_search_ride["driver_phone"]
    
    # Check detail view privacy
    details_before = client.get(f"/ride/{ride_id}", headers={"X-User-Id": rider_id}).json()
    assert details_before["driver_phone"] != driver_phone
    
    # 4. Book Ride (Rider)
    book_res = client.post(
        "/book-ride",
        json={"ride_id": ride_id},
        headers={"X-User-Id": rider_id}
    )
    assert book_res.status_code == 201
    booking_id = book_res.json()["booking_id"]
    
    # Prevent duplicate booking
    dup_book = client.post(
        "/book-ride",
        json={"ride_id": ride_id},
        headers={"X-User-Id": rider_id}
    )
    assert dup_book.status_code == 400
    
    # Prevent driver booking own ride
    own_book = client.post(
        "/book-ride",
        json={"ride_id": ride_id},
        headers={"X-User-Id": driver_id}
    )
    assert own_book.status_code == 400
    
    # 5. Fetch Driver Bookings
    driver_reqs = client.get("/driver/bookings", headers={"X-User-Id": driver_id}).json()
    our_req = next((b for b in driver_reqs if b["booking_id"] == booking_id), None)
    assert our_req is not None
    assert our_req["booking_status"] == "PENDING"
    # Rider phone masked for driver before confirmation
    assert our_req["rider_phone"] != rider_phone
    
    # 6. Accept Booking
    accept_res = client.post(
        f"/bookings/{booking_id}/respond",
        json={"action": "ACCEPT"},
        headers={"X-User-Id": driver_id}
    )
    assert accept_res.status_code == 200
    assert accept_res.json()["status"] == "CONFIRMED"
    
    # 7. Verify Phone Number Unmasked & Seat decremented
    # Fetch details again
    details_after = client.get(f"/ride/{ride_id}", headers={"X-User-Id": rider_id}).json()
    # Phone number MUST be unmasked after booking confirmation!
    assert details_after["driver_phone"] == driver_phone
    assert details_after["available_seats"] == 1 # 2 seats initially, decremented to 1
    
    # Verify booking lists
    rider_bookings = client.get("/bookings", headers={"X-User-Id": rider_id}).json()
    our_rider_b = next((b for b in rider_bookings if b["booking_id"] == booking_id), None)
    assert our_rider_b is not None
    assert our_rider_b["booking_status"] == "CONFIRMED"
    assert our_rider_b["driver_phone"] == driver_phone


def test_duplicate_ride_prevention(client):
    """Verify that posting the exact same ride twice for the same user, route, and time fails."""
    driver_phone = get_unique_phone()
    
    # 1. Register User (role RIDER or DRIVER, role constraints relaxed)
    driver_reg = client.post("/register", json={
        "name": "Rider Posting Ride",
        "phone": driver_phone,
        "password": "password123",
        "role": "RIDER"  # Role RIDER can now post rides!
    }).json()
    driver_id = driver_reg["id"]
    
    # 2. Create Ride (First time)
    ride1 = client.post(
        "/create-ride",
        json={
            "start": "Miyapur",
            "end": "Gachibowli",
            "time": "09:00 AM",
            "available_seats": 3
        },
        headers={"X-User-Id": driver_id}
    )
    assert ride1.status_code == 201
    
    # 3. Create Duplicate Ride (Second time - same details)
    ride2 = client.post(
        "/create-ride",
        json={
            "start": "Miyapur",
            "end": "Gachibowli",
            "time": "09:00 AM",
            "available_seats": 3
        },
        headers={"X-User-Id": driver_id}
    )
    assert ride2.status_code == 400
    assert "duplicate active ride offer already exists" in ride2.json()["detail"]


def test_simulated_messages(client):
    """Verify that simulated messages are created on booking events and retrieved successfully."""
    # 1. Register a driver and a rider
    d_phone = get_unique_phone()
    r_phone = get_unique_phone()
    
    driver = client.post("/register", json={"name": "Drv Msg", "phone": d_phone, "password": "pass", "role": "DRIVER"}).json()
    rider = client.post("/register", json={"name": "Rdr Msg", "phone": r_phone, "password": "pass", "role": "RIDER"}).json()
    
    # 2. Create Ride
    ride = client.post(
        "/create-ride",
        json={"start": "Madhapur", "end": "Gachibowli", "time": "06:00 PM", "available_seats": 2},
        headers={"X-User-Id": driver["id"]}
    ).json()
    
    # 3. Book Ride
    book = client.post(
        "/book-ride",
        json={"ride_id": ride["ride_id"]},
        headers={"X-User-Id": rider["id"]}
    ).json()
    
    # 4. Check Messages for Rider (should have PENDING notification)
    r_messages = client.get("/messages", headers={"X-User-Id": rider["id"]}).json()
    assert len(r_messages) >= 1
    # Check that a message contains "PENDING"
    pending_msg = next((m for m in r_messages if "pending" in m["body"].lower()), None)
    assert pending_msg is not None
    assert pending_msg["to_phone"] == r_phone
    
    # 5. Check Messages for Driver (should have request notification)
    d_messages = client.get("/messages", headers={"X-User-Id": driver["id"]}).json()
    assert len(d_messages) >= 1
    req_msg = next((m for m in d_messages if "new ride request" in m["body"].lower()), None)
    assert req_msg is not None
    assert req_msg["to_phone"] == d_phone
    
    # 6. Respond to booking (Accept)
    accept = client.post(
        f"/bookings/{book['booking_id']}/respond",
        json={"action": "ACCEPT"},
        headers={"X-User-Id": driver["id"]}
    )
    assert accept.status_code == 200
    
    # 7. Check Messages for Rider again (should have CONFIRMED notification)
    r_messages_after = client.get("/messages", headers={"X-User-Id": rider["id"]}).json()
    confirmed_msg = next((m for m in r_messages_after if "confirmed" in m["body"].lower()), None)
    assert confirmed_msg is not None
    assert d_phone in confirmed_msg["body"]  # Exposes driver phone number!
