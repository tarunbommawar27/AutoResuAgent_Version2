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

from src.orchestration import run_pipeline, run_batch
import yaml


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


def print_batch_results(results: list[dict]):
    """Print batch processing results in a summary table."""
    print("\n" + "=" * 100)
    print("BATCH PROCESSING RESULTS")
    print("=" * 100)

    # Calculate column widths
    max_job_len = max(len(Path(r["job_path"]).name) for r in results)
    max_resume_len = max(len(Path(r["resume_path"]).name) for r in results)
    job_col = max(max_job_len, 15)
    resume_col = max(max_resume_len, 15)

    # Print header
    print(f"\n{'Status':<8} {'Job':<{job_col}} {'Resume':<{resume_col}} {'Errors':<10}")
    print("-" * 100)

    # Print each result
    for result in results:
        job_name = Path(result["job_path"]).name
        resume_name = Path(result["resume_path"]).name
        error_count = len(result["errors"])

        if result["success"]:
            if error_count == 0:
                status = "✅ OK"
            else:
                status = "⚠️  WARN"
        else:
            status = "❌ FAIL"

        print(f"{status:<8} {job_name:<{job_col}} {resume_name:<{resume_col}} {error_count:<10}")

    # Print summary
    print("-" * 100)
    successful = sum(1 for r in results if r["success"])
    failed = len(results) - successful
    print(f"\nSummary: {successful} succeeded, {failed} failed out of {len(results)} total jobs")

    # Print detailed errors for failed jobs
    failed_jobs = [r for r in results if not r["success"]]
    if failed_jobs:
        print(f"\n🔴 Failed Jobs Details:")
        for result in failed_jobs:
            job_name = Path(result["job_path"]).name
            print(f"\n   {job_name}:")
            for error in result["errors"][:3]:  # Show first 3 errors
                print(f"      - {error}")
            if len(result["errors"]) > 3:
                print(f"      ... and {len(result['errors']) - 3} more errors")

    print("=" * 100)


async def main_async(args):
    """Async main function."""
    print_header()

    # Check mode: compare, batch, or single
    if hasattr(args, 'compare') and args.compare:
        await main_compare_async(args)
    elif args.batch_config:
        await main_batch_async(args)
    else:
        await main_single_async(args)


async def main_single_async(args):
    """Async main function for single job processing."""
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


