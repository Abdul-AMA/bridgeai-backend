"""
Background RTM generation service.
Follows the BackgroundSummaryGenerator pattern exactly.
"""

import asyncio
import logging
import time
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, Optional, Set

logger = logging.getLogger(__name__)

DRAFT_DEBOUNCE_SECONDS = 300  # 5 minutes


@dataclass
class RTMGenerationTask:
    project_id: int
    trigger: str  # "save" | "status_change" | "draft" | "manual"
    created_at: datetime = field(default_factory=datetime.utcnow)


class BackgroundRTMGenerator:
    """
    Singleton asyncio worker that queues and processes RTM refreshes.

    Debounce: draft-triggered requests are skipped if the same project was queued
    within the last 5 minutes. All other triggers always proceed immediately.
    Deduplication: if a project is already being processed, additional requests are dropped.
    """

    _instance: Optional["BackgroundRTMGenerator"] = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._initialized = True
        self.task_queue: asyncio.Queue = asyncio.Queue()
        self.processing_projects: Set[int] = set()
        self._last_queued: Dict[int, float] = {}
        logger.info("BackgroundRTMGenerator initialized")

    def queue_generation(self, project_id: int, trigger: str) -> bool:
        """
        Queue an RTM refresh task.

        Returns True if queued, False if skipped (debounced or already processing).
        """
        now = time.monotonic()

        if trigger == "draft":
            last = self._last_queued.get(project_id, 0.0)
            if now - last < DRAFT_DEBOUNCE_SECONDS:
                logger.debug(
                    f"RTM debounced for project {project_id} "
                    f"({now - last:.0f}s since last queue)"
                )
                return False

        if project_id in self.processing_projects:
            logger.debug(
                f"RTM already generating for project {project_id}, skipping"
            )
            return False

        self._last_queued[project_id] = now
        task = RTMGenerationTask(project_id=project_id, trigger=trigger)
        self.task_queue.put_nowait(task)
        logger.info(
            f"RTM generation queued for project {project_id} (trigger={trigger})"
        )
        return True

    def is_refreshing(self, project_id: int) -> bool:
        return project_id in self.processing_projects

    async def start_worker(self):
        """Process tasks from the queue indefinitely."""
        logger.info("BackgroundRTMGenerator worker started")
        while True:
            try:
                task: RTMGenerationTask = await self.task_queue.get()
                self.processing_projects.add(task.project_id)
                try:
                    await self._process_task(task)
                finally:
                    self.processing_projects.discard(task.project_id)
                    self.task_queue.task_done()
            except asyncio.CancelledError:
                break
            except Exception as exc:
                logger.error(f"RTM worker error: {exc}", exc_info=True)
                await asyncio.sleep(1)

    async def _process_task(self, task: RTMGenerationTask):
        from app.db.session import SessionLocal

        db = SessionLocal()
        try:
            await _run_rtm_refresh(task.project_id, task.trigger, db)
        except Exception as exc:
            logger.error(
                f"RTM task failed for project {task.project_id}: {exc}",
                exc_info=True,
            )
        finally:
            db.close()


