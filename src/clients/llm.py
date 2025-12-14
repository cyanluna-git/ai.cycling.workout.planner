"""LLM API Client.

This module provides a unified interface for different LLM providers
(OpenAI, Anthropic, Google Gemini) for workout generation.
"""

import logging
from abc import ABC, abstractmethod
from typing import Optional

from ..config import LLMConfig

logger = logging.getLogger(__name__)


class BaseLLMClient(ABC):
    """Abstract base class for LLM clients."""

    @abstractmethod
    def generate(self, system_prompt: str, user_prompt: str) -> str:
        """Generate a response from the LLM.

        Args:
            system_prompt: System message setting the context.
            user_prompt: User message with the actual request.

        Returns:
            Generated text response.
        """
        pass


class OpenAIClient(BaseLLMClient):
    """OpenAI API client."""

    def __init__(self, api_key: str, model: str = "gpt-4o"):
        """Initialize OpenAI client.

        Args:
            api_key: OpenAI API key.
            model: Model to use (default: gpt-4o).
        """
        try:
            from openai import OpenAI
        except ImportError:
            raise ImportError(
                "openai package is required. Install with: pip install openai"
            )

        self.client = OpenAI(api_key=api_key)
        self.model = model

    def generate(self, system_prompt: str, user_prompt: str) -> str:
        """Generate a response using OpenAI API.

        Args:
            system_prompt: System message setting the context.
            user_prompt: User message with the actual request.

        Returns:
            Generated text response.
        """
        logger.info(f"Generating with OpenAI ({self.model})...")

        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.7,
            max_tokens=1000,
        )

        return response.choices[0].message.content or ""


class AnthropicClient(BaseLLMClient):
    """Anthropic Claude API client."""

    def __init__(self, api_key: str, model: str = "claude-3-5-sonnet-20241022"):
        """Initialize Anthropic client.

        Args:
            api_key: Anthropic API key.
            model: Model to use (default: claude-3-5-sonnet-20241022).
        """
        try:
            import anthropic
        except ImportError:
            raise ImportError(
                "anthropic package is required. Install with: pip install anthropic"
            )

        self.client = anthropic.Anthropic(api_key=api_key)
        self.model = model

    def generate(self, system_prompt: str, user_prompt: str) -> str:
        """Generate a response using Anthropic API.

        Args:
            system_prompt: System message setting the context.
            user_prompt: User message with the actual request.

        Returns:
            Generated text response.
        """
        logger.info(f"Generating with Anthropic ({self.model})...")

        response = self.client.messages.create(
            model=self.model,
            max_tokens=1000,
            system=system_prompt,
            messages=[
                {"role": "user", "content": user_prompt},
            ],
        )

        return response.content[0].text if response.content else ""


class GeminiClient(BaseLLMClient):
    """Google Gemini API client."""

    def __init__(self, api_key: str, model: str = "gemini-2.0-flash"):
        """Initialize Gemini client.

        Args:
            api_key: Google API key.
            model: Model to use (default: gemini-2.0-flash).
        """
        try:
            import google.generativeai as genai
        except ImportError:
            raise ImportError(
                "google-generativeai package is required. Install with: pip install google-generativeai"
            )

        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel(model)

    def generate(self, system_prompt: str, user_prompt: str) -> str:
        """Generate a response using Gemini API.

        Args:
            system_prompt: System message setting the context.
            user_prompt: User message with the actual request.

        Returns:
            Generated text response.
        """
        logger.info(f"Generating with Gemini...")

        # Combine prompts for Gemini
        full_prompt = f"{system_prompt}\n\n{user_prompt}"
        response = self.model.generate_content(full_prompt)

        return response.text if response.text else ""


class LLMClient:
    """Unified LLM client factory.

    Creates the appropriate LLM client based on the configuration.

    Example:
        >>> from src.config import load_config
        >>> config = load_config()
        >>> llm = LLMClient.from_config(config.llm)
        >>> response = llm.generate(
        ...     system_prompt="You are a cycling coach.",
        ...     user_prompt="Create an interval workout."
        ... )
    """

    def __init__(self, client: BaseLLMClient):
        """Initialize with a specific client.

        Args:
            client: An instance of a BaseLLMClient implementation.
        """
        self._client = client

    @classmethod
    def from_config(cls, config: LLMConfig) -> "LLMClient":
        """Create an LLM client from configuration.

        Args:
            config: LLMConfig with provider, api_key, and model.

        Returns:
            Configured LLMClient instance.

        Raises:
            ValueError: If the provider is not supported.
        """
        provider = config.provider.lower()

        if provider == "openai":
            client = OpenAIClient(api_key=config.api_key, model=config.model)
        elif provider == "anthropic":
            client = AnthropicClient(api_key=config.api_key, model=config.model)
        elif provider == "gemini":
            client = GeminiClient(api_key=config.api_key, model=config.model)
        else:
            raise ValueError(
                f"Unsupported LLM provider: {provider}. Use 'openai', 'anthropic', or 'gemini'."
            )

        logger.info(f"Initialized {provider} LLM client")
        return cls(client)

    def generate(self, system_prompt: str, user_prompt: str) -> str:
        """Generate a response from the LLM.

        Args:
            system_prompt: System message setting the context.
            user_prompt: User message with the actual request.

        Returns:
            Generated text response.
        """
        return self._client.generate(system_prompt, user_prompt)