async def main_compare_async(args):
    """Async main function for system comparison mode."""
    job_path = Path(args.job)
    resume_path = Path(args.resume)
    output_dir = Path(args.output) if args.output else Path("outputs")

    # Validate inputs
    if not job_path.exists():
        print(f"\n❌ Error: Job file not found: {job_path}")
        sys.exit(1)

    if not resume_path.exists():
        print(f"\n❌ Error: Resume file not found: {resume_path}")
        sys.exit(1)

    # Optional: gold standard bullets
    gold_bullets = None
    if hasattr(args, 'gold') and args.gold:
        gold_path = Path(args.gold)
        if not gold_path.exists():
            print(f"\n❌ Error: Gold file not found: {gold_path}")
            sys.exit(1)

        # Load gold bullets from JSON
        try:
            import json
            with open(gold_path, 'r', encoding='utf-8') as f:
                gold_data = json.load(f)
                # Expect {"bullets": ["bullet 1", "bullet 2", ...]}
                gold_bullets = gold_data.get("bullets", [])
                print(f"\n📋 Loaded {len(gold_bullets)} gold-standard bullets")
        except Exception as e:
            print(f"\n⚠️  Warning: Could not load gold bullets: {e}")

    # Print configuration
    print(f"\n📋 Comparison Configuration:")
    print(f"   Job:          {job_path}")
    print(f"   Resume:       {resume_path}")
    if gold_bullets:
        print(f"   Gold bullets: {len(gold_bullets)} reference bullets")
    print(f"   Output dir:   {output_dir}")
    print(f"   LLM Provider: {args.provider}")

    print(f"\n🔬 Running system comparison...")
    print(f"   This will compare 3 systems:")
    print(f"   - System A: Original Resume (no LLM)")
    print(f"   - System B: LLM Baseline (no retrieval)")
    print(f"   - System C: AutoResuAgent (full system)")

    try:
        from src.orchestration.config import get_config
        from src.models import load_job_from_yaml, load_resume_from_json
        from src.embeddings import SentenceBertEncoder
        from src.evaluation.comparison import compare_systems, print_comparison_table, save_comparison_results

        # Load configuration
        config = get_config()

        if args.provider == "openai":
            if not config.openai_api_key:
                raise ValueError("OpenAI API key not set. Set OPENAI_API_KEY environment variable.")
            llm = config.get_llm_client("openai")
        else:
            if not config.anthropic_api_key:
                raise ValueError("Anthropic API key not set. Set ANTHROPIC_API_KEY environment variable.")
            llm = config.get_llm_client("anthropic")

        # Load job and resume
        job = load_job_from_yaml(job_path)
        resume = load_resume_from_json(resume_path)

        # Initialize encoder
        encoder = SentenceBertEncoder()

        # Run comparison
        results = await compare_systems(job, resume, llm, encoder, gold_bullets)

        # Print table
        print_comparison_table(results)

        # Save results
        job_name = job.company or "company"
        job_title = job.title.replace(" ", "_")
        comparison_dir = output_dir / f"{job_name}_{job_title}_comparison"
        comparison_dir.mkdir(parents=True, exist_ok=True)

        comparison_file = comparison_dir / "comparison.json"
        save_comparison_results(results, comparison_file)

        print(f"\n✅ Comparison results saved to: {comparison_file}")
        print(f"\n💡 Tip: Use these metrics to demonstrate AutoResuAgent's improvements over baselines")

        sys.exit(0)

    except KeyboardInterrupt:
        print("\n\n⚠️  Interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


async def main_batch_async(args):
    """Async main function for batch processing."""
    batch_config_path = Path(args.batch_config)
    output_dir = Path(args.output) if args.output else Path("outputs")

    # Validate batch config file
    if not batch_config_path.exists():
        print(f"\n❌ Error: Batch config file not found: {batch_config_path}")
        sys.exit(1)

    # Load batch config
    try:
        with open(batch_config_path, 'r', encoding='utf-8') as f:
            batch_config = yaml.safe_load(f)
    except Exception as e:
        print(f"\n❌ Error loading batch config: {e}")
        sys.exit(1)

    # Parse job-resume pairs
    if "pairs" not in batch_config:
        print(f"\n❌ Error: Batch config must contain 'pairs' key")
        sys.exit(1)

    job_resume_pairs = []
    for i, pair in enumerate(batch_config["pairs"]):
        if "job" not in pair or "resume" not in pair:
            print(f"\n❌ Error: Pair {i+1} missing 'job' or 'resume' key")
            sys.exit(1)

        job_path = Path(pair["job"])
        resume_path = Path(pair["resume"])

        if not job_path.exists():
            print(f"\n❌ Error: Job file not found: {job_path}")
            sys.exit(1)

        if not resume_path.exists():
            print(f"\n❌ Error: Resume file not found: {resume_path}")
            sys.exit(1)

        job_resume_pairs.append((job_path, resume_path))

    # Get max_concurrent from config or use default
    max_concurrent = batch_config.get("max_concurrent", 3)

    # Print configuration
    print(f"\n📋 Batch Configuration:")
    print(f"   Batch config:  {batch_config_path}")
    print(f"   Job pairs:     {len(job_resume_pairs)}")
    print(f"   Max concurrent: {max_concurrent}")
    print(f"   Output dir:    {output_dir}")
    print(f"   LLM Provider:  {args.provider}")
    print(f"   Verbose:       {args.verbose}")

    print(f"\n📝 Jobs to process:")
    for i, (job_path, resume_path) in enumerate(job_resume_pairs, 1):
        print(f"   {i}. {job_path.name} + {resume_path.name}")

    # Run batch pipeline
    print(f"\n🚀 Starting batch processing...")
    print(f"   (This may take several minutes depending on the number of jobs)")

    try:
        results = await run_batch(
            job_resume_pairs=job_resume_pairs,
            provider=args.provider,
            output_dir=output_dir,
            verbose=args.verbose,
            max_concurrent=max_concurrent
        )

        # Print results
        print_batch_results(results)

        # Exit code (fail if any job failed)
        all_success = all(r["success"] for r in results)
        sys.exit(0 if all_success else 1)

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

  # Batch processing mode
  python main.py --batch-config data/batch.yaml

  # Batch processing with custom provider and output
  python main.py --batch-config data/batch.yaml --provider anthropic --output my_batch_outputs

  # System comparison mode (evaluates 3 systems)
  python main.py --compare --job data/jobs/ml-engineer.yaml --resume data/resumes/jane-doe.json

  # Comparison with gold-standard bullets
  python main.py --compare --job data/jobs/ml-engineer.yaml --resume data/resumes/jane-doe.json --gold data/gold/bullets.json

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
        required=False,
        help="Path to job description YAML file (e.g., data/jobs/ml-engineer-sample.yaml)"
    )

    parser.add_argument(
        "--resume",
        type=str,
        required=False,
        help="Path to resume JSON file (e.g., data/resumes/jane-doe-sample.json)"
    )

    parser.add_argument(
        "--batch-config",
        type=str,
        required=False,
        help="Path to batch config YAML file for processing multiple jobs (e.g., data/batch.yaml)"
    )

    parser.add_argument(
        "--compare",
        action="store_true",
        help="Run system comparison mode (compares Original Resume, LLM Baseline, and AutoResuAgent)"
    )

    parser.add_argument(
        "--gold",
        type=str,
        required=False,
        help="Path to gold-standard bullets JSON file for comparison metrics (optional, only valid with --compare)"
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

    # Validate arguments: mutually exclusive modes
    modes = sum([bool(args.batch_config), bool(args.compare)])

    if modes > 1:
        parser.error("Cannot use --batch-config and --compare together. Choose one mode.")

    if args.compare:
        # Compare mode: requires job and resume
        if not args.job or not args.resume:
            parser.error("--compare mode requires both --job and --resume")
    elif args.batch_config:
        # Batch mode: ignore job and resume if provided
        if args.job or args.resume:
            print("\n⚠️  Warning: --job and --resume are ignored when using --batch-config")
        if args.gold:
            parser.error("--gold is only valid with --compare mode")
    else:
        # Single mode: both job and resume are required
        if not args.job or not args.resume:
            parser.error("Either --batch-config, --compare, OR both --job and --resume must be provided")
        if args.gold:
            parser.error("--gold is only valid with --compare mode")

    # Setup logging
    setup_logging(args.verbose)

    # Run async main
    asyncio.run(main_async(args))


if __name__ == "__main__":
    main()
