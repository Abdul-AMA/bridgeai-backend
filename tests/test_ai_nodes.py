"""Tests for AI nodes - echo, memory, and template filler nodes."""
import pytest
from unittest.mock import Mock, MagicMock, patch
from sqlalchemy.orm import Session

from app.ai.nodes.echo_node import echo_node
from app.ai.nodes.memory_node import memory_node
from app.ai.nodes.template_filler.template_filler_node import template_filler_node
from app.ai.state import AgentState


class TestEchoNode:
    """Tests for the echo node."""

    def test_echo_node_basic(self):
        """Test echo node returns echoed input."""
        state: AgentState = {
            "user_input": "Hello, World!",
            "conversation_history": [],
        }
        
        result = echo_node(state)
        
        assert "output" in result
        assert result["output"] == "Echo: Hello, World!"

    def test_echo_node_empty_input(self):
        """Test echo node with empty input."""
        state: AgentState = {
            "user_input": "",
            "conversation_history": [],
        }
        
        result = echo_node(state)
        
        assert result["output"] == "Echo: "


class TestMemoryNode:
    """Tests for the memory node."""

    def test_memory_node_stores_clear_requirement(self, db: Session):
        """Test memory node stores clear requirements."""
        state: AgentState = {
            "intent": "requirement",
            "needs_clarification": False,
            "user_input": "The system must support 1000 concurrent users",
            "db": db,
            "project_id": 1,
            "message_id": 123,
            "clarity_score": 0.95,
            "output": "Requirement received",
        }
        
        result = memory_node(state)
        
        assert "output" in result
        assert "saved to project memory" in result["output"]
        assert result["last_node"] == "memory"

    def test_memory_node_skips_unclear_requirement(self, db: Session):
        """Test memory node skips requirements needing clarification."""
        state: AgentState = {
            "intent": "requirement",
            "needs_clarification": True,
            "user_input": "The system should be fast",
            "db": db,
            "project_id": 1,
            "message_id": 123,
        }
        
        result = memory_node(state)
        
        # When skipping, returns dict with last_node but doesn't modify output
        assert result == {"last_node": "memory"}
        assert "output" not in result

    def test_memory_node_skips_non_requirement(self, db: Session):
        """Test memory node skips non-requirement intents."""
        state: AgentState = {
            "intent": "question",
            "needs_clarification": False,
            "user_input": "What features are available?",
            "db": db,
            "project_id": 1,
            "message_id": 123,
        }
        
        result = memory_node(state)
        
        assert result == {"last_node": "memory"}
        assert "output" not in result

    def test_memory_node_handles_missing_db(self):
        """Test memory node handles missing database gracefully."""
        state: AgentState = {
            "intent": "requirement",
            "needs_clarification": False,
            "user_input": "Test requirement",
            "db": None,
            "project_id": 1,
            "message_id": 123,
        }
        
        result = memory_node(state)
        
        # Should not crash, returns dict without storing
        assert result == {"last_node": "memory"}
        assert "output" not in result

    def test_memory_node_handles_missing_project_id(self, db: Session):
        """Test memory node handles missing project ID."""
        state: AgentState = {
            "intent": "requirement",
            "needs_clarification": False,
            "user_input": "Test requirement",
            "db": db,
            "project_id": None,
            "message_id": 123,
        }
        
        result = memory_node(state)
        
        assert result == {"last_node": "memory"}
        assert "output" not in result

    def test_memory_node_handles_exception(self, db: Session):
        """Test memory node handles exceptions gracefully."""
        # Create a mock db that raises an exception
        mock_db = Mock()
        mock_db.add.side_effect = Exception("Database error")
        
        state: AgentState = {
            "intent": "requirement",
            "needs_clarification": False,
            "user_input": "Test requirement",
            "db": mock_db,
            "project_id": 1,
            "message_id": 123,
            "clarity_score": 0.9,
        }
        
        # Should not crash, just return with last_node
        result = memory_node(state)
        
        # On exception, returns dict with last_node (may include output from error handling)
        assert "last_node" in result
        assert result["last_node"] == "memory"


