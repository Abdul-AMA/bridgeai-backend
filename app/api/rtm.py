"""
RTM API — Requirements Traceability Matrix endpoints.
Prefix: /api/projects/{project_id}/rtm  (registered in __init__.py)
"""

import json
import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.core.security import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.rtm import (
    GenerateTestCasesRequest,
    GenerateTestCasesResponse,
    GeneratedRequirementTestCases,
    RTMStatusOut,
    RTMTriggerRequest,
    RequirementDetailOut,
    RequirementOut,
    TestCaseCreate,
    TestCaseOut,
    TestCaseUpdate,
    TraceabilityLinkCreate,
    TraceabilityLinkOut,
)
from app.services.permission_service import PermissionService

logger = logging.getLogger(__name__)

router = APIRouter()


# ─── Helpers ──────────────────────────────────────────────────────────────────

def _get_rtm_status_row(project_id: int, db: Session):
    from app.models.rtm_status import RTMStatus

    row = db.query(RTMStatus).filter(RTMStatus.project_id == project_id).first()
    if not row:
        row = RTMStatus(project_id=project_id)
        db.add(row)
        db.commit()
        db.refresh(row)
    return row


def _requirement_out(req, db: Session) -> RequirementOut:
    from app.models.traceability_link import TraceabilityLink
    from app.models.test_case import TestCase
    from sqlalchemy import func

    src_count = (
        db.query(func.count(TraceabilityLink.id))
        .filter(TraceabilityLink.requirement_id == req.id)
        .scalar()
    ) or 0
    tc_count = (
        db.query(func.count(TestCase.id))
        .filter(TestCase.requirement_id == req.id)
        .scalar()
    ) or 0
    return RequirementOut(
        id=req.id,
        req_id=req.req_id,
        section=req.section,
        description=req.description,
        full_text=req.full_text,
        status=req.status.value if hasattr(req.status, "value") else req.status,
        source_count=src_count,
        test_case_count=tc_count,
        created_at=req.created_at,
    )


def _tc_out(tc) -> TestCaseOut:
    from app.core.json_utils import safe_json_loads

    steps = safe_json_loads(tc.steps, default=[])
    if not isinstance(steps, list):
        steps = [str(steps)]
    return TestCaseOut(
        id=tc.id,
        requirement_id=tc.requirement_id,
        title=tc.title,
        preconditions=tc.preconditions,
        steps=steps,
        expected_result=tc.expected_result,
        is_auto_generated=tc.is_auto_generated,
        status=tc.status.value if hasattr(tc.status, "value") else tc.status,
        created_at=tc.created_at,
    )


# ─── RTM Status ───────────────────────────────────────────────────────────────

