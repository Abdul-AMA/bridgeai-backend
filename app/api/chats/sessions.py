"""
Chat Sessions Module.
Handles CRUD operations for chat sessions.
"""
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import desc, func
from sqlalchemy.orm import Session, joinedload

from app.core.security import get_current_user
from app.db.session import get_db
from app.models.message import Message
from app.models.session_model import SessionModel, SessionStatus
from app.models.user import User
from app.schemas.chat import (
    SessionCreate,
    SessionListOut,
    SessionOut,
    SessionUpdate,
)
from app.services.permission_service import PermissionService


router = APIRouter()


@router.get("/{project_id}/chats", response_model=List[SessionListOut])
def get_project_chats(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get all chat sessions for a specific project."""
    # Get project and verify access
    project = PermissionService.verify_project_access(db, project_id, current_user.id)

    # Get all sessions for the project with message count
    sessions = (
        db.query(SessionModel, func.count(Message.id).label("message_count"))
        .outerjoin(Message, SessionModel.id == Message.session_id)
        .filter(SessionModel.project_id == project_id)
        .group_by(SessionModel.id)
        .order_by(desc(SessionModel.started_at))
        .all()
    )

    # Format response
    result = []
    for session, message_count in sessions:
        result.append(
            SessionListOut(
                id=session.id,
                project_id=session.project_id,
                user_id=session.user_id,
                crs_document_id=session.crs_document_id,
                crs_pattern=session.crs_pattern,
                name=session.name,
                status=session.status,
                started_at=session.started_at,
                ended_at=session.ended_at,
                message_count=message_count,
            )
        )

    return result


@router.post(
    "/{project_id}/chats",
    response_model=SessionOut,
    status_code=status.HTTP_201_CREATED,
)
def create_project_chat(
    project_id: int,
    session_data: SessionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create a new chat session for a project."""
    # Get project and verify access
    project = PermissionService.verify_project_access(db, project_id, current_user.id)

    # Create new session
    new_session = SessionModel(
        project_id=project_id,
        user_id=current_user.id,
        crs_document_id=session_data.crs_document_id,
        crs_pattern=session_data.crs_pattern.value if session_data.crs_pattern else "babok",
        name=session_data.name,
        status=SessionStatus.active,
    )

    db.add(new_session)
    db.commit()
    db.refresh(new_session)

    # Return session with empty messages list
    return SessionOut(
        id=new_session.id,
        project_id=new_session.project_id,
        user_id=new_session.user_id,
        crs_document_id=new_session.crs_document_id,
        crs_pattern=new_session.crs_pattern,
        name=new_session.name,
        status=new_session.status,
        started_at=new_session.started_at,
        ended_at=new_session.ended_at,
        messages=[],
    )


@router.get("/{project_id}/chats/{chat_id}", response_model=SessionOut)
def get_project_chat(
    project_id: int,
    chat_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get a specific chat session by its ID with all messages."""
    # Get project and verify access
    project = PermissionService.verify_project_access(db, project_id, current_user.id)

    # Get session and verify it belongs to this project
    session = (
        db.query(SessionModel)
        .options(joinedload(SessionModel.messages))
        .filter(SessionModel.id == chat_id, SessionModel.project_id == project_id)
        .first()
    )

    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chat session not found in this project",
        )

    return session


@router.put("/{project_id}/chats/{chat_id}", response_model=SessionOut)
def update_project_chat(
    project_id: int,
    chat_id: int,
    session_update: SessionUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Update a chat session status."""
    # Get project and verify access
    project = PermissionService.verify_project_access(db, project_id, current_user.id)

    # Get session and verify it belongs to this project
    session = (
        db.query(SessionModel)
        .filter(SessionModel.id == chat_id, SessionModel.project_id == project_id)
        .first()
    )

    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chat session not found in this project",
        )

    # Update session fields
    if session_update.name is not None:
        session.name = session_update.name

    if session_update.status is not None:
        session.status = session_update.status

        # If marking as completed, set ended_at timestamp
        if session_update.status == SessionStatus.completed and not session.ended_at:
            session.ended_at = func.now()

    db.commit()
    db.refresh(session)

    # Get session with messages
    session_with_messages = (
        db.query(SessionModel)
        .options(joinedload(SessionModel.messages))
        .filter(SessionModel.id == chat_id)
        .first()
    )

    return session_with_messages


@router.delete("/{project_id}/chats/{chat_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_project_chat(
    project_id: int,
    chat_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Delete a chat session and all its messages."""
    # Get project and verify access
    project = PermissionService.verify_project_access(db, project_id, current_user.id)

    # Get session and verify it belongs to this project
    session = (
        db.query(SessionModel)
        .filter(SessionModel.id == chat_id, SessionModel.project_id == project_id)
        .first()
    )

    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chat session not found in this project",
        )

    # Delete all messages first
    db.query(Message).filter(Message.session_id == chat_id).delete()

    # Delete the session
    db.delete(session)
    db.commit()

    return None
