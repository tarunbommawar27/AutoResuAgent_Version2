"""
Generators Package
LLM-based content generation for resumes and cover letters.
"""

from .bullet_generator import generate_bullets_for_job
from .cover_letter_generator import generate_cover_letter

__all__ = [
    "generate_bullets_for_job",
    "generate_cover_letter",
]
