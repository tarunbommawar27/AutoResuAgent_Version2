"""
Pipeline Orchestrator
End-to-end workflow coordinator for AutoResuAgent.
"""

import json
import logging
import asyncio
from pathlib import Path
from typing import Literal, Any

import yaml

logger = logging.getLogger(__name__)


async def run_pipeline(
    job_path: Path,
    resume_path: Path,
    use_openai: bool = True,
    output_dir: Path | None = None
) -> dict:
    """
    Run the complete AutoResuAgent pipeline for a single job.

    Steps:
    1. Load configuration and initialize LLM client
    2. Initialize encoder for retrieval
    3. Run agent executor (retrieve → generate → validate)
    4. Render LaTeX templates
    5. Compile to PDF (if pdflatex available)
    6. Return paths and errors

    Args:
        job_path: Path to job description YAML
        resume_path: Path to resume JSON
        use_openai: If True use OpenAI, else use Anthropic
        output_dir: Directory for outputs (default: outputs/)

    Returns:
        Dictionary with:
        {
            "success": bool,
            "package": FullGeneratedPackage or None,
            "resume_tex": Path or None,
            "cover_letter_tex": Path or None,
            "resume_pdf": Path or None,
            "cover_letter_pdf": Path or None,
            "errors": list[str],
            "warnings": list[str]
        }

    Example:
        >>> result = await run_pipeline(
        ...     Path("data/jobs/ml-engineer.yaml"),
        ...     Path("data/resumes/jane-doe.json"),
        ...     use_openai=True
        ... )
        >>> if result["success"]:
        ...     print(f"Resume PDF: {result['resume_pdf']}")
        ...     print(f"Cover letter PDF: {result['cover_letter_pdf']}")
    """
    from .config import get_config
    from ..models import load_job_from_yaml, load_resume_from_json
    from ..llm import OpenAILLMClient, AnthropicLLMClient
    from ..embeddings import SentenceBertEncoder
    from ..agent import AgentExecutor
    from ..renderer import (
        render_resume_tex,
        render_cover_letter_tex,
        compile_tex_to_pdf,
        check_pdflatex_installed
    )

    logger.info(f"Starting pipeline for {job_path.name}")

    # Set default output directory
    if output_dir is None:
        output_dir = Path("outputs")

    output_dir.mkdir(parents=True, exist_ok=True)

    errors = []
    warnings = []

    try:
        # Step 1: Initialize configuration and LLM client
        logger.info("Step 1: Initializing configuration...")
        config = get_config()

        if use_openai:
            if not config.openai_api_key:
                raise ValueError(
                    "OpenAI API key not set. Set OPENAI_API_KEY environment variable."
                )
            llm = OpenAILLMClient(config)
            logger.info(f"Using OpenAI ({llm.get_model_name()})")
        else:
            if not config.anthropic_api_key:
                raise ValueError(
                    "Anthropic API key not set. Set ANTHROPIC_API_KEY environment variable."
                )
            llm = AnthropicLLMClient(config)
            logger.info(f"Using Anthropic ({llm.get_model_name()})")

        # Step 2: Initialize encoder
        logger.info("Step 2: Initializing SentenceBERT encoder...")
        encoder = SentenceBertEncoder()

        # Step 3: Run agent executor
        logger.info("Step 3: Running agent executor...")
        executor = AgentExecutor(llm, encoder, max_retries=config.max_retries)

        package, agent_errors, metrics = await executor.run_single_job(job_path, resume_path)

        if not package:
            errors.append("Agent executor failed to generate package")
            errors.extend(agent_errors)
            return {
                "success": False,
                "package": None,
                "resume_tex": None,
                "cover_letter_tex": None,
                "resume_pdf": None,
                "cover_letter_pdf": None,
                "errors": errors,
                "warnings": warnings
            }

        # Add agent errors as warnings if package was generated
        if agent_errors:
            warnings.extend(agent_errors)

        logger.info("Package generated successfully")

        # Load models for rendering
        job = load_job_from_yaml(job_path)
        resume = load_resume_from_json(resume_path)

        # Step 4: Render LaTeX
        logger.info("Step 4: Rendering LaTeX templates...")

        # Create job-specific output directory
        job_output_dir = output_dir / f"{job.company}_{job.title}".replace(" ", "_")
        job_output_dir.mkdir(parents=True, exist_ok=True)

        template_dir = Path("data/templates")

        # Render resume
        resume_tex_path = job_output_dir / "resume.tex"
        resume_tex = render_resume_tex(
            package,
            resume,
            template_dir / "resume.tex.jinja",
            resume_tex_path
        )
        logger.info(f"Resume LaTeX rendered: {resume_tex}")

        # Render cover letter
        cover_letter_tex_path = job_output_dir / "cover_letter.tex"
        cover_letter_tex = render_cover_letter_tex(
            package,
            resume,
            job,
            template_dir / "cover_letter.tex.jinja",
            cover_letter_tex_path
        )
        logger.info(f"Cover letter LaTeX rendered: {cover_letter_tex}")

        # Step 5: Compile to PDF
        logger.info("Step 5: Compiling to PDF...")

        resume_pdf = None
        cover_letter_pdf = None

        if check_pdflatex_installed():
            try:
                resume_pdf = compile_tex_to_pdf(resume_tex, job_output_dir)
                logger.info(f"Resume PDF compiled: {resume_pdf}")
            except Exception as e:
                warnings.append(f"Resume PDF compilation failed: {e}")
                logger.warning(f"Resume PDF compilation failed: {e}")

            try:
                cover_letter_pdf = compile_tex_to_pdf(cover_letter_tex, job_output_dir)
                logger.info(f"Cover letter PDF compiled: {cover_letter_pdf}")
            except Exception as e:
                warnings.append(f"Cover letter PDF compilation failed: {e}")
                logger.warning(f"Cover letter PDF compilation failed: {e}")
        else:
            warning_msg = (
                "pdflatex not found. LaTeX files generated but not compiled to PDF. "
                "Install LaTeX (TeX Live or MiKTeX) to generate PDFs."
            )
            warnings.append(warning_msg)
            logger.warning(warning_msg)

        # Step 6: Write metrics to JSON
        logger.info("Step 6: Writing metrics to JSON...")
        if metrics:
            try:
                import json
                metrics_path = job_output_dir / "metrics.json"
                metrics_data = {
                    "job_file": str(job_path),
                    "resume_file": str(resume_path),
                    "metrics": metrics,
                    "validation_errors": agent_errors if agent_errors else []
                }

                with open(metrics_path, 'w', encoding='utf-8') as f:
                    json.dump(metrics_data, f, indent=2, ensure_ascii=False)

                logger.info(f"Metrics written to: {metrics_path}")
            except Exception as e:
                warning_msg = f"Failed to write metrics JSON: {e}"
                warnings.append(warning_msg)
                logger.warning(warning_msg)

        # Success!
        logger.info("Pipeline completed successfully")

        return {
            "success": True,
            "package": package,
            "resume_tex": resume_tex,
            "cover_letter_tex": cover_letter_tex,
            "resume_pdf": resume_pdf,
            "cover_letter_pdf": cover_letter_pdf,
            "errors": errors,
            "warnings": warnings
        }

    except Exception as e:
        error_msg = f"Pipeline failed: {str(e)}"
        logger.error(error_msg)
        errors.append(error_msg)

        import traceback
        traceback.print_exc()

        return {
            "success": False,
            "package": None,
            "resume_tex": None,
            "cover_letter_tex": None,
            "resume_pdf": None,
            "cover_letter_pdf": None,
            "errors": errors,
            "warnings": warnings
        }


