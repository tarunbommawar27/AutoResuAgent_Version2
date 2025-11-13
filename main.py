"""
AutoResuAgent - Main CLI Application
Automated resume and cover letter generation using LLMs and semantic retrieval.
"""

import sys
import argparse
import asyncio
import logging
from pathlib import Path

# Fix Unicode encoding for Windows console
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8')

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.orchestration import run_pipeline


def setup_logging(verbose: bool = False):
    """Configure logging for the application."""
    level = logging.DEBUG if verbose else logging.INFO

    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )


def print_header():
    """Print application header."""
    print("\n" + "=" * 70)
    print("  AutoResuAgent - Automated Resume & Cover Letter Generator")
    print("=" * 70)


def print_result(result: dict):
    """Print pipeline result in a user-friendly format."""
    print("\n" + "-" * 70)

    if result["success"]:
        print("✅ Pipeline completed successfully!")

        print("\n📄 Generated Files:")
        if result["resume_tex"]:
            print(f"   Resume (LaTeX):       {result['resume_tex']}")
        if result["cover_letter_tex"]:
            print(f"   Cover Letter (LaTeX): {result['cover_letter_tex']}")

        if result["resume_pdf"]:
            print(f"   Resume (PDF):         {result['resume_pdf']}")
        if result["cover_letter_pdf"]:
            print(f"   Cover Letter (PDF):   {result['cover_letter_pdf']}")

        # Warnings
        if result["warnings"]:
            print(f"\n⚠️  Warnings ({len(result['warnings'])}):")
            for warning in result["warnings"]:
                print(f"   - {warning}")

        # Package stats
        if result["package"]:
            pkg = result["package"]
            print(f"\n📊 Package Statistics:")
            print(f"   Bullets generated:    {len(pkg.bullets)}")
            print(f"   Cover letter sections: 3 (opening, body, closing)")
            if pkg.cover_letter:
                full_text = pkg.cover_letter.get_full_text()
                print(f"   Cover letter length:  {len(full_text)} chars")

    else:
        print("❌ Pipeline failed!")

        if result["errors"]:
            print(f"\n🔴 Errors ({len(result['errors'])}):")
            for error in result["errors"]:
                print(f"   - {error}")

    print("-" * 70)


async def main_async(args):
    """Async main function."""
    print_header()

    # Validate inputs
    job_path = Path(args.job)
    resume_path = Path(args.resume)
    output_dir = Path(args.output) if args.output else Path("outputs")

    if not job_path.exists():
        print(f"\n❌ Error: Job file not found: {job_path}")
        sys.exit(1)

    if not resume_path.exists():
        print(f"\n❌ Error: Resume file not found: {resume_path}")
        sys.exit(1)

    # Print configuration
    print(f"\n📋 Configuration:")
    print(f"   Job:          {job_path}")
    print(f"   Resume:       {resume_path}")
    print(f"   Output dir:   {output_dir}")
    print(f"   LLM Provider: {args.provider}")
    print(f"   Verbose:      {args.verbose}")

    # Run pipeline
    print(f"\n🚀 Starting pipeline...")
    print(f"   (This may take 30-90 seconds depending on API speed)")

    try:
        result = await run_pipeline(
            job_path=job_path,
            resume_path=resume_path,
            use_openai=(args.provider == "openai"),
            output_dir=output_dir
        )

        # Print results
        print_result(result)

        # Exit code
        sys.exit(0 if result["success"] else 1)

    except KeyboardInterrupt:
        print("\n\n⚠️  Interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="AutoResuAgent - Automated Resume & Cover Letter Generator",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Generate resume for a specific job using OpenAI
  python main.py --job data/jobs/ml-engineer-sample.yaml --resume data/resumes/jane-doe-sample.json

  # Use Anthropic Claude instead of OpenAI
  python main.py --job data/jobs/ml-engineer-sample.yaml --resume data/resumes/jane-doe-sample.json --provider anthropic

  # Specify custom output directory
  python main.py --job data/jobs/ml-engineer-sample.yaml --resume data/resumes/jane-doe-sample.json --output my_outputs

  # Enable verbose logging
  python main.py --job data/jobs/ml-engineer-sample.yaml --resume data/resumes/jane-doe-sample.json --verbose

Requirements:
  - At least one API key must be set in .env file:
    - OPENAI_API_KEY (for OpenAI GPT models)
    - ANTHROPIC_API_KEY (for Anthropic Claude models)

  - Optional: Install LaTeX (TeX Live or MiKTeX) for PDF generation
    - Without LaTeX, only .tex files will be generated
    - .tex files can be manually compiled to PDF later

Notes:
  - The pipeline will:
    1. Load job description and resume
    2. Build semantic search index (FAISS)
    3. Retrieve relevant experiences
    4. Generate tailored bullets using LLM
    5. Validate output (hallucination detection, length checks)
    6. Generate cover letter
    7. Render LaTeX templates
    8. Compile to PDF (if LaTeX installed)

  - Generated files are saved in: outputs/<company>_<job_title>/
"""
    )

    parser.add_argument(
        "--job",
        type=str,
        required=True,
        help="Path to job description YAML file (e.g., data/jobs/ml-engineer-sample.yaml)"
    )

    parser.add_argument(
        "--resume",
        type=str,
        required=True,
        help="Path to resume JSON file (e.g., data/resumes/jane-doe-sample.json)"
    )

    parser.add_argument(
        "--provider",
        type=str,
        choices=["openai", "anthropic"],
        default="openai",
        help="LLM provider to use (default: openai)"
    )

    parser.add_argument(
        "--output",
        type=str,
        default=None,
        help="Output directory for generated files (default: outputs/)"
    )

    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Enable verbose logging"
    )

    args = parser.parse_args()

    # Setup logging
    setup_logging(args.verbose)

    # Run async main
    asyncio.run(main_async(args))


if __name__ == "__main__":
    main()
