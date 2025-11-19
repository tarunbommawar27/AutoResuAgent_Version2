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
    """
    from ..models import GeneratedBullet

    logger.info("Generating bullets using baseline (no retrieval)")

    # Build simple prompt with all resume bullets
    all_bullets = []
    for exp in resume.experiences:
        all_bullets.extend(exp.bullets)

    bullets_text = "\n".join(f"- {b}" for b in all_bullets[:20])  # Limit to first 20

    prompt = f"""You are a professional resume writer. Rewrite resume bullets to match this job posting.

JOB TITLE: {job.title}
COMPANY: {job.company or 'N/A'}
REQUIRED SKILLS: {', '.join(job.required_skills) if job.required_skills else 'N/A'}

RESPONSIBILITIES:
{chr(10).join(f"- {r}" for r in job.responsibilities[:5])}

CANDIDATE'S CURRENT RESUME BULLETS:
{bullets_text}

TASK: Generate {len(job.responsibilities)} tailored resume bullets for this job.

REQUIREMENTS:
- Each bullet must be 30-150 characters
- Use strong action verbs
- Highlight relevant skills from the job requirements
- Be specific and quantifiable

OUTPUT FORMAT (JSON):
{{
  "bullets": [
    {{
      "id": "bullet-001",
      "text": "Your bullet text here",
      "skills_covered": ["Skill1", "Skill2"]
    }},
    ...
  ]
}}

Generate ONLY the JSON, no other text."""

    # Call LLM
    try:
        response = await llm.generate(prompt)

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
    """
    from ..models import GeneratedCoverLetter

    logger.info("Generating cover letter using baseline")

    prompt = f"""Write a professional cover letter for this job application.

CANDIDATE: {resume.name}
JOB: {job.title} at {job.company or 'the company'}
REQUIRED SKILLS: {', '.join(job.required_skills[:5]) if job.required_skills else 'N/A'}

Write a concise, professional cover letter (200-500 words) that:
- Expresses interest in the position
- Highlights relevant experience
- Explains why the candidate is a good fit

OUTPUT ONLY THE COVER LETTER TEXT (no subject line, no "Dear" salutation, no signature)."""

    try:
        response = await llm.generate(prompt)

        cover_letter = GeneratedCoverLetter(
            id=f"baseline-cover-{job.job_id}",
            job_id=job.job_id,
            job_title=job.title,
            company=job.company,
            tone="professional",
            text=response.strip()
        )

        logger.info("Generated baseline cover letter")
        return cover_letter

    except Exception as e:
        logger.error(f"Baseline cover letter generation failed: {e}")
        return None
