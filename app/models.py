from datetime import time, date
from typing import List
from uuid import uuid4
from sqlalchemy import (
    ForeignKey, String, Boolean, Integer,
    Date, Time, ForeignKeyConstraint
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base

class Users(Base):
    __tablename__ = "users"

    id:Mapped[str]=mapped_column(String,primary_key=True,default=lambda: str(uuid4()))
    username:Mapped[str]=mapped_column(String,unique=True,nullable=False)
    email:Mapped[str]=mapped_column(String,unique=True,nullable=False)
    password:Mapped[str]=mapped_column(String,nullable=False)
    is_admin:Mapped[bool]=mapped_column(Boolean,default=False)

class RoomDb(Base):
    __tablename__ = "rooms"

    id:Mapped[int]=mapped_column(Integer,primary_key=True,autoincrement=True)
    name:Mapped[str]=mapped_column(String,nullable=False,unique=True)
    capacity:Mapped[int]=mapped_column(Integer,nullable=False)

    time_slots:Mapped[List['TimeSlotDb']]=relationship(back_populates="room",
                                                       cascade='all,delete-orphan',
                                                       order_by='TimeSlotDb.slot_index',
                                                       lazy='selectin',)


class TimeSlotDb(Base):
    __tablename__ = "time_slots"


    room_id:Mapped[int]=mapped_column(Integer,ForeignKey('rooms.id',ondelete='CASCADE'),primary_key=True)
    start_time:Mapped[time]=mapped_column(Time,nullable=False)
    end_time:Mapped[time]=mapped_column(Time,nullable=False)
    slot_index:Mapped[int]=mapped_column(Integer,primary_key=True)
    room: Mapped['RoomDb'] = relationship(back_populates='time_slots')
class BookingDb(Base):
    __tablename__ = "bookings"

    id:Mapped[str]=mapped_column(String,primary_key=True,default=lambda: str(uuid4()))
    room_id:Mapped[int]=mapped_column(Integer,nullable=False)
    time_slot_index:Mapped[int]=mapped_column(Integer,nullable=False)
    booking_date:Mapped[date]=mapped_column(Date,nullable=False)
    user_id:Mapped[str]=mapped_column(String,ForeignKey('users.id',ondelete='CASCADE'),nullable=False)


    __table_args__ = (
        ForeignKeyConstraint(['room_id','time_slot_index'],
                             ['time_slots.room_id','time_slots.slot_index'],
                             ondelete='CASCADE',),)
