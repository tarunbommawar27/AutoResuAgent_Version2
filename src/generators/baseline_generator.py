"""
Baseline Generator
Simple one-shot LLM generation without retrieval or validation.

This is used for baseline comparison to demonstrate the value of the full
AutoResuAgent system with retrieval, validation, and retry loops.
"""

import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..models import JobDescription, CandidateProfile, GeneratedBullet, GeneratedCoverLetter
    from ..llm import BaseLLMClient

logger = logging.getLogger(__name__)


async def generate_bullets_baseline(
    job: "JobDescription",
    resume: "CandidateProfile",
    llm: "BaseLLMClient"
) -> list["GeneratedBullet"]:
    """
    Baseline bullet generation using one-shot LLM without retrieval.

    This is a simple baseline that:
    - Does NOT use SentenceBERT retrieval
    - Does NOT use FAISS indexing
    - Does NOT validate or retry
    - Just asks LLM to rewrite bullets for the job

    Args:
        job: Target job description
        resume: Candidate's resume/profile
        llm: LLM client for generation

    Returns:
        List of generated bullets (may contain hallucinations)

    Note:
        This is intentionally simple to serve as a baseline comparison.
        For mode="baseline" evaluation runs.
    """
    from ..models import GeneratedBullet

    logger.info("Generating bullets using baseline (no retrieval)")

    # Build simple prompt with all resume bullets from experiences + projects
    all_bullets = []
    for exp in resume.experiences:
        all_bullets.extend(exp.bullets)

    # Also include project bullets if available
    if hasattr(resume, 'projects') and resume.projects:
        for proj in resume.projects:
            if hasattr(proj, 'bullets') and proj.bullets:
                all_bullets.extend(proj.bullets)

    bullets_text = "\n".join(f"- {b}" for b in all_bullets[:20])  # Limit to first 20

    # Build system prompt
    system_prompt = """You are a professional resume writer. Generate tailored resume bullets for job applications.

Rules:
- Use strong action verbs
- Highlight relevant skills from the job requirements
- Be specific and quantifiable
- Each bullet must be 30-250 characters
- NO first-person pronouns (I, me, my, we, our)

Respond with valid JSON only."""

    # Build user prompt
    user_prompt = f"""Rewrite resume bullets to match this job posting.

JOB TITLE: {job.title}
COMPANY: {job.company or 'N/A'}
REQUIRED SKILLS: {', '.join(job.required_skills) if job.required_skills else 'N/A'}

RESPONSIBILITIES:
{chr(10).join(f"- {r}" for r in job.responsibilities[:5])}

CANDIDATE'S CURRENT RESUME BULLETS:
{bullets_text}

TASK: Generate {max(5, len(job.responsibilities))} tailored resume bullets for this job.

OUTPUT FORMAT (JSON):
{{
  "bullets": [
    {{
      "id": "bullet-001",
      "text": "Your bullet text here (30-250 chars)",
      "skills_covered": ["Skill1", "Skill2"]
    }},
    ...
  ]
}}

Generate ONLY the JSON, no other text."""

    # Call LLM with correct signature (keyword arguments)
    try:
        response = await llm.generate_with_retry(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            json_mode=True
        )

        # Parse JSON response
        import json
        import re

        # Extract JSON from response (handle potential markdown wrapping)
        json_match = re.search(r'\{.*\}', response, re.DOTALL)
        if json_match:
            data = json.loads(json_match.group())
        else:
            raise ValueError("No JSON found in LLM response")

        # Convert to GeneratedBullet objects
        bullets = []
        for i, bullet_data in enumerate(data.get("bullets", [])):
            try:
                bullet = GeneratedBullet(
                    id=bullet_data.get("id", f"baseline-bullet-{i+1:03d}"),
                    text=bullet_data.get("text", ""),
                    source_experience_id=None,  # No retrieval, so no source
                    skills_covered=bullet_data.get("skills_covered", [])
                )
                bullets.append(bullet)
            except Exception as e:
                logger.warning(f"Failed to parse bullet {i+1}: {e}")
                continue

        logger.info(f"Generated {len(bullets)} baseline bullets")
        return bullets

    except Exception as e:
        logger.error(f"Baseline generation failed: {e}")
        return []


async def generate_cover_letter_baseline(
    job: "JobDescription",
    resume: "CandidateProfile",
    llm: "BaseLLMClient"
) -> "GeneratedCoverLetter | None":
    """
    Baseline cover letter generation using one-shot LLM.

    Args:
        job: Target job description
        resume: Candidate's resume/profile
        llm: LLM client for generation

    Returns:
        Generated cover letter or None if generation fails

    Note:
        For mode="baseline" evaluation runs. Uses simple prompt without
        retrieval context. Returns a GeneratedCoverLetter with the `text` field.
    """
    from ..models import GeneratedCoverLetter
    import json

    logger.info("Generating cover letter using baseline")

    # Build system prompt
    system_prompt = """You are a professional career advisor and cover letter writer.

Write compelling, personalized cover letters that:
- Express genuine interest in the role
- Highlight relevant experience
- Maintain professional tone
- Are concise (250-400 words)

Return ONLY a JSON object with this structure:
{
  "id": "cover-001",
  "job_title": "<job title>",
  "company": "<company name>",
  "tone": "professional",
  "text": "<full cover letter body as a single string>"
}"""

    # Build user prompt
    user_prompt = f"""Write a professional cover letter for this job application.

CANDIDATE: {resume.name}
JOB: {job.title} at {job.company or 'the company'}
REQUIRED SKILLS: {', '.join(job.required_skills[:5]) if job.required_skills else 'N/A'}

Write a concise, professional cover letter (200-500 words) that:
- Expresses interest in the position
- Highlights relevant experience
- Explains why the candidate is a good fit

OUTPUT FORMAT (JSON):
{{
  "id": "cover-baseline-001",
  "job_id": "{job.job_id}",
  "job_title": "{job.title}",
  "company": "{job.company or 'N/A'}",
  "tone": "professional",
  "text": "<full cover letter text here>"
}}

Generate ONLY the JSON, no other text."""

    try:
        response = await llm.generate_with_retry(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            json_mode=True
        )

        # Parse JSON
        data = json.loads(response)

        # Normalize so we ALWAYS have `text`
        if "text" not in data or not isinstance(data["text"], str) or not data["text"].strip():
            # Try common alternative keys
            for key in ("body", "content", "letter", "full_text"):
                if key in data and isinstance(data[key], str) and data[key].strip():
                    data["text"] = data[key].strip()
                    break

        # If still no text, create minimal placeholder
        if "text" not in data or not isinstance(data["text"], str) or not data["text"].strip():
            data["text"] = "Dear Hiring Manager,\n\nI am writing to express my interest in the position.\n\nSincerely,\n" + resume.name

        # Ensure required fields
        if "job_id" not in data:
            data["job_id"] = job.job_id
        if "job_title" not in data:
            data["job_title"] = job.title
        if "company" not in data:
            data["company"] = job.company

        cover_letter = GeneratedCoverLetter(**data)

        logger.info(f"Generated baseline cover letter ({cover_letter.get_word_count()} words)")
        return cover_letter

    except Exception as e:
        logger.error(f"Baseline cover letter generation failed: {e}")
        import traceback
        traceback.print_exc()
        return None
