"""
Job Description Ingestion
Converts raw job description text into structured JobDescription using LLM.
"""

import json
import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..llm.base import BaseLLMClient

from ..models.job_description import JobDescription

logger = logging.getLogger(__name__)

# Schema description for the LLM prompt
JOB_DESCRIPTION_SCHEMA = """
{
  "job_id": "unique-id-based-on-company-and-role (e.g., 'techcorp-ml-engineer-2024')",
  "title": "Job Title",
  "company": "Company Name (or null if not found)",
  "location": "City, State or Remote (or null if not found)",
  "seniority": "Entry/Mid/Senior/Lead/Principal (or null if not clear)",
  "responsibilities": [
    "Key responsibility 1",
    "Key responsibility 2",
    "Key responsibility 3"
  ],
  "required_skills": [
    "Required Skill 1",
    "Required Skill 2"
  ],
  "nice_to_have_skills": [
    "Preferred Skill 1",
    "Preferred Skill 2"
  ],
  "extra_metadata": {
    "salary_range": "if mentioned",
    "employment_type": "Full-time/Part-time/Contract",
    "remote_policy": "Remote/Hybrid/On-site",
    "years_experience": "if mentioned"
  }
}
"""

SYSTEM_PROMPT = """You are a job description parser that converts job postings into a strict JSON schema.

Your task is to extract all information from the provided job description text and return ONLY valid JSON matching the schema below. Do not include any explanations, markdown formatting, or text before or after the JSON object.

JSON Schema:
""" + JOB_DESCRIPTION_SCHEMA + """

Rules:
1. Return ONLY the JSON object, nothing else
2. Generate a unique job_id based on company and role (e.g., "cisco-ml-engineer-2024")
3. Extract company name from the posting if available
4. Identify seniority from title or requirements (Entry, Mid, Senior, Lead, Principal)
5. Split requirements into responsibilities, required_skills, and nice_to_have_skills
6. Required skills are explicitly stated as "required", "must have", or are in a requirements section
7. Nice-to-have skills are stated as "preferred", "bonus", "nice to have", or similar
8. Include any salary, benefits, or other metadata in extra_metadata
9. Use null for fields that cannot be determined from the text
"""

RETRY_PROMPT = """Your previous response was not valid JSON. Please return ONLY a valid JSON object matching the schema, with no additional text, markdown, or explanations."""


async def parse_job_text_to_description(
    raw_text: str,
    client: "BaseLLMClient",
    max_retries: int = 2
) -> JobDescription:
    """
    Use the LLM to convert raw job description text into a JobDescription object.

    Args:
        raw_text: Raw job description text to parse
        client: LLM client (OpenAI or Anthropic)
        max_retries: Maximum retry attempts for JSON parsing (default: 2)

    Returns:
        Validated JobDescription object

    Raises:
        ValueError: If parsing fails after all retries
        json.JSONDecodeError: If LLM returns invalid JSON after retries
        pydantic.ValidationError: If JSON doesn't match JobDescription schema

    Example:
        >>> from src.orchestration import get_config
        >>> config = get_config()
        >>> client = config.get_llm_client("openai")
        >>> raw_text = open("data/raw/job.txt").read()
        >>> job = await parse_job_text_to_description(raw_text, client)
        >>> print(job.title)
        Senior ML Engineer
    """
    logger.info("Parsing job description text to JobDescription...")

    user_prompt = f"""Parse the following job description into the JSON schema:

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

Original job description text:
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
            job = JobDescription(**data)

            logger.info(f"Successfully parsed job: {job.title}")
            logger.info(f"  - Company: {job.company}")
            logger.info(f"  - {len(job.required_skills)} required skills")
            logger.info(f"  - {len(job.nice_to_have_skills or [])} nice-to-have skills")
            logger.info(f"  - {len(job.responsibilities)} responsibilities")

            return job

        except json.JSONDecodeError as e:
            last_error = e
            logger.warning(f"Attempt {attempt + 1}: Invalid JSON - {e}")

        except Exception as e:
            last_error = e
            logger.warning(f"Attempt {attempt + 1}: Validation error - {e}")

    # All retries exhausted
    error_msg = f"Failed to parse job description after {max_retries} attempts. Last error: {last_error}"
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
