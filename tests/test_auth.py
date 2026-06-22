from app.main import UserCreate

def test_register_user(client):
    user_data=UserCreate(username="newuser",
                    email="new@test.com",
                    password="123")
    response=client.post("/register",json=user_data.model_dump())
    assert response.status_code == 201
    data=response.json()
    assert data['username'] == "newuser"
    assert data['email'] == "new@test.com"
    assert data['is_admin'] is False
    assert 'id' in data

def test_register_duplicate_username(client):
    user_data = UserCreate(username="newuser",
                           email="new@test.com",
                           password="123")
    user_data2 = UserCreate(username="newuser",
                           email="new2@test.com",
                           password="123")
    response = client.post("/register", json=user_data.model_dump())
    response = client.post("/register", json=user_data2.model_dump())
    assert response.status_code == 400
    assert response.json() == {'detail':'Username or email already registered'}

def test_register_duplicate_email(client):
    user_data = UserCreate(username="newuser",
                           email="new@test.com",
                           password="123")
    user_data2 = UserCreate(username="newuser2",
                           email="new@test.com",
                           password="123")
    response = client.post("/register", json=user_data.model_dump())
    response = client.post("/register", json=user_data2.model_dump())
    assert response.status_code == 400
    assert response.json() == {'detail':'Username or email already registered'}

def test_login_user(client):
    user_data = UserCreate(username="newuser",
                           email="new@test.com",
                           password="123")
    client.post('register', json=user_data.model_dump())
    response = client.post('/login', data={'username': 'newuser', 'password': '123'})
    assert response.status_code == 200
    data=response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"

def test_login_wrong_password(client):
    user_data = UserCreate(username="newuser",
                           email="new@test.com",
                           password="123")
    client.post('register', json=user_data.model_dump())
    response = client.post('/login', data={'username': 'newuser', 'password': '1234'})
    assert response.status_code == 401

def test_protected_endpoint_with_invalid_token(client):
    response = client.get(
        "/bookings",
        headers={"Authorization": "XXXXXXXXXXXXXXXX"}
    )
    assert response.status_code == 401

def test_protected_endpoint_without_token(client):
    response = client.get("/bookings")
    assert response.status_code == 401