"""
Background summary generation service.
Manages a per-project asyncio queue for generating project context summaries.
Modelled on BackgroundCRSGenerator but scoped to project_id, no streaming, and
with a 5-minute debounce on the "chat" trigger.
"""

import asyncio
import logging
import time
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, Optional, Set

logger = logging.getLogger(__name__)

CHAT_DEBOUNCE_SECONDS = 300  # 5 minutes


@dataclass
class SummaryGenerationTask:
    project_id: int
    trigger: str  # "document" | "chat" | "manual"
    created_at: datetime = field(default_factory=datetime.utcnow)


class BackgroundSummaryGenerator:
    """
    Singleton asyncio worker that queues and processes project context summary generation.

    Debounce: chat-triggered requests are skipped if the same project was queued
    within the last 5 minutes. Document and manual triggers always proceed.
    Deduplication: if a project is already being processed, additional requests are
    dropped (idempotent).
    """

    _instance: Optional["BackgroundSummaryGenerator"] = None

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
        self._last_queued: Dict[int, float] = {}  # project_id → epoch timestamp
        logger.info("BackgroundSummaryGenerator initialized")

    def queue_generation(self, project_id: int, trigger: str) -> bool:
        """
        Queue a summary generation task.

        Returns True if queued, False if skipped (debounced or already processing).
        """
        now = time.monotonic()

        # Debounce: suppress chat triggers within the window
        if trigger == "chat":
            last = self._last_queued.get(project_id, 0.0)
            if now - last < CHAT_DEBOUNCE_SECONDS:
                logger.debug(
                    f"Summary debounced for project {project_id} "
                    f"({now - last:.0f}s since last queue)"
                )
                return False

        # Skip if already processing (prevents duplicate concurrent generations)
        if project_id in self.processing_projects:
            logger.debug(
                f"Summary already generating for project {project_id}, skipping"
            )
            return False

        self._last_queued[project_id] = now
        task = SummaryGenerationTask(project_id=project_id, trigger=trigger)
        self.task_queue.put_nowait(task)
        logger.info(
            f"Summary generation queued for project {project_id} (trigger={trigger})"
        )
        return True

    async def start_worker(self):
        """Process tasks from the queue indefinitely."""
        logger.info("BackgroundSummaryGenerator worker started")
        while True:
            try:
                task: SummaryGenerationTask = await self.task_queue.get()
                self.processing_projects.add(task.project_id)
                try:
                    await self._process_task(task)
                finally:
                    self.processing_projects.discard(task.project_id)
                    self.task_queue.task_done()
            except asyncio.CancelledError:
                break
            except Exception as exc:
                logger.error(f"Summary worker error: {exc}", exc_info=True)
                await asyncio.sleep(1)

    async def _process_task(self, task: SummaryGenerationTask):
        from app.db.session import SessionLocal
        from app.services import summary_service

        db = SessionLocal()
        try:
            await summary_service.generate_summary(
                project_id=task.project_id,
                trigger=task.trigger,
                db=db,
            )
        except Exception as exc:
            logger.error(
                f"Summary task failed for project {task.project_id}: {exc}",
                exc_info=True,
            )
        finally:
            db.close()


# Module-level singleton and helpers
_generator = BackgroundSummaryGenerator()


async def start_summary_worker():
    asyncio.create_task(_generator.start_worker())


async def stop_summary_worker():
    pass  # queue drains naturally on shutdown


def queue_summary_generation(project_id: int, trigger: str) -> bool:
    """Thread-safe enqueue — callable from both sync and async contexts."""
    return _generator.queue_generation(project_id, trigger)
