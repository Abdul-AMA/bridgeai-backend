from sqlalchemy import Column, DateTime, Integer, String, Text
from sqlalchemy.sql import func

from app.db.session import Base


class SystemErrorLog(Base):
    __tablename__ = "system_error_logs"

    id = Column(Integer, primary_key=True, index=True)
    error_code = Column(String(64), nullable=False, index=True)
    path = Column(String(512), nullable=False)
    method = Column(String(16), nullable=False)
    message = Column(Text, nullable=False)
    stack_trace = Column(Text, nullable=True)
    user_id = Column(Integer, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)

    __table_args__ = ({"mysql_engine": "InnoDB"},)
