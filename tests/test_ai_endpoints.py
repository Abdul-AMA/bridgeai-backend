"""
Tests for AI analysis endpoints.
"""

import pytest
from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient

# Mock the graph before importing the app/router if possible, 
# but since we use TestClient with the already imported app, 
# we need to patch existing objects.

class TestAnalyzeRequirements:
    """Test the /analyze-requirements endpoint."""

    @pytest.fixture
    def mock_graph_invoke(self):
        """Mock the graph.invoke method."""
        with patch("app.api.ai.graph.invoke") as mock_invoke:
            yield mock_invoke

    def test_analyze_requirements_success(self, client: TestClient, mock_graph_invoke):
        """Test successful requirements analysis."""
        # Setup mock return value
        mock_graph_invoke.return_value = {
            "output": "Analysis complete",
            "clarification_questions": ["What is the user role?"],
            "ambiguities": [{"text": "secure", "reason": "vague"}],
            "needs_clarification": True,
            "clarity_score": 85,
            "quality_summary": "Good start",
            "last_node": "clarification"
        }

        response = client.post(
            "/api/ai/analyze-requirements",
            json={
                "user_input": "I want a secure app",
                "conversation_history": [],
                "extracted_fields": {}
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert data["output"] == "Analysis complete"
        assert len(data["clarification_questions"]) == 1
        assert data["needs_clarification"] is True
        assert data["clarity_score"] == 85

    def test_analyze_requirements_no_clarification_needed(self, client: TestClient, mock_graph_invoke):
        """Test analysis when no clarification is needed."""
        mock_graph_invoke.return_value = {
            "output": "Requirements extracted",
            "clarification_questions": [],
            "ambiguities": [],
            "needs_clarification": False,
            "clarity_score": 95,
            "quality_summary": "Excellent",
            "last_node": "memory"
        }

        response = client.post(
            "/api/ai/analyze-requirements",
            json={
                "user_input": "I want a login page",
                "conversation_history": [],
                "extracted_fields": {}
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert data["needs_clarification"] is False
        assert data["last_node"] == "memory"

    def test_analyze_requirements_error_handling(self, client: TestClient, mock_graph_invoke):
        """Test error handling during analysis."""
        # Simulate an exception in the graph
        mock_graph_invoke.side_effect = Exception("AI Service Down")

        response = client.post(
            "/api/ai/analyze-requirements",
            json={
                "user_input": "Crash me",
            }
        )

        # The endpoint catches exceptions and returns a graceful response
        assert response.status_code == 200
        data = response.json()
        assert "error" in data["output"].lower()
        assert "AI Service Down" in data["quality_summary"]
        assert data["last_node"] == "error"

    def test_analyze_requirements_validation(self, client: TestClient):
        """Test input validation."""
        response = client.post(
            "/api/ai/analyze-requirements",
            json={}  # Missing user_input
        )
        assert response.status_code == 422
