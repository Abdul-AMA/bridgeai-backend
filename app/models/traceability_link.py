import enum

from sqlalchemy import Boolean, Column, DateTime, Enum, ForeignKey, Integer, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.db.session import Base


class SourceType(enum.Enum):
    chat_message = "chat_message"
    document = "document"


class TraceabilityLink(Base):
    __tablename__ = "traceability_links"

    id = Column(Integer, primary_key=True, index=True)
    requirement_id = Column(
        Integer,
        ForeignKey("requirements.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    source_type = Column(Enum(SourceType), nullable=False)
    source_id = Column(Integer, nullable=False)
    excerpt = Column(Text, nullable=False)
    is_auto_generated = Column(Boolean, nullable=False, default=True, server_default="1")
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = ({"mysql_engine": "InnoDB"},)

    requirement = relationship("Requirement", back_populates="traceability_links")
