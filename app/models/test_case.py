import enum

from sqlalchemy import Boolean, Column, DateTime, Enum, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.db.session import Base


class TestCaseStatus(enum.Enum):
    active = "active"
    archived = "archived"


class TestCase(Base):
    __tablename__ = "test_cases"

    id = Column(Integer, primary_key=True, index=True)
    requirement_id = Column(
        Integer,
        ForeignKey("requirements.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    title = Column(String(300), nullable=False)
    preconditions = Column(Text, nullable=True)
    steps = Column(Text, nullable=False)  # JSON array of step strings
    expected_result = Column(Text, nullable=False)
    is_auto_generated = Column(Boolean, nullable=False, default=False, server_default="0")
    status = Column(
        Enum(TestCaseStatus),
        nullable=False,
        default=TestCaseStatus.active,
        server_default="active",
    )
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    __table_args__ = ({"mysql_engine": "InnoDB"},)

    requirement = relationship("Requirement", back_populates="test_cases")
