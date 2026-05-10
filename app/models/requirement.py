import enum

from sqlalchemy import Column, DateTime, Enum, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.db.session import Base


class RequirementStatus(enum.Enum):
    active = "active"
    archived = "archived"


class Requirement(Base):
    __tablename__ = "requirements"

    id = Column(Integer, primary_key=True, index=True)
    req_id = Column(String(20), nullable=False)
    project_id = Column(
        Integer, ForeignKey("projects.id"), nullable=False, index=True
    )
    crs_document_id = Column(
        Integer, ForeignKey("crs_documents.id"), nullable=False
    )
    section = Column(String(100), nullable=False)
    description = Column(String(500), nullable=False)
    full_text = Column(Text, nullable=False)
    status = Column(
        Enum(RequirementStatus),
        nullable=False,
        default=RequirementStatus.active,
        server_default="active",
    )
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    __table_args__ = ({"mysql_engine": "InnoDB"},)

    traceability_links = relationship(
        "TraceabilityLink", back_populates="requirement", cascade="all, delete-orphan"
    )
    test_cases = relationship(
        "TestCase", back_populates="requirement", cascade="all, delete-orphan"
    )
    comments = relationship("Comment", back_populates="requirement")