async def _run_rtm_refresh(project_id: int, trigger: str, db):
    """
    Full RTM refresh pipeline:
      1. Load the latest CRS document for the project
      2. Extract requirements (hybrid parser)
      3. Semantic match against existing requirements
      4. Persist new requirements, archive removed ones, migrate links/test cases
      5. Auto-link sources for new requirements
      6. Update rtm_status row
    """
    import asyncio
    from datetime import datetime, timezone

    from app.models.crs import CRSDocument, CRSStatus
    from app.models.requirement import Requirement, RequirementStatus
    from app.models.rtm_status import RTMStatus, RTMTrigger
    from app.services.rtm_extraction_service import extract_requirements
    from app.services.rtm_matching_service import (
        match_requirements,
        migrate_links_and_test_cases,
    )
    from app.services.rtm_source_linker import auto_link_sources

    # Mark as refreshing
    status_row = db.query(RTMStatus).filter(RTMStatus.project_id == project_id).first()
    if not status_row:
        status_row = RTMStatus(project_id=project_id)
        db.add(status_row)
    status_row.is_refreshing = True
    db.commit()

    try:
        # Get latest non-rejected CRS
        crs = (
            db.query(CRSDocument)
            .filter(
                CRSDocument.project_id == project_id,
                CRSDocument.status != CRSStatus.rejected,
            )
            .order_by(CRSDocument.created_at.desc())
            .first()
        )
        if not crs:
            logger.info(f"No CRS found for project {project_id} — skipping RTM refresh")
            return

        # Extract requirements from CRS
        new_req_data = extract_requirements(crs, db)

        # Match against existing active requirements
        match_result = match_requirements(new_req_data, project_id, db)

        # Archive removed requirements
        if match_result.removed_ids:
            db.query(Requirement).filter(
                Requirement.id.in_(match_result.removed_ids)
            ).update({"status": RequirementStatus.archived}, synchronize_session=False)

        # Persist matched requirements (replace old with new, migrate data)
        new_requirement_ids: list[int] = []
        for req_data, old_id in match_result.matched:
            new_req = Requirement(
                req_id=req_data.req_id,
                project_id=project_id,
                crs_document_id=crs.id,
                section=req_data.section,
                description=req_data.description,
                full_text=req_data.full_text,
                status=RequirementStatus.active,
            )
            db.add(new_req)
            db.flush()
            migrate_links_and_test_cases(old_id, new_req.id, db)
            # Archive the old one
            db.query(Requirement).filter(Requirement.id == old_id).update(
                {"status": RequirementStatus.archived}, synchronize_session=False
            )
            new_requirement_ids.append(new_req.id)

        # Persist unmatched (new) requirements
        for req_data in match_result.unmatched:
            new_req = Requirement(
                req_id=req_data.req_id,
                project_id=project_id,
                crs_document_id=crs.id,
                section=req_data.section,
                description=req_data.description,
                full_text=req_data.full_text,
                status=RequirementStatus.active,
            )
            db.add(new_req)
            db.flush()
            new_requirement_ids.append(new_req.id)

        db.commit()

        # Auto-link sources for all new requirements
        all_new = (
            db.query(Requirement)
            .filter(Requirement.id.in_(new_requirement_ids))
            .all()
        )
        for req in all_new:
            try:
                auto_link_sources(req, project_id, db)
            except Exception as exc:
                logger.warning(f"Source linking failed for req {req.id}: {exc}")
        db.commit()

        # Update rtm_status counts
        from app.models.traceability_link import TraceabilityLink
        from app.models.test_case import TestCase
        from sqlalchemy import func

        total = (
            db.query(func.count(Requirement.id))
            .filter(
                Requirement.project_id == project_id,
                Requirement.status == RequirementStatus.active,
            )
            .scalar()
        ) or 0

        unverified = (
            db.query(func.count(Requirement.id))
            .filter(
                Requirement.project_id == project_id,
                Requirement.status == RequirementStatus.active,
            )
            .filter(
                ~db.query(TraceabilityLink.id)
                .filter(TraceabilityLink.requirement_id == Requirement.id)
                .exists()
            )
            .scalar()
        ) or 0

        untested = (
            db.query(func.count(Requirement.id))
            .filter(
                Requirement.project_id == project_id,
                Requirement.status == RequirementStatus.active,
            )
            .filter(
                ~db.query(TestCase.id)
                .filter(TestCase.requirement_id == Requirement.id)
                .exists()
            )
            .scalar()
        ) or 0

        trigger_enum = RTMTrigger[trigger] if trigger in RTMTrigger.__members__ else RTMTrigger.manual
        status_row.is_refreshing = False
        status_row.last_refreshed_at = datetime.now(timezone.utc)
        status_row.last_trigger = trigger_enum
        status_row.requirement_count = total
        status_row.unverified_count = unverified
        status_row.untested_count = untested
        db.commit()

        logger.info(
            f"RTM refresh complete for project {project_id}: "
            f"{total} requirements, {unverified} unverified, {untested} untested"
        )

    except Exception:
        status_row.is_refreshing = False
        db.commit()
        raise


# Module-level singleton and helpers
_generator = BackgroundRTMGenerator()
_event_loop: asyncio.AbstractEventLoop | None = None


async def start_rtm_worker():
    global _event_loop
    _event_loop = asyncio.get_running_loop()
    asyncio.create_task(_generator.start_worker())


async def stop_rtm_worker():
    pass  # queue drains naturally on shutdown


def queue_rtm_generation(project_id: int, trigger: str) -> bool:
    """Enqueue from async context (event loop thread)."""
    return _generator.queue_generation(project_id, trigger)


def queue_rtm_generation_from_thread(project_id: int, trigger: str) -> bool:
    """
    Thread-safe enqueue for use from sync background threads.
    """
    if _event_loop is not None and _event_loop.is_running():
        _event_loop.call_soon_threadsafe(
            lambda: _generator.queue_generation(project_id, trigger)
        )
        return True
    return _generator.queue_generation(project_id, trigger)
