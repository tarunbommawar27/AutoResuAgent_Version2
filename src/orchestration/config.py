"""
Configuration Management
Handles application configuration and environment variables.

Uses pydantic-settings for type-safe configuration loading from:
- Environment variables
- .env file
- Default values

Configuration is lazily loaded and cached via get_config() singleton.
"""

from pathlib import Path
from typing import Optional, Literal, TYPE_CHECKING
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# Avoid heavy imports at module load time
if TYPE_CHECKING:
    from ..llm.base import BaseLLM


class Config(BaseSettings):
    """
    Application configuration loaded from environment variables and .env file.

    All fields can be set via environment variables (case-insensitive).
    Example: OPENAI_API_KEY=sk-... in .env or environment
    """

    # ===== API Keys =====
    openai_api_key: Optional[str] = Field(
        default=None,
        description="OpenAI API key for GPT models"
    )
    anthropic_api_key: Optional[str] = Field(
        default=None,
        description="Anthropic API key for Claude models"
    )

    # ===== LLM Configuration =====
    model_openai: str = Field(
        default="gpt-4o-mini",
        description="OpenAI model to use (e.g., gpt-4o, gpt-4o-mini)"
    )
    model_anthropic: str = Field(
        default="claude-3-5-sonnet-latest",
        description="Anthropic model to use (e.g., claude-3-5-sonnet-latest)"
    )
    llm_provider: Literal["openai", "anthropic"] = Field(
        default="openai",
        description="Default LLM provider"
    )
    llm_temperature: float = Field(
        default=0.7,
        ge=0.0,
        le=2.0,
        description="Temperature for LLM generation (0.0-2.0)"
    )
    llm_max_tokens: int = Field(
        default=1500,
        gt=0,
        description="Maximum tokens for LLM generation"
    )

    # ===== Embedding Configuration =====
    embedding_model: str = Field(
        default="all-MiniLM-L6-v2",
        description="Sentence-BERT model for embeddings"
    )

    # ===== Retrieval Configuration =====
    retrieval_top_k: int = Field(
        default=5,
        gt=0,
        description="Number of experiences to retrieve from FAISS"
    )

    # ===== Agent Configuration =====
    max_retries: int = Field(
        default=3,
        ge=0,
        description="Maximum retry attempts for validation loop"
    )
    concurrency_limit: int = Field(
        default=5,
        gt=0,
        description="Maximum concurrent job processing"
    )

    # ===== Paths =====
    data_dir: Path = Field(
        default=Path("./autoresuagent/data"),
        description="Base data directory"
    )
    templates_dir: Path = Field(
        default=Path("./autoresuagent/data/templates"),
        description="LaTeX template directory"
    )
    output_dir: Path = Field(
        default=Path("./autoresuagent/outputs"),
        description="Output directory for generated files"
    )
    logs_dir: Path = Field(
        default=Path("./autoresuagent/outputs/logs"),
        description="Logs directory"
    )

    # ===== Logging =====
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = Field(
        default="INFO",
        description="Logging level"
    )

    # ===== Pydantic Settings Configuration =====
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_ignore_empty=True,
        extra="ignore",  # Changed from "allow" to "ignore" for stricter validation
        case_sensitive=False,  # Allow case-insensitive env vars
    )

    @field_validator("logs_dir", "data_dir", "templates_dir", "output_dir")
    @classmethod
    def create_directories(cls, v: Path) -> Path:
        """Ensure directories exist on validation."""
        if v and not v.exists():
            v.mkdir(parents=True, exist_ok=True)
        return v

    def validate_api_keys(self, provider: Optional[str] = None) -> None:
        """
        Validate that required API keys are present for the specified provider.

        Args:
            provider: LLM provider to validate ("openai" or "anthropic").
                     If None, uses self.llm_provider

        Raises:
            ValueError: If required API key is missing
        """
        provider = provider or self.llm_provider

        if provider == "openai" and not self.openai_api_key:
            raise ValueError(
                "OpenAI API key required when using OpenAI provider. "
                "Set OPENAI_API_KEY environment variable or in .env file."
            )
        if provider == "anthropic" and not self.anthropic_api_key:
            raise ValueError(
                "Anthropic API key required when using Anthropic provider. "
                "Set ANTHROPIC_API_KEY environment variable or in .env file."
            )

    def get_model_name(self, provider: Optional[str] = None) -> str:
        """
        Get the model name for the specified provider.

        Args:
            provider: LLM provider ("openai" or "anthropic").
                     If None, uses self.llm_provider

        Returns:
            Model name string
        """
        provider = provider or self.llm_provider
        return self.model_openai if provider == "openai" else self.model_anthropic

    def get_llm_client(self, provider: Optional[str] = None) -> "BaseLLM":
        """
        Get configured LLM client instance.

        Args:
            provider: LLM provider to use. If None, uses self.llm_provider

        Returns:
            Configured LLM client (OpenAIClient or AnthropicClient)

        Raises:
            ValueError: If API key is missing or provider is invalid

        Note:
            Import is deferred to avoid circular dependencies and heavy imports
            at module load time.
        """
        from ..llm import OpenAILLMClient, AnthropicLLMClient

        provider = provider or self.llm_provider
        self.validate_api_keys(provider)

        if provider == "openai":
            return OpenAILLMClient(
                api_key=self.openai_api_key,
                model=self.model_openai,
                temperature=self.llm_temperature,
                max_tokens=self.llm_max_tokens,
                max_retries=self.max_retries,
            )
        elif provider == "anthropic":
            return AnthropicLLMClient(
                api_key=self.anthropic_api_key,
                model=self.model_anthropic,
                temperature=self.llm_temperature,
                max_tokens=self.llm_max_tokens,
                max_retries=self.max_retries,
            )
        else:
            raise ValueError(f"Unknown LLM provider: {provider}")


# ===== Singleton Pattern =====
_config_instance: Optional[Config] = None


def get_config(reload: bool = False) -> Config:
    """
    Get the global configuration singleton.

    This function lazily loads the configuration on first access and caches it.
    Subsequent calls return the cached instance unless reload=True.

    Args:
        reload: If True, reload configuration from environment/files

    Returns:
        Config instance

    Example:
        >>> config = get_config()
        >>> print(config.model_openai)
        gpt-4o-mini
    """
    global _config_instance

    if _config_instance is None or reload:
        _config_instance = Config()

    return _config_instance


def reset_config() -> None:
    """
    Reset the configuration singleton (useful for testing).

    This forces the next call to get_config() to reload from environment.
    """
    global _config_instance
    _config_instance = None
