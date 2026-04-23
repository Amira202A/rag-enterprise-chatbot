from sqlalchemy import Column, Integer, String, Boolean, DateTime
from sqlalchemy.sql import func
from app.database.sql import Base

class Employee(Base):
    __tablename__ = "employees"

    id               = Column(Integer, primary_key=True, index=True)
    nom              = Column(String(100), nullable=False)
    prenom           = Column(String(100), nullable=False)
    cin              = Column(String(20),  unique=True, index=True, nullable=False)
    email            = Column(String(255), unique=True, index=True, nullable=False)
    matricule        = Column(String(50),  nullable=True)
    num_poste        = Column(String(50),  nullable=True)
    num_personnel    = Column(String(50),  nullable=True)
    unit_label       = Column(String(100), nullable=True)
    subsidiary_label = Column(String(100), nullable=True)
    upper_hierarchy  = Column(String(100), nullable=True)
    is_registered    = Column(Boolean, default=False)
    add_date         = Column(DateTime, server_default=func.now())