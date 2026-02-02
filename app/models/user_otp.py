from sqlalchemy import Column, DateTime, Integer, String
from sqlalchemy.sql import func
from app.db.session import Base
from datetime import datetime, timedelta

class UserOTP(Base):
    __tablename__ = "user_otps"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(256), index=True, nullable=False)
    otp_code = Column(String(6), nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    @property
    def is_expired(self) -> bool:
        """Check if OTP has expired."""
        return datetime.utcnow() > self.expires_at.replace(tzinfo=None)
