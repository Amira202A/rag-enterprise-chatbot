from sqlalchemy import Column, Integer, String
from app.database.sql import Base

class User(Base):
    __tablename__ = "users"

    id       = Column(Integer, primary_key=True, index=True)
    nom      = Column(String(100), nullable=False)
    cin      = Column(String(20),  unique=True, index=True, nullable=False)
    email    = Column(String(255), unique=True, index=True, nullable=False)
    password = Column(String(255), nullable=False)  # bcrypt hash