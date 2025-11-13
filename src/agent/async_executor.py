"""
Async Executor
Handles concurrent processing of multiple jobs using asyncio.Semaphore for rate limiting.
"""

import asyncio
import logging
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..models import FullGeneratedPackage
    from ..llm import BaseLLMClient

from .executor import AgentExecutor

logger = logging.getLogger(__name__)


async def run_jobs_concurrently(
    job_resume_pairs: list[tuple[Path, Path]],
    llm: "BaseLLMClient",
    concurrency: int
) -> list[tuple["FullGeneratedPackage | None", list[str]]]:
    """
    Run multiple job applications concurrently with rate limiting.

    Uses asyncio.Semaphore to limit the number of concurrent API calls to
    prevent rate limiting from LLM providers.

    Args:
        job_resume_pairs: List of (job_path, resume_path) tuples
        llm: LLM client to use for generation
        concurrency: Maximum number of concurrent jobs

    Returns:
        List of (package, errors) tuples for each job

    Example:
        >>> pairs = [
        ...     (Path("data/jobs/job1.yaml"), Path("data/resumes/resume.json")),
        ...     (Path("data/jobs/job2.yaml"), Path("data/resumes/resume.json")),
        ... ]
        >>> results = await run_jobs_concurrently(pairs, llm_client, concurrency=3)
        >>> for i, (pkg, errors) in enumerate(results):
        ...     if pkg and not errors:
        ...         print(f"Job {i+1}: Success!")
        ...     else:
        ...         print(f"Job {i+1}: Failed with {len(errors)} errors")
    """
    logger.info(f"Running {len(job_resume_pairs)} jobs with concurrency={concurrency}")

    # Create semaphore for rate limiting
    semaphore = asyncio.Semaphore(concurrency)

    # Create executor (will be shared across all tasks)
    from ..embeddings import SentenceBertEncoder
    encoder = SentenceBertEncoder()
    executor = AgentExecutor(llm, encoder, max_retries=3)

    async def process_single_job_with_semaphore(
        job_path: Path,
        resume_path: Path
    ) -> tuple["FullGeneratedPackage | None", list[str]]:
        """Process a single job with semaphore control."""
        async with semaphore:
            logger.info(f"Processing: {job_path.name}")
            result = await executor.run_single_job(job_path, resume_path)
            logger.info(f"Completed: {job_path.name}")
            return result

    # Create tasks for all jobs
    tasks = [
        process_single_job_with_semaphore(job_path, resume_path)
        for job_path, resume_path in job_resume_pairs
    ]

    # Run all tasks concurrently (semaphore limits actual concurrency)
    logger.info(f"Starting concurrent execution...")
    results = await asyncio.gather(*tasks, return_exceptions=False)

    logger.info(f"Completed all {len(results)} jobs")
    return results


class AsyncJobExecutor:
    """
    Manages concurrent job processing with rate limiting.

    Wraps AgentExecutor to provide concurrent execution capabilities
    using asyncio.Semaphore for API rate limiting.

    Example:
        >>> from ..embeddings import SentenceBertEncoder
        >>> encoder = SentenceBertEncoder()
        >>> agent_executor = AgentExecutor(llm, encoder)
        >>> async_executor = AsyncJobExecutor(agent_executor, max_concurrent=3)
        >>> pairs = [(job1_path, resume_path), (job2_path, resume_path)]
        >>> results = await async_executor.process_jobs(pairs)
    """

    def __init__(self, agent_executor: AgentExecutor, max_concurrent: int = 5):
        """
        Initialize async executor.

        Args:
            agent_executor: Instance of AgentExecutor
            max_concurrent: Maximum concurrent jobs (default: 5)
        """
        self.agent_executor = agent_executor
        self.max_concurrent = max_concurrent
        self.semaphore = asyncio.Semaphore(max_concurrent)

    async def process_single_job(
        self,
        job_path: Path,
        resume_path: Path
    ) -> dict:
        """
        Process a single job with semaphore control.

        Args:
            job_path: Path to job description YAML
            resume_path: Path to resume JSON

        Returns:
            Dictionary with job info, status, and results
        """
        async with self.semaphore:
            try:
                logger.info(f"Processing: {job_path.name}")

                package, errors = await self.agent_executor.run_single_job(
                    job_path, resume_path
                )

                if package:
                    status = "success" if not errors else "success_with_warnings"
                else:
                    status = "failed"

                return {
                    "job_path": str(job_path),
                    "resume_path": str(resume_path),
                    "status": status,
                    "package": package,
                    "errors": errors
                }

            except Exception as e:
                logger.error(f"Job processing failed for {job_path.name}: {e}")
                return {
                    "job_path": str(job_path),
                    "resume_path": str(resume_path),
                    "status": "failed",
                    "package": None,
                    "errors": [f"Exception: {str(e)}"]
                }

    async def process_jobs(
        self,
        job_resume_pairs: list[tuple[Path, Path]]
    ) -> list[dict]:
        """
        Process multiple jobs concurrently.

        Args:
            job_resume_pairs: List of (job_path, resume_path) tuples

        Returns:
            List of result dictionaries for each job

        Example:
            >>> pairs = [
            ...     (Path("data/jobs/job1.yaml"), Path("data/resumes/resume.json")),
            ...     (Path("data/jobs/job2.yaml"), Path("data/resumes/resume.json")),
            ... ]
            >>> results = await async_executor.process_jobs(pairs)
            >>> successful = [r for r in results if r["status"] == "success"]
            >>> print(f"{len(successful)}/{len(results)} jobs completed successfully")
        """
        logger.info(
            f"Processing {len(job_resume_pairs)} jobs with max_concurrent={self.max_concurrent}"
        )

        # Create tasks for all jobs
        tasks = [
            self.process_single_job(job_path, resume_path)
            for job_path, resume_path in job_resume_pairs
        ]

        # Run all tasks concurrently (semaphore limits actual concurrency)
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Handle any exceptions from gather
        processed_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                job_path, resume_path = job_resume_pairs[i]
                logger.error(f"Job {job_path.name} raised exception: {result}")
                processed_results.append({
                    "job_path": str(job_path),
                    "resume_path": str(resume_path),
                    "status": "failed",
                    "package": None,
                    "errors": [f"Exception: {str(result)}"]
                })
            else:
                processed_results.append(result)

        # Summary
        successful = sum(1 for r in processed_results if r["status"] == "success")
        logger.info(f"Completed: {successful}/{len(processed_results)} successful")

        return processed_results
