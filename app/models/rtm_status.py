import enum

from sqlalchemy import Boolean, Column, DateTime, Enum, ForeignKey, Integer
from sqlalchemy.sql import func

from app.db.session import Base


class RTMTrigger(enum.Enum):
    save = "save"
    status_change = "status_change"
    draft = "draft"
    manual = "manual"


class RTMStatus(Base):
    __tablename__ = "rtm_status"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(
        Integer, ForeignKey("projects.id"), nullable=False, unique=True, index=True
    )
    is_refreshing = Column(Boolean, nullable=False, default=False, server_default="0")
    last_refreshed_at = Column(DateTime(timezone=True), nullable=True)
    last_trigger = Column(Enum(RTMTrigger), nullable=True)
    requirement_count = Column(Integer, nullable=False, default=0, server_default="0")
    unverified_count = Column(Integer, nullable=False, default=0, server_default="0")
    untested_count = Column(Integer, nullable=False, default=0, server_default="0")

    __table_args__ = ({"mysql_engine": "InnoDB"},)
