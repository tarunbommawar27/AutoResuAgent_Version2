"""
Base LLM Interface
Abstract class for language model clients with async support.
"""

from abc import ABC, abstractmethod
import asyncio
import logging
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from ..orchestration import Config

logger = logging.getLogger(__name__)


class BaseLLMClient(ABC):
    """
    Abstract base class for async LLM clients.

    Provides common interface for OpenAI and Anthropic clients with:
    - Async generation
    - JSON mode support
    - Automatic retries
    - Configuration integration (optional)

    Can be initialized with either:
    - A Config object (legacy pattern)
    - Direct parameters: api_key, model, max_tokens, temperature
    """

    def __init__(
        self,
        config: Optional["Config"] = None,
        *,
        max_retries: int = 3,
    ):
        """
        Initialize LLM client.

        Args:
            config: Application configuration object (optional, for backwards compatibility)
            max_retries: Maximum retry attempts (default: 3)

        Note:
            Subclasses should initialize their specific API clients
        """
        self.config = config
        self.max_retries = config.max_retries if config else max_retries
        self.logger = logging.getLogger(self.__class__.__name__)

    @abstractmethod
    async def generate(
        self,
        *,
        system_prompt: str,
        user_prompt: str,
        json_mode: bool = True,
    ) -> str:
        """
        Generate text from prompts.

        Args:
            system_prompt: System instruction (required, keyword-only)
            user_prompt: User message/prompt (required, keyword-only)
            json_mode: If True, request JSON output and return raw JSON string

        Returns:
            Generated text (raw JSON string if json_mode=True)

        Raises:
            Exception: If generation fails after retries

        Note:
            Implementations should:
            - Use self.config for model/temperature/max_tokens
            - Implement retry logic with self.max_retries
            - Handle API-specific errors
            - Return raw JSON string when json_mode=True
        """
        pass

    async def generate_with_retry(
        self,
        *,
        system_prompt: str,
        user_prompt: str,
        json_mode: bool = True,
    ) -> str:
        """
        Generate with automatic retry logic.

        This is a helper that subclasses can call to implement retries.
        Subclasses should implement their own retry logic or use this.

        Args:
            system_prompt: System instruction
            user_prompt: User prompt
            json_mode: Request JSON output

        Returns:
            Generated text

        Raises:
            Exception: If all retries exhausted
        """
        last_error = None

        for attempt in range(self.max_retries):
            try:
                return await self.generate(
                    system_prompt=system_prompt,
                    user_prompt=user_prompt,
                    json_mode=json_mode,
                )
            except Exception as e:
                last_error = e
                self.logger.warning(
                    f"Attempt {attempt + 1}/{self.max_retries} failed: {e}"
                )

                if attempt < self.max_retries - 1:
                    # Exponential backoff
                    wait_time = 2 ** attempt
                    self.logger.info(f"Retrying in {wait_time}s...")
                    await asyncio.sleep(wait_time)

        # All retries exhausted
        raise Exception(
            f"Generation failed after {self.max_retries} attempts. "
            f"Last error: {last_error}"
        )

    def get_model_name(self) -> str:
        """Get the model name for this client (to be overridden)."""
        return "unknown"

    def __repr__(self) -> str:
        """String representation."""
        return f"{self.__class__.__name__}(model={self.get_model_name()})"
