"""
Resume Ingestion
Converts raw resume text into structured CandidateProfile using LLM.
"""

import json
import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..llm.base import BaseLLMClient

from ..models.resume import CandidateProfile

logger = logging.getLogger(__name__)

# Schema description for the LLM prompt
CANDIDATE_PROFILE_SCHEMA = """
{
  "candidate_id": "unique-id-based-on-name-and-year (e.g., 'john-doe-2024')",
  "name": "Full Name",
  "email": "email@example.com",
  "phone": "+1-555-0123 (or null if not found)",
  "location": "City, State (or null if not found)",
  "summary": "Professional summary paragraph (or null if not found)",
  "skills": ["Skill1", "Skill2", "Skill3"],
  "experiences": [
    {
      "id": "exp-001",
      "role": "Job Title",
      "company": "Company Name",
      "start_date": "YYYY-MM or Month YYYY",
      "end_date": "YYYY-MM or Month YYYY or null for current",
      "bullets": [
        "Accomplishment bullet 1",
        "Accomplishment bullet 2"
      ]
    }
  ],
  "education": [
    {
      "degree": "Degree Name",
      "institution": "School Name",
      "year": 2024,
      "details": ["GPA: 3.8", "Honors", "Relevant coursework"]
    }
  ]
}
"""

SYSTEM_PROMPT = """You are a resume parser that converts human resumes into a strict JSON schema.

Your task is to extract all information from the provided resume text and return ONLY valid JSON matching the schema below. Do not include any explanations, markdown formatting, or text before or after the JSON object.

JSON Schema:
""" + CANDIDATE_PROFILE_SCHEMA + """

Rules:
1. Return ONLY the JSON object, nothing else
2. Generate a unique candidate_id based on name and current year (e.g., "john-doe-2024")
3. Assign unique experience IDs: "exp-001", "exp-002", etc.
4. Use null for missing optional fields (phone, location, summary)
5. Extract ALL skills mentioned anywhere in the resume
6. Parse dates in "YYYY-MM" format when possible
7. Use null for end_date if position is current
8. Include education details like GPA, honors, relevant coursework
9. Ensure all bullet points are complete sentences or fragments describing accomplishments
"""

RETRY_PROMPT = """Your previous response was not valid JSON. Please return ONLY a valid JSON object matching the schema, with no additional text, markdown, or explanations."""


async def parse_resume_text_to_profile(
    raw_text: str,
    client: "BaseLLMClient",
    max_retries: int = 2
) -> CandidateProfile:
    """
    Use the LLM to convert raw resume text into a CandidateProfile object.

    Args:
        raw_text: Raw resume text to parse
        client: LLM client (OpenAI or Anthropic)
        max_retries: Maximum retry attempts for JSON parsing (default: 2)

    Returns:
        Validated CandidateProfile object

    Raises:
        ValueError: If parsing fails after all retries
        json.JSONDecodeError: If LLM returns invalid JSON after retries
        pydantic.ValidationError: If JSON doesn't match CandidateProfile schema

    Example:
        >>> from src.orchestration import get_config
        >>> config = get_config()
        >>> client = config.get_llm_client("openai")
        >>> raw_text = open("data/raw/resume.txt").read()
        >>> profile = await parse_resume_text_to_profile(raw_text, client)
        >>> print(profile.name)
        John Doe
    """
    logger.info("Parsing resume text to CandidateProfile...")

    user_prompt = f"""Parse the following resume into the JSON schema:

---
{raw_text}
---

Return ONLY the JSON object, no other text."""

    last_error = None

    for attempt in range(max_retries):
        try:
            logger.debug(f"Attempt {attempt + 1}/{max_retries}")

            # Use retry prompt if this is a retry
            if attempt > 0:
                user_prompt = f"""{RETRY_PROMPT}

Original resume text:
---
{raw_text}
---

Return ONLY valid JSON."""

            # Generate response using LLM
            response = await client.generate(
                system_prompt=SYSTEM_PROMPT,
                user_prompt=user_prompt,
                json_mode=True
            )

            # Clean up response (remove markdown if present)
            response = _clean_json_response(response)

            # Parse JSON
            data = json.loads(response)

            # Validate with Pydantic
            profile = CandidateProfile(**data)

            logger.info(f"Successfully parsed resume for: {profile.name}")
            logger.info(f"  - {len(profile.skills)} skills")
            logger.info(f"  - {len(profile.experiences)} experiences")
            logger.info(f"  - {len(profile.education)} education entries")

            return profile

        except json.JSONDecodeError as e:
            last_error = e
            logger.warning(f"Attempt {attempt + 1}: Invalid JSON - {e}")

        except Exception as e:
            last_error = e
            logger.warning(f"Attempt {attempt + 1}: Validation error - {e}")

    # All retries exhausted
    error_msg = f"Failed to parse resume after {max_retries} attempts. Last error: {last_error}"
    logger.error(error_msg)
    raise ValueError(error_msg)


def _clean_json_response(response: str) -> str:
    """
    Clean up LLM response to extract pure JSON.

    Handles common issues like markdown code blocks.

    Args:
        response: Raw LLM response

    Returns:
        Cleaned JSON string
    """
    response = response.strip()

    # Remove markdown code blocks if present
    if response.startswith("```json"):
        response = response[7:]
    elif response.startswith("```"):
        response = response[3:]

    if response.endswith("```"):
        response = response[:-3]

    return response.strip()
