from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase
import os

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+psycopg://postgres:admin@127.0.0.1:5432/postgres"
)
engine = create_engine(DATABASE_URL)
Sessionlocal = sessionmaker(bind=engine)

class Base(DeclarativeBase):
    pass

def get_db():
    db=Sessionlocal()
    try:
        yield db
    finally:
        db.close()