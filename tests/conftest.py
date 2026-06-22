import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.database import Base,get_db

from app.main import app,UserCreate,RoomCreate,TimeSlot


DATABASE_URL = 'sqlite:///test.db'
engine=create_engine(DATABASE_URL)
TestingSessionLocal=sessionmaker(bind=engine)


@pytest.fixture(scope='function')
def db_session():
    Base.metadata.create_all(engine)
    db=TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(engine)

@pytest.fixture(scope='function')
def client(db_session):
    def override_get_db():
        try:
            yield db_session
        finally:
            pass
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()




@pytest.fixture
def admin_token(client):
    admin_data = UserCreate(
        username="admin",
        email="admin@test.com",
        password="admin123",
        is_admin=True
    )
    response = client.post("/register", json=admin_data.model_dump())
    assert response.status_code in [200, 201]

    login_response = client.post("/login", data={
        "username": admin_data.username,
        "password": admin_data.password
    })
    return login_response.json()["access_token"]


@pytest.fixture
def user_token(client):
    user_data = UserCreate(
        username="john",
        email="john@test.com",
        password="secret123",
        is_admin=False
    )
    response = client.post("/register", json=user_data.model_dump())
    assert response.status_code in [200, 201]

    login_response = client.post("/login", data={
        "username": user_data.username,
        "password": user_data.password
    })
    return login_response.json()["access_token"]

@pytest.fixture
def user_token(client):
    user_data = UserCreate(
        username="john",
        email="john@test.com",
        password="secret123",
        is_admin=False
    )
    response = client.post("/register", json=user_data.model_dump())
    assert response.status_code in [200, 201]

    login_response = client.post("/login", data={
        "username": user_data.username,
        "password": user_data.password
    })
    return login_response.json()["access_token"]


@pytest.fixture
def room(client, admin_token):

    room_data = RoomCreate(
        name="Test Room",
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
    return response.json()