class TestTemplateFillerNode:
    """Tests for the template filler node."""

    def test_template_filler_node_basic(self, db: Session, client_user):
        """Test template filler node basic functionality."""
        state: AgentState = {
            "user_input": "Create a user authentication system",
            "conversation_history": [
                {"role": "user", "content": "I need user authentication"},
                {"role": "assistant", "content": "What authentication method?"},
                {"role": "user", "content": "Email and password"},
            ],
            "extracted_fields": {},
            "db": db,
            "project_id": 1,
            "user_id": client_user.id,
            "crs_pattern": "ieee_830",
        }
        
        # Mock the LLM response
        with patch(
            "app.ai.nodes.template_filler.template_filler_node.LLMTemplateFiller"
        ) as mock_filler_class:
            mock_filler = MagicMock()
            mock_filler.fill_template.return_value = {
                "crs_template": {"project_title": "Auth System"},
                "crs_content": '{"project_title": "Auth System"}',
                "summary_points": ["User login", "Password hashing"],
                "extracted_fields": {"auth_method": "email_password"},
                "is_complete": True,
                "overall_summary": "Authentication system with email/password",
            }
            mock_filler_class.return_value = mock_filler
            
            result = template_filler_node(state)
            
            assert "crs_template" in result
            assert "summary_points" in result
            assert result["last_node"] == "template_filler"

    def test_template_filler_with_existing_fields(self, db: Session, client_user):
        """Test template filler preserves existing extracted fields."""
        state: AgentState = {
            "user_input": "Add two-factor authentication",
            "conversation_history": [],
            "extracted_fields": {"project_title": "Existing Project"},
            "db": db,
            "project_id": 1,
            "user_id": client_user.id,
            "crs_pattern": "babok",
        }
        
        with patch(
            "app.ai.nodes.template_filler.template_filler_node.LLMTemplateFiller"
        ) as mock_filler_class:
            mock_filler = MagicMock()
            mock_filler.fill_template.return_value = {
                "crs_template": {"project_title": "Existing Project"},
                "crs_content": '{"project_title": "Existing Project"}',
                "summary_points": ["2FA support"],
                "extracted_fields": {
                    "project_title": "Existing Project",
                    "2fa": True,
                },
                "is_complete": True,
                "overall_summary": "Added 2FA support",
            }
            mock_filler_class.return_value = mock_filler
            
            result = template_filler_node(state)
            
            # Verify extracted fields were passed
            mock_filler.fill_template.assert_called_once()
            call_args = mock_filler.fill_template.call_args
            assert call_args[1]["extracted_fields"]["project_title"] == "Existing Project"

    def test_template_filler_different_patterns(self, db: Session, client_user):
        """Test template filler works with different CRS patterns."""
        patterns = ["ieee_830", "babok", "agile_user_stories", "iso_iec_ieee_29148"]
        
        for pattern in patterns:
            state: AgentState = {
                "user_input": "Test requirement",
                "conversation_history": [],
                "extracted_fields": {},
                "db": db,
                "project_id": 1,
                "user_id": client_user.id,
                "crs_pattern": pattern,
            }
            
            with patch(
                "app.ai.nodes.template_filler.template_filler_node.LLMTemplateFiller"
            ) as mock_filler_class:
                mock_filler = MagicMock()
                mock_filler.fill_template.return_value = {
                    "crs_template": {"pattern": pattern},
                    "crs_content": '{"pattern": "' + pattern + '"}',
                    "summary_points": ["Test"],
                    "extracted_fields": {},
                    "is_complete": True,
                    "overall_summary": "Test requirement",
                }
                mock_filler_class.return_value = mock_filler
                
                result = template_filler_node(state)
                
                # Verify pattern was used
                mock_filler_class.assert_called_once_with(pattern=pattern)
