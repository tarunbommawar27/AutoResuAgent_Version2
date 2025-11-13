"""
Anthropic Claude Client
Async client for Anthropic's Claude models with JSON output support.
"""

import asyncio
import json
from typing import TYPE_CHECKING

from .base import BaseLLMClient

if TYPE_CHECKING:
    from anthropic import AsyncAnthropic
    from ..orchestration import Config


class AnthropicLLMClient(BaseLLMClient):
    """
    Async Anthropic API client for Claude models.

    Features:
    - JSON mode via prompt engineering
    - Automatic retry with exponential backoff
    - Configuration from Config object
    - Async generation

    Note:
        Anthropic doesn't have native JSON mode like OpenAI,
        so we use clear prompt instructions to request JSON output.

    Example:
        >>> from src.orchestration import get_config
        >>> config = get_config()
        >>> client = AnthropicLLMClient(config)
        >>> result = await client.generate(
        ...     system_prompt="You are a helpful assistant",
        ...     user_prompt="Write a haiku about Python",
        ...     json_mode=False
        ... )
    """

    def __init__(self, config: "Config"):
        """
        Initialize Anthropic client.

        Args:
            config: Application configuration with anthropic_api_key and model_anthropic

        Raises:
            ValueError: If anthropic_api_key not set in config
        """
        super().__init__(config)

        if not config.anthropic_api_key:
            raise ValueError(
                "Anthropic API key not found in config. "
                "Set ANTHROPIC_API_KEY environment variable or in .env file."
            )

        # Lazy import to avoid dependency at module load
        from anthropic import AsyncAnthropic

        self.client: "AsyncAnthropic" = AsyncAnthropic(
            api_key=config.anthropic_api_key,
        )
        self.model = config.model_anthropic
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
        Generate text using Anthropic's API.

        Args:
            system_prompt: System instruction
            user_prompt: User message
            json_mode: If True, instruct model to output JSON

        Returns:
            Generated text (raw JSON string if json_mode=True)

        Raises:
            Exception: If API call fails

        Note:
            Unlike OpenAI, Anthropic doesn't have native JSON mode.
            We use prompt engineering to request JSON output.
        """
        # Enhance system prompt for JSON mode
        if json_mode and "json" not in system_prompt.lower():
            system_prompt = (
                f"{system_prompt}\n\n"
                "IMPORTANT: You must respond with valid JSON only. "
                "Do not include any text before or after the JSON object. "
                "Ensure all strings are properly quoted and the JSON is valid."
            )

        # Also add JSON instruction to user prompt for emphasis
        if json_mode and "json" not in user_prompt.lower():
            user_prompt = (
                f"{user_prompt}\n\n"
                "Remember: Respond with valid JSON only."
            )

        self.logger.debug(f"Calling Anthropic API with model={self.model}")

        try:
            response = await self.client.messages.create(
                model=self.model,
                max_tokens=self.max_tokens,
                temperature=self.temperature,
                system=system_prompt,
                messages=[
                    {"role": "user", "content": user_prompt}
                ],
            )

            # Extract content from response
            if not response.content or len(response.content) == 0:
                raise ValueError("Anthropic returned empty content")

            # Get text from first content block
            content = response.content[0].text

            if not content:
                raise ValueError("Anthropic returned empty text content")

            # If JSON mode, validate that it's actually JSON
            if json_mode:
                try:
                    json.loads(content)  # Validate JSON
                except json.JSONDecodeError as e:
                    self.logger.warning(
                        f"JSON mode enabled but response is not valid JSON: {e}"
                    )
                    # Try to extract JSON from response if wrapped in markdown
                    if "```json" in content:
                        # Extract JSON from markdown code block
                        content = content.split("```json")[1].split("```")[0].strip()
                        json.loads(content)  # Validate again
                    else:
                        raise ValueError(
                            f"Expected JSON output but got invalid JSON: {e}"
                        )

            self.logger.debug(f"Generated {len(content)} characters")
            return content

        except Exception as e:
            self.logger.error(f"Anthropic API error: {e}")
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
            f"Anthropic generation failed after {self.max_retries} attempts. "
            f"Last error: {last_error}"
        )
        self.logger.error(error_msg)
        raise Exception(error_msg)

    def get_model_name(self) -> str:
        """Get the Anthropic model name."""
        return self.model

    def __repr__(self) -> str:
        """String representation."""
        return f"AnthropicLLMClient(model={self.model})"
