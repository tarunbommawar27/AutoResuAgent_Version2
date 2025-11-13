"""
Pipeline Orchestrator
End-to-end workflow coordinator for AutoResuAgent.
"""

import logging
import asyncio
from pathlib import Path

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

        package, agent_errors = await executor.run_single_job(job_path, resume_path)

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
