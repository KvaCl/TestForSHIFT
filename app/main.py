from contextlib import asynccontextmanager
from pydantic import BaseModel
from fastapi import FastAPI, HTTPException,Depends,Query
from fastapi.security import OAuth2PasswordRequestForm
from datetime import time, date
from typing import Optional, List

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.database import engine, Base, get_db
from app.models import Users, RoomDb, TimeSlotDb, BookingDb
from app.auth import (
    get_current_user, hash_password, verify_password,
    create_access_token, require_admin
)




@asynccontextmanager
async def lifespan(_:FastAPI):
    Base.metadata.create_all(bind=engine)
    yield
app = FastAPI(lifespan=lifespan)

# пользователи
class UserCreate(BaseModel):
    username: str
    email: str
    password: str
    is_admin: bool = False

class UserResponse(BaseModel):
    id: str
    username: str
    email: str
    is_admin: bool

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"





#комнаты
class TimeSlot(BaseModel):
    start: time
    end: time



class Room(BaseModel):
    id: int
    name: str
    time_slots: List[TimeSlot]
    capacity: int
class RoomCreate(BaseModel):
    name: str
    time_slots: List[TimeSlot]
    capacity: int

#бронирования
class Booking(BaseModel):
    id: str
    time_slot_index: int
    room_id: int
    booking_date: date
    user_id: str


class BookingResponse(BaseModel):
    time_slot_index: int
    room_id: int
    start_time: time
    end_time: time
    is_available:bool

class BookingCreate(BaseModel):
    room_id: int
    time_slot_index: int
    booking_date: date







@app.get("/")
def read_root():
    return {"Hello": "World"}
#ручки с комнатами
@app.get("/rooms")
def read_all_rooms(db:Session=Depends(get_db))->list[Room]:
    db_rooms=db.scalars(select(RoomDb)).all()
    return [
        Room(
        id=r.id,
        name=r.name,
        capacity=r.capacity,
        time_slots=[TimeSlot(start=s.start_time,end=s.end_time)for s in r.time_slots]
        ) for r in db_rooms
    ]


@app.get("/rooms/{room_id}")
def read_room(room_id: int,db:Session=Depends(get_db))->Room:
    room = db.scalars(select(RoomDb).where(RoomDb.id==room_id)).first()
    if not room:
        raise HTTPException(status_code=404, detail="Room not found")
    return Room(
        id=room.id,
        name=room.name,
        capacity=room.capacity,
        time_slots=[TimeSlot(start=s.start_time,end=s.end_time)for s in room.time_slots]
    )
@app.post("/rooms")
def append_room(payload: RoomCreate,db:Session=Depends(get_db),current_user: Users=Depends(require_admin))->Room:
    room=RoomDb(name=payload.name, capacity=payload.capacity)

    for i,slot in enumerate(payload.time_slots):
        db_slot=TimeSlotDb(

            slot_index=i,
            start_time=slot.start,
            end_time=slot.end,
        )
        room.time_slots.append(db_slot)
    db.add(room)
    db.commit()
    db.refresh(room)
    return Room(
        id=room.id,
        name=room.name,
        capacity=room.capacity,
        time_slots=[TimeSlot(start=s.start_time, end=s.end_time) for s in room.time_slots]
    )

@app.delete("/rooms/{room_id}")
def delete_room(room_id: int,db:Session=Depends(get_db),current_user:Users=Depends(require_admin))->None:
    room=db.scalars(select(RoomDb).where(RoomDb.id==room_id)).first()
    if not room:
        raise HTTPException(status_code=404, detail="Room not found")
    db.delete(room)
    db.commit()
    return None


