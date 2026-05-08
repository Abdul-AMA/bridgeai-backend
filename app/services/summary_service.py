"""
Project Context Summary service.
Generates and persists a human-readable summary of everything known about a project.
"""

import logging
from datetime import datetime, timezone
from typing import Optional

from langchain_core.messages import HumanMessage
from sqlalchemy.orm import Session

from app.ai.llm_factory import get_summary_llm
from app.ai.memory_service import search_project_memories
from app.models.message import Message, SenderType
from app.models.project import Project
from app.models.project_context_summary import ProjectContextSummary, TriggerType
from app.models.session_model import SessionModel

logger = logging.getLogger(__name__)

SUMMARY_PROMPT = """You are a requirements analyst assistant. Write a 150-400 word summary of the project below.
Cover: project purpose, known requirements, key constraints, and open questions.
Be concise and factual — do not invent details.

PROJECT DESCRIPTION:
{project_description}

RECENT CLIENT MESSAGES (last 20):
{chat_history}

RELEVANT DOCUMENT CONTEXT (top 10 chunks):
{document_context}

Respond with the summary paragraph only. No headings, no bullet points."""


def get_or_none(project_id: int, db: Session) -> Optional[ProjectContextSummary]:
    return (
        db.query(ProjectContextSummary)
        .filter(ProjectContextSummary.project_id == project_id)
        .first()
    )


def get_summary_content(project_id: int, db: Session) -> str:
    """Return summary content or a fallback string — never raises."""
    row = get_or_none(project_id, db)
    if row and row.content:
        return row.content
    return "No project summary available yet."


async def generate_summary(project_id: int, trigger: str, db: Session) -> None:
    """
    Generate and persist the project context summary for a project.
    Called by BackgroundSummaryGenerator — errors are caught and logged,
    and the previous content (if any) is preserved on failure.
    """
    row = get_or_none(project_id, db)
    if row is None:
        row = ProjectContextSummary(
            project_id=project_id,
            is_generating=True,
            last_trigger=TriggerType[trigger],
        )
        db.add(row)
    else:
        row.is_generating = True
        row.last_trigger = TriggerType[trigger]
    db.commit()

    try:
        # Fetch project description
        project = db.query(Project).filter(Project.id == project_id).first()
        project_description = (project.description or "No description provided.") if project else "No description provided."

        # Fetch last 20 client messages across all sessions for this project
        session_ids = [
            s.id
            for s in db.query(SessionModel.id)
            .filter(SessionModel.project_id == project_id)
            .all()
        ]
        chat_history = "No chat history yet."
        if session_ids:
            messages = (
                db.query(Message)
                .filter(
                    Message.session_id.in_(session_ids),
                    Message.sender_type == SenderType.client,
                )
                .order_by(Message.timestamp.desc())
                .limit(20)
                .all()
            )
            if messages:
                messages.reverse()
                chat_history = "\n".join(f"- {m.content}" for m in messages)

        # Build a rich RAG query from project description + recent chat so we
        # surface document chunks even when the project description is sparse.
        recent_messages_text = (
            chat_history.replace("- ", "").replace("\n", " ")
            if chat_history != "No chat history yet."
            else ""
        )
        rag_query = " ".join(
            filter(None, [project_description, recent_messages_text])
        ) or "project requirements"

        # Fetch top-5 document chunks via semantic search (keep below typical
        # collection size to avoid ChromaDB n_results > collection_size errors).
        doc_chunks = search_project_memories(
            db=db,
            project_id=project_id,
            query=rag_query,
            limit=5,
            similarity_threshold=0.05,
            source_type="document",
        )
        document_context = "No documents uploaded yet."
        if doc_chunks:
            document_context = "\n".join(
                f"[{r.get('metadata', {}).get('filename', 'document')}]: {r['text']}"
                for r in doc_chunks
            )

        prompt = SUMMARY_PROMPT.format(
            project_description=project_description,
            chat_history=chat_history,
            document_context=document_context,
        )

        llm = get_summary_llm()
        response = await llm.ainvoke([HumanMessage(content=prompt)])
        content = response.content.strip()

        row.content = content
        row.generated_at = datetime.now(timezone.utc)
        row.is_generating = False
        db.commit()
        logger.info(f"Summary generated for project {project_id} (trigger={trigger})")

    except Exception as exc:
        logger.error(
            f"Summary generation failed for project {project_id}: {exc}",
            exc_info=True,
        )
        row.is_generating = False
        db.commit()
