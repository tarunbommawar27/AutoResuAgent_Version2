#!/usr/bin/env python3
"""
Job Description Ingestion CLI Tool
Converts raw job description text files into structured JobDescription YAML.

Usage:
    python tools/ingest_job.py --input data/raw/job.txt --output data/jobs/job.yaml --provider openai

Example:
    python tools/ingest_job.py \
        --input data/raw/cisco_ml_engineer.txt \
        --output data/jobs/cisco_ml_engineer.yaml \
        --provider openai \
        --verbose
"""

import sys
import asyncio
import argparse
import logging
from pathlib import Path

import yaml

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.orchestration import get_config
from src.ingestion import parse_job_text_to_description


def setup_logging(verbose: bool = False) -> None:
    """Configure logging for the CLI tool."""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[logging.StreamHandler(sys.stdout)]
    )


async def main_async(args: argparse.Namespace) -> int:
    """
    Async main function for job description ingestion.

    Args:
        args: Parsed command line arguments

    Returns:
        Exit code (0 for success, 1 for failure)
    """
    input_path = Path(args.input)
    output_path = Path(args.output)

    # Validate input file
    if not input_path.exists():
        print(f"Error: Input file not found: {input_path}")
        return 1

    # Read raw text
    print(f"Reading raw job description from: {input_path}")
    with open(input_path, 'r', encoding='utf-8') as f:
        raw_text = f.read()

    if not raw_text.strip():
        print("Error: Input file is empty")
        return 1

    print(f"Read {len(raw_text)} characters")

    # Initialize LLM client
    print(f"Initializing {args.provider} LLM client...")
    try:
        config = get_config()
        client = config.get_llm_client(args.provider)
        print(f"Using model: {client.get_model_name()}")
    except Exception as e:
        print(f"Error initializing LLM client: {e}")
        return 1

    # Parse job description
    print("Parsing job description with LLM...")
    try:
        job = await parse_job_text_to_description(raw_text, client)
    except Exception as e:
        print(f"Error parsing job description: {e}")
        return 1

    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Convert to dict for YAML output
    job_dict = job.model_dump(exclude_none=True)

    # Write YAML output
    print(f"Writing YAML to: {output_path}")
    with open(output_path, 'w', encoding='utf-8') as f:
        yaml.safe_dump(
            job_dict,
            f,
            default_flow_style=False,
            allow_unicode=True,
            sort_keys=False,
            width=120
        )

    # Print summary
    print("\n" + "=" * 50)
    print("Job Description Ingestion Complete!")
    print("=" * 50)
    print(f"Title:           {job.title}")
    print(f"Company:         {job.company or 'N/A'}")
    print(f"Location:        {job.location or 'N/A'}")
    print(f"Seniority:       {job.seniority or 'N/A'}")
    print(f"Required Skills: {len(job.required_skills)} skills")
    print(f"Nice-to-Have:    {len(job.nice_to_have_skills or [])} skills")
    print(f"Responsibilities:{len(job.responsibilities)} items")
    print(f"Output:          {output_path}")
    print("=" * 50)

    return 0


def main() -> None:
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Convert raw job description text to structured JobDescription YAML",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Basic usage with OpenAI
  python tools/ingest_job.py --input data/raw/job.txt --output data/jobs/job.yaml

  # Use Anthropic instead
  python tools/ingest_job.py --input data/raw/job.txt --output data/jobs/job.yaml --provider anthropic

  # With verbose logging
  python tools/ingest_job.py --input data/raw/job.txt --output data/jobs/job.yaml --verbose
"""
    )

    parser.add_argument(
        "--input", "-i",
        type=str,
        required=True,
        help="Path to raw job description text file"
    )

    parser.add_argument(
        "--output", "-o",
        type=str,
        required=True,
        help="Path to output YAML file"
    )

    parser.add_argument(
        "--provider",
        type=str,
        choices=["openai", "anthropic"],
        default="openai",
        help="LLM provider to use (default: openai)"
    )

    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable verbose logging"
    )

    args = parser.parse_args()

    # Setup logging
    setup_logging(args.verbose)

    # Run async main
    exit_code = asyncio.run(main_async(args))
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
