"""
Ingestion Package
Converts raw text resumes and job descriptions into structured formats.
"""

from .resume_ingestion import parse_resume_text_to_profile
from .job_ingestion import parse_job_text_to_description

__all__ = [
    "parse_resume_text_to_profile",
    "parse_job_text_to_description",
]
