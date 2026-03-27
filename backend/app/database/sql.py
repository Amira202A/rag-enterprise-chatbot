from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
import os

# ✅ URL compatible Docker
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "mysql+pymysql://chatbot:1234@mysql:3306/chatbot_admin"
)

engine = create_engine(DATABASE_URL)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

Base = declarative_base()