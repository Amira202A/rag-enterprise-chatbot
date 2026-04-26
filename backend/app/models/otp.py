from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.sql import func
from app.database.sql import Base
from datetime import datetime, timedelta

class OTPCode(Base):
    __tablename__ = "otp_codes"

    id         = Column(Integer, primary_key=True, index=True)
    cin        = Column(String(20), index=True, nullable=False)
    code       = Column(String(6),  nullable=False)
    expires_at = Column(DateTime,   nullable=False)
    used       = Column(String(1),  default="0")  # "0" = non utilisé

    def is_valid(self) -> bool:
        return self.used == "0" and datetime.utcnow() < self.expires_at