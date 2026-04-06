from sqlalchemy import Column, Integer, String, Boolean, DateTime
from sqlalchemy.sql import func
from app.database.sql import Base

class User(Base):
    __tablename__ = "users"

    id                  = Column(Integer, primary_key=True, index=True)
    nom                 = Column(String(100), nullable=False)
    prenom              = Column(String(100), nullable=True)
    cin                 = Column(String(20),  unique=True, index=True, nullable=False)
    email               = Column(String(255), unique=True, index=True, nullable=False)
    password            = Column(String(255), nullable=False)

    # Champs RH — remplis par l'admin
    matricule           = Column(String(50),  nullable=True)
    num_poste           = Column(String(50),  nullable=True)
    num_personnel       = Column(String(50),  nullable=True)
    upper_hierarchy     = Column(String(100), nullable=True)
    unit_label          = Column(String(100), nullable=True)
    subsidiary_label    = Column(String(100), nullable=True)

    is_active           = Column(Boolean, default=True)
    is_admin            = Column(Boolean, default=False)
    add_date            = Column(DateTime, server_default=func.now())