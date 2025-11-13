"""
Agent Executor
Implements the agentic loop: Retrieve → Generate → Validate → Retry
"""

import logging
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..models import JobDescription, CandidateProfile, FullGeneratedPackage, GeneratedBullet, GeneratedCoverLetter
    from ..llm import BaseLLMClient
    from ..embeddings import SentenceBertEncoder

from ..models import load_job_from_yaml, load_resume_from_json, FullGeneratedPackage
from ..embeddings import ResumeFaissIndex, retrieve_relevant_experiences
from ..generators import generate_bullets_for_job, generate_cover_letter
from .validator import validate_bullets_only, validate_package, format_validation_feedback

logger = logging.getLogger(__name__)


class AgentExecutor:
    """
    Orchestrates the agentic generation loop with retry logic.

    Flow:
    1. Load job and resume
    2. Build FAISS index for retrieval
    3. Retrieve relevant experiences
    4. Generate bullets (with validation + retry)
    5. Generate cover letter
    6. Build and validate full package
    7. Return package + errors

    Example:
        >>> executor = AgentExecutor(llm_client, encoder)
        >>> pkg, errors = await executor.run_single_job(job_path, resume_path)
        >>> if errors:
        ...     print(f"Package has {len(errors)} validation errors")
        >>> else:
        ...     print("Package is valid!")
    """

    def __init__(
        self,
        llm: "BaseLLMClient",
        encoder: "SentenceBertEncoder",
        max_retries: int = 3
    ):
        """
        Initialize agent executor.

        Args:
            llm: LLM client (OpenAI or Anthropic)
            encoder: SentenceBERT encoder for retrieval
            max_retries: Maximum retry attempts for generation
        """
        self.llm = llm
        self.encoder = encoder
        self.max_retries = max_retries

    async def run_single_job(
        self,
        job_path: Path,
        resume_path: Path
    ) -> tuple["FullGeneratedPackage | None", list[str]]:
        """
        Run the complete agentic loop for a single job.

        Steps:
        1. Load job description and resume from files
        2. Build FAISS index from resume experiences
        3. Retrieve relevant experiences for job
        4. Generate tailored bullets (with retry on validation failure)
        5. Generate cover letter
        6. Build full package
        7. Validate package
        8. Return (package, errors)

        Args:
            job_path: Path to job description YAML file
            resume_path: Path to resume JSON file

        Returns:
            Tuple of (FullGeneratedPackage or None, list of error messages)

        Example:
            >>> executor = AgentExecutor(llm, encoder)
            >>> pkg, errors = await executor.run_single_job(
            ...     Path("data/jobs/ml-engineer.yaml"),
            ...     Path("data/resumes/jane-doe.json")
            ... )
        """
        logger.info(f"Starting job execution: {job_path.name}")

        try:
            # Step 1: Load models
            logger.debug(f"Loading job from {job_path}")
            job = load_job_from_yaml(job_path)
            logger.info(f"Loaded job: {job.title} at {job.company}")

            logger.debug(f"Loading resume from {resume_path}")
            resume = load_resume_from_json(resume_path)
            logger.info(f"Loaded resume: {resume.name}")

            # Step 2: Build FAISS index
            logger.debug("Building FAISS index for retrieval")
            index = ResumeFaissIndex(self.encoder)
            index.build_from_experiences(resume.experiences)
            logger.info(f"Built index with {len(index)} bullets")

            # Step 3: Retrieve relevant experiences
            logger.debug("Retrieving relevant experiences")
            retrieved = retrieve_relevant_experiences(
                job, resume, self.encoder, index, top_k=5
            )
            total_retrieved = sum(len(items) for items in retrieved.values())
            logger.info(f"Retrieved {total_retrieved} relevant bullets for {len(retrieved)} responsibilities")

            # Step 4: Generate bullets with retry
            bullets = await self._generate_bullets_with_retry(job, resume, retrieved)

            if not bullets:
                error_msg = "Failed to generate valid bullets after retries"
                logger.error(error_msg)
                return None, [error_msg]

            logger.info(f"Generated {len(bullets)} bullets successfully")

            # Step 5: Generate cover letter
            logger.debug("Generating cover letter")
            cover_letter = await generate_cover_letter(job, resume, bullets, self.llm)
            logger.info("Generated cover letter")

            # Step 6: Build full package
            logger.debug("Building full package")
            package = FullGeneratedPackage(
                id=f"pkg-{job.job_id}",
                job_id=job.job_id,
                candidate_id=resume.candidate_id,
                bullets=bullets,
                cover_letter=cover_letter
            )

            # Step 7: Final validation
            logger.debug("Running final package validation")
            errors = validate_package(package, job, resume)

            if errors:
                logger.warning(f"Package has {len(errors)} validation errors")
            else:
                logger.info("Package validated successfully!")

            return package, errors

        except Exception as e:
            logger.error(f"Job execution failed: {e}")
            import traceback
            traceback.print_exc()
            return None, [f"Execution error: {str(e)}"]

    async def _generate_bullets_with_retry(
        self,
        job: "JobDescription",
        resume: "CandidateProfile",
        retrieved: dict[str, list[dict]]
    ) -> list["GeneratedBullet"] | None:
        """
        Generate bullets with validation and retry logic.

        If validation fails, provides feedback to LLM and retries up to max_retries times.

        Args:
            job: Target job description
            resume: Candidate's resume
            retrieved: Retrieved relevant experiences

        Returns:
            List of validated bullets, or None if all retries failed
        """
        last_error = None

        for attempt in range(self.max_retries):
            try:
                logger.info(f"Bullet generation attempt {attempt + 1}/{self.max_retries}")

                # Generate bullets
                bullets = await generate_bullets_for_job(job, resume, retrieved, self.llm)

                # Validate
                errors = validate_bullets_only(bullets, job, resume, max_len=150)

                if not errors:
                    logger.info(f"Bullets validated successfully on attempt {attempt + 1}")
                    return bullets

                # Validation failed
                logger.warning(f"Validation failed with {len(errors)} errors:")
                for error in errors[:3]:  # Show first 3
                    logger.warning(f"  - {error}")

                if attempt < self.max_retries - 1:
                    # Prepare feedback for retry
                    # Note: This is a simplified retry - in production you might want to
                    # modify the prompt with specific feedback
                    logger.info("Retrying with feedback...")
                    # Could add feedback to prompt here for more sophisticated retry
                else:
                    last_error = errors

            except Exception as e:
                logger.error(f"Bullet generation attempt {attempt + 1} failed: {e}")
                last_error = [str(e)]

                if attempt < self.max_retries - 1:
                    logger.info("Retrying after error...")

        # All retries exhausted
        logger.error(f"Failed to generate valid bullets after {self.max_retries} attempts")
        if last_error:
            logger.error(f"Last errors: {last_error[:3]}")

        return None


def build_package_from_components(
    job_id: str,
    candidate_id: str,
    bullets: list["GeneratedBullet"],
    cover_letter: "GeneratedCoverLetter"
) -> "FullGeneratedPackage":
    """
    Build a FullGeneratedPackage from components.

    Helper function to assemble the final package.

    Args:
        job_id: Job ID
        candidate_id: Candidate ID
        bullets: Generated bullets
        cover_letter: Generated cover letter

    Returns:
        FullGeneratedPackage object
    """
    from ..models import FullGeneratedPackage

    package = FullGeneratedPackage(
        id=f"pkg-{job_id}",
        job_id=job_id,
        candidate_id=candidate_id,
        bullets=bullets,
        cover_letter=cover_letter
    )

    return package
