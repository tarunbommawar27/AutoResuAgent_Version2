"""
Evaluation Metrics
Metrics for assessing resume quality and job matching.
"""

from typing import List, Dict, Any, TYPE_CHECKING

if TYPE_CHECKING:
    from ..models import FullGeneratedPackage, JobDescription, CandidateProfile, GeneratedBullet


def compute_package_metrics(
    pkg: "FullGeneratedPackage",
    job: "JobDescription",
    resume: "CandidateProfile"
) -> dict:
    """
    Compute comprehensive metrics for a generated package.

    This function analyzes the quality and coverage of the generated content
    without performing validation or logging. It's a pure metrics computation.

    Args:
        pkg: Full generated package with bullets and cover letter
        job: Target job description
        resume: Candidate's resume/profile

    Returns:
        Dictionary with the following keys:
        - num_bullets: Total number of bullets generated
        - avg_bullet_length_chars: Average bullet length in characters
        - avg_bullet_length_words: Average bullet length in words
        - min_bullet_length_chars: Shortest bullet length
        - max_bullet_length_chars: Longest bullet length
        - num_required_skills: Number of required skills in job description
        - num_required_skills_covered_in_bullets: Number of required skills mentioned in bullets
        - required_skill_coverage_ratio: Ratio of required skills covered (0.0-1.0)
        - num_resume_skills: Total skills in resume
        - num_resume_skills_used_in_bullets: Number of resume skills used in bullets
        - resume_skill_usage_ratio: Ratio of resume skills used (0.0-1.0)
        - cover_letter_word_count: Word count of cover letter
        - cover_letter_paragraph_count: Number of paragraphs in cover letter
        - hallucinated_skills_count: Number of skills in bullets not in resume

    Example:
        >>> metrics = compute_package_metrics(pkg, job, resume)
        >>> print(f"Skill coverage: {metrics['required_skill_coverage_ratio']:.2%}")
    """
    # Get bullets from package
    # The package might have bullets directly or in sections
    bullets = []
    if hasattr(pkg, 'bullets') and pkg.bullets:
        bullets = pkg.bullets
    elif hasattr(pkg, 'sections') and pkg.sections:
        for section in pkg.sections:
            bullets.extend(section.bullets)

    # Initialize metrics
    metrics = {}

    # Bullet count metrics
    metrics["num_bullets"] = len(bullets)

    if bullets:
        # Bullet length metrics
        bullet_lengths_chars = [len(b.text) for b in bullets]
        bullet_lengths_words = [len(b.text.split()) for b in bullets]

        metrics["avg_bullet_length_chars"] = sum(bullet_lengths_chars) / len(bullet_lengths_chars)
        metrics["avg_bullet_length_words"] = sum(bullet_lengths_words) / len(bullet_lengths_words)
        metrics["min_bullet_length_chars"] = min(bullet_lengths_chars)
        metrics["max_bullet_length_chars"] = max(bullet_lengths_chars)

        # Collect all skills mentioned in bullets
        bullet_skills_mentioned = set()
        for bullet in bullets:
            if bullet.skills_covered:
                bullet_skills_mentioned.update(s.lower() for s in bullet.skills_covered)

        # Required skills coverage
        required_skills = job.required_skills if job.required_skills else []
        metrics["num_required_skills"] = len(required_skills)

        if required_skills:
            required_skills_lower = set(s.lower() for s in required_skills)
            covered_required = bullet_skills_mentioned & required_skills_lower
            metrics["num_required_skills_covered_in_bullets"] = len(covered_required)
            metrics["required_skill_coverage_ratio"] = len(covered_required) / len(required_skills)
        else:
            metrics["num_required_skills_covered_in_bullets"] = 0
            metrics["required_skill_coverage_ratio"] = 1.0  # No required skills means 100% coverage

        # Resume skills usage
        resume_skills = resume.skills if resume.skills else []
        metrics["num_resume_skills"] = len(resume_skills)

        if resume_skills:
            resume_skills_lower = set(s.lower() for s in resume_skills)
            used_resume_skills = bullet_skills_mentioned & resume_skills_lower
            metrics["num_resume_skills_used_in_bullets"] = len(used_resume_skills)
            metrics["resume_skill_usage_ratio"] = len(used_resume_skills) / len(resume_skills)

            # Hallucination detection: skills in bullets but not in resume
            hallucinated = bullet_skills_mentioned - resume_skills_lower
            metrics["hallucinated_skills_count"] = len(hallucinated)
        else:
            metrics["num_resume_skills_used_in_bullets"] = 0
            metrics["resume_skill_usage_ratio"] = 0.0
            # If resume has no skills, any skill in bullets is potentially hallucinated
            metrics["hallucinated_skills_count"] = len(bullet_skills_mentioned)

    else:
        # No bullets - zero out metrics
        metrics["avg_bullet_length_chars"] = 0.0
        metrics["avg_bullet_length_words"] = 0.0
        metrics["min_bullet_length_chars"] = 0
        metrics["max_bullet_length_chars"] = 0
        metrics["num_required_skills"] = len(job.required_skills) if job.required_skills else 0
        metrics["num_required_skills_covered_in_bullets"] = 0
        metrics["required_skill_coverage_ratio"] = 0.0
        metrics["num_resume_skills"] = len(resume.skills) if resume.skills else 0
        metrics["num_resume_skills_used_in_bullets"] = 0
        metrics["resume_skill_usage_ratio"] = 0.0
        metrics["hallucinated_skills_count"] = 0

    # Cover letter metrics
    if pkg.cover_letter:
        metrics["cover_letter_word_count"] = pkg.cover_letter.get_word_count()
        metrics["cover_letter_paragraph_count"] = pkg.cover_letter.get_paragraph_count()
    else:
        metrics["cover_letter_word_count"] = 0
        metrics["cover_letter_paragraph_count"] = 0

    return metrics


