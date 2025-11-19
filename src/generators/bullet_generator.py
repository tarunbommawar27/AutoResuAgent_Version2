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
    llm: "BaseLLMClient"
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
    """
    # Job details
    prompt_parts = [
        "Generate tailored resume bullet points for the following job application:\n",
        f"**Job Title:** {job.title}",
        f"**Company:** {job.company}",
    ]

    if job.location:
        prompt_parts.append(f"**Location:** {job.location}")

    if job.seniority:
        prompt_parts.append(f"**Seniority Level:** {job.seniority}")

    # Responsibilities
    if job.responsibilities:
        prompt_parts.append(f"\n**Key Responsibilities ({len(job.responsibilities)}):**")
        for i, resp in enumerate(job.responsibilities, 1):
            prompt_parts.append(f"{i}. {resp}")

    # Required skills
    if job.required_skills:
        prompt_parts.append(f"\n**Required Skills:** {', '.join(job.required_skills)}")

    # Nice-to-have skills
    if job.nice_to_have_skills:
        prompt_parts.append(f"**Nice-to-Have Skills:** {', '.join(job.nice_to_have_skills)}")

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

    # Instructions for output format
    prompt_parts.append("\n**Task:**")
    prompt_parts.append(
        "Based on the job requirements and the candidate's relevant experience above, "
        "generate 5-8 tailored resume bullet points that strongly align with this job."
    )
    prompt_parts.append("\n**Output Format (JSON):**")
    prompt_parts.append("""
{
  "bullets": [
    {
      "id": "bullet-001",
      "text": "The tailored bullet point text (use action verbs, no first-person pronouns)",
      "source_experience_id": "exp-001",
      "skills_covered": ["Python", "AWS", "Machine Learning"]
    },
    ...
  ]
}
""")

    prompt_parts.append("\n**Important Rules:**")
    prompt_parts.append("- Each bullet must be 30-250 characters")
    prompt_parts.append("- Start with strong action verbs")
    prompt_parts.append("- NO first-person pronouns (I, me, my, we, our, etc.)")
    prompt_parts.append("- Include metrics and quantifiable results when possible")
    prompt_parts.append("- Match the job's required skills and responsibilities")
    prompt_parts.append("- Use the candidate's actual experience as evidence")
    prompt_parts.append('- Generate unique IDs like "bullet-001", "bullet-002", etc.')

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
