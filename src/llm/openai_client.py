"""
OpenAI LLM Client
Async client for OpenAI's GPT models with JSON mode support.
"""

import asyncio
from typing import TYPE_CHECKING, Optional, Union

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
    - Configuration from Config object OR direct parameters
    - Async generation

    Can be initialized two ways:

    1. With Config object (legacy):
        >>> from src.orchestration import get_config
        >>> config = get_config()
        >>> client = OpenAILLMClient(config)

    2. With direct parameters:
        >>> client = OpenAILLMClient(
        ...     api_key="sk-...",
        ...     model="gpt-4o-mini",
        ...     max_tokens=4096,
        ...     temperature=0.0
        ... )
    """

    def __init__(
        self,
        config_or_api_key: Union["Config", str, None] = None,
        *,
        api_key: Optional[str] = None,
        model: str = "gpt-4o-mini",
        max_tokens: int = 4096,
        temperature: float = 0.0,
        max_retries: int = 3,
    ):
        """
        Initialize OpenAI client.

        Args:
            config_or_api_key: Either a Config object (legacy) or API key string
            api_key: OpenAI API key (keyword-only, alternative to config_or_api_key)
            model: Model name (default: gpt-4o-mini)
            max_tokens: Maximum tokens for generation (default: 4096)
            temperature: Temperature for generation (default: 0.0)
            max_retries: Maximum retry attempts (default: 3)

        Raises:
            ValueError: If no API key is provided

        Examples:
            # Using Config object
            >>> client = OpenAILLMClient(config)

            # Using direct parameters
            >>> client = OpenAILLMClient(
            ...     api_key="sk-...",
            ...     model="gpt-4o-mini",
            ...     max_tokens=1024
            ... )
        """
        # Determine if config_or_api_key is a Config object or string
        config = None
        resolved_api_key = api_key

        if config_or_api_key is not None:
            # Check if it's a Config object (has openai_api_key attribute)
            if hasattr(config_or_api_key, 'openai_api_key'):
                config = config_or_api_key
                resolved_api_key = config.openai_api_key
                model = config.model_openai
                temperature = config.llm_temperature
                max_tokens = config.llm_max_tokens
                max_retries = config.max_retries
            elif isinstance(config_or_api_key, str):
                # It's an API key string
                resolved_api_key = config_or_api_key

        # Initialize base class
        super().__init__(config, max_retries=max_retries)

        # Validate API key
        if not resolved_api_key:
            raise ValueError(
                "OpenAI API key required. Either pass a Config object, "
                "provide api_key parameter, or set OPENAI_API_KEY environment variable."
            )

        # Store parameters
        self.api_key = resolved_api_key
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens

        # Lazy import to avoid dependency at module load
        from openai import AsyncOpenAI

        self.client: "AsyncOpenAI" = AsyncOpenAI(
            api_key=self.api_key,
        )

    async def generate(
        self,
        prompt: Optional[str] = None,
        *,
        system_prompt: Optional[str] = None,
        user_prompt: Optional[str] = None,
        json_mode: bool = False,
    ) -> str:
        """
        Generate text using OpenAI's API.

        Supports two calling patterns:
        1. Simple: generate(prompt) - Single-turn generation
        2. Advanced: generate(system_prompt=..., user_prompt=..., json_mode=...)

        Args:
            prompt: Single prompt for simple generation (positional)
            system_prompt: System instruction (keyword-only)
            user_prompt: User message (keyword-only)
            json_mode: If True, use JSON response format

        Returns:
            Generated text (raw JSON string if json_mode=True)

        Raises:
            Exception: If API call fails
        """
        # Handle both calling patterns
        if prompt is not None:
            # Simple pattern: generate(prompt)
            messages = [
                {"role": "user", "content": prompt}
            ]
        elif system_prompt is not None and user_prompt is not None:
            # Advanced pattern: generate(system_prompt=..., user_prompt=...)
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ]
        else:
            raise ValueError(
                "Either provide 'prompt' (simple) or both 'system_prompt' and 'user_prompt' (advanced)"
            )

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
