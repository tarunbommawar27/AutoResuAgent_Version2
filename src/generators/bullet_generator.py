"""
Resume Bullet Generator
Generates tailored resume bullet points using LLMs and retrieved context.
"""

import json
import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..models import JobDescription, CandidateProfile, GeneratedBullet
    from ..llm import BaseLLMClient

logger = logging.getLogger(__name__)


async def generate_bullets_for_job(
    job: "JobDescription",
    resume: "CandidateProfile",
    retrieved: dict[str, list[dict]],
    llm: "BaseLLMClient",
    validation_feedback: str | None = None
) -> list["GeneratedBullet"]:
    """
    Generate tailored resume bullets for a specific job.

    Uses retrieved relevant experiences and LLM to create bullets that:
    - Match job responsibilities and required skills
    - Use strong action verbs
    - Highlight quantifiable achievements
    - Avoid first-person pronouns

    Args:
        job: Target job description with responsibilities and skills
        resume: Candidate's full resume profile
        retrieved: Dictionary mapping each responsibility to list of relevant bullets:
            {
                "responsibility text": [
                    {"experience_id": "exp-001", "text": "bullet text", "score": 0.85},
                    ...
                ],
                ...
            }
        llm: LLM client (OpenAI or Anthropic)

    Returns:
        List of GeneratedBullet objects with validation applied

    Example:
        >>> retrieved = retrieve_relevant_experiences(job, resume, encoder, index)
        >>> bullets = await generate_bullets_for_job(job, resume, retrieved, llm)
        >>> for bullet in bullets:
        ...     print(f"{bullet.text} (from {bullet.source_experience_id})")
    """
    logger.info(f"Generating bullets for job: {job.title} at {job.company}")

    # Build system prompt
    system_prompt = """You are an expert resume writer specializing in tailoring resume content to job descriptions.

Your task is to generate compelling, professional resume bullet points that:
- Use strong action verbs (e.g., "Developed", "Optimized", "Led", "Architected")
- Include quantifiable results and metrics when possible
- Align with the job's responsibilities and required skills
- Never use first-person pronouns (I, me, my, we, our, etc.)
- Are concise (30-250 characters)
- Follow the STAR format (Situation, Task, Action, Result) when appropriate

Respond with valid JSON only."""

    # Build user prompt with job details and retrieved context
    user_prompt = _build_bullet_generation_prompt(job, resume, retrieved)

    # Add validation feedback if this is a retry
    if validation_feedback:
        user_prompt += f"""

**VALIDATION FEEDBACK FROM PREVIOUS ATTEMPT:**
The previous bullet generation had these issues:
{validation_feedback}

**IMPORTANT:** Please fix these issues in your new generation. Pay special attention to covering all missing skills.
"""

    # Generate bullets using LLM
    logger.debug(f"Calling LLM with {len(retrieved)} responsibilities")

    try:
        response = await llm.generate_with_retry(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            json_mode=True
        )

        # Parse JSON response
        data = json.loads(response)

        # Handle both {"bullets": [...]} and direct list formats
        if isinstance(data, dict) and "bullets" in data:
            bullets_data = data["bullets"]
        elif isinstance(data, list):
            bullets_data = data
        else:
            raise ValueError(f"Unexpected JSON structure: {list(data.keys())}")

        # Import here to avoid circular dependency
        from ..models import GeneratedBullet

        # Convert to GeneratedBullet objects (Pydantic will validate)
        # Post-process to ensure source_experience_id is set
        bullets = []
        for bullet_dict in bullets_data:
            # If LLM didn't provide source_experience_id, infer it from retrieved context
            llm_provided_id = bullet_dict.get("source_experience_id")

            if not llm_provided_id:
                # Try to match bullet to retrieved context based on skills/content
                source_exp_id = _infer_source_experience_id(bullet_dict, retrieved, resume)
                if source_exp_id:
                    bullet_dict["source_experience_id"] = source_exp_id
                    logger.info(f"✓ Inferred source_experience_id={source_exp_id} for bullet {bullet_dict.get('id', '?')}")
                else:
                    logger.warning(f"✗ Could not infer source_experience_id for bullet {bullet_dict.get('id', '?')}")
            else:
                logger.info(f"✓ LLM provided source_experience_id={llm_provided_id} for bullet {bullet_dict.get('id', '?')}")

            bullets.append(GeneratedBullet(**bullet_dict))

        logger.info(f"Generated {len(bullets)} bullets successfully")

        # Log summary of source_experience_id distribution
        exp_id_counts = {}
        for b in bullets:
            exp_id = b.source_experience_id
            if exp_id:
                exp_id_counts[exp_id] = exp_id_counts.get(exp_id, 0) + 1

        logger.info(f"Bullet distribution by source_experience_id: {exp_id_counts}")

        return bullets

    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse LLM response as JSON: {e}")
        raise ValueError(f"LLM did not return valid JSON: {e}")
    except Exception as e:
        logger.error(f"Bullet generation failed: {e}")
        raise


