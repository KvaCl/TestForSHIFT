from app.main import BookingCreate


def test_create_booking(client, user_token, room):
    booking_data = BookingCreate(
        room_id=room["id"],
        time_slot_index=0,
        booking_date="2026-06-20"
    )
    response = client.post(
        "/bookings",
        json=booking_data.model_dump(mode='json'),
        headers={"Authorization": f"Bearer {user_token}"}
    )
    assert response.status_code in [200, 201]
    data = response.json()
    assert data["room_id"] == booking_data.room_id
    assert data["time_slot_index"] == 0
    assert data["booking_date"] == "2026-06-20"
    assert "id" in data


def test_create_booking_without_token(client, room):
    booking_data = BookingCreate(
        room_id=room["id"],
        time_slot_index=0,
        booking_date="2026-06-20"
    )
    response = client.post(
        "/bookings",
        json=booking_data.model_dump(mode='json')
    )
    assert response.status_code == 401


def test_double_booking_forbidden(client, user_token, room):
    booking_data = BookingCreate(
        room_id=room["id"],
        time_slot_index=0,
        booking_date="2026-06-20"
    )
    response1 = client.post(
        "/bookings",
        json=booking_data.model_dump(mode='json'),
        headers={"Authorization": f"Bearer {user_token}"}
    )
    assert response1.status_code in [200, 201]


    response2 = client.post(
        "/bookings",
        json=booking_data.model_dump(mode='json'),
        headers={"Authorization": f"Bearer {user_token}"}
    )
    assert response2.status_code == 400


def test_booking_nonexistent_room(client, user_token):
    booking_data = BookingCreate(
        room_id=9999,
        time_slot_index=0,
        booking_date="2026-06-20"
    )
    response = client.post(
        "/bookings",
        json=booking_data.model_dump(mode='json'),
        headers={"Authorization": f"Bearer {user_token}"}
    )
    assert response.status_code == 404


def test_cancel_own_booking(client, user_token, room):
    booking_data = BookingCreate(
        room_id=room["id"],
        time_slot_index=0,
        booking_date="2026-06-20"
    )
    create_response = client.post(
        "/bookings",
        json=booking_data.model_dump(mode='json'),
        headers={"Authorization": f"Bearer {user_token}"}
    )
    booking_id = create_response.json()["id"]

    delete_response = client.delete(
        f"/bookings/{booking_id}",
        headers={"Authorization": f"Bearer {user_token}"}
    )
    assert delete_response.status_code in [200, 204]


def test_user_cannot_cancel_others_booking(client, user_token, admin_token, room):
    booking_data = BookingCreate(
        room_id=room["id"],
        time_slot_index=0,
        booking_date="2026-06-20"
    )

    create_response = client.post(
        "/bookings",
        json=booking_data.model_dump(mode='json'),
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    booking_id = create_response.json()["id"]


    response = client.delete(
        f"/bookings/{booking_id}",
        headers={"Authorization": f"Bearer {user_token}"}
    )
    assert response.status_code == 403


def test_admin_can_cancel_any_booking(client, user_token, admin_token, room):
    booking_data = BookingCreate(
        room_id=room["id"],
        time_slot_index=0,
        booking_date="2026-06-20"
    )


    create_response = client.post(
        "/bookings",
        json=booking_data.model_dump(mode='json'),
        headers={"Authorization": f"Bearer {user_token}"}
    )
    booking_id = create_response.json()["id"]

    response = client.delete(
        f"/bookings/{booking_id}",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert response.status_code in [200, 204]


def test_get_my_bookings(client, user_token, room):
    booking_data = BookingCreate(
        room_id=room["id"],
        time_slot_index=0,
        booking_date="2026-06-20"
    )


    client.post(
        "/bookings",
        json=booking_data.model_dump(mode='json'),
        headers={"Authorization": f"Bearer {user_token}"}
    )

    response = client.get(
        "/bookings",
        headers={"Authorization": f"Bearer {user_token}"}
    )
    assert response.status_code == 200
    bookings = response.json()
    assert len(bookings) >= 1


def test_admin_sees_all_bookings(client, user_token, admin_token, room):
    booking_data = BookingCreate(
        room_id=room["id"],
        time_slot_index=0,
        booking_date="2026-06-20"
    )


    client.post(
        "/bookings",
        json=booking_data.model_dump(mode='json'),
        headers={"Authorization": f"Bearer {user_token}"}
    )


    response = client.get(
        "/bookings",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert response.status_code == 200
    bookings = response.json()
    assert len(bookings) >= 1


def test_availability_shows_booked_slot(client, user_token, room):

    booking_data = BookingCreate(
        room_id=room["id"],
        time_slot_index=0,
        booking_date="2026-06-20"
    )

    client.post(
        "/bookings",
        json=booking_data.model_dump(mode='json'),
        headers={"Authorization": f"Bearer {user_token}"}
    )

    response = client.get(f"/rooms/{room['id']}/slots?booking_date=2026-06-20")
    assert response.status_code == 200
    slots = response.json()
    assert len(slots) == 2
    assert slots[0]["is_available"] is False
    assert slots[1]["is_available"] is True