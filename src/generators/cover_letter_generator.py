"""
Cover Letter Generator
Generates personalized cover letters using LLMs and tailored resume bullets.
"""

import json
import logging
from typing import TYPE_CHECKING

from ..models import GeneratedCoverLetter

if TYPE_CHECKING:
    from ..models import JobDescription, CandidateProfile, GeneratedBullet
    from ..llm import BaseLLMClient

logger = logging.getLogger(__name__)


async def generate_cover_letter(
    job: "JobDescription",
    resume: "CandidateProfile",
    bullets: list["GeneratedBullet"],
    llm: "BaseLLMClient"
) -> "GeneratedCoverLetter":
    """
    Generate a tailored cover letter for a job application.

    Uses the job description, candidate profile, and generated bullets to create
    a compelling, personalized cover letter that:
    - References specific job requirements
    - Highlights relevant skills and experiences
    - Maintains professional tone
    - Avoids generic template language
    - Does not hallucinate experiences
    """

    logger.info(f"Generating cover letter for job: {job.title} at {job.company}")

    system_prompt = """You are an expert career advisor and professional cover letter writer.

Your task is to write a compelling, personalized cover letter that:
- Opens with a strong statement of interest in the specific role and company
- Highlights 2-3 key relevant experiences that match the job requirements
- Demonstrates genuine enthusiasm and understanding of the company/role
- Maintains a professional yet personable tone
- Is concise (3-4 paragraphs, approximately 250-400 words)
- Uses the candidate's actual experiences (do not fabricate or exaggerate)
- Avoids generic template language and clichés

Return ONLY a JSON object with this exact structure:

{
  "id": "cover-001",
  "job_title": "<job title>",
  "company": "<company name>",
  "tone": "professional",
  "text": "<full cover letter body as a single string>"
}
"""

    user_prompt = _build_cover_letter_prompt(job, resume, bullets)

    logger.debug("Calling LLM for cover letter generation")

    try:
        response = await llm.generate_with_retry(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            json_mode=True,
        )

        # Try to parse JSON
        try:
            data = json.loads(response)
        except Exception as e:
            logger.error(f"Failed to parse LLM response as JSON: {e}")
            # Fallback: treat raw response as the text body
            return GeneratedCoverLetter(text=response)

        # Sometimes the model might wrap content like {"cover_letter": {...}}
        if isinstance(data, dict) and "cover_letter" in data and isinstance(data["cover_letter"], dict):
            data = data["cover_letter"]

        # 🔑 Normalize so we ALWAYS have `text`
        if "text" not in data or not isinstance(data["text"], str) or not data["text"].strip():
            # Try common alternative keys
            for key in ("body", "content", "letter", "full_text"):
                if key in data and isinstance(data[key], str) and data[key].strip():
                    data["text"] = data[key].strip()
                    break

        # If still no text, try to stitch from parts (opening/body/closing)
        if "text" not in data or not isinstance(data["text"], str) or not data["text"].strip():
            parts = []
            for key in ("opening", "body", "closing"):
                if key in data and isinstance(data[key], str) and data[key].strip():
                    parts.append(data[key].strip())
            stitched = "\n\n".join(parts)
            if not stitched:
                stitched = "Dear Hiring Manager,\n\n[Cover letter text missing]\n"
            data["text"] = stitched

        # Pydantic validation happens here (min/max length, word count, etc.)
            # 🔗 Make sure IDs & metadata are present for validators
        if "job_id" not in data or not data.get("job_id"):
            data["job_id"] = job.job_id
        if "job_title" not in data or not data.get("job_title"):
            data["job_title"] = job.title
        if "company" not in data or not data.get("company"):
            data["company"] = job.company

        cover_letter = GeneratedCoverLetter(**data)


        logger.info(
            f"Generated cover letter successfully "
            f"({cover_letter.get_word_count()} words, "
            f"{cover_letter.get_paragraph_count()} paragraphs)"
        )
        return cover_letter

    except Exception as e:
        logger.error(f"Cover letter generation failed: {e}")
        raise