def _infer_source_experience_id(
    bullet_dict: dict,
    retrieved: dict[str, list[dict]],
    resume: "CandidateProfile"
) -> str | None:
    """
    Infer the source_experience_id for a bullet when LLM doesn't provide it.

    Uses heuristics:
    1. Find the most common experience_id in retrieved context
    2. Default to first experience if no clear match

    Args:
        bullet_dict: The bullet dictionary from LLM (may have skills_covered)
        retrieved: Retrieved context used for generation
        resume: Candidate's resume

    Returns:
        Inferred experience_id or None
    """
    # Count experience_id occurrences in retrieved context
    exp_id_counts: dict[str, int] = {}

    for responsibility, items in retrieved.items():
        for item in items:
            exp_id = item.get("experience_id")
            if exp_id:
                exp_id_counts[exp_id] = exp_id_counts.get(exp_id, 0) + 1
                logger.debug(f"Found experience_id={exp_id} in retrieved item for '{responsibility[:50]}...'")

    logger.debug(f"Experience ID counts from retrieval: {exp_id_counts}")

    # Return most common experience_id
    if exp_id_counts:
        most_common_exp_id = max(exp_id_counts.items(), key=lambda x: x[1])[0]
        logger.debug(f"Most common experience_id: {most_common_exp_id}")
        return most_common_exp_id

    # Fallback: use first experience from resume
    if resume.experiences:
        fallback_id = resume.experiences[0].id
        logger.debug(f"No experience_ids in retrieval, using fallback: {fallback_id}")
        return fallback_id

    logger.warning("Could not infer experience_id: no retrieval data and no resume experiences")
    return None


