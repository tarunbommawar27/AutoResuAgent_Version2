"""
Agent Validator
Validates generated content using custom rules and business logic.
"""

import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..models import GeneratedBullet, FullGeneratedPackage, JobDescription, CandidateProfile

logger = logging.getLogger(__name__)


def validate_bullet_length(
    bullet: "GeneratedBullet",
    max_len: int = 150
) -> str | None:
    """
    Validate bullet point length for LaTeX compatibility.

    Args:
        bullet: Generated bullet to validate
        max_len: Maximum character length (default 150 for standard LaTeX margins)

    Returns:
        None if valid, error message string if invalid

    Example:
        >>> error = validate_bullet_length(bullet, max_len=150)
        >>> if error:
        ...     print(f"Validation failed: {error}")
    """
    bullet_len = len(bullet.text)

    # Check minimum length (already validated by Pydantic, but double-check)
    if bullet_len < 30:
        return f"Bullet '{bullet.id}' too short: {bullet_len} chars (min 30)"

    # Check maximum length
    if bullet_len > max_len:
        return f"Bullet '{bullet.id}' too long: {bullet_len} chars (max {max_len})"

    return None


def validate_skill_coverage(
    bullet: "GeneratedBullet",
    required_skills: list[str]
) -> str | None:
    """
    Validate that bullet covers at least one required skill.

    Args:
        bullet: Generated bullet to validate
        required_skills: List of required skills from job description

    Returns:
        None if valid, error message string if invalid

    Example:
        >>> error = validate_skill_coverage(bullet, ["Python", "AWS", "Docker"])
        >>> if error:
        ...     print(f"Skill coverage issue: {error}")
    """
    if not bullet.skills_covered:
        return f"Bullet '{bullet.id}' has no skills listed"

    if not required_skills:
        # No required skills to validate against
        return None

    # Normalize for case-insensitive comparison
    bullet_skills_lower = {skill.lower() for skill in bullet.skills_covered}
    required_skills_lower = {skill.lower() for skill in required_skills}

    # Check if at least one required skill is covered
    overlap = bullet_skills_lower & required_skills_lower

    if not overlap:
        return (
            f"Bullet '{bullet.id}' does not mention any required skills. "
            f"Required: {required_skills[:5]}, "
            f"Mentioned: {bullet.skills_covered[:5]}"
        )

    return None


def detect_hallucinations(
    bullet: "GeneratedBullet",
    resume_skills: list[str]
) -> str | None:
    """
    Detect potential hallucinations by checking if claimed skills exist in resume.

    Simple heuristic: Any skill in bullet.skills_covered that's not in the
    candidate's resume skills list is flagged as a potential hallucination.

    Args:
        bullet: Generated bullet to validate
        resume_skills: List of all skills from candidate's resume

    Returns:
        None if valid, error message string if hallucination detected

    Example:
        >>> error = detect_hallucinations(bullet, resume.skills)
        >>> if error:
        ...     print(f"Hallucination detected: {error}")

    Note:
        This is a simple check. In production, you might want more sophisticated
        NLP-based hallucination detection or allow partial matches (e.g., "ML" vs "Machine Learning").
    """
    if not bullet.skills_covered:
        return None  # No skills to validate

    if not resume_skills:
        # Resume has no skills listed - flag this as suspicious
        return (
            f"Bullet '{bullet.id}' claims skills {bullet.skills_covered[:3]} "
            f"but resume has no skills listed"
        )

    # Normalize for case-insensitive comparison
    bullet_skills_lower = {skill.lower() for skill in bullet.skills_covered}
    resume_skills_lower = {skill.lower() for skill in resume_skills}

    # Find skills in bullet that aren't in resume
    hallucinated_skills = bullet_skills_lower - resume_skills_lower

    if hallucinated_skills:
        # Convert back to original case for error message
        hallucinated_original = [
            skill for skill in bullet.skills_covered
            if skill.lower() in hallucinated_skills
        ]

        return (
            f"Bullet '{bullet.id}' mentions skills not found in resume: "
            f"{hallucinated_original}. "
            f"This may be a hallucination. Resume skills: {resume_skills[:10]}"
        )

    return None


