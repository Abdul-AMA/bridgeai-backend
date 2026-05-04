"""
LLM Factory - Centralized LLM instance creation with multi-provider support.

This factory provides a single point of configuration for all AI models used in the application.
Supports multiple providers: Anthropic, OpenAI, Google Gemini, Groq, and Mistral.

Provider: Multiple (Anthropic, OpenAI, Google, Groq, Mistral)
Integration: langchain-anthropic, langchain-openai, langchain-google-genai, langchain-groq, langchain-mistralai
"""

import logging
from typing import Any, Dict, Optional, Union
from langchain_anthropic import ChatAnthropic
from langchain_openai import ChatOpenAI
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_groq import ChatGroq
from langchain_mistralai import ChatMistralAI
from app.core.config import settings

logger = logging.getLogger(__name__)


class LLMProvider:
    """Enum-like class for AI providers."""

    ANTHROPIC = "anthropic"
    OPENAI = "openai"
    GEMINI = "gemini"
    GROQ = "groq"
    MISTRAL = "mistral"


class LLMFactory:
    """
    Factory class for creating LLM instances with multi-provider support.

    This factory supports multiple AI providers while maintaining a consistent interface.
    Falls back to default Anthropic configuration when user-specific config is not available.
    """

    @staticmethod
    def create_llm(
        provider: str,
        model: str,
        api_key: str,
        temperature: float = 0.3,
        max_tokens: Optional[int] = None,
    ) -> Any:
        """
        Create an LLM instance for the specified provider.

        Args:
            provider: Provider name (anthropic, openai, gemini, groq, mistral)
            model: Model identifier
            api_key: API key for the provider
            temperature: Sampling temperature (default: 0.3)
            max_tokens: Maximum tokens to generate (default: provider-specific)

        Returns:
            LangChain chat model instance

        Raises:
            ValueError: If provider is not supported
        """
        provider_lower = provider.lower()

        if provider_lower == LLMProvider.ANTHROPIC:
            return ChatAnthropic(
                model=model,
                anthropic_api_key=api_key,
                temperature=temperature,
                max_tokens=max_tokens or 2048,
            )
        elif provider_lower == LLMProvider.OPENAI:
            return ChatOpenAI(
                model=model,
                openai_api_key=api_key,
                temperature=temperature,
                max_tokens=max_tokens or 2048,
            )
        elif provider_lower == LLMProvider.GEMINI:
            return ChatGoogleGenerativeAI(
                model=model,
                google_api_key=api_key,
                temperature=temperature,
                max_output_tokens=max_tokens or 2048,
            )
        elif provider_lower == LLMProvider.GROQ:
            return ChatGroq(
                model=model,
                groq_api_key=api_key,
                temperature=temperature,
                max_tokens=max_tokens or 2048,
            )
        elif provider_lower == LLMProvider.MISTRAL:
            return ChatMistralAI(
                model=model,
                mistral_api_key=api_key,
                temperature=temperature,
                max_tokens=max_tokens or 2048,
            )
        else:
            raise ValueError(f"Unsupported provider: {provider}")

    @staticmethod
    def create_summary_llm() -> ChatGroq:
        """Create LLM instance for project context summarization."""
        return ChatGroq(
            model=settings.LLM_CLARIFICATION_MODEL,
            groq_api_key=settings.GROQ_API_KEY,
            temperature=0.3,
            max_tokens=512,
        )

    @staticmethod
    def create_clarification_llm() -> ChatGroq:
        """Create LLM instance for clarification/ambiguity detection."""
        return ChatGroq(
            model=settings.LLM_CLARIFICATION_MODEL,
            groq_api_key=settings.GROQ_API_KEY,
            temperature=settings.LLM_CLARIFICATION_TEMPERATURE,
            max_tokens=settings.LLM_CLARIFICATION_MAX_TOKENS,
        )

    @staticmethod
    def create_template_filler_llm() -> ChatGroq:
        """Create LLM instance for template filling/CRS generation."""
        return ChatGroq(
            model=settings.LLM_TEMPLATE_FILLER_MODEL,
            groq_api_key=settings.GROQ_API_KEY,
            temperature=settings.LLM_TEMPLATE_FILLER_TEMPERATURE,
            max_tokens=settings.LLM_TEMPLATE_FILLER_MAX_TOKENS,
        )

    @staticmethod
    def create_suggestions_llm() -> ChatGroq:
        """Create LLM instance for generating improvement suggestions."""
        return ChatGroq(
            model=settings.LLM_SUGGESTIONS_MODEL,
            groq_api_key=settings.GROQ_API_KEY,
            temperature=settings.LLM_SUGGESTIONS_TEMPERATURE,
            max_tokens=settings.LLM_SUGGESTIONS_MAX_TOKENS,
        )

    @staticmethod
    def create_custom_llm(
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> ChatGroq:
        """Create a custom LLM instance, falling back to default settings."""
        return ChatGroq(
            model=model or settings.LLM_DEFAULT_MODEL,
            groq_api_key=settings.GROQ_API_KEY,
            temperature=temperature if temperature is not None else 0.3,
            max_tokens=max_tokens or 2048,
        )


def get_summary_llm() -> ChatGroq:
    """Get LLM instance for project context summarization (low token cap — summaries are short)."""
    return LLMFactory.create_summary_llm()


def get_clarification_llm() -> ChatGroq:
    """Get LLM instance for clarification tasks."""
    return LLMFactory.create_clarification_llm()


def get_template_filler_llm() -> ChatGroq:
    """Get LLM instance for template filling tasks."""
    return LLMFactory.create_template_filler_llm()


def get_suggestions_llm() -> ChatGroq:
    """Get LLM instance for suggestions generation."""
    return LLMFactory.create_suggestions_llm()


def get_llm(
    model: Optional[str] = None,
    temperature: Optional[float] = None,
    max_tokens: Optional[int] = None,
) -> ChatGroq:
    """Get a custom LLM instance."""
    return LLMFactory.create_custom_llm(model, temperature, max_tokens)