def _build_bullet_generation_prompt(
    job: "JobDescription",
    resume: "CandidateProfile",
    retrieved: dict[str, list[dict]]
) -> str:
    """
    Build the user prompt for bullet generation.

    Includes job details, responsibilities, skills, and retrieved context.
    NOW WITH STRONG EMPHASIS ON SKILL COVERAGE.
    """
    # Build required skills emphasis
    required_skills_str = ', '.join(job.required_skills) if job.required_skills else 'None specified'
    nice_skills_str = ', '.join(job.nice_to_have_skills) if job.nice_to_have_skills else 'None'

    # Start with critical requirement
    prompt_parts = [
        "Generate tailored resume bullet points for this job application.\n",
        "**CRITICAL REQUIREMENT:** You MUST ensure that collectively, your bullets cover ALL required skills listed below. Each bullet should mention at least one required skill, and all required skills must appear across the complete set of bullets.\n",
        f"**Job Title:** {job.title}",
        f"**Company:** {job.company or 'N/A'}",
    ]

    if job.location:
        prompt_parts.append(f"**Location:** {job.location}")

    if job.seniority:
        prompt_parts.append(f"**Seniority Level:** {job.seniority}")

    # EMPHASIZE required skills
    prompt_parts.append("\n**REQUIRED SKILLS (MUST COVER ALL OF THESE):**")
    prompt_parts.append(required_skills_str)

    # Nice-to-have skills
    prompt_parts.append(f"\n**Nice-to-Have Skills (bonus if included):**")
    prompt_parts.append(nice_skills_str)

    # Responsibilities
    if job.responsibilities:
        prompt_parts.append(f"\n**Job Responsibilities:**")
        for i, resp in enumerate(job.responsibilities[:8], 1):
            prompt_parts.append(f"{i}. {resp}")

    # Retrieved relevant experiences
    prompt_parts.append("\n**Candidate's Relevant Experience (Retrieved by Semantic Search):**\n")

    # Group retrieved bullets by experience_id to show context
    experience_bullets: dict[str, list[str]] = {}
    for responsibility, items in retrieved.items():
        for item in items[:3]:  # Top 3 per responsibility
            exp_id = item["experience_id"]
            if exp_id not in experience_bullets:
                experience_bullets[exp_id] = []
            experience_bullets[exp_id].append(item["text"])

    # Deduplicate and show bullets by experience
    shown_bullets = set()
    for exp_id, bullets in experience_bullets.items():
        # Find the experience to get company/role
        experience = None
        for exp in resume.experiences:
            if exp.id == exp_id:
                experience = exp
                break

        if experience:
            prompt_parts.append(f"\nFrom **{experience.role}** at **{experience.company}**:")
            for bullet in bullets:
                if bullet not in shown_bullets:
                    prompt_parts.append(f"  - {bullet}")
                    shown_bullets.add(bullet)

    # Instructions for output format with STRONG skill coverage emphasis
    target_bullets = max(5, len(job.responsibilities)) if job.responsibilities else 6
    prompt_parts.append(f"\n**Task:** Generate {target_bullets} tailored resume bullets that:")
    prompt_parts.append("1. **COVER ALL REQUIRED SKILLS** - Collectively, your bullets must mention every skill from the required list above")
    prompt_parts.append("2. Strongly align with the job responsibilities")
    prompt_parts.append("3. Use specific metrics, numbers, and impact statements where possible")
    prompt_parts.append("4. Are achievement-oriented and action-verb driven")
    prompt_parts.append("5. Are 40-200 characters each (concise but descriptive)")
    prompt_parts.append("6. Avoid first-person pronouns (I, me, my, we, our)")
    prompt_parts.append("7. Each bullet must specify which skills it covers in the skills_covered field")

    prompt_parts.append("\n**SKILL COVERAGE CHECK:** Before finalizing, verify that every required skill appears in at least one bullet's skills_covered list.")

    prompt_parts.append("\n**Output Format (JSON):**")
    prompt_parts.append("""
{
  "bullets": [
    {
      "id": "bullet-001",
      "text": "Designed and deployed scalable ML pipelines using Python and TensorFlow, reducing training time by 40%",
      "source_experience_id": "exp-001",
      "skills_covered": ["Python", "TensorFlow", "Machine Learning"]
    },
    ...
  ]
}
""")

    prompt_parts.append("\n**Remember:** Every required skill must appear in at least one bullet's skills_covered field. If a skill is missing, add another bullet to cover it.")

    return "\n".join(prompt_parts)


def _extract_experience_context(
    resume: "CandidateProfile",
    retrieved: dict[str, list[dict]],
    max_bullets_per_resp: int = 3
) -> str:
    """
    Extract and format retrieved experience context for the prompt.

    Args:
        resume: Candidate's resume
        retrieved: Retrieved bullets per responsibility
        max_bullets_per_resp: Maximum bullets to show per responsibility

    Returns:
        Formatted string of relevant experience context
    """
    context_parts = []

    for responsibility, items in retrieved.items():
        if not items:
            continue

        context_parts.append(f"\n**For responsibility:** \"{responsibility[:80]}...\"")

        # Show top matches
        for i, item in enumerate(items[:max_bullets_per_resp], 1):
            exp_id = item["experience_id"]
            text = item["text"]
            score = item["score"]

            # Find experience details
            experience = None
            for exp in resume.experiences:
                if exp.id == exp_id:
                    experience = exp
                    break

            if experience:
                context_parts.append(
                    f"  {i}. [{score:.2f}] {text}"
                )
                context_parts.append(f"     (from {experience.role} at {experience.company})")
            else:
                context_parts.append(f"  {i}. [{score:.2f}] {text}")

    return "\n".join(context_parts) if context_parts else "No relevant experience retrieved."
