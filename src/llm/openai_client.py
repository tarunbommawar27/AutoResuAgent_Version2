"""
OpenAI LLM Client
Async client for OpenAI's GPT models with JSON mode support.
"""

import asyncio
from typing import TYPE_CHECKING

from .base import BaseLLMClient

if TYPE_CHECKING:
    from openai import AsyncOpenAI
    from ..orchestration import Config


class OpenAILLMClient(BaseLLMClient):
    """
    Async OpenAI API client for GPT models.

    Features:
    - Native JSON mode via response_format
    - Automatic retry with exponential backoff
    - Configuration from Config object
    - Async generation

    Example:
        >>> from src.orchestration import get_config
        >>> config = get_config()
        >>> client = OpenAILLMClient(config)
        >>> result = await client.generate(
        ...     system_prompt="You are a helpful assistant",
        ...     user_prompt="Write a haiku about Python",
        ...     json_mode=False
        ... )
    """

    def __init__(self, config: "Config"):
        """
        Initialize OpenAI client.

        Args:
            config: Application configuration with openai_api_key and model_openai

        Raises:
            ValueError: If openai_api_key not set in config
        """
        super().__init__(config)

        if not config.openai_api_key:
            raise ValueError(
                "OpenAI API key not found in config. "
                "Set OPENAI_API_KEY environment variable or in .env file."
            )

        # Lazy import to avoid dependency at module load
        from openai import AsyncOpenAI

        self.client: "AsyncOpenAI" = AsyncOpenAI(
            api_key=config.openai_api_key,
        )
        self.model = config.model_openai
        self.temperature = config.llm_temperature
        self.max_tokens = config.llm_max_tokens

    async def generate(
        self,
        *,
        system_prompt: str,
        user_prompt: str,
        json_mode: bool = True,
    ) -> str:
        """
        Generate text using OpenAI's API.

        Args:
            system_prompt: System instruction
            user_prompt: User message
            json_mode: If True, use JSON response format

        Returns:
            Generated text (raw JSON string if json_mode=True)

        Raises:
            Exception: If API call fails
        """
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]

        # Build API call parameters
        params = {
            "model": self.model,
            "messages": messages,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
        }

        # Add JSON mode if requested
        if json_mode:
            params["response_format"] = {"type": "json_object"}
            # Also add explicit instruction in system prompt if not already there
            if "json" not in system_prompt.lower():
                messages[0]["content"] += "\n\nRespond with valid JSON only."

        self.logger.debug(f"Calling OpenAI API with model={self.model}")

        try:
            response = await self.client.chat.completions.create(**params)

            # Extract content
            content = response.choices[0].message.content

            if not content:
                raise ValueError("OpenAI returned empty content")

            self.logger.debug(f"Generated {len(content)} characters")
            return content

        except Exception as e:
            self.logger.error(f"OpenAI API error: {e}")
            raise

    async def generate_with_retry(
        self,
        *,
        system_prompt: str,
        user_prompt: str,
        json_mode: bool = True,
    ) -> str:
        """
        Generate with automatic retry logic.

        Uses exponential backoff: 1s, 2s, 4s for retries.

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
        error_msg = (
            f"OpenAI generation failed after {self.max_retries} attempts. "
            f"Last error: {last_error}"
        )
        self.logger.error(error_msg)
        raise Exception(error_msg)

    def get_model_name(self) -> str:
        """Get the OpenAI model name."""
        return self.model

    def __repr__(self) -> str:
        """String representation."""
        return f"OpenAILLMClient(model={self.model})"
