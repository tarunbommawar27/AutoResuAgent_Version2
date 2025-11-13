"""
Agent Planner
Analyzes job-resume fit and creates a tailoring strategy.
"""

from typing import Dict, List, Any
from ..models import JobDescription, CandidateProfile, Experience


class Planner:
    """
    Creates a plan for tailoring a resume to a job.

    TODO:
    - Analyze skill gaps
    - Identify relevant experiences
    - Determine which sections to emphasize
    - Create action plan for bullet generation
    """

    def __init__(self):
        """Initialize planner."""
        pass

    def create_plan(
        self,
        job: JobDescription,
        resume: CandidateProfile,
        retrieved_experiences: List[Experience]
    ) -> Dict[str, Any]:
        """
        Create a tailoring plan.

        Args:
            job: Target job description
            resume: Candidate's resume
            retrieved_experiences: Relevant experiences from FAISS retrieval

        Returns:
            Dictionary containing:
            - experiences_to_tailor: List of experiences to modify
            - keywords_to_include: Important keywords from job
            - tone: Recommended tone (technical, leadership, etc.)
            - focus_areas: Skills/areas to emphasize

        TODO: Implement planning logic
        """
        plan = {
            "experiences_to_tailor": [],
            "keywords_to_include": job.keywords,
            "tone": "professional",
            "focus_areas": job.required_skills[:5],  # Top 5 required skills
            "num_bullets_per_experience": 3,
        }

        # TODO: Implement sophisticated planning logic
        # - Calculate skill overlap
        # - Prioritize experiences
        # - Identify gaps

        return plan

    def analyze_skill_gap(
        self,
        job_skills: List[str],
        resume_skills: List[str]
    ) -> Dict[str, List[str]]:
        """
        Analyze skill gaps between job and resume.

        Returns:
            Dictionary with 'matched', 'missing', 'extra' skills

        TODO: Implement skill matching logic (consider synonyms)
        """
        return {
            "matched": [],
            "missing": [],
            "extra": []
        }
