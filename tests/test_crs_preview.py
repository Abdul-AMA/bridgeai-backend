"""
Tests for CRS preview generation and API endpoints.
"""

from unittest.mock import MagicMock, Mock, patch

import pytest

from app.models.message import Message, SenderType
from app.models.session_model import SessionModel
from app.models.user import User
from app.services.crs_service import generate_preview_crs


class TestCRSPreviewGeneration:
    """Test CRS preview generation from conversation."""

    @pytest.mark.asyncio
    @patch("app.ai.nodes.template_filler.llm_template_filler.get_template_filler_llm")
    async def test_generate_preview_with_sufficient_conversation(
        self, mock_llm, db_session
    ):
        """Test preview generation with enough conversation context."""
        # Setup mock LLM
        mock_llm_instance = MagicMock()
        mock_llm.return_value = mock_llm_instance
        
        # Mock the LLM response
        mock_response = MagicMock()
        mock_response.content = '{"project_title": "Test Project", "project_description": "A comprehensive task management system with real-time collaboration", "functional_requirements": [{"id": "FR-001", "title": "Task Creation", "description": "Users should be able to create tasks with title and description", "priority": "high"}], "project_objectives": [], "target_users": [], "stakeholders": [], "performance_requirements": [], "security_requirements": [], "scalability_requirements": [], "technology_stack": {}, "integrations": [], "budget_constraints": "", "timeline_constraints": "", "technical_constraints": [], "success_metrics": [], "acceptance_criteria": [], "assumptions": [], "risks": [], "out_of_scope": []}'
        mock_llm_instance.invoke.return_value = mock_response

        # Create test data
        user = User(id=1, full_name="Test User", email="test@test.com", role="client", password_hash="test")
        db_session.add(user)
        db_session.commit()

        session = SessionModel(id=1, user_id=1, project_id=1, name="Test Session", status="active")
        db_session.add(session)
        db_session.commit()

        # Add messages
        messages = [
            Message(
                session_id=1,
                sender_type=SenderType.client,
                sender_id=1,
                content="I need a task management system",
            ),
            Message(
                session_id=1,
                sender_type=SenderType.ai,
                content="Great! Can you tell me more about the features you need?",
            ),
            Message(
                session_id=1,
                sender_type=SenderType.client,
                sender_id=1,
                content="Users should be able to create tasks, assign them, and track progress",
            ),
        ]
        for msg in messages:
            db_session.add(msg)
        db_session.commit()

        # Generate preview
        result = await generate_preview_crs(db_session, session_id=1, user_id=1)

        # Assertions
        assert "content" in result
        assert result["completeness_percentage"] >= 0
        assert result["project_id"] == 1
        assert result["session_id"] == 1
        assert "weak_fields" in result
        assert "field_sources" in result

        # Verify LLM was called
        mock_llm.assert_called_once()

    @pytest.mark.asyncio
    async def test_generate_preview_no_messages_raises_error(self, db_session):
        """Test preview generation fails with no messages."""
        user = User(id=1, full_name="Test User", email="test@test.com", role="client", password_hash="test")
        db_session.add(user)
        db_session.commit()

        session = SessionModel(id=1, user_id=1, project_id=1, name="Test Session", status="active")
        db_session.add(session)
        db_session.commit()

        # Should raise error
        with pytest.raises(ValueError, match="No messages found"):
            await generate_preview_crs(db_session, session_id=1, user_id=1)

    @pytest.mark.asyncio
    async def test_generate_preview_wrong_user_raises_error(self, db_session):
        """Test preview generation fails for wrong user."""
        user = User(id=1, full_name="Test User", email="test@test.com", role="client", password_hash="test")
        db_session.add(user)
        db_session.commit()

        session = SessionModel(id=1, user_id=1, project_id=1, name="Test Session", status="active")
        db_session.add(session)
        db_session.commit()

        # Different user ID
        with pytest.raises(ValueError, match="does not have access"):
            await generate_preview_crs(db_session, session_id=1, user_id=999)

    @pytest.mark.asyncio
    @patch("app.ai.nodes.template_filler.llm_template_filler.get_template_filler_llm")
    async def test_generate_preview_minimal_conversation_raises_error(
        self, mock_llm, db_session
    ):
        """Test preview generation with minimal conversation that produces no content."""
        # Setup mock LLM
        mock_llm_instance = MagicMock()
        mock_llm.return_value = mock_llm_instance
        
        # Mock the LLM response with empty content
        mock_response = MagicMock()
        mock_response.content = '{}'
        mock_llm_instance.invoke.return_value = mock_response

        # Create test data
        user = User(id=1, full_name="Test User", email="test@test.com", role="client", password_hash="test")
        db_session.add(user)
        db_session.commit()

        session = SessionModel(id=1, user_id=1, project_id=1, name="Test Session", status="active")
        db_session.add(session)
        db_session.commit()

        # Single vague message
        message = Message(
            session_id=1, sender_type=SenderType.client, sender_id=1, content="Hi"
        )
        db_session.add(message)
        db_session.commit()

        # Should raise error for insufficient content
        with pytest.raises(ValueError, match="No CRS content available yet"):
            await generate_preview_crs(db_session, session_id=1, user_id=1)

    @pytest.mark.asyncio
    @patch("app.ai.nodes.template_filler.llm_template_filler.get_template_filler_llm")
    async def test_generate_preview_with_weak_fields(self, mock_llm, db_session):
        """Test preview correctly identifies weak fields."""
        # Setup mock LLM
        mock_llm_instance = MagicMock()
        mock_llm.return_value = mock_llm_instance
        
        # Mock the LLM response with weak fields
        mock_response = MagicMock()
        mock_response.content = '{"project_title": "App", "project_description": "Short", "functional_requirements": [], "project_objectives": [], "target_users": [], "stakeholders": [], "performance_requirements": [], "security_requirements": [], "scalability_requirements": [], "technology_stack": {}, "integrations": [], "budget_constraints": "", "timeline_constraints": "", "technical_constraints": [], "success_metrics": [], "acceptance_criteria": [], "assumptions": [], "risks": [], "out_of_scope": []}'
        mock_llm_instance.invoke.return_value = mock_response

        # Create test data
        user = User(id=1, full_name="Test User", email="test@test.com", role="client", password_hash="test")
        db_session.add(user)
        db_session.commit()

        session = SessionModel(id=1, user_id=1, project_id=1, name="Test Session", status="active")
        db_session.add(session)
        db_session.commit()

        message = Message(
            session_id=1,
            sender_type=SenderType.client,
            sender_id=1,
            content="I want an app",
        )
        db_session.add(message)
        db_session.commit()

        # Generate preview
        result = await generate_preview_crs(db_session, session_id=1, user_id=1)

        # Assertions
        assert result["completeness_percentage"] >= 0
        assert "weak_fields" in result
        assert "field_sources" in result


