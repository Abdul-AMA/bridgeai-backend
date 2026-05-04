import enum

from sqlalchemy import Boolean, Column, DateTime, Enum, ForeignKey, Index, Integer, Text

from app.db.session import Base


class TriggerType(enum.Enum):
    document = "document"
    chat = "chat"
    manual = "manual"


class ProjectContextSummary(Base):
    __tablename__ = "project_context_summaries"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(
        Integer, ForeignKey("projects.id"), nullable=False, unique=True, index=True
    )
    content = Column(Text, nullable=True)
    generated_at = Column(DateTime(timezone=True), nullable=True)
    is_generating = Column(Boolean, nullable=False, default=False)
    last_trigger = Column(
        Enum(TriggerType), nullable=False, default=TriggerType.manual
    )

    __table_args__ = (
        Index(
            "ix_project_context_summaries_project_id", "project_id", unique=True
        ),
        {"mysql_engine": "InnoDB"},
    )
