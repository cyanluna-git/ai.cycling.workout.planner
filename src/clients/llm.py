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


class GroqClient(BaseLLMClient):
    """Groq API client (OpenAI-compatible, super fast!)."""

    def __init__(self, api_key: str, model: str = "llama-3.3-70b-versatile"):
        """Initialize Groq client.

        Args:
            api_key: Groq API key.
            model: Model to use (default: llama-3.3-70b-versatile).
        """
        try:
            from openai import OpenAI
        except ImportError:
            raise ImportError(
                "openai package is required. Install with: pip install openai"
            )

        # Groq uses OpenAI-compatible API
        self.client = OpenAI(api_key=api_key, base_url="https://api.groq.com/openai/v1")
        self.model = model

    def generate(self, system_prompt: str, user_prompt: str) -> str:
        """Generate a response using Groq API.

        Args:
            system_prompt: System message setting the context.
            user_prompt: User message with the actual request.

        Returns:
            Generated text response.
        """
        logger.info(f"Generating with Groq ({self.model})...")

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


class HuggingFaceClient(BaseLLMClient):
    """Hugging Face Serverless Inference API client."""

    def __init__(self, api_key: str, model: str = "mistralai/Mistral-7B-Instruct-v0.3"):
        """Initialize HuggingFace client.

        Args:
            api_key: HuggingFace API key.
            model: Model to use (default: mistralai/Mistral-7B-Instruct-v0.3).
        """
        try:
            import requests
        except ImportError:
            raise ImportError(
                "requests package is required. Install with: pip install requests"
            )

        self.api_key = api_key
        self.model = model
        self.base_url = f"https://api-inference.huggingface.co/models/{model}"

    def generate(self, system_prompt: str, user_prompt: str) -> str:
        """Generate a response using HuggingFace API.

        Args:
            system_prompt: System message setting the context.
            user_prompt: User message with the actual request.

        Returns:
            Generated text response.
        """
        import requests

        logger.info(f"Generating with HuggingFace ({self.model})...")

        headers = {"Authorization": f"Bearer {self.api_key}"}
        full_prompt = f"{system_prompt}\n\n{user_prompt}"
        payload = {
            "inputs": full_prompt,
            "parameters": {"max_new_tokens": 1000, "temperature": 0.7},
        }

        response = requests.post(self.base_url, headers=headers, json=payload)
        response.raise_for_status()

        result = response.json()
        if isinstance(result, list) and len(result) > 0:
            return result[0].get("generated_text", "")
        return ""


# Quota/Rate limit error patterns for each provider
QUOTA_ERROR_PATTERNS = [
    "quota",
    "rate limit",
    "exceeded",
    "429",
    "too many requests",
    "resource exhausted",
    "insufficient_quota",
]


def is_quota_error(error: Exception) -> bool:
    """Check if an exception is a quota/rate limit error."""
    error_str = str(error).lower()
    return any(pattern in error_str for pattern in QUOTA_ERROR_PATTERNS)


class FallbackLLMClient(BaseLLMClient):
    """LLM client with automatic fallback on quota errors.

    Tries multiple providers in order, falling back to next on quota errors.
    """

    def __init__(self, clients: list[tuple[str, BaseLLMClient]]):
        """Initialize with multiple clients.

        Args:
            clients: List of (name, client) tuples in priority order.
        """
        self.clients = clients
        if not clients:
            raise ValueError("At least one client must be provided")

    @classmethod
    def from_api_keys(
        cls,
        groq_api_key: Optional[str] = None,
        gemini_api_key: Optional[str] = None,
        hf_api_key: Optional[str] = None,
        openai_api_key: Optional[str] = None,
        groq_model: Optional[str] = None,
        gemini_model: Optional[str] = None,
        hf_model: Optional[str] = None,
        openai_model: Optional[str] = None,
    ) -> "FallbackLLMClient":
        """Create fallback client from API keys.

        Clients are added in priority order (Groq first, then Gemini, etc.)
        Models can be customized via parameters or use defaults.
        """
        clients: list[tuple[str, BaseLLMClient]] = []

        # Default models
        default_groq_model = groq_model or "llama-3.3-70b-versatile"
        default_gemini_model = gemini_model or "gemini-1.5-flash-latest"
        default_hf_model = hf_model or "mistralai/Mistral-7B-Instruct-v0.3"
        default_openai_model = openai_model or "gpt-4o-mini"

        # Priority order: Groq > Gemini > HuggingFace > OpenAI
        if groq_api_key:
            try:
                clients.append(("Groq", GroqClient(groq_api_key, default_groq_model)))
                logger.info(f"Added Groq ({default_groq_model}) to fallback chain")
            except Exception as e:
                logger.warning(f"Failed to init Groq: {e}")

        if gemini_api_key:
            try:
                clients.append(
                    ("Gemini", GeminiClient(gemini_api_key, default_gemini_model))
                )
                logger.info(f"Added Gemini ({default_gemini_model}) to fallback chain")
            except Exception as e:
                logger.warning(f"Failed to init Gemini: {e}")

        if hf_api_key:
            try:
                clients.append(
                    ("HuggingFace", HuggingFaceClient(hf_api_key, default_hf_model))
                )
                logger.info(f"Added HuggingFace ({default_hf_model}) to fallback chain")
            except Exception as e:
                logger.warning(f"Failed to init HuggingFace: {e}")

        if openai_api_key:
            try:
                clients.append(
                    ("OpenAI", OpenAIClient(openai_api_key, default_openai_model))
                )
                logger.info(f"Added OpenAI ({default_openai_model}) to fallback chain")
            except Exception as e:
                logger.warning(f"Failed to init OpenAI: {e}")

        if not clients:
            raise ValueError("No valid API keys provided for any LLM provider")

        return cls(clients)

    def generate(self, system_prompt: str, user_prompt: str) -> str:
        """Generate with automatic fallback on quota errors.

        Args:
            system_prompt: System message setting the context.
            user_prompt: User message with the actual request.

        Returns:
            Generated text response.

        Raises:
            Exception: If all providers fail.
        """
        last_error = None

        for name, client in self.clients:
            try:
                logger.info(f"Trying {name}...")
                response = client.generate(system_prompt, user_prompt)
                logger.info(f"Success with {name}")
                return response
            except Exception as e:
                last_error = e
                if is_quota_error(e):
                    logger.warning(f"{name} quota exceeded, trying next provider...")
                    continue
                else:
                    # Non-quota error, still try next provider
                    logger.warning(f"{name} failed: {e}, trying next...")
                    continue

        # All providers failed
        raise Exception(f"All LLM providers failed. Last error: {last_error}")


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
        elif provider == "groq":
            client = GroqClient(api_key=config.api_key, model=config.model)
        elif provider == "huggingface":
            client = HuggingFaceClient(api_key=config.api_key, model=config.model)
        else:
            raise ValueError(
                f"Unsupported LLM provider: {provider}. Use 'openai', 'anthropic', 'gemini', 'groq', or 'huggingface'."
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