class ResumeMetrics:
    """
    Evaluation metrics for resume quality.

    TODO:
    - Skill match percentage
    - Keyword coverage
    - Bullet quality scores
    - ATS compatibility score
    """

    @staticmethod
    def calculate_skill_match(
        job_skills: List[str],
        resume_skills: List[str]
    ) -> float:
        """
        Calculate percentage of job skills present in resume.

        Returns:
            Match percentage (0.0 to 1.0)

        TODO: Implement with fuzzy matching / synonyms
        """
        if not job_skills:
            return 1.0

        # Simple exact match (TODO: improve with embeddings or synonyms)
        job_set = set(s.lower() for s in job_skills)
        resume_set = set(s.lower() for s in resume_skills)

        matched = job_set & resume_set
        return len(matched) / len(job_set)

    @staticmethod
    def calculate_keyword_coverage(
        job_keywords: List[str],
        resume_text: str
    ) -> Dict[str, Any]:
        """
        Calculate keyword coverage in resume.

        Returns:
            Dictionary with coverage stats

        TODO: Implement keyword analysis
        """
        resume_lower = resume_text.lower()
        found_keywords = [kw for kw in job_keywords if kw.lower() in resume_lower]

        return {
            "total_keywords": len(job_keywords),
            "found_keywords": len(found_keywords),
            "coverage": len(found_keywords) / len(job_keywords) if job_keywords else 1.0,
            "found": found_keywords,
            "missing": [kw for kw in job_keywords if kw not in found_keywords]
        }

    @staticmethod
    def evaluate_bullet_quality(bullet: str) -> Dict[str, Any]:
        """
        Evaluate quality of a single resume bullet.

        Returns:
            Dictionary with quality metrics

        TODO:
        - Check for action verbs
        - Check for quantifiable results
        - Check length
        - Check for weak phrases
        """
        return {
            "has_action_verb": False,  # TODO
            "has_metrics": False,  # TODO
            "length_ok": 50 <= len(bullet) <= 200,
            "score": 0.0  # TODO: composite score
        }