async def run_batch(
    job_resume_pairs: list[tuple[Path, Path]],
    provider: Literal["openai", "anthropic"] = "openai",
    output_dir: Path | None = None,
    verbose: bool = False,
    max_concurrent: int = 3
) -> list[dict]:
    """
    Run batch processing for multiple (job, resume) pairs.

    This function processes multiple job applications concurrently using
    AgentBatchExecutor with controlled concurrency. Each job goes through
    the complete pipeline: retrieval, generation, validation.

    Args:
        job_resume_pairs: List of (job_path, resume_path) tuples to process
        provider: LLM provider to use ("openai" or "anthropic")
        output_dir: Directory for outputs (default: outputs/)
        verbose: Enable verbose logging
        max_concurrent: Maximum number of concurrent jobs (default: 3)

    Returns:
        List of result dictionaries with keys:
        - job_path: Path to job description (str)
        - resume_path: Path to resume (str)
        - success: True if successful, False otherwise
        - errors: List of error/warning messages
        - output_dir: Path to job-specific output directory (if applicable)

    Example:
        >>> pairs = [
        ...     (Path("data/jobs/job1.yaml"), Path("data/resumes/resume.json")),
        ...     (Path("data/jobs/job2.yaml"), Path("data/resumes/resume.json")),
        ... ]
        >>> results = await run_batch(pairs, provider="openai", max_concurrent=3)
        >>> successful = [r for r in results if r["success"]]
        >>> print(f"{len(successful)}/{len(results)} jobs completed successfully")
    """
    from .config import get_config
    from ..agent import AgentBatchExecutor

    logger.info(f"Starting batch pipeline for {len(job_resume_pairs)} jobs")
    logger.info(f"Provider: {provider}, Max concurrent: {max_concurrent}")

    # Set default output directory
    if output_dir is None:
        output_dir = Path("outputs")

    output_dir.mkdir(parents=True, exist_ok=True)

    try:
        # Step 1: Get configuration
        config = get_config()

        # Validate API key for provider
        if provider == "openai":
            if not config.openai_api_key:
                raise ValueError(
                    "OpenAI API key not set. Set OPENAI_API_KEY environment variable."
                )
            config.llm_provider = "openai"
        else:
            if not config.anthropic_api_key:
                raise ValueError(
                    "Anthropic API key not set. Set ANTHROPIC_API_KEY environment variable."
                )
            config.llm_provider = "anthropic"

        logger.info(f"Using {provider} with model: {config.get_model_name(provider)}")

        # Step 2: Create batch executor
        batch_executor = AgentBatchExecutor(
            jobs=job_resume_pairs,
            config=config,
            max_concurrent=max_concurrent
        )

        # Step 3: Run all jobs
        logger.info("Starting batch execution...")
        raw_results = await batch_executor.run_all()

        # Step 4: Format results
        formatted_results = []
        for job_path, resume_path, success, errors in raw_results:
            result = {
                "job_path": str(job_path),
                "resume_path": str(resume_path),
                "success": success,
                "errors": errors,
                "output_dir": None
            }

            # If successful, determine output directory
            if success:
                try:
                    from ..models import load_job_from_yaml
                    job = load_job_from_yaml(job_path)
                    job_output_dir = output_dir / f"{job.company}_{job.title}".replace(" ", "_")
                    result["output_dir"] = str(job_output_dir)
                except Exception as e:
                    logger.warning(f"Could not determine output dir for {job_path.name}: {e}")

            formatted_results.append(result)

        # Log summary
        successful = sum(1 for r in formatted_results if r["success"])
        failed = len(formatted_results) - successful
        logger.info(f"Batch pipeline completed: {successful} succeeded, {failed} failed")

        return formatted_results

    except Exception as e:
        error_msg = f"Batch pipeline failed: {str(e)}"
        logger.error(error_msg)

        import traceback
        traceback.print_exc()

        # Return error results for all jobs
        return [
            {
                "job_path": str(job_path),
                "resume_path": str(resume_path),
                "success": False,
                "errors": [error_msg],
                "output_dir": None
            }
            for job_path, resume_path in job_resume_pairs
        ]


