"""
Comment service for CRS feedback management.
"""

import logging
import uuid
from typing import List, Optional

from sqlalchemy.orm import Session

from app.ai import chroma_manager
from app.models.ai_memory_index import SourceType
from app.models.comment import Comment
from app.repositories.crs_repository import CRSRepository, CommentRepository
from app.repositories.user_repository import UserRepository
from app.repositories.ai_memory_repository import AIMemoryIndexRepository

logger = logging.getLogger(__name__)


def create_comment(
    db: Session, *, crs_id: int, author_id: int, content: str
) -> Comment:
    """
    Create a new comment on a CRS document.

    Args:
        db: Database session
        crs_id: ID of the CRS document to comment on
        author_id: ID of the user creating the comment
        content: Comment text content

    Returns:
        Created Comment object

    Raises:
        ValueError: If CRS document not found
    """
    # Verify CRS document exists
    crs_repo = CRSRepository(db)
    crs = crs_repo.get_by_id(crs_id)
    if not crs:
        raise ValueError(f"CRS document with id={crs_id} not found")

    comment = Comment(crs_id=crs_id, author_id=author_id, content=content)

    db.add(comment)
    db.commit()
    db.refresh(comment)

    logger.info(f"Comment {comment.id} created on CRS {crs_id} by user {author_id}")

    # Store in AI Memory (ChromaDB)
    try:
        embedding_id = str(uuid.uuid4())

        # Get author details for metadata
        user_repo = UserRepository(db)
        author = user_repo.get_by_id(author_id)
        author_role = author.role.value if author else "unknown"

        # Store in Vector DB
        chroma_manager.store_embedding(
            embedding_id=embedding_id,
            text=content,
            metadata={
                "project_id": crs.project_id,
                "source_type": SourceType.comment.value,
                "source_id": comment.id,
                "author_id": author_id,
                "author_role": author_role,
                "crs_id": crs_id,
            },
        )

        # Create Index Record using repository
        memory_repo = AIMemoryIndexRepository(db)
        index_record = memory_repo.create({
            "project_id": crs.project_id,
            "source_type": SourceType.comment,
            "source_id": comment.id,
            "embedding_id": embedding_id,
        })
        logger.info(f"Comment {comment.id} stored in AI memory with id {embedding_id}")

    except Exception as e:
        logger.error(f"Failed to store comment {comment.id} in AI memory: {str(e)}")
        # We don't rollback the comment creation as it's the primary action
        pass

    return comment


def get_comments_by_crs(
    db: Session, *, crs_id: int, skip: int = 0, limit: int = 100
) -> List[Comment]:
    """
    Retrieve all comments for a specific CRS document.

    Args:
        db: Database session
        crs_id: ID of the CRS document
        skip: Number of records to skip (pagination)
        limit: Maximum number of records to return

    Returns:
        List of Comment objects ordered by creation time (newest first)
    """
    comment_repo = CommentRepository(db)
    return comment_repo.get_crs_comments(crs_id, skip=skip, limit=limit)


def get_comment_by_id(db: Session, *, comment_id: int) -> Optional[Comment]:
    """
    Retrieve a specific comment by ID.

    Args:
        db: Database session
        comment_id: ID of the comment

    Returns:
        Comment object or None if not found
    """
    comment_repo = CommentRepository(db)
    return comment_repo.get_by_id(comment_id)


def update_comment(db: Session, *, comment_id: int, content: str) -> Comment:
    """
    Update the content of an existing comment.

    Args:
        db: Database session
        comment_id: ID of the comment to update
        content: New comment content

    Returns:
        Updated Comment object

    Raises:
        ValueError: If comment not found
    """
    comment_repo = CommentRepository(db)
    comment = comment_repo.get_by_id(comment_id)
    if not comment:
        raise ValueError(f"Comment with id={comment_id} not found")

    comment.content = content
    db.commit()
    db.refresh(comment)

    logger.info(f"Comment {comment_id} updated")

    # Update in AI Memory
    try:
        # Find associated index record
        memory_repo = AIMemoryIndexRepository(db)
        index_record = memory_repo.get_by_source(SourceType.comment, comment_id)

        if index_record:
            # Get CRS project_id
            crs_repo = CRSRepository(db)
            crs = crs_repo.get_by_id(comment.crs_id)
            project_id = crs.project_id if crs else 0

            user_repo = UserRepository(db)
            author = user_repo.get_by_id(comment.author_id)
            author_role = author.role.value if author else "unknown"

            # Simple re-store (upsert)
            chroma_manager.store_embedding(
                embedding_id=index_record.embedding_id,
                text=content,
                metadata={
                    "project_id": project_id,
                    "source_type": SourceType.comment.value,
                    "source_id": comment_id,
                    "author_id": comment.author_id,
                    "author_role": author_role,
                    "crs_id": comment.crs_id,
                },
            )
            logger.info(f"Comment {comment_id} updated in AI memory")

    except Exception as e:
        logger.error(f"Failed to update comment {comment_id} in AI memory: {str(e)}")

    return comment


def delete_comment(db: Session, *, comment_id: int) -> bool:
    """
    Delete a comment.

    Args:
        db: Database session
        comment_id: ID of the comment to delete

    Returns:
        True if deleted, False if not found
    """
    comment_repo = CommentRepository(db)
    comment = comment_repo.get_by_id(comment_id)
    if not comment:
        return False

    # Delete from AI Memory first
    try:
        memory_repo = AIMemoryIndexRepository(db)
        index_record = memory_repo.get_by_source(SourceType.comment, comment_id)

        if index_record:
            chroma_manager.delete_embedding(index_record.embedding_id)
            db.delete(index_record)
            # We don't commit yet, we commit with comment deletion to be atomic-ish
    except Exception as e:
        logger.error(f"Failed to delete comment {comment_id} from AI memory: {str(e)}")

    db.delete(comment)
    db.commit()

    logger.info(f"Comment {comment_id} deleted")

    return True


def get_comments_count_by_crs(db: Session, *, crs_id: int) -> int:
    """
    Get the total count of comments for a CRS document.

    Args:
        db: Database session
        crs_id: ID of the CRS document

    Returns:
        Total number of comments
    """
    comment_repo = CommentRepository(db)
    return comment_repo.count_by_crs_id(crs_id)
