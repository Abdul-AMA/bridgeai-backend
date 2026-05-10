"""
Tests for BackgroundCRSGenerator — singleton, deduplication, retry, and status transitions.
"""

import asyncio
import pytest

from app.services.background_crs_generator import (
    BackgroundCRSGenerator,
    CRSGenerationStatus,
    CRSGenerationTask,
)


@pytest.fixture(autouse=True)
def reset_singleton():
    """Reset the singleton between tests so each test gets a clean instance."""
    BackgroundCRSGenerator._instance = None
    import app.services.background_crs_generator as mod
    mod._generator_instance = None
    mod._worker_task = None
    yield
    BackgroundCRSGenerator._instance = None
    mod._generator_instance = None
    mod._worker_task = None


class TestSingleton:
    def test_same_instance_returned(self):
        a = BackgroundCRSGenerator()
        b = BackgroundCRSGenerator()
        assert a is b

    def test_get_crs_generator_returns_same_instance(self):
        from app.services.background_crs_generator import get_crs_generator
        g1 = get_crs_generator()
        g2 = get_crs_generator()
        assert g1 is g2


class TestQueueDeduplication:
    @pytest.mark.asyncio
    async def test_first_queue_returns_true(self):
        gen = BackgroundCRSGenerator()
        result = await gen.queue_generation(
            session_id=1, project_id=10, user_id=5, pattern="babok"
        )
        assert result is True

    @pytest.mark.asyncio
    async def test_duplicate_queue_same_session_returns_false(self):
        gen = BackgroundCRSGenerator()
        await gen.queue_generation(session_id=1, project_id=10, user_id=5)
        result = await gen.queue_generation(session_id=1, project_id=10, user_id=5)
        assert result is False

    @pytest.mark.asyncio
    async def test_different_sessions_both_queued(self):
        gen = BackgroundCRSGenerator()
        r1 = await gen.queue_generation(session_id=1, project_id=10, user_id=5)
        r2 = await gen.queue_generation(session_id=2, project_id=10, user_id=5)
        assert r1 is True
        assert r2 is True

    @pytest.mark.asyncio
    async def test_queue_adds_session_to_queued_set(self):
        gen = BackgroundCRSGenerator()
        await gen.queue_generation(session_id=42, project_id=10, user_id=5)
        assert 42 in gen.queued_sessions

    @pytest.mark.asyncio
    async def test_processing_session_cannot_be_re_queued(self):
        gen = BackgroundCRSGenerator()
        gen.processing_sessions.add(99)
        result = await gen.queue_generation(session_id=99, project_id=10, user_id=5)
        assert result is False


class TestStatusTransitions:
    def test_initial_status_is_idle(self):
        gen = BackgroundCRSGenerator()
        assert gen.get_status(session_id=1) == CRSGenerationStatus.IDLE

    @pytest.mark.asyncio
    async def test_queued_status_after_queue_generation(self):
        gen = BackgroundCRSGenerator()
        await gen.queue_generation(session_id=7, project_id=10, user_id=5)
        assert gen.get_status(7) == CRSGenerationStatus.QUEUED

    def test_unknown_session_returns_idle(self):
        gen = BackgroundCRSGenerator()
        assert gen.get_status(9999) == CRSGenerationStatus.IDLE


class TestRetryTask:
    def test_task_initial_retry_count_is_zero(self):
        task = CRSGenerationTask(
            session_id=1, project_id=10, user_id=5, pattern="ieee_830"
        )
        assert task.retry_count == 0

    def test_task_max_retries_default(self):
        task = CRSGenerationTask(
            session_id=1, project_id=10, user_id=5, pattern="ieee_830"
        )
        assert task.max_retries == 3

    def test_retry_count_increments(self):
        task = CRSGenerationTask(
            session_id=1, project_id=10, user_id=5, pattern="ieee_830"
        )
        for i in range(1, 4):
            task.retry_count = i
            assert task.retry_count == i

    def test_retry_does_not_exceed_max_retries(self):
        task = CRSGenerationTask(
            session_id=1, project_id=10, user_id=5, pattern="ieee_830", max_retries=3
        )
        assert task.retry_count < task.max_retries


class TestCancelGeneration:
    @pytest.mark.asyncio
    async def test_cancel_nonexistent_session_returns_false(self):
        gen = BackgroundCRSGenerator()
        result = await gen.cancel_generation(session_id=404)
        assert result is False

    @pytest.mark.asyncio
    async def test_cancel_active_task_returns_true(self):
        gen = BackgroundCRSGenerator()

        async def dummy():
            await asyncio.sleep(60)

        task = asyncio.create_task(dummy())
        gen.active_tasks[55] = task
        gen.processing_sessions.add(55)
        gen.session_status[55] = CRSGenerationStatus.GENERATING

        result = await gen.cancel_generation(session_id=55)
        assert result is True
        assert 55 not in gen.active_tasks
        assert 55 not in gen.processing_sessions
        assert gen.get_status(55) == CRSGenerationStatus.IDLE
        task.cancel()