async def run_batch_pipeline(
    batch_config_path: Path,
    provider: Literal["openai", "anthropic"] = "openai"
) -> list[dict[str, Any]]:
    """
    Run the complete batch pipeline from a YAML configuration file.

    Parses the batch config, runs all (job, resume) pairs concurrently,
    renders LaTeX for successful packages, and persists metrics to JSONL.

    Args:
        batch_config_path: Path to batch configuration YAML file
        provider: LLM provider to use ("openai" or "anthropic")

    Returns:
        List of result dictionaries with keys:
        - job_path: Path to job description (str)
        - resume_path: Path to resume (str)
        - success: True if successful, False otherwise
        - errors: List of error/warning messages
        - output_dir: Path to job-specific output directory (str or None)
        - metrics: Dictionary of computed metrics (or None)

    Batch Config YAML Format:
        ```yaml
        batch_id: "my-batch-01"
        pairs:
          - job: "data/jobs/job1.yaml"
            resume: "data/resumes/resume.json"
          - job: "data/jobs/job2.yaml"
            resume: "data/resumes/resume.json"
        max_concurrent: 3
        output_dir: "outputs/batch_my_batch"
        ```

    Output Structure:
        ```
        outputs/batch_my_batch/
        ├── <job_id>__<candidate_id>/
        │   ├── resume.tex
        │   ├── cover_letter.tex
        │   ├── resume.pdf (if pdflatex available)
        │   └── cover_letter.pdf
        ├── metrics.jsonl
        ```

    Example:
        >>> results = await run_batch_pipeline(
        ...     Path("data/batches/example_batch.yaml"),
        ...     provider="openai"
        ... )
        >>> successful = [r for r in results if r["success"]]
        >>> print(f"{len(successful)}/{len(results)} jobs succeeded")
    """
    from .config import get_config
    from ..models import load_job_from_yaml, load_resume_from_json
    from ..embeddings import SentenceBertEncoder
    from ..agent import AsyncBatchExecutor, BatchJobResult
    from ..renderer import (
        render_resume_tex,
        render_cover_letter_tex,
        compile_tex_to_pdf,
        check_pdflatex_installed
    )

    logger.info(f"Starting batch pipeline from: {batch_config_path}")

    # Step 1: Parse batch configuration
    logger.info("Step 1: Parsing batch configuration...")
    with open(batch_config_path, 'r', encoding='utf-8') as f:
        batch_config = yaml.safe_load(f)

    batch_id = batch_config.get("batch_id", "batch")
    max_concurrent = batch_config.get("max_concurrent", 3)
    output_dir = Path(batch_config.get("output_dir", f"outputs/batch_{batch_id}"))

    # Parse pairs
    pairs: list[tuple[Path, Path]] = []
    for pair in batch_config.get("pairs", []):
        job_path = Path(pair["job"])
        resume_path = Path(pair["resume"])
        pairs.append((job_path, resume_path))

    logger.info(f"Batch ID: {batch_id}")
    logger.info(f"Job pairs: {len(pairs)}")
    logger.info(f"Max concurrent: {max_concurrent}")
    logger.info(f"Output dir: {output_dir}")

    # Create output directory
    output_dir.mkdir(parents=True, exist_ok=True)

    # Step 2: Initialize components
    logger.info("Step 2: Initializing LLM client and encoder...")
    config = get_config()

    if provider == "openai":
        if not config.openai_api_key:
            raise ValueError("OpenAI API key not set. Set OPENAI_API_KEY environment variable.")
        llm = config.get_llm_client("openai")
        logger.info(f"Using OpenAI ({llm.get_model_name()})")
    else:
        if not config.anthropic_api_key:
            raise ValueError("Anthropic API key not set. Set ANTHROPIC_API_KEY environment variable.")
        llm = config.get_llm_client("anthropic")
        logger.info(f"Using Anthropic ({llm.get_model_name()})")

    encoder = SentenceBertEncoder()
    logger.info("Encoder initialized")

    # Step 3: Run batch executor
    logger.info("Step 3: Running batch executor...")
    batch_executor = AsyncBatchExecutor(pairs, max_concurrent=max_concurrent)
    batch_results: list[BatchJobResult] = await batch_executor.run(
        llm, encoder, max_retries=config.max_retries
    )

    # Step 4: Process results - render LaTeX and collect metrics
    logger.info("Step 4: Processing results (rendering LaTeX, collecting metrics)...")
    template_dir = Path("data/templates")
    pdflatex_available = check_pdflatex_installed()

    if not pdflatex_available:
        logger.warning("pdflatex not found - only .tex files will be generated")

    formatted_results: list[dict[str, Any]] = []
    metrics_records: list[dict[str, Any]] = []

    for result in batch_results:
        result_dict: dict[str, Any] = {
            "job_path": str(result.job_path),
            "resume_path": str(result.resume_path),
            "success": result.success,
            "errors": result.errors,
            "output_dir": None,
            "metrics": result.metrics
        }

        # Metrics record for JSONL (always write, even for failures)
        metrics_record: dict[str, Any] = {
            "job_path": str(result.job_path),
            "resume_path": str(result.resume_path),
            "success": result.success,
            "errors": result.errors,
            "metrics": result.metrics
        }

        if result.success and result.package:
            try:
                # Load models for rendering
                job = load_job_from_yaml(result.job_path)
                resume = load_resume_from_json(result.resume_path)

                # Create job-specific output directory: <job_id>__<candidate_id>
                job_output_name = f"{job.job_id}__{resume.candidate_id}".replace(" ", "_")
                job_output_dir = output_dir / job_output_name
                job_output_dir.mkdir(parents=True, exist_ok=True)

                result_dict["output_dir"] = str(job_output_dir)
                metrics_record["output_dir"] = str(job_output_dir)

                # Render resume LaTeX
                resume_tex_path = job_output_dir / "resume.tex"
                render_resume_tex(
                    result.package,
                    resume,
                    template_dir / "resume.tex.jinja",
                    resume_tex_path
                )
                logger.info(f"Rendered: {resume_tex_path}")

                # Render cover letter LaTeX
                cover_letter_tex_path = job_output_dir / "cover_letter.tex"
                render_cover_letter_tex(
                    result.package,
                    resume,
                    job,
                    template_dir / "cover_letter.tex.jinja",
                    cover_letter_tex_path
                )
                logger.info(f"Rendered: {cover_letter_tex_path}")

                # Compile to PDF if available
                if pdflatex_available:
                    try:
                        compile_tex_to_pdf(resume_tex_path, job_output_dir)
                        logger.info(f"Compiled: {job_output_dir / 'resume.pdf'}")
                    except Exception as e:
                        logger.warning(f"Resume PDF compilation failed: {e}")
                        result_dict["errors"].append(f"Resume PDF compilation failed: {e}")

                    try:
                        compile_tex_to_pdf(cover_letter_tex_path, job_output_dir)
                        logger.info(f"Compiled: {job_output_dir / 'cover_letter.pdf'}")
                    except Exception as e:
                        logger.warning(f"Cover letter PDF compilation failed: {e}")
                        result_dict["errors"].append(f"Cover letter PDF compilation failed: {e}")

            except Exception as e:
                error_msg = f"Post-processing failed for {result.job_path.name}: {e}"
                logger.error(error_msg)
                result_dict["errors"].append(error_msg)
                metrics_record["errors"].append(error_msg)

        formatted_results.append(result_dict)
        metrics_records.append(metrics_record)

    # Step 5: Write metrics.jsonl
    logger.info("Step 5: Writing metrics.jsonl...")
    metrics_path = output_dir / "metrics.jsonl"
    with open(metrics_path, 'w', encoding='utf-8') as f:
        for record in metrics_records:
            f.write(json.dumps(record, ensure_ascii=False) + '\n')
    logger.info(f"Metrics written to: {metrics_path}")

    # Log final summary
    successful = sum(1 for r in formatted_results if r["success"])
    failed = len(formatted_results) - successful
    logger.info(f"Batch pipeline completed: {successful} succeeded, {failed} failed")

    return formatted_results
