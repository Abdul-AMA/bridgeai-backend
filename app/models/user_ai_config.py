import enum

from sqlalchemy import Boolean, Column, DateTime, Enum, ForeignKey, Integer, String
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.db.session import Base


class AIProvider(str, enum.Enum):
    anthropic = "anthropic"
    openai = "openai"
    gemini = "gemini"
    groq = "groq"
    mistral = "mistral"


class UserAIConfig(Base):
    __tablename__ = "user_ai_configs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False)
    provider = Column(Enum(AIProvider), nullable=False)
    model_id = Column(String(128), nullable=False)
    api_key_encrypted = Column(String(512), nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    user = relationship("User", backref="ai_config")
