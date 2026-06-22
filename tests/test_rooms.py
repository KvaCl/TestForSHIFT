from app.main import RoomCreate, TimeSlot


def test_create_room_as_admin(client, admin_token):

    room_data = RoomCreate(
        name="Room A",
        capacity=10,
        time_slots=[
            TimeSlot(start="09:00:00", end="10:00:00"),
            TimeSlot(start="10:00:00", end="11:00:00")
        ]
    )
    response = client.post(
        "/rooms",
        json=room_data.model_dump(mode='json'),
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert response.status_code in [200, 201]
    data = response.json()
    assert data["name"] == "Room A"
    assert data["capacity"] == 10
    assert len(data["time_slots"]) == 2


def test_create_room_as_user_forbidden(client, user_token):

    room_data = RoomCreate(
        name="Room",
        capacity=5,
        time_slots=[TimeSlot(start="09:00:00", end="10:00:00")]
    )
    response = client.post(
        "/rooms",
        json=room_data.model_dump(mode='json'),
        headers={"Authorization": f"Bearer {user_token}"}
    )
    assert response.status_code == 403


def test_create_room_without_token(client):
    room_data = RoomCreate(
        name="Room",
        capacity=5,
        time_slots=[TimeSlot(start="09:00:00", end="10:00:00")]
    )
    response = client.post(
        "/rooms",
        json=room_data.model_dump(mode='json')
    )
    assert response.status_code == 401


def test_get_all_rooms(client, room):

    response = client.get("/rooms")
    assert response.status_code == 200
    rooms = response.json()
    assert isinstance(rooms, list)
    assert len(rooms) >= 1


def test_get_room_by_id(client, room):

    room_id = room["id"]
    response = client.get(f"/rooms/{room_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == room_id
    assert data["name"] == "Test Room"


def test_get_nonexistent_room(client):
    response = client.get("/rooms/9999")
    assert response.status_code == 404


def test_get_room_slots(client, room):
    room_id = room["id"]
    response = client.get(f"/rooms/{room_id}/slots")
    assert response.status_code == 200
    slots = response.json()
    assert len(slots) == 2


def test_get_room_slots_with_availability(client, room):
    room_id = room["id"]
    response = client.get(f"/rooms/{room_id}/slots?booking_date=2026-06-20")
    assert response.status_code == 200
    slots = response.json()
    assert len(slots) == 2
    assert all(s["is_available"] for s in slots)


def test_delete_room_as_admin(client, admin_token, room):
    room_id = room["id"]
    response = client.delete(
        f"/rooms/{room_id}",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert response.status_code in [200, 204]

    get_response = client.get(f"/rooms/{room_id}")
    assert get_response.status_code == 404


def test_delete_room_as_user_forbidden(client, user_token, room):
    room_id = room["id"]
    response = client.delete(
        f"/rooms/{room_id}",
        headers={"Authorization": f"Bearer {user_token}"}
    )
    assert response.status_code == 403


def test_delete_nonexistent_room(client, admin_token):
    response = client.delete(
        "/rooms/9999",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert response.status_code == 404