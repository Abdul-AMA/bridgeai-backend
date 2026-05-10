from sqlalchemy import Column, DateTime, ForeignKey, Integer, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.db.session import Base


class Comment(Base):
    __tablename__ = "comments"

    id = Column(Integer, primary_key=True, index=True)
    crs_id = Column(
        Integer, ForeignKey("crs_documents.id"), nullable=True, index=True
    )  # Nullable: RTM requirement comments have no crs_id
    requirement_id = Column(
        Integer, ForeignKey("requirements.id", ondelete="CASCADE"), nullable=True, index=True
    )  # Set when comment belongs to an RTM requirement
    author_id = Column(
        Integer, ForeignKey("users.id"), nullable=False
    )  # No index - rarely query comments by author
    content = Column(Text, nullable=False)
    created_at = Column(
        DateTime(timezone=True), server_default=func.now()
    )  # No index - ordered in app or composite later

    __table_args__ = ({"mysql_engine": "InnoDB"},)

    # Relationships
    crs_document = relationship("CRSDocument", backref="comments")
    requirement = relationship("Requirement", back_populates="comments")
    author = relationship("User", backref="comments")
