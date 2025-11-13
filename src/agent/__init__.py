"""
Agent Package
Implements the agentic loop for resume generation.
"""

from .validator import (
    validate_bullet_length,
    validate_skill_coverage,
    detect_hallucinations,
    validate_package,
    validate_bullets_only,
    format_validation_feedback,
)
from .executor import AgentExecutor, build_package_from_components
from .async_executor import AsyncJobExecutor, run_jobs_concurrently

__all__ = [
    # Validation functions
    "validate_bullet_length",
    "validate_skill_coverage",
    "detect_hallucinations",
    "validate_package",
    "validate_bullets_only",
    "format_validation_feedback",
    # Executor classes
    "AgentExecutor",
    "AsyncJobExecutor",
    # Helper functions
    "build_package_from_components",
    "run_jobs_concurrently",
]