def validate_package(
    pkg: "FullGeneratedPackage",
    job: "JobDescription",
    resume: "CandidateProfile"
) -> list[str]:
    """
    Validate entire generated package (bullets + cover letter).

    Runs all validation checks and collects errors.

    Args:
        pkg: Full generated package to validate
        job: Target job description
        resume: Candidate's resume

    Returns:
        List of error messages (empty list if all valid)

    Example:
        >>> errors = validate_package(pkg, job, resume)
        >>> if errors:
        ...     print(f"Found {len(errors)} validation errors:")
        ...     for error in errors:
        ...         print(f"  - {error}")
        >>> else:
        ...     print("Package is valid!")
    """
    errors = []

    # Validate bullets
    if pkg.bullets:
        logger.debug(f"Validating {len(pkg.bullets)} bullets")

        for bullet in pkg.bullets:
            # Length validation
            error = validate_bullet_length(bullet, max_len=150)
            if error:
                errors.append(error)

            # Skill coverage validation
            if job.required_skills:
                error = validate_skill_coverage(bullet, job.required_skills)
                # Only warn, don't fail - some bullets might be general achievements
                if error:
                    logger.warning(error)

            # Hallucination detection
            error = detect_hallucinations(bullet, resume.skills)
            if error:
                errors.append(error)

    else:
        errors.append("Package has no bullets")

    # Validate cover letter
    if pkg.cover_letter:
        # Check that job_id matches
        if pkg.cover_letter.job_id != job.job_id:
            errors.append(
                f"Cover letter job_id '{pkg.cover_letter.job_id}' "
                f"does not match job '{job.job_id}'"
            )

        # Check cover letter has content
        # full_text = pkg.cover_letter.get_full_text()
        # if len(full_text) < 200:
        #     errors.append(
        #         f"Cover letter too short: {len(full_text)} chars (min 200)"
        #     )
        # elif len(full_text) > 2000:
        #     errors.append(
        #         f"Cover letter too long: {len(full_text)} chars (max 2000)"
        #     )

        # # Check sections are not empty
        # if not pkg.cover_letter.opening:
        #     errors.append("Cover letter missing opening paragraph")
        # if not pkg.cover_letter.body:
        #     errors.append("Cover letter missing body")
        # if not pkg.cover_letter.closing:
        #     errors.append("Cover letter missing closing paragraph")

    # Minimal cover letter length check (using `text`)
    if len(pkg.cover_letter.text.strip()) < 200:
        errors.append("Cover letter text too short (< 200 chars)")


    else:
        errors.append("Package has no cover letter")

    # Package-level validation
    if pkg.job_id != job.job_id:
        errors.append(
            f"Package job_id '{pkg.job_id}' does not match job '{job.job_id}'"
        )

    logger.info(f"Validation complete: {len(errors)} errors found")
    return errors


def format_validation_feedback(errors: list[str]) -> str:
    """
    Format validation errors into a feedback prompt for LLM retry.

    Args:
        errors: List of validation error messages

    Returns:
        Formatted feedback string for LLM

    Example:
        >>> feedback = format_validation_feedback(errors)
        >>> # Use this in retry prompt to fix issues
    """
    if not errors:
        return "All validation checks passed."

    feedback_parts = [
        "The generated content had the following validation issues:\n",
    ]

    for i, error in enumerate(errors, 1):
        feedback_parts.append(f"{i}. {error}")

    feedback_parts.append("\nPlease regenerate addressing these issues:")
    feedback_parts.append("- Ensure all bullets are 30-150 characters")
    feedback_parts.append("- Only use skills that exist in the candidate's resume")
    feedback_parts.append("- Cover all required skills across multiple bullets")
    feedback_parts.append("- Ensure cover letter has all sections (opening, body, closing)")

    return "\n".join(feedback_parts)


def validate_bullets_only(
    bullets: list["GeneratedBullet"],
    job: "JobDescription",
    resume: "CandidateProfile",
    max_len: int = 150
) -> list[str]:
    """
    Validate only bullets (used during iterative generation).

    Args:
        bullets: List of generated bullets
        job: Target job description
        resume: Candidate's resume
        max_len: Maximum bullet length

    Returns:
        List of error messages (empty if all valid)

    Example:
        >>> errors = validate_bullets_only(bullets, job, resume)
        >>> if errors:
        ...     # Retry bullet generation with feedback
        ...     feedback = format_validation_feedback(errors)
        ...     # ... regenerate with feedback
    """
    errors = []

    if not bullets:
        errors.append("No bullets generated")
        return errors

    for bullet in bullets:
        # Length validation
        error = validate_bullet_length(bullet, max_len=max_len)
        if error:
            errors.append(error)

        # Hallucination detection
        error = detect_hallucinations(bullet, resume.skills)
        if error:
            errors.append(error)

    return errors