def _build_cover_letter_prompt(
    job: "JobDescription",
    resume: "CandidateProfile",
    bullets: list["GeneratedBullet"]
) -> str:
    """
    Build the user prompt for cover letter generation.

    Includes job details, candidate info, and sample tailored bullets for context.
    """
    prompt_parts = [
        "Generate a personalized cover letter for the following job application:\n",
        f"**Job Title:** {job.title}",
        f"**Company:** {job.company}",
    ]

    if job.location:
        prompt_parts.append(f"**Location:** {job.location}")

    # Job details
    if job.responsibilities:
        prompt_parts.append(f"\n**Key Responsibilities (showing top 3):**")
        for i, resp in enumerate(job.responsibilities[:3], 1):
            prompt_parts.append(f"{i}. {resp}")
        if len(job.responsibilities) > 3:
            prompt_parts.append(f"   ...and {len(job.responsibilities) - 3} more")

    if job.required_skills:
        prompt_parts.append(f"\n**Required Skills:** {', '.join(job.required_skills[:8])}")
        if len(job.required_skills) > 8:
            prompt_parts.append(f"   ...and {len(job.required_skills) - 8} more")

    # Candidate information
    prompt_parts.append(f"\n**Candidate Information:**")
    prompt_parts.append(f"**Name:** {resume.name}")
    prompt_parts.append(f"**Email:** {resume.email}")

    if resume.location:
        prompt_parts.append(f"**Location:** {resume.location}")

    # Top skills
    if resume.skills:
        prompt_parts.append(f"**Key Skills:** {', '.join(resume.skills[:10])}")

    # Recent experience summary
    if resume.experiences:
        prompt_parts.append(f"\n**Recent Experience:**")
        for exp in resume.experiences[:2]:  # Show 2 most recent
            date_range = f"{exp.start_date or 'N/A'} - {exp.end_date or 'Present'}"
            prompt_parts.append(f"- {exp.role} at {exp.company} ({date_range})")

    # Sample tailored bullets for context
    if bullets:
        prompt_parts.append(f"\n**Tailored Resume Bullets for This Job (for reference):**")
        prompt_parts.append("These bullets demonstrate the candidate's relevant experience:\n")

        # Show top 5 bullets as examples
        for i, bullet in enumerate(bullets[:5], 1):
            prompt_parts.append(f"{i}. {bullet.text}")

        if len(bullets) > 5:
            prompt_parts.append(f"   ...and {len(bullets) - 5} more relevant accomplishments")

    # Instructions
    prompt_parts.append("\n**Task:**")
    prompt_parts.append(
        "Write a compelling cover letter that connects the candidate's experience "
        "to the job requirements. Use specific examples from the tailored bullets above, "
        "but write naturally and conversationally (not as a list of bullet points)."
    )

    # Output format
    prompt_parts.append("\n**Output Format (JSON):**")
    prompt_parts.append("""
{
  "id": "cover-001",
  "job_id": "The job ID from the job description",
  "opening": "Opening paragraph (1-2 sentences expressing interest in the role)",
  "body": "Main body text (2-3 paragraphs highlighting relevant experience and skills, written in flowing prose)",
  "closing": "Closing paragraph (1-2 sentences with call to action)",
  "tone": "professional"
}
""")

    prompt_parts.append("\n**Important Guidelines:**")
    prompt_parts.append("- Opening: Express genuine interest in the specific role and company")
    prompt_parts.append("- Body: Weave in 2-3 specific examples from the candidate's experience")
    prompt_parts.append("- Body: Connect experiences directly to job requirements")
    prompt_parts.append("- Body: Write as natural paragraphs, NOT as bullet points")
    prompt_parts.append("- Closing: Include enthusiasm and call to action (e.g., discussion opportunity)")
    prompt_parts.append("- Tone: Professional yet personable, confident but not arrogant")
    prompt_parts.append("- Length: Body should be 200-350 words total")
    prompt_parts.append("- DO NOT fabricate experiences not mentioned in the bullets")
    prompt_parts.append("- DO NOT use generic phrases like 'I am writing to apply' or 'Please find my resume attached'")
    prompt_parts.append('- Use id format like "cover-001"')

    return "\n".join(prompt_parts)


def _format_experience_summary(
    resume: "CandidateProfile",
    max_experiences: int = 3
) -> str:
    """
    Format a brief summary of candidate's experience.

    Args:
        resume: Candidate's resume
        max_experiences: Maximum number of experiences to include

    Returns:
        Formatted experience summary
    """
    if not resume.experiences:
        return "No experience listed."

    summary_parts = []

    for i, exp in enumerate(resume.experiences[:max_experiences]):
        date_range = f"{exp.start_date or 'N/A'} - {exp.end_date or 'Present'}"
        summary_parts.append(
            f"{i+1}. **{exp.role}** at **{exp.company}** ({date_range})"
        )

        # Include 1-2 sample bullets
        if exp.bullets:
            for bullet in exp.bullets[:2]:
                summary_parts.append(f"   - {bullet}")

    if len(resume.experiences) > max_experiences:
        summary_parts.append(f"\n...and {len(resume.experiences) - max_experiences} more positions")

    return "\n".join(summary_parts)
