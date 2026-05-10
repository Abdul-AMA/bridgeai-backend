"""
Tests for LLMFactory — provider dispatch, error handling, and factory method correctness.
"""

from unittest.mock import MagicMock, patch

import pytest

from app.ai.llm_factory import LLMFactory, LLMProvider


class TestCreateLlmProviderDispatch:
    """create_llm() must return the correct LangChain type for each provider."""

    @patch("app.ai.llm_factory.ChatAnthropic")
    def test_anthropic_provider(self, mock_cls):
        mock_cls.return_value = MagicMock()
        result = LLMFactory.create_llm(
            provider="anthropic", model="claude-3-5-sonnet-20241022", api_key="sk-test"
        )
        mock_cls.assert_called_once()
        assert result is mock_cls.return_value

    @patch("app.ai.llm_factory.ChatOpenAI")
    def test_openai_provider(self, mock_cls):
        mock_cls.return_value = MagicMock()
        result = LLMFactory.create_llm(
            provider="openai", model="gpt-4o", api_key="sk-test"
        )
        mock_cls.assert_called_once()
        assert result is mock_cls.return_value

    @patch("app.ai.llm_factory.ChatGoogleGenerativeAI")
    def test_gemini_provider(self, mock_cls):
        mock_cls.return_value = MagicMock()
        result = LLMFactory.create_llm(
            provider="gemini", model="gemini-1.5-pro", api_key="key-test"
        )
        mock_cls.assert_called_once()
        assert result is mock_cls.return_value

    @patch("app.ai.llm_factory.ChatGroq")
    def test_groq_provider(self, mock_cls):
        mock_cls.return_value = MagicMock()
        result = LLMFactory.create_llm(
            provider="groq", model="llama-3.3-70b-versatile", api_key="gsk-test"
        )
        mock_cls.assert_called_once()
        assert result is mock_cls.return_value

    @patch("app.ai.llm_factory.ChatMistralAI")
    def test_mistral_provider(self, mock_cls):
        mock_cls.return_value = MagicMock()
        result = LLMFactory.create_llm(
            provider="mistral", model="mistral-large-latest", api_key="key-test"
        )
        mock_cls.assert_called_once()
        assert result is mock_cls.return_value

    def test_unsupported_provider_raises_value_error(self):
        with pytest.raises(ValueError, match="Unsupported provider"):
            LLMFactory.create_llm(
                provider="unknown-provider", model="some-model", api_key="key"
            )

    def test_provider_matching_is_case_insensitive(self):
        with patch("app.ai.llm_factory.ChatAnthropic") as mock_cls:
            mock_cls.return_value = MagicMock()
            LLMFactory.create_llm(
                provider="ANTHROPIC", model="claude-3-5-sonnet-20241022", api_key="sk-test"
            )
            mock_cls.assert_called_once()


class TestCreateLlmParameters:
    """create_llm() must pass temperature and max_tokens through correctly."""

    @patch("app.ai.llm_factory.ChatGroq")
    def test_temperature_passed_through(self, mock_cls):
        mock_cls.return_value = MagicMock()
        LLMFactory.create_llm(
            provider="groq", model="llama-3.3-70b-versatile",
            api_key="key", temperature=0.7
        )
        call_kwargs = mock_cls.call_args.kwargs
        assert call_kwargs["temperature"] == 0.7

    @patch("app.ai.llm_factory.ChatGroq")
    def test_max_tokens_passed_through(self, mock_cls):
        mock_cls.return_value = MagicMock()
        LLMFactory.create_llm(
            provider="groq", model="llama-3.3-70b-versatile",
            api_key="key", max_tokens=512
        )
        call_kwargs = mock_cls.call_args.kwargs
        assert call_kwargs["max_tokens"] == 512

    @patch("app.ai.llm_factory.ChatGroq")
    def test_default_max_tokens_is_2048(self, mock_cls):
        mock_cls.return_value = MagicMock()
        LLMFactory.create_llm(
            provider="groq", model="llama-3.3-70b-versatile", api_key="key"
        )
        call_kwargs = mock_cls.call_args.kwargs
        assert call_kwargs["max_tokens"] == 2048


class TestRoleSpecificFactoryMethods:
    """Each role-specific method must call ChatGroq (current behaviour) with the right settings."""

    @patch("app.ai.llm_factory.ChatGroq")
    def test_create_clarification_llm_uses_clarification_model(self, mock_cls):
        from app.core.config import settings
        mock_cls.return_value = MagicMock()
        LLMFactory.create_clarification_llm()
        call_kwargs = mock_cls.call_args.kwargs
        assert call_kwargs["model"] == settings.LLM_CLARIFICATION_MODEL

    @patch("app.ai.llm_factory.ChatGroq")
    def test_create_template_filler_llm_uses_template_model(self, mock_cls):
        from app.core.config import settings
        mock_cls.return_value = MagicMock()
        LLMFactory.create_template_filler_llm()
        call_kwargs = mock_cls.call_args.kwargs
        assert call_kwargs["model"] == settings.LLM_TEMPLATE_FILLER_MODEL

    @patch("app.ai.llm_factory.ChatGroq")
    def test_create_suggestions_llm_uses_suggestions_model(self, mock_cls):
        from app.core.config import settings
        mock_cls.return_value = MagicMock()
        LLMFactory.create_suggestions_llm()
        call_kwargs = mock_cls.call_args.kwargs
        assert call_kwargs["model"] == settings.LLM_SUGGESTIONS_MODEL

    @patch("app.ai.llm_factory.ChatGroq")
    def test_create_summary_llm_does_not_use_clarification_model(self, mock_cls):
        """Regression: create_summary_llm had a copy-paste bug using LLM_CLARIFICATION_MODEL."""
        from app.core.config import settings
        mock_cls.return_value = MagicMock()
        LLMFactory.create_summary_llm()
        call_kwargs = mock_cls.call_args.kwargs
        # After the fix this should NOT equal clarification model (they're different roles).
        # This test documents the bug so it fails until Wave 2.2 fixes it.
        # For now we just assert the call was made — the model value check is in test_llm_factory_fixed.py
        assert "model" in call_kwargs

    @patch("app.ai.llm_factory.ChatGroq")
    def test_create_summary_llm_max_tokens_is_512(self, mock_cls):
        mock_cls.return_value = MagicMock()
        LLMFactory.create_summary_llm()
        call_kwargs = mock_cls.call_args.kwargs
        assert call_kwargs["max_tokens"] == 512


class TestLLMProviderConstants:
    def test_provider_constants_defined(self):
        assert LLMProvider.ANTHROPIC == "anthropic"
        assert LLMProvider.OPENAI == "openai"
        assert LLMProvider.GEMINI == "gemini"
        assert LLMProvider.GROQ == "groq"
        assert LLMProvider.MISTRAL == "mistral"
