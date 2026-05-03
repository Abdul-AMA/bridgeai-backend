"""
Documents API — project-scoped knowledge base file uploads.
Endpoints: POST/GET/DELETE /api/projects/{project_id}/documents
"""

from fastapi import (
    APIRouter,
    BackgroundTasks,
    Depends,
    HTTPException,
    UploadFile,
    status,
)
from sqlalchemy.orm import Session

from app.core.security import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.documents import DocumentListOut, DocumentOut
from app.services.document_service import ALLOWED_EXTENSIONS, DocumentService
from app.services.permission_service import PermissionService

router = APIRouter()


@router.post(
    "/{project_id}/documents",
    response_model=DocumentOut,
    status_code=status.HTTP_202_ACCEPTED,
)
async def upload_document(
    project_id: int,
    file: UploadFile,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Upload a document to the project knowledge base. Processing happens in background."""
    PermissionService.verify_project_access(db, project_id, current_user.id)

    filename = file.filename or "unnamed"
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file type '.{ext}'. Allowed: {', '.join(sorted(ALLOWED_EXTENSIONS))}",
        )

    file_bytes = await file.read()

    try:
        doc = DocumentService.upload_document(
            db=db,
            project_id=project_id,
            user_id=current_user.id,
            filename=filename,
            file_bytes=file_bytes,
            file_type=ext,
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    background_tasks.add_task(DocumentService.process_document_embeddings, doc.id)

    return DocumentOut.model_validate(doc)


@router.get("/{project_id}/documents", response_model=DocumentListOut)
def list_documents(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List all documents in the project knowledge base."""
    PermissionService.verify_project_access(db, project_id, current_user.id)
    docs = DocumentService.list_documents(db, project_id)
    return DocumentListOut(
        items=[DocumentOut.model_validate(d) for d in docs],
        total=len(docs),
    )


@router.delete(
    "/{project_id}/documents/{doc_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_document(
    project_id: int,
    doc_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Delete a document and all its embeddings from the project knowledge base."""
    PermissionService.verify_project_access(db, project_id, current_user.id)
    try:
        DocumentService.delete_document(db, doc_id=doc_id, project_id=project_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
