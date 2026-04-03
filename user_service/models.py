from sqlalchemy import Column, String, Integer
from database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    login = Column(String(20), unique=True)
    password = Column(String)
