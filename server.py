"""
FastAPI Backend Server for AutoResuAgent Web Application

Provides REST API endpoints for:
- Parsing raw job/resume text into structured data
- Generating tailored resumes using the agent executor
"""

import os
import json
import yaml
import asyncio
import logging
from pathlib import Path
from typing import Optional
from datetime import datetime

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# AutoResuAgent imports
from src.llm import OpenAILLMClient
from src.embeddings import SentenceBertEncoder
from src.agent import AgentExecutor
from src.parsers import DataParser
from src.models import load_job_from_yaml, load_resume_from_json

# Initialize FastAPI app
app = FastAPI(
    title="AutoResuAgent API",
    description="API for parsing and generating tailored resumes",
    version="1.0.0"
)

# CORS middleware - allow all origins for development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify exact origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global state for LLM and encoder (initialized on startup)
llm_client: Optional[OpenAILLMClient] = None
encoder: Optional[SentenceBertEncoder] = None
parser: Optional[DataParser] = None


# Request/Response Models
class ParseJobRequest(BaseModel):
    """Request model for job parsing."""
    raw_text: str


class ParseJobResponse(BaseModel):
    """Response model for job parsing."""
    yaml_content: str


class ParseResumeRequest(BaseModel):
    """Request model for resume parsing."""
    raw_text: str


class ParseResumeResponse(BaseModel):
    """Response model for resume parsing."""
    json_content: str


class GenerateRequest(BaseModel):
    """Request model for resume generation."""
    job_yaml: str
    resume_json: str


class GenerateResponse(BaseModel):
    """Response model for resume generation."""
    success: bool
    cover_letter: Optional[str] = None
    cover_letter_latex: Optional[str] = None
    bullets: Optional[list[dict]] = None
    resume_latex: Optional[str] = None
    change_summary: Optional[str] = None
    errors: Optional[list[str]] = None
    job_id: Optional[str] = None
    candidate_id: Optional[str] = None


# Startup event - initialize LLM and encoder
@app.on_event("startup")
async def startup_event():
    """Initialize LLM client and encoder on server startup."""
    global llm_client, encoder, parser

    logger.info("=" * 60)
    logger.info("Starting AutoResuAgent API Server")
    logger.info("=" * 60)

    # Get OpenAI API key from environment
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        logger.error("OPENAI_API_KEY environment variable not set!")
        raise RuntimeError(
            "OPENAI_API_KEY environment variable not set. "
            "Please set it before starting the server."
        )

    logger.info("Initializing LLM client...")
    # Initialize LLM client
    llm_client = OpenAILLMClient(
        api_key=api_key,
        model="gpt-4o-mini",  # Use fast model for parsing and generation
        max_tokens=4096,
        temperature=0.0
    )
    logger.info(f"✅ LLM client initialized: {llm_client.model}")

    logger.info("Initializing SentenceBERT encoder...")
    # Initialize SentenceBERT encoder
    encoder = SentenceBertEncoder()
    logger.info(f"✅ Encoder initialized: {encoder.model_name}")

    # Initialize parser
    parser = DataParser(llm_client)
    logger.info("✅ DataParser initialized")

    logger.info("=" * 60)
    logger.info("Server ready! Listening for requests...")
    logger.info("=" * 60)


# Health check endpoint
@app.get("/")
async def root():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "AutoResuAgent API",
        "version": "1.0.0"
    }


# Parse job endpoint
@app.post("/parse/job", response_model=ParseJobResponse)
async def parse_job(request: ParseJobRequest):
    """
    Parse raw job posting text into structured YAML.

    Accepts raw text from LinkedIn, company careers pages, etc.
    and extracts structured job information.
    """
    if not parser:
        raise HTTPException(status_code=503, detail="Parser not initialized")

    try:
        yaml_content = await parser.parse_raw_job(request.raw_text)
        return ParseJobResponse(yaml_content=yaml_content)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to parse job posting: {str(e)}"
        )


