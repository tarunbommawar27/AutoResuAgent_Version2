"""
Agent Validator
Validates generated content using custom rules and business logic.
"""

import logging
import re
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..models import GeneratedBullet, FullGeneratedPackage, JobDescription, CandidateProfile

logger = logging.getLogger(__name__)


def validate_bullet_length(
    bullet: "GeneratedBullet",
    max_len: int = 150
) -> str | None:
    """
    Validate bullet point length.

    Minimum length is enforced strictly (hard error).
    Maximum length is a soft limit used only for logging/analysis (no error).

    This allows slightly longer bullets to pass validation without triggering
    retry loops, while still providing visibility into length distribution.

    Args:
        bullet: Generated bullet to validate
        max_len: Maximum character length for soft warning (default 150)

    Returns:
        None if valid, error message string if minimum length violated

    Example:
        >>> error = validate_bullet_length(bullet, max_len=150)
        >>> if error:
        ...     print(f"Validation failed: {error}")
    """
    bullet_len = len(bullet.text)

    # Check minimum length (HARD CHECK - strictly enforced)
    if bullet_len < 30:
        return f"Bullet '{bullet.id}' too short: {bullet_len} chars (min 30)"

    # Check maximum length (SOFT CHECK - warning only, no failure)
    if bullet_len > max_len:
        logger.warning(
            "Soft length warning: bullet '%s' length %d > max %d; keeping it anyway",
            bullet.id,
            bullet_len,
            max_len,
        )

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


def detect_bullet_hallucinations(
    bullet: "GeneratedBullet",
    job: "JobDescription",
    resume: "CandidateProfile"
) -> list[str]:
    """
    Comprehensive hallucination detection for bullets.

    Checks for three types of potential hallucinations:
    1. Skills not in resume
    2. Company names not in resume work history
    3. Technologies not in resume skills or job requirements

    Args:
        bullet: Generated bullet to check
        job: Target job description
        resume: Candidate's resume/profile

    Returns:
        List of warning messages (empty if no hallucinations detected)

    Example:
        >>> warnings = detect_bullet_hallucinations(bullet, job, resume)
        >>> for warning in warnings:
        ...     logger.warning(warning)
    """
    warnings = []

    # 1. Check for hallucinated skills
    # SOFT CHECK: LLM may introduce useful wording like "Data Pipelines", "DevOps", "Microservices", etc.
    # We only log when a skill phrase is not in resume.skills, but we do NOT fail validation or trigger retries.
    if bullet.skills_covered:
        resume_skills = resume.skills if resume.skills else []

        if not resume_skills:
            # Resume has no skills listed - log soft warning only
            logger.warning(
                "Soft skill consistency warning: bullet '%s' claims skills %s but resume has no skills listed. "
                "This is logged for analysis only and does NOT block validation.",
                bullet.id,
                bullet.skills_covered[:3]
            )
        else:
            # Normalize for case-insensitive comparison
            bullet_skills_lower = {skill.lower() for skill in bullet.skills_covered}
            resume_skills_lower = {skill.lower() for skill in resume_skills}

            # Find skills in bullet that aren't in resume
            missing_from_resume = bullet_skills_lower - resume_skills_lower

            if missing_from_resume:
                # Convert back to original case for warning message
                missing_original = [
                    skill for skill in bullet.skills_covered
                    if skill.lower() in missing_from_resume
                ]

                # SOFT CHECK: Only log, do NOT add to warnings list (which becomes errors)
                logger.warning(
                    "Soft skill consistency warning: bullet '%s' mentions skills %s not found in resume skills %s. "
                    "This is logged for analysis only and does NOT block validation.",
                    bullet.id,
                    missing_original,
                    resume_skills[:10]
                )
                # Do NOT add to warnings list here

    # 2. Check for hallucinated company names
    # Extract company names from resume
    resume_companies = set()
    for exp in resume.experiences:
        if exp.company:
            resume_companies.add(exp.company.lower().strip())

    if resume_companies:
        # Look for patterns like "at <CompanyName>" in bullet text
        # This is a simple heuristic - matches " at XYZ" patterns
        at_pattern = re.compile(r'\bat\s+([A-Z][A-Za-z0-9&\s]+?)(?:\s|,|\.|\)|\]|$)', re.MULTILINE)
        matches = at_pattern.findall(bullet.text)

        for match in matches:
            company_candidate = match.strip()
            # Check if this looks like a company name (has capital letter, reasonable length)
            if len(company_candidate) > 2 and company_candidate.lower() not in resume_companies:
                # Check if it's not just a common phrase
                common_phrases = {'present', 'scale', 'time', 'risk', 'cost', 'peak', 'least'}
                if company_candidate.lower() not in common_phrases:
                    warnings.append(
                        f"Bullet '{bullet.id}' mentions company '{company_candidate}' "
                        f"not found in resume work history. Resume companies: {list(resume_companies)[:5]}"
                    )

    # 3. Check for hallucinated technologies (SOFT CHECK - warnings only, no hard failure)
    # Build whitelist from resume skills and job requirements
    technology_whitelist = set()

    # Add resume skills
    if resume.skills:
        technology_whitelist.update(s.lower() for s in resume.skills)

    # Add job required skills
    if job.required_skills:
        technology_whitelist.update(s.lower() for s in job.required_skills)

    # Add job nice-to-have skills
    if job.nice_to_have_skills:
        technology_whitelist.update(s.lower() for s in job.nice_to_have_skills)

    if technology_whitelist:
        # Extract potential technology names from bullet text
        # Look for capitalized words/acronyms that might be technologies
        # Pattern: capitalized words, acronyms (2+ caps), or hyphenated tech names
        tech_pattern = re.compile(r'\b([A-Z][a-z]+(?:[A-Z][a-z]+)*|[A-Z]{2,}|[A-Z][a-z]+-[A-Z][a-z]+)\b')
        potential_techs = tech_pattern.findall(bullet.text)

        # Common non-technology words to ignore
        common_words = {
            'built', 'developed', 'created', 'designed', 'implemented', 'achieved',
            'led', 'managed', 'worked', 'used', 'improved', 'reduced', 'increased',
            'i', 'january', 'february', 'march', 'april', 'may', 'june',
            'july', 'august', 'september', 'october', 'november', 'december',
            'monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday',
            'collaborated', 'trained', 'coordinated', 'organized', 'supported'
        }

        unknown_techs = []
        for tech in potential_techs:
            tech_lower = tech.lower()
            # Skip if it's in the whitelist or a common word
            if tech_lower not in technology_whitelist and tech_lower not in common_words:
                # Additional check: only flag if it looks like a technology (length > 2, not all caps unless acronym)
                if len(tech) > 2 and (len(tech) <= 4 or not tech.isupper() or len(tech) >= 6):
                    # Only flag technologies that appear to be specific tools/frameworks
                    # Skip if it's likely a proper noun in a sentence context
                    if not tech[0].isupper() or len(tech) > 3:  # Basic heuristic
                        unknown_techs.append(tech)

        # SOFT CHECK: Only log warnings, do NOT add to warnings list (which becomes errors)
        # This avoids false positives on verbs like "Collaborated", "Trained", etc.
        if unknown_techs:
            logger.warning(
                f"Soft tech hallucination warning: bullet '{bullet.id}' mentions possible tech(s) {unknown_techs} "
                f"not in resume/job terms. This is logged for informational purposes only."
            )

    return warnings


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

            # Comprehensive hallucination detection
            hallucination_warnings = detect_bullet_hallucinations(bullet, job, resume)
            if hallucination_warnings:
                for warning in hallucination_warnings:
                    logger.warning(f"[Hallucination Warning] {warning}")
                    # Add warnings to errors list so they're tracked in metrics
                    errors.append(warning)

    else:
        errors.append("Package has no bullets")

    # Validate cover letter
    if pkg.cover_letter:
        # Check that job_id matches
        if pkg.cover_letter.job_id and pkg.cover_letter.job_id != job.job_id:
            errors.append(
                f"Cover letter job_id '{pkg.cover_letter.job_id}' "
                f"does not match job '{job.job_id}'"
            )

        # Minimal cover letter length check (using `text`)
        if hasattr(pkg.cover_letter, 'text') and pkg.cover_letter.text:
            if len(pkg.cover_letter.text.strip()) < 200:
                errors.append("Cover letter text too short (< 200 chars)")
        else:
            errors.append("Cover letter missing text content")

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


