"""
RTM Source Linker — auto-links requirements to source chat messages and documents
using the existing ChromaDB memory service.
"""

import logging

from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

AUTO_LINK_LIMIT = 3
AUTO_LINK_THRESHOLD = 0.3
ALLOWED_SOURCE_TYPES = {"message", "document"}


def auto_link_sources(requirement, project_id: int, db: Session) -> list:
    """
    Find the top-3 semantically similar project memories for a requirement
    and create TraceabilityLink records with is_auto_generated=True.

    Deletes existing auto-generated links for this requirement before inserting new ones.
    Returns the list of newly created TraceabilityLink instances.
    """
    from app.ai.memory_service import search_project_memories
    from app.models.traceability_link import TraceabilityLink, SourceType

    # Remove stale auto-generated links
    db.query(TraceabilityLink).filter(
        TraceabilityLink.requirement_id == requirement.id,
        TraceabilityLink.is_auto_generated.is_(True),
    ).delete(synchronize_session=False)

    results = search_project_memories(
        db=db,
        project_id=project_id,
        query=requirement.full_text,
        limit=AUTO_LINK_LIMIT,
        similarity_threshold=AUTO_LINK_THRESHOLD,
        source_type=None,
    )

    new_links = []
    for result in results:
        src_type = result.get("source_type", "")
        if src_type not in ALLOWED_SOURCE_TYPES:
            continue

        chroma_source = SourceType.chat_message if src_type == "message" else SourceType.document
        excerpt = result.get("text", "")[:500]

        link = TraceabilityLink(
            requirement_id=requirement.id,
            source_type=chroma_source,
            source_id=result["source_id"],
            excerpt=excerpt,
            is_auto_generated=True,
        )
        db.add(link)
        new_links.append(link)

    logger.debug(
        f"Auto-linked {len(new_links)} sources for requirement {requirement.req_id}"
    )
    return new_links
