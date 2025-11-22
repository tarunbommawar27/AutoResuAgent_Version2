"""
Async Executor
Handles concurrent processing of multiple jobs using asyncio.Semaphore for rate limiting.
"""

import asyncio
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from ..models import FullGeneratedPackage
    from ..llm import BaseLLMClient
    from ..orchestration.config import Config

from .executor import AgentExecutor

logger = logging.getLogger(__name__)


@dataclass
class BatchJobResult:
    """
    Result from processing a single (job, resume) pair in a batch.

    Attributes:
        job_path: Path to the job description YAML file
        resume_path: Path to the resume JSON file
        package: Generated package if successful, None otherwise
        errors: List of error/warning messages
        metrics: Dictionary of computed metrics, or None if unavailable
        success: True if package was generated, False otherwise

    Example:
        >>> result = BatchJobResult(
        ...     job_path=Path("data/jobs/job1.yaml"),
        ...     resume_path=Path("data/resumes/resume.json"),
        ...     package=generated_package,
        ...     errors=[],
        ...     metrics={"num_bullets": 5, "avg_bullet_length_chars": 120.5}
        ... )
        >>> if result.success:
        ...     print(f"Generated {len(result.package.bullets)} bullets")
    """
    job_path: Path
    resume_path: Path
    package: "FullGeneratedPackage | None" = None
    errors: list[str] = field(default_factory=list)
    metrics: dict[str, Any] | None = None

    @property
    def success(self) -> bool:
        """Return True if a package was successfully generated."""
        return self.package is not None


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
    ) -> tuple["FullGeneratedPackage | None", list[str], dict | None]:
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

                package, errors, metrics = await self.agent_executor.run_single_job(
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


class AgentBatchExecutor:
    """
    Batch executor for processing multiple (job, resume) pairs with controlled concurrency.

    This class provides a high-level interface for batch processing jobs using the
    agent pipeline with semantic retrieval, generation, and validation.

    Example:
        >>> from ..orchestration.config import Config
        >>> config = Config()
        >>> pairs = [
        ...     (Path("data/jobs/job1.yaml"), Path("data/resumes/resume.json")),
        ...     (Path("data/jobs/job2.yaml"), Path("data/resumes/resume.json")),
        ... ]
        >>> batch_executor = AgentBatchExecutor(pairs, config, max_concurrent=3)
        >>> results = await batch_executor.run_all()
        >>> for job_path, resume_path, success, errors in results:
        ...     print(f"{job_path.name}: {'SUCCESS' if success else 'FAILED'}")
    """

    def __init__(
        self,
        jobs: list[tuple[Path, Path]],
        config: "Config",
        max_concurrent: int = 3
    ):
        """
        Initialize batch executor.

        Args:
            jobs: List of (job_path, resume_path) tuples to process
            config: Application configuration object
            max_concurrent: Maximum number of concurrent jobs (default: 3)
        """
        self.jobs = jobs
        self.config = config
        self.max_concurrent = max_concurrent
        self.semaphore = asyncio.Semaphore(max_concurrent)

        # Initialize shared components
        from ..embeddings import SentenceBertEncoder
        self.encoder = SentenceBertEncoder()

        # Get LLM client from config
        self.llm = config.get_llm_client()

        logger.info(
            f"Initialized AgentBatchExecutor with {len(jobs)} jobs, "
            f"max_concurrent={max_concurrent}"
        )

    async def _process_single_pair(
        self,
        job_path: Path,
        resume_path: Path,
        index: int
    ) -> tuple[Path, Path, bool, list[str]]:
        """
        Process a single (job, resume) pair with semaphore control.

        Args:
            job_path: Path to job description YAML
            resume_path: Path to resume JSON
            index: Index of this job in the batch (for logging)

        Returns:
            Tuple of (job_path, resume_path, success_flag, errors)
        """
        async with self.semaphore:
            try:
                logger.info(
                    f"[{index + 1}/{len(self.jobs)}] Processing: "
                    f"job={job_path.name}, resume={resume_path.name}"
                )

                # Create a fresh AgentExecutor for this job
                executor = AgentExecutor(
                    self.llm,
                    self.encoder,
                    max_retries=self.config.max_retries
                )

                # Run the pipeline for this job
                package, errors, metrics = await executor.run_single_job(job_path, resume_path)

                if package and not errors:
                    logger.info(
                        f"[{index + 1}/{len(self.jobs)}] SUCCESS: "
                        f"job={job_path.name}, resume={resume_path.name}"
                    )
                    return (job_path, resume_path, True, [])
                elif package and errors:
                    logger.warning(
                        f"[{index + 1}/{len(self.jobs)}] SUCCESS WITH WARNINGS: "
                        f"job={job_path.name}, resume={resume_path.name}, "
                        f"warnings={len(errors)}"
                    )
                    return (job_path, resume_path, True, errors)
                else:
                    logger.error(
                        f"[{index + 1}/{len(self.jobs)}] FAILED: "
                        f"job={job_path.name}, resume={resume_path.name}, "
                        f"errors={len(errors)}"
                    )
                    return (job_path, resume_path, False, errors)

            except Exception as e:
                logger.error(
                    f"[{index + 1}/{len(self.jobs)}] EXCEPTION: "
                    f"job={job_path.name}, resume={resume_path.name}, "
                    f"error={str(e)}"
                )
                return (job_path, resume_path, False, [f"Exception: {str(e)}"])

    async def run_all(self) -> list[tuple[Path, Path, bool, list[str]]]:
        """
        Run all jobs concurrently with controlled concurrency.

        Uses asyncio.gather with a semaphore to limit concurrent execution.
        Each job reuses the same encoder and LLM client but creates its own
        AgentExecutor to avoid state conflicts.

        Returns:
            List of tuples: (job_path, resume_path, success_flag, errors)
            - job_path: Path to the job description
            - resume_path: Path to the resume
            - success_flag: True if successful, False otherwise
            - errors: List of error/warning messages

        Example:
            >>> results = await batch_executor.run_all()
            >>> successful = [r for r in results if r[2]]  # r[2] is success_flag
            >>> print(f"{len(successful)}/{len(results)} jobs succeeded")
        """
        logger.info(f"Starting batch execution of {len(self.jobs)} jobs")
        logger.info(f"Concurrency limit: {self.max_concurrent}")

        # Create tasks for all job pairs
        tasks = [
            self._process_single_pair(job_path, resume_path, i)
            for i, (job_path, resume_path) in enumerate(self.jobs)
        ]

        # Run all tasks concurrently (semaphore limits actual concurrency)
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Handle any exceptions from gather
        final_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                job_path, resume_path = self.jobs[i]
                logger.error(
                    f"[{i + 1}/{len(self.jobs)}] Unexpected exception: "
                    f"job={job_path.name}, error={str(result)}"
                )
                final_results.append(
                    (job_path, resume_path, False, [f"Unexpected error: {str(result)}"])
                )
            else:
                final_results.append(result)

        # Log summary
        successful = sum(1 for r in final_results if r[2])
        failed = len(final_results) - successful
        logger.info(
            f"Batch execution completed: {successful} succeeded, {failed} failed"
        )

        return final_results


class AsyncBatchExecutor:
    """
    Enhanced batch executor for processing multiple (job, resume) pairs with controlled concurrency.

    Returns detailed BatchJobResult objects containing packages and metrics for downstream
    processing (e.g., LaTeX rendering, metrics aggregation).

    Args:
        pairs: List of (job_path, resume_path) tuples to process
        max_concurrent: Maximum number of concurrent jobs (default: 3)

    Example:
        >>> from ..llm import OpenAILLMClient
        >>> from ..embeddings import SentenceBertEncoder
        >>> llm = OpenAILLMClient(config)
        >>> encoder = SentenceBertEncoder()
        >>> pairs = [
        ...     (Path("data/jobs/job1.yaml"), Path("data/resumes/resume.json")),
        ...     (Path("data/jobs/job2.yaml"), Path("data/resumes/resume.json")),
        ... ]
        >>> executor = AsyncBatchExecutor(pairs, max_concurrent=3)
        >>> results = await executor.run(llm, encoder)
        >>> for result in results:
        ...     if result.success:
        ...         print(f"{result.job_path.name}: {len(result.package.bullets)} bullets")
    """

    def __init__(
        self,
        pairs: list[tuple[Path, Path]],
        max_concurrent: int = 3
    ):
        """
        Initialize async batch executor.

        Args:
            pairs: List of (job_path, resume_path) tuples
            max_concurrent: Maximum number of concurrent jobs (default: 3)
        """
        self.pairs = pairs
        self.max_concurrent = max_concurrent
        self._semaphore: asyncio.Semaphore | None = None

    async def run(
        self,
        llm: "BaseLLMClient",
        encoder: "SentenceBertEncoder",
        max_retries: int = 3
    ) -> list[BatchJobResult]:
        """
        Run all jobs concurrently and return detailed results.

        Each result contains the package, metrics, and errors for downstream
        processing (LaTeX rendering, metrics persistence, etc.).

        Args:
            llm: LLM client (OpenAI or Anthropic)
            encoder: SentenceBERT encoder for retrieval
            max_retries: Maximum retry attempts for generation per job

        Returns:
            List of BatchJobResult objects, one per (job, resume) pair

        Example:
            >>> results = await executor.run(llm, encoder)
            >>> successful = [r for r in results if r.success]
            >>> print(f"{len(successful)}/{len(results)} jobs succeeded")
        """
        logger.info(f"Starting batch: {len(self.pairs)} pairs, max_concurrent={self.max_concurrent}")

        # Create semaphore for concurrency control
        self._semaphore = asyncio.Semaphore(self.max_concurrent)

        # Create tasks
        tasks = [
            self._process_pair(job_path, resume_path, idx, llm, encoder, max_retries)
            for idx, (job_path, resume_path) in enumerate(self.pairs)
        ]

        # Run all tasks concurrently
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Process results, converting exceptions to failed results
        final_results: list[BatchJobResult] = []
        for idx, result in enumerate(results):
            if isinstance(result, Exception):
                job_path, resume_path = self.pairs[idx]
                logger.error(f"[{idx + 1}/{len(self.pairs)}] Exception: {job_path.name} - {result}")
                final_results.append(BatchJobResult(
                    job_path=job_path,
                    resume_path=resume_path,
                    package=None,
                    errors=[f"Unexpected error: {str(result)}"],
                    metrics=None
                ))
            else:
                final_results.append(result)

        # Log summary
        successful = sum(1 for r in final_results if r.success)
        failed = len(final_results) - successful
        logger.info(f"Batch completed: {successful} succeeded, {failed} failed")

        return final_results

    async def _process_pair(
        self,
        job_path: Path,
        resume_path: Path,
        idx: int,
        llm: "BaseLLMClient",
        encoder: "SentenceBertEncoder",
        max_retries: int
    ) -> BatchJobResult:
        """
        Process a single (job, resume) pair with semaphore control.

        Args:
            job_path: Path to job description YAML
            resume_path: Path to resume JSON
            idx: Index of this pair (for logging)
            llm: LLM client
            encoder: SentenceBERT encoder
            max_retries: Maximum retry attempts

        Returns:
            BatchJobResult with package, errors, and metrics
        """
        async with self._semaphore:
            logger.info(f"[{idx + 1}/{len(self.pairs)}] Starting: {job_path.name} + {resume_path.name}")

            try:
                # Create executor for this job
                executor = AgentExecutor(llm, encoder, max_retries=max_retries)

                # Run the agent pipeline
                package, errors, metrics = await executor.run_single_job(job_path, resume_path)

                if package:
                    status = "SUCCESS" if not errors else "SUCCESS_WITH_WARNINGS"
                    logger.info(f"[{idx + 1}/{len(self.pairs)}] {status}: {job_path.name}")
                else:
                    logger.error(f"[{idx + 1}/{len(self.pairs)}] FAILED: {job_path.name}")

                return BatchJobResult(
                    job_path=job_path,
                    resume_path=resume_path,
                    package=package,
                    errors=errors if errors else [],
                    metrics=metrics
                )

            except Exception as e:
                logger.error(f"[{idx + 1}/{len(self.pairs)}] Exception: {job_path.name} - {e}")
                return BatchJobResult(
                    job_path=job_path,
                    resume_path=resume_path,
                    package=None,
                    errors=[f"Exception: {str(e)}"],
                    metrics=None
                )