@router.get("/{project_id}/rtm/status", response_model=RTMStatusOut, tags=["rtm"])
def get_rtm_status(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    PermissionService.verify_project_access(db, project_id, current_user.id)
    row = _get_rtm_status_row(project_id, db)
    return RTMStatusOut(
        project_id=row.project_id,
        is_refreshing=row.is_refreshing,
        last_refreshed_at=row.last_refreshed_at,
        last_trigger=row.last_trigger.value if row.last_trigger else None,
        requirement_count=row.requirement_count,
        unverified_count=row.unverified_count,
        untested_count=row.untested_count,
    )


@router.post(
    "/{project_id}/rtm/refresh",
    status_code=status.HTTP_202_ACCEPTED,
    tags=["rtm"],
)
def trigger_rtm_refresh(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    PermissionService.verify_project_access(db, project_id, current_user.id)
    PermissionService.verify_ba_role(current_user)

    from app.services.background_rtm_generator import _generator

    if _generator.is_refreshing(project_id):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="RTM refresh already in progress.",
        )

    from app.services.background_rtm_generator import queue_rtm_generation

    queue_rtm_generation(project_id, "manual")
    return {"queued": True}


# ─── Requirements ─────────────────────────────────────────────────────────────

@router.get(
    "/{project_id}/rtm/requirements",
    response_model=list[RequirementOut],
    tags=["rtm"],
)
def list_requirements(
    project_id: int,
    section: Optional[str] = Query(None),
    coverage: Optional[str] = Query(None),
    q: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    PermissionService.verify_project_access(db, project_id, current_user.id)

    from app.models.requirement import Requirement, RequirementStatus
    from app.models.traceability_link import TraceabilityLink
    from app.models.test_case import TestCase

    query = db.query(Requirement).filter(
        Requirement.project_id == project_id,
        Requirement.status == RequirementStatus.active,
    )
    if section:
        query = query.filter(Requirement.section == section)
    if q:
        query = query.filter(
            Requirement.full_text.ilike(f"%{q}%")
            | Requirement.description.ilike(f"%{q}%")
        )

    requirements = query.order_by(Requirement.req_id).all()

    result = []
    for req in requirements:
        out = _requirement_out(req, db)
        if coverage == "unverified" and out.source_count > 0:
            continue
        if coverage == "untested" and out.test_case_count > 0:
            continue
        if coverage == "complete" and (out.source_count == 0 or out.test_case_count == 0):
            continue
        result.append(out)

    return result


@router.get(
    "/{project_id}/rtm/requirements/{req_id}",
    response_model=RequirementDetailOut,
    tags=["rtm"],
)
def get_requirement_detail(
    project_id: int,
    req_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    PermissionService.verify_project_access(db, project_id, current_user.id)

    from app.models.requirement import Requirement, RequirementStatus
    from app.models.traceability_link import TraceabilityLink
    from app.models.test_case import TestCase
    from app.models.comment import Comment

    req = (
        db.query(Requirement)
        .filter(
            Requirement.project_id == project_id,
            Requirement.req_id == req_id,
            Requirement.status == RequirementStatus.active,
        )
        .first()
    )
    if not req:
        raise HTTPException(status_code=404, detail="Requirement not found.")

    out = _requirement_out(req, db)

    links = (
        db.query(TraceabilityLink)
        .filter(TraceabilityLink.requirement_id == req.id)
        .order_by(TraceabilityLink.created_at.desc())
        .all()
    )
    tcs = (
        db.query(TestCase)
        .filter(TestCase.requirement_id == req.id)
        .order_by(TestCase.created_at.asc())
        .all()
    )
    comments = (
        db.query(Comment)
        .filter(Comment.requirement_id == req.id)
        .order_by(Comment.created_at.asc())
        .all()
    )

    return RequirementDetailOut(
        **out.model_dump(),
        source_links=[
            TraceabilityLinkOut(
                id=lk.id,
                source_type=lk.source_type.value if hasattr(lk.source_type, "value") else lk.source_type,
                source_id=lk.source_id,
                excerpt=lk.excerpt,
                is_auto_generated=lk.is_auto_generated,
                created_at=lk.created_at,
            )
            for lk in links
        ],
        test_cases=[_tc_out(tc) for tc in tcs],
        comments=[
            {"id": c.id, "author_id": c.author_id, "content": c.content, "created_at": c.created_at}
            for c in comments
        ],
    )


# ─── Source Links ──────────────────────────────────────────────────────────────

@router.post(
    "/{project_id}/rtm/requirements/{req_id}/links",
    response_model=TraceabilityLinkOut,
    status_code=status.HTTP_201_CREATED,
    tags=["rtm"],
)
def add_source_link(
    project_id: int,
    req_id: str,
    payload: TraceabilityLinkCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    PermissionService.verify_project_access(db, project_id, current_user.id)
    PermissionService.verify_ba_role(current_user)

    from app.models.requirement import Requirement, RequirementStatus
    from app.models.traceability_link import TraceabilityLink, SourceType

    req = (
        db.query(Requirement)
        .filter(
            Requirement.project_id == project_id,
            Requirement.req_id == req_id,
            Requirement.status == RequirementStatus.active,
        )
        .first()
    )
    if not req:
        raise HTTPException(status_code=404, detail="Requirement not found.")

    link = TraceabilityLink(
        requirement_id=req.id,
        source_type=SourceType(payload.source_type.value),
        source_id=payload.source_id,
        excerpt=payload.excerpt,
        is_auto_generated=False,
    )
    db.add(link)
    db.commit()
    db.refresh(link)
    return TraceabilityLinkOut(
        id=link.id,
        source_type=link.source_type.value,
        source_id=link.source_id,
        excerpt=link.excerpt,
        is_auto_generated=link.is_auto_generated,
        created_at=link.created_at,
    )


@router.delete(
    "/{project_id}/rtm/requirements/{req_id}/links/{link_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    tags=["rtm"],
)
def remove_source_link(
    project_id: int,
    req_id: str,
    link_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    PermissionService.verify_project_access(db, project_id, current_user.id)
    PermissionService.verify_ba_role(current_user)

    from app.models.requirement import Requirement, RequirementStatus
    from app.models.traceability_link import TraceabilityLink

    req = (
        db.query(Requirement)
        .filter(
            Requirement.project_id == project_id,
            Requirement.req_id == req_id,
            Requirement.status == RequirementStatus.active,
        )
        .first()
    )
    if not req:
        raise HTTPException(status_code=404, detail="Requirement not found.")

    link = (
        db.query(TraceabilityLink)
        .filter(
            TraceabilityLink.id == link_id,
            TraceabilityLink.requirement_id == req.id,
        )
        .first()
    )
    if not link:
        raise HTTPException(status_code=404, detail="Link not found.")
    if link.is_auto_generated:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Auto-generated links cannot be deleted manually.",
        )

    db.delete(link)
    db.commit()


# ─── Test Cases ────────────────────────────────────────────────────────────────

@router.post(
    "/{project_id}/rtm/test-cases/generate",
    response_model=GenerateTestCasesResponse,
    tags=["rtm"],
)
def generate_test_cases(
    project_id: int,
    payload: GenerateTestCasesRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    PermissionService.verify_project_access(db, project_id, current_user.id)
    PermissionService.verify_ba_role(current_user)

    from app.models.requirement import Requirement, RequirementStatus
    from app.models.test_case import TestCase as TestCaseModel
    from app.services.rtm_test_case_service import generate_test_cases as svc_generate
    from sqlalchemy import func

    if payload.generate_all_untested:
        # All untested active requirements for this project (cap at 10)
        req_ids = (
            db.query(Requirement.id)
            .filter(
                Requirement.project_id == project_id,
                Requirement.status == RequirementStatus.active,
            )
            .filter(
                ~db.query(TestCaseModel.id)
                .filter(TestCaseModel.requirement_id == Requirement.id)
                .exists()
            )
            .limit(10)
            .all()
        )
        requirement_ids = [r.id for r in req_ids]
    else:
        requirement_ids = payload.requirement_ids[:10]

    if not requirement_ids:
        return GenerateTestCasesResponse(generated=[], skipped=[])

    created_tcs = svc_generate(requirement_ids, db)
    db.commit()

    # Group by requirement_id
    by_req: dict[int, list] = {}
    for tc in created_tcs:
        by_req.setdefault(tc.requirement_id, []).append(_tc_out(tc))

    generated = [
        GeneratedRequirementTestCases(requirement_id=rid, test_cases=tcs)
        for rid, tcs in by_req.items()
    ]
    skipped = [rid for rid in requirement_ids if rid not in by_req]

    return GenerateTestCasesResponse(generated=generated, skipped=skipped)


@router.post(
    "/{project_id}/rtm/requirements/{req_id}/test-cases",
    response_model=TestCaseOut,
    status_code=status.HTTP_201_CREATED,
    tags=["rtm"],
)
def add_test_case(
    project_id: int,
    req_id: str,
    payload: TestCaseCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    PermissionService.verify_project_access(db, project_id, current_user.id)
    PermissionService.verify_ba_role(current_user)

    from app.models.requirement import Requirement, RequirementStatus
    from app.models.test_case import TestCase

    req = (
        db.query(Requirement)
        .filter(
            Requirement.project_id == project_id,
            Requirement.req_id == req_id,
            Requirement.status == RequirementStatus.active,
        )
        .first()
    )
    if not req:
        raise HTTPException(status_code=404, detail="Requirement not found.")

    tc = TestCase(
        requirement_id=req.id,
        title=payload.title,
        preconditions=payload.preconditions,
        steps=json.dumps(payload.steps),
        expected_result=payload.expected_result,
        is_auto_generated=False,
    )
    db.add(tc)
    db.commit()
    db.refresh(tc)
    return _tc_out(tc)


@router.put(
    "/{project_id}/rtm/requirements/{req_id}/test-cases/{tc_id}",
    response_model=TestCaseOut,
    tags=["rtm"],
)
def update_test_case(
    project_id: int,
    req_id: str,
    tc_id: int,
    payload: TestCaseUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    PermissionService.verify_project_access(db, project_id, current_user.id)
    PermissionService.verify_ba_role(current_user)

    from app.models.requirement import Requirement, RequirementStatus
    from app.models.test_case import TestCase

    req = (
        db.query(Requirement)
        .filter(
            Requirement.project_id == project_id,
            Requirement.req_id == req_id,
            Requirement.status == RequirementStatus.active,
        )
        .first()
    )
    if not req:
        raise HTTPException(status_code=404, detail="Requirement not found.")

    tc = (
        db.query(TestCase)
        .filter(TestCase.id == tc_id, TestCase.requirement_id == req.id)
        .first()
    )
    if not tc:
        raise HTTPException(status_code=404, detail="Test case not found.")

    if payload.title is not None:
        tc.title = payload.title
    if payload.preconditions is not None:
        tc.preconditions = payload.preconditions
    if payload.steps is not None:
        tc.steps = json.dumps(payload.steps)
    if payload.expected_result is not None:
        tc.expected_result = payload.expected_result

    db.commit()
    db.refresh(tc)
    return _tc_out(tc)


@router.delete(
    "/{project_id}/rtm/requirements/{req_id}/test-cases/{tc_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    tags=["rtm"],
)
def delete_test_case(
    project_id: int,
    req_id: str,
    tc_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    PermissionService.verify_project_access(db, project_id, current_user.id)
    PermissionService.verify_ba_role(current_user)

    from app.models.requirement import Requirement, RequirementStatus
    from app.models.test_case import TestCase

    req = (
        db.query(Requirement)
        .filter(
            Requirement.project_id == project_id,
            Requirement.req_id == req_id,
            Requirement.status == RequirementStatus.active,
        )
        .first()
    )
    if not req:
        raise HTTPException(status_code=404, detail="Requirement not found.")

    tc = (
        db.query(TestCase)
        .filter(TestCase.id == tc_id, TestCase.requirement_id == req.id)
        .first()
    )
    if not tc:
        raise HTTPException(status_code=404, detail="Test case not found.")

    db.delete(tc)
    db.commit()


# ─── Export ────────────────────────────────────────────────────────────────────

@router.get("/{project_id}/rtm/export", tags=["rtm"])
def export_rtm(
    project_id: int,
    format: str = Query("csv"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    PermissionService.verify_project_access(db, project_id, current_user.id)

    from app.models.requirement import Requirement, RequirementStatus
    from app.models.traceability_link import TraceabilityLink
    from app.models.test_case import TestCase
    from app.services.export_service import export_rtm_csv, export_rtm_pdf

    requirements = (
        db.query(Requirement)
        .filter(
            Requirement.project_id == project_id,
            Requirement.status == RequirementStatus.active,
        )
        .order_by(Requirement.req_id)
        .all()
    )
    req_ids = [r.id for r in requirements]
    links = (
        db.query(TraceabilityLink)
        .filter(TraceabilityLink.requirement_id.in_(req_ids))
        .all()
        if req_ids
        else []
    )
    test_cases = (
        db.query(TestCase)
        .filter(TestCase.requirement_id.in_(req_ids))
        .all()
        if req_ids
        else []
    )

    if format == "pdf":
        content = export_rtm_pdf(requirements, links, test_cases)
        return StreamingResponse(
            iter([content]),
            media_type="application/pdf",
            headers={"Content-Disposition": f"attachment; filename=rtm_{project_id}.pdf"},
        )
    else:
        content = export_rtm_csv(requirements, links, test_cases)
        return StreamingResponse(
            iter([content]),
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename=rtm_{project_id}.csv"},
        )


# ─── Internal Trigger ─────────────────────────────────────────────────────────

@router.post(
    "/{project_id}/rtm/_trigger",
    status_code=status.HTTP_202_ACCEPTED,
    tags=["rtm"],
)
def internal_trigger(
    project_id: int,
    payload: RTMTriggerRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    PermissionService.verify_project_access(db, project_id, current_user.id)

    from app.services.background_rtm_generator import queue_rtm_generation

    queued = queue_rtm_generation(project_id, payload.trigger.value)
    if not queued:
        return {"queued": False, "reason": "debounced"}
    return {"queued": True}
