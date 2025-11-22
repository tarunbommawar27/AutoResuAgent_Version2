#!/usr/bin/env python3
"""
Resume Ingestion CLI Tool
Converts raw resume text files into structured CandidateProfile JSON.

Usage:
    python tools/ingest_resume.py --input data/raw/resume.txt --output data/resumes/resume.json --provider openai

Example:
    python tools/ingest_resume.py \
        --input data/raw/tarun_resume.txt \
        --output data/resumes/tarun_resume.json \
        --provider openai \
        --verbose
"""

import sys
import json
import asyncio
import argparse
import logging
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.orchestration import get_config
from src.ingestion import parse_resume_text_to_profile


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
    Async main function for resume ingestion.

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
    print(f"Reading raw resume from: {input_path}")
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

    # Parse resume
    print("Parsing resume with LLM...")
    try:
        profile = await parse_resume_text_to_profile(raw_text, client)
    except Exception as e:
        print(f"Error parsing resume: {e}")
        return 1

    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Write JSON output
    print(f"Writing JSON to: {output_path}")
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(profile.model_dump(), f, indent=2, ensure_ascii=False)

    # Print summary
    print("\n" + "=" * 50)
    print("Resume Ingestion Complete!")
    print("=" * 50)
    print(f"Name:        {profile.name}")
    print(f"Email:       {profile.email}")
    print(f"Location:    {profile.location or 'N/A'}")
    print(f"Skills:      {len(profile.skills)} skills")
    print(f"Experience:  {len(profile.experiences)} positions")
    print(f"Education:   {len(profile.education)} entries")
    print(f"Output:      {output_path}")
    print("=" * 50)

    return 0


def main() -> None:
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Convert raw resume text to structured CandidateProfile JSON",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Basic usage with OpenAI
  python tools/ingest_resume.py --input data/raw/resume.txt --output data/resumes/resume.json

  # Use Anthropic instead
  python tools/ingest_resume.py --input data/raw/resume.txt --output data/resumes/resume.json --provider anthropic

  # With verbose logging
  python tools/ingest_resume.py --input data/raw/resume.txt --output data/resumes/resume.json --verbose
"""
    )

    parser.add_argument(
        "--input", "-i",
        type=str,
        required=True,
        help="Path to raw resume text file"
    )

    parser.add_argument(
        "--output", "-o",
        type=str,
        required=True,
        help="Path to output JSON file"
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