@app.get("/rooms/{room_id}/slots")
def read_room_slots(
        room_id: int,
        booking_date: Optional[date] = Query(default=None, description="Дата для проверки доступности"),
        db: Session = Depends(get_db)
):

    room = db.scalars(select(RoomDb).where(RoomDb.id == room_id)).first()
    if not room:
        raise HTTPException(status_code=404, detail="Room not found")


    if booking_date is None:
        return [
            TimeSlot(start=s.start_time, end=s.end_time)
            for s in room.time_slots
        ]

    booked_slots = set(db.scalars(
        select(BookingDb.time_slot_index).where(
            BookingDb.room_id == room_id,
            BookingDb.booking_date == booking_date
        )
    ).all())

    return [
        BookingResponse(
            time_slot_index=i,
            room_id=room_id,
            start_time=slot.start_time,
            end_time=slot.end_time,
            is_available=(i not in booked_slots)
        )
        for i, slot in enumerate(room.time_slots)
    ]


@app.post("/bookings")
def create_booking(payload:BookingCreate,db:Session=Depends(get_db),current_user:Users=Depends(get_current_user))->Booking:
    room=db.scalars(select(RoomDb).where(RoomDb.id==payload.room_id)).first()
    if not room:
        raise HTTPException(status_code=404, detail="Room not found")
    available=db.scalars(select(BookingDb).where(BookingDb.room_id==payload.room_id,
                                               BookingDb.time_slot_index==payload.time_slot_index,
                                               BookingDb.booking_date==payload.booking_date)).first()
    if available:
        raise HTTPException(status_code=400, detail="Timeslot not available")
    booking=BookingDb(room_id=payload.room_id,
                      time_slot_index=payload.time_slot_index,
                      booking_date=payload.booking_date,
                      user_id=current_user.id)
    db.add(booking)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail=f"Room {payload.room_id} don't have {payload.time_slot_index} slot")
    db.refresh(booking)

    return Booking(id=booking.id,
                   time_slot_index=booking.time_slot_index,
                   room_id=booking.room_id,
                   booking_date=booking.booking_date,
                   user_id=booking.user_id)

@app.get('/bookings')
def get_bookings(db:Session=Depends(get_db),current_user:Users=Depends(get_current_user))->List[Booking]:
    if current_user.is_admin:
        bookings = db.scalars(select(BookingDb)).all()
    else:
        bookings = db.scalars(
            select(BookingDb).where(BookingDb.user_id == current_user.id)
        ).all()
    return [Booking(id=b.id,
                    time_slot_index=b.time_slot_index,
                    room_id=b.room_id,
                    booking_date=b.booking_date,
                    user_id=b.user_id) for b in bookings]

@app.delete('/bookings/{booking_id}')
def delete_booking(booking_id: str, db:Session=Depends(get_db),current_user:Users=Depends(get_current_user)):
    booking=db.scalars(select(BookingDb).where(BookingDb.id==booking_id)).first()
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")
    if booking.user_id != current_user.id and not current_user.is_admin:
        raise HTTPException(status_code=403, detail="You are not allowed to delete this booking")
    db.delete(booking)
    db.commit()
    return None










@app.post("/register",status_code=201)
def register(payload: UserCreate, db: Session = Depends(get_db))->UserResponse:

    existing = db.scalars(
        select(Users).where(
            (Users.username == payload.username) |
            (Users.email == payload.email)
        )
    ).first()

    if existing:
        raise HTTPException(
            status_code=400,
            detail="Username or email already registered"
        )

    new_user = Users(
        username=payload.username,
        email=payload.email,
        password=hash_password(payload.password),
        is_admin=payload.is_admin
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return UserResponse(
        id=new_user.id,
        username=new_user.username,
        email=new_user.email,
        is_admin=new_user.is_admin
    )


@app.post("/login")
def login(form_data:OAuth2PasswordRequestForm=Depends(), db: Session = Depends(get_db))->Token:


    user = db.scalars(
        select(Users).where(Users.username == form_data.username)
    ).first()


    if not user or not verify_password(form_data.password, user.password):
        raise HTTPException(
            status_code=401,
            detail="Incorrect username or password"
        )


    access_token = create_access_token(
        data={"sub": user.id, "role": "admin" if user.is_admin else "user"}
    )

    return Token(access_token=access_token)

