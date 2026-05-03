from sqlalchemy import Column, DateTime, Integer, String
from sqlalchemy.sql import func

from app.db.session import Base


class AIUsageLog(Base):
    __tablename__ = "ai_usage_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, index=True, nullable=False)
    project_id = Column(Integer, index=True, nullable=True)
    session_id = Column(Integer, index=True, nullable=True)
    node_type = Column(String(64), nullable=False)
    model_name = Column(String(128), nullable=False)
    provider = Column(String(64), nullable=False, default="anthropic")
    input_tokens = Column(Integer, nullable=False, default=0)
    output_tokens = Column(Integer, nullable=False, default=0)
    total_tokens = Column(Integer, nullable=False, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