def validate_skill_coverage_strict(
    bullets: list["GeneratedBullet"],
    job: "JobDescription",
    minimum_coverage: float = 0.8
) -> list[str]:
    """
    Validate that bullets adequately cover required skills.

    Args:
        bullets: List of generated bullets
        job: Job description with required skills
        minimum_coverage: Minimum fraction of skills that must be covered (0.0-1.0)

    Returns:
        List of error messages (empty if validation passes)
    """
    errors = []

    if not job.required_skills:
        return errors  # No skills to validate

    # Collect all skills mentioned across all bullets
    all_mentioned_skills = set()
    for bullet in bullets:
        if bullet.skills_covered:
            # Normalize to lowercase for comparison
            all_mentioned_skills.update(s.lower().strip() for s in bullet.skills_covered)

    # Check coverage of required skills
    required_skills_lower = {s.lower().strip() for s in job.required_skills}
    missing_skills = []

    for req_skill in required_skills_lower:
        # Check exact match or if skill is substring of mentioned skill
        found = False
        for mentioned in all_mentioned_skills:
            if req_skill in mentioned or mentioned in req_skill:
                found = True
                break
        if not found:
            missing_skills.append(req_skill)

    # Calculate coverage
    coverage = 1.0 - (len(missing_skills) / len(job.required_skills))

    if missing_skills:
        errors.append(
            f"Missing required skills in bullets: {', '.join(missing_skills)} "
            f"(coverage: {coverage:.1%}, need: {minimum_coverage:.1%})"
        )

    if coverage < minimum_coverage:
        errors.append(
            f"Insufficient skill coverage: {coverage:.1%} (minimum required: {minimum_coverage:.1%})"
        )

    return errors


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

        # Comprehensive hallucination detection
        hallucination_warnings = detect_bullet_hallucinations(bullet, job, resume)
        if hallucination_warnings:
            errors.extend(hallucination_warnings)

    # ADD THIS: Skill coverage check (collective across all bullets)
    skill_coverage_errors = validate_skill_coverage_strict(bullets, job, minimum_coverage=0.8)
    errors.extend(skill_coverage_errors)

    return errors
