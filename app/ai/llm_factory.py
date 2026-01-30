"""
LLM Factory - Centralized LLM instance creation

This factory provides a single point of configuration for all AI models used in the application.

IMPORTANT: This system uses CLAUDE (Anthropic) EXCLUSIVELY for all AI operations.
All LLM instances are created using ChatAnthropic from langchain-anthropic.

Provider: Anthropic (https://console.anthropic.com)
Integration: langchain-anthropic
"""
import logging
from typing import Optional
from langchain_anthropic import ChatAnthropic
from app.core.config import settings

logger = logging.getLogger(__name__)


class LLMFactory:
    """
    Factory class for creating Claude LLM instances with centralized configuration.

    This factory uses CLAUDE (Anthropic) EXCLUSIVELY - all models are Claude models accessed via the Anthropic API.
    Supports different models for different components while maintaining consistency.

    All instances are ChatAnthropic objects from langchain-anthropic.
    """

    @staticmethod
    def create_clarification_llm() -> ChatAnthropic:
        """
        Create LLM instance for clarification/ambiguity detection.

        Returns:
            ChatAnthropic: Configured LLM instance for clarification tasks
        """
        return ChatAnthropic(
            model=settings.LLM_CLARIFICATION_MODEL,
            anthropic_api_key=settings.ANTHROPIC_API_KEY,
            temperature=settings.LLM_CLARIFICATION_TEMPERATURE,
            max_tokens=settings.LLM_CLARIFICATION_MAX_TOKENS
        )

    @staticmethod
    def create_template_filler_llm() -> ChatAnthropic:
        """
        Create LLM instance for template filling/CRS generation.

        Returns:
            ChatAnthropic: Configured LLM instance for template filling tasks
        """
        return ChatAnthropic(
            model=settings.LLM_TEMPLATE_FILLER_MODEL,
            anthropic_api_key=settings.ANTHROPIC_API_KEY,
            temperature=settings.LLM_TEMPLATE_FILLER_TEMPERATURE,
            max_tokens=settings.LLM_TEMPLATE_FILLER_MAX_TOKENS
        )

    @staticmethod
    def create_suggestions_llm() -> ChatAnthropic:
        """
        Create LLM instance for generating creative suggestions.

        Returns:
            ChatAnthropic: Configured LLM instance for suggestions generation
        """
        return ChatAnthropic(
            model=settings.LLM_SUGGESTIONS_MODEL,
            anthropic_api_key=settings.ANTHROPIC_API_KEY,
            temperature=settings.LLM_SUGGESTIONS_TEMPERATURE,
            max_tokens=settings.LLM_SUGGESTIONS_MAX_TOKENS
        )

    @staticmethod
    def create_custom_llm(
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None
    ) -> ChatAnthropic:
        """
        Create a custom LLM instance with specific parameters.
        Falls back to default settings for any unspecified parameters.

        Args:
            model: Model name (defaults to LLM_DEFAULT_MODEL)
            temperature: Temperature setting (defaults to 0.3)
            max_tokens: Maximum tokens (defaults to 2048)

        Returns:
            ChatAnthropic: Configured LLM instance
        """
        return ChatAnthropic(
            model=model or settings.LLM_DEFAULT_MODEL,
            anthropic_api_key=settings.ANTHROPIC_API_KEY,
            temperature=temperature if temperature is not None else 0.3,
            max_tokens=max_tokens or 2048
        )


# Convenience functions for backward compatibility
def get_clarification_llm() -> ChatAnthropic:
    """Get LLM instance for clarification tasks."""
    return LLMFactory.create_clarification_llm()


def get_template_filler_llm() -> ChatAnthropic:
    """Get LLM instance for template filling tasks."""
    return LLMFactory.create_template_filler_llm()


def get_suggestions_llm() -> ChatAnthropic:
    """Get LLM instance for suggestions generation."""
    return LLMFactory.create_suggestions_llm()


def get_llm(
    model: Optional[str] = None,
    temperature: Optional[float] = None,
    max_tokens: Optional[int] = None
) -> ChatAnthropic:
    """
    Get a custom LLM instance.

    Args:
        model: Model name (optional)
        temperature: Temperature setting (optional)
        max_tokens: Maximum tokens (optional)

    Returns:
        ChatAnthropic: Configured LLM instance
    """
    return LLMFactory.create_custom_llm(model, temperature, max_tokens)