class TestOptimisticLocking:
    """Test optimistic locking for CRS updates."""

    def test_update_crs_status_with_correct_version(self, db_session):
        """Test successful update with correct version."""
        from app.models.crs import CRSDocument, CRSStatus
        from app.services.crs_service import update_crs_status

        # Create CRS
        crs = CRSDocument(
            project_id=1,
            created_by=1,
            content="{}",
            summary_points="[]",
            field_sources="{}",
            version=1,
            edit_version=1,
            status=CRSStatus.draft,
        )
        db_session.add(crs)
        db_session.commit()

        # Update with correct version
        updated = update_crs_status(
            db_session,
            crs_id=crs.id,
            new_status=CRSStatus.under_review,
            expected_version=1,
        )

        assert updated.status == CRSStatus.under_review
        assert updated.edit_version == 2  # Incremented

    def test_update_crs_status_with_wrong_version_raises_error(self, db_session):
        """Test update fails with wrong version (concurrent modification)."""
        from app.models.crs import CRSDocument, CRSStatus
        from app.services.crs_service import update_crs_status

        # Create CRS
        crs = CRSDocument(
            project_id=1,
            created_by=1,
            content="{}",
            summary_points="[]",
            field_sources="{}",
            version=1,
            edit_version=2,  # Someone already updated it
            status=CRSStatus.draft,
        )
        db_session.add(crs)
        db_session.commit()

        # Try to update with old version
        with pytest.raises(ValueError, match="was modified by another user"):
            update_crs_status(
                db_session,
                crs_id=crs.id,
                new_status=CRSStatus.under_review,
                expected_version=1,  # Stale version
            )

    def test_update_crs_status_without_version_check(self, db_session):
        """Test update without version check still works (backward compatible)."""
        from app.models.crs import CRSDocument, CRSStatus
        from app.services.crs_service import update_crs_status

        # Create CRS
        crs = CRSDocument(
            project_id=1,
            created_by=1,
            content="{}",
            summary_points="[]",
            field_sources="{}",
            version=1,
            edit_version=1,
            status=CRSStatus.draft,
        )
        db_session.add(crs)
        db_session.commit()

        # Update without version check (None)
        updated = update_crs_status(
            db_session,
            crs_id=crs.id,
            new_status=CRSStatus.under_review,
            expected_version=None,  # No check
        )

        assert updated.status == CRSStatus.under_review
        assert updated.edit_version == 2


# Fixtures
@pytest.fixture
def db_session():
    """Create a test database session."""
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker

    from app.db.session import Base

    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)

    Session = sessionmaker(bind=engine)
    session = Session()

    yield session

    session.close()