# Parse resume endpoint
@app.post("/parse/resume", response_model=ParseResumeResponse)
async def parse_resume(request: ParseResumeRequest):
    """
    Parse raw resume text into structured JSON.

    Accepts raw text from LinkedIn profiles, PDF resumes, etc.
    and extracts structured candidate information.
    """
    if not parser:
        raise HTTPException(status_code=503, detail="Parser not initialized")

    try:
        json_content = await parser.parse_raw_resume(request.raw_text)
        return ParseResumeResponse(json_content=json_content)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to parse resume: {str(e)}"
        )


# Generate tailored resume endpoint
@app.post("/generate", response_model=GenerateResponse)
async def generate_resume(request: GenerateRequest):
    """
    Generate tailored resume from structured job and resume data.

    Accepts YAML job description and JSON resume, saves them to temp files,
    runs the agent executor, and returns the generated content.
    """
    if not llm_client or not encoder:
        raise HTTPException(status_code=503, detail="Services not initialized")

    # Create temp directory if it doesn't exist
    temp_dir = Path("data/temp")
    temp_dir.mkdir(parents=True, exist_ok=True)

    # Generate unique filenames with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    job_path = temp_dir / f"job_{timestamp}.yaml"
    resume_path = temp_dir / f"resume_{timestamp}.json"

    try:
        logger.info("=" * 60)
        logger.info(f"🚀 Starting resume generation (timestamp: {timestamp})")
        logger.info("=" * 60)

        # Smart parsing: Try structured format first, fallback to raw text parsing

        # --- Process Job Data ---
        logger.info("📄 Processing job data...")
        job_yaml_content = request.job_yaml
        try:
            # Try parsing as structured YAML
            job_data = yaml.safe_load(request.job_yaml)
            # If it's valid YAML but just a string (raw text), it needs parsing
            if isinstance(job_data, str):
                raise yaml.YAMLError("Content is plain text, not structured YAML")
            logger.info("✅ Job data is valid YAML")
        except yaml.YAMLError:
            # Failed to parse as YAML - assume it's raw text
            logger.info("⚠️  Job data is raw text, parsing with LLM...")
            # Use DataParser to convert raw text to structured YAML
            if not parser:
                raise HTTPException(
                    status_code=503,
                    detail="Parser not initialized for raw text conversion"
                )
            try:
                job_yaml_content = await parser.parse_raw_job(request.job_yaml)
                logger.info("✅ Job data parsed successfully")
            except Exception as e:
                logger.error(f"❌ Job parsing failed: {e}")
                raise HTTPException(
                    status_code=400,
                    detail=f"Failed to parse job text (raw or YAML): {str(e)}"
                )

        # Save job YAML
        with open(job_path, "w", encoding="utf-8") as f:
            f.write(job_yaml_content)
        logger.info(f"💾 Job saved to {job_path}")

        # --- Process Resume Data ---
        logger.info("📄 Processing resume data...")
        resume_json_content = request.resume_json
        try:
            # Try parsing as structured JSON
            resume_data = json.loads(request.resume_json)
            logger.info("✅ Resume data is valid JSON")
        except json.JSONDecodeError:
            # Failed to parse as JSON - assume it's raw text
            logger.info("⚠️  Resume data is raw text, parsing with LLM...")
            # Use DataParser to convert raw text to structured JSON
            if not parser:
                raise HTTPException(
                    status_code=503,
                    detail="Parser not initialized for raw text conversion"
                )
            try:
                resume_json_content = await parser.parse_raw_resume(request.resume_json)
                logger.info("✅ Resume data parsed successfully")
            except Exception as e:
                logger.error(f"❌ Resume parsing failed: {e}")
                raise HTTPException(
                    status_code=400,
                    detail=f"Failed to parse resume text (raw or JSON): {str(e)}"
                )

        # Save resume JSON
        with open(resume_path, "w", encoding="utf-8") as f:
            f.write(resume_json_content)
        logger.info(f"💾 Resume saved to {resume_path}")

        # Load and validate using Pydantic models
        logger.info("🔍 Validating data against Pydantic schemas...")
        try:
            job = load_job_from_yaml(job_path)
            resume = load_resume_from_json(resume_path)
            logger.info(f"✅ Schemas validated: Job='{job.title}' at {job.company}, Candidate='{resume.name}'")
        except Exception as e:
            logger.error(f"❌ Schema validation failed: {e}")
            raise HTTPException(
                status_code=400,
                detail=f"Schema validation failed: {str(e)}"
            )

        # Run agent executor
        logger.info("🤖 Initializing AgentExecutor...")
        executor = AgentExecutor(
            llm=llm_client,
            encoder=encoder,
            max_retries=2  # Reduce retries for faster web response
        )
        logger.info("✅ AgentExecutor initialized")

        logger.info("🎯 Running full generation pipeline (this may take 30-60 seconds)...")
        logger.info("   Step 1: Building FAISS index from resume experiences...")
        logger.info("   Step 2: Retrieving relevant experiences for job...")
        logger.info("   Step 3: Generating tailored bullets with validation...")
        logger.info("   Step 4: Generating cover letter...")

        package, errors, metrics = await executor.run_single_job(
            job_path=job_path,
            resume_path=resume_path,
            mode="full"
        )

        if not package:
            logger.error("❌ Generation failed - no package returned")
            return GenerateResponse(
                success=False,
                errors=errors or ["Generation failed"]
            )

        logger.info(f"✅ Generation complete! Generated {len(package.bullets)} bullets")

        # Format bullets for response
        bullets_data = [
            {
                "id": bullet.id,
                "text": bullet.text,
                "responsibility_id": bullet.responsibility_id,
                "source_experience_id": bullet.source_experience_id,
                "source_project_id": getattr(bullet, 'source_project_id', None)
            }
            for bullet in package.bullets
        ]

        # === NEW FEATURE 1: Generate LaTeX Output ===
        logger.info("📝 Generating LaTeX resume...")
        try:
            resume_latex = await parser.generate_resume_latex(
                candidate_data=resume.dict(),
                tailored_bullets=bullets_data,
                job_title=job.title,
                company=job.company or "Target Company"
            )
            logger.info(f"✅ Resume LaTeX generated ({len(resume_latex)} chars)")
        except Exception as e:
            logger.warning(f"⚠️  LaTeX resume generation failed: {e}")
            resume_latex = None

        logger.info("📝 Generating LaTeX cover letter...")
        try:
            cover_letter_latex = await parser.generate_cover_letter_latex(
                cover_letter_text=package.cover_letter.text,
                candidate_name=resume.name,
                candidate_email=str(resume.email),
                candidate_phone=resume.phone or "N/A",
                job_title=job.title,
                company=job.company or "Target Company"
            )
            logger.info(f"✅ Cover letter LaTeX generated ({len(cover_letter_latex)} chars)")
        except Exception as e:
            logger.warning(f"⚠️  LaTeX cover letter generation failed: {e}")
            cover_letter_latex = None

        # === NEW FEATURE 2: Generate Change Summary ===
        logger.info("📊 Generating change summary (semantic diff)...")
        try:
            change_summary = await parser.generate_change_summary(
                original_resume_data=resume.dict(),
                tailored_bullets=bullets_data,
                job_description=job.dict()
            )
            logger.info(f"✅ Change summary generated")
            logger.info(f"Summary preview:\n{change_summary[:200]}...")
        except Exception as e:
            logger.warning(f"⚠️  Change summary generation failed: {e}")
            change_summary = None

        logger.info("=" * 60)
        logger.info("✨ All tasks completed successfully!")
        logger.info("=" * 60)

        return GenerateResponse(
            success=True,
            cover_letter=package.cover_letter.text,
            cover_letter_latex=cover_letter_latex,
            bullets=bullets_data,
            resume_latex=resume_latex,
            change_summary=change_summary,
            errors=errors if errors else None,
            job_id=package.job_id,
            candidate_id=package.candidate_id
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error("=" * 60)
        logger.error(f"❌ CRITICAL ERROR: {str(e)}")
        logger.error("=" * 60)
        import traceback
        logger.error(traceback.format_exc())
        raise HTTPException(
            status_code=500,
            detail=f"Generation failed: {str(e)}"
        )
    finally:
        # Clean up temp files (optional - you may want to keep for debugging)
        # if job_path.exists():
        #     job_path.unlink()
        # if resume_path.exists():
        #     resume_path.unlink()
        pass


# Run server
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "server:app",
        host="0.0.0.0",
        port=8000,
        reload=True  # Enable auto-reload during development
    )
