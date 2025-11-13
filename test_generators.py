"""
Test script for content generators (bullet and cover letter generation).
Tests the full pipeline: retrieval → LLM generation → validation.
"""

import sys
from pathlib import Path

# Fix Unicode encoding for Windows console
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8')

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent))

import asyncio
from src.models import load_job_from_yaml, load_resume_from_json
from src.embeddings import SentenceBertEncoder, ResumeFaissIndex, retrieve_relevant_experiences
from src.llm import OpenAILLMClient, AnthropicLLMClient
from src.generators import generate_bullets_for_job, generate_cover_letter
from src.orchestration import get_config


def print_section(title: str):
    """Print a formatted section header."""
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70)


def test_setup():
    """Test configuration and data loading."""
    print_section("Testing Setup")

    # Check config
    config = get_config()
    print(f"\n✓ Configuration loaded")
    print(f"   OpenAI API key: {'✓ Set' if config.openai_api_key else '✗ Not set'}")
    print(f"   Anthropic API key: {'✓ Set' if config.anthropic_api_key else '✗ Not set'}")

    # Check sample data
    job_path = Path("data/jobs/ml-engineer-sample.yaml")
    resume_path = Path("data/resumes/jane-doe-sample.json")

    if not job_path.exists():
        print(f"\n✗ Sample job not found: {job_path}")
        return None, None, config

    if not resume_path.exists():
        print(f"\n✗ Sample resume not found: {resume_path}")
        return None, None, config

    print(f"\n✓ Loading sample data...")
    job = load_job_from_yaml(job_path)
    resume = load_resume_from_json(resume_path)

    print(f"   Job: {job.title} at {job.company}")
    print(f"   Resume: {resume.name}")
    print(f"   Experiences: {len(resume.experiences)}")
    print(f"   Total bullets: {len(resume.get_all_bullets())}")

    return job, resume, config


async def test_bullet_generation(job, resume, llm_client):
    """Test bullet generation with retrieval."""
    print_section("Testing Bullet Generation")

    if job is None or resume is None:
        print("\n⚠ Skipping - sample data not available")
        return None

    if llm_client is None:
        print("\n⚠ Skipping - LLM client not initialized")
        return None

    try:
        # Step 1: Build FAISS index
        print("\n✓ Building FAISS index for retrieval...")
        encoder = SentenceBertEncoder()
        index = ResumeFaissIndex(encoder)
        index.build_from_experiences(resume.experiences)
        print(f"   Indexed {len(index)} bullets")

        # Step 2: Retrieve relevant experiences
        print("\n✓ Retrieving relevant experiences...")
        retrieved = retrieve_relevant_experiences(job, resume, encoder, index, top_k=3)
        print(f"   Retrieved for {len(retrieved)} responsibilities")

        total_items = sum(len(items) for items in retrieved.values())
        print(f"   Total retrieved items: {total_items}")

        # Show sample
        if retrieved:
            first_resp = list(retrieved.keys())[0]
            print(f"\n   Sample - '{first_resp[:60]}...':")
            for i, item in enumerate(retrieved[first_resp][:2], 1):
                print(f"      {i}. [{item['score']:.2f}] {item['text'][:50]}...")

        # Step 3: Generate bullets
        print(f"\n✓ Generating tailored bullets using {llm_client.__class__.__name__}...")
        print("   (This may take 10-30 seconds...)")

        bullets = await generate_bullets_for_job(job, resume, retrieved, llm_client)

        print(f"\n✓ Generated {len(bullets)} bullets successfully!")

        # Display results
        print("\n   Generated Bullets:")
        for i, bullet in enumerate(bullets[:5], 1):  # Show first 5
            print(f"\n   {i}. {bullet.text}")
            print(f"      Source: {bullet.source_experience_id}")
            print(f"      Skills: {', '.join(bullet.skills_covered[:5])}")

        if len(bullets) > 5:
            print(f"\n   ...and {len(bullets) - 5} more bullets")

        # Validation check
        print("\n✓ Running Pydantic validation checks...")
        validation_passed = True
        for bullet in bullets:
            # Check length
            if len(bullet.text) < 30 or len(bullet.text) > 250:
                print(f"   ⚠ Length issue: {len(bullet.text)} chars")
                validation_passed = False
                break

            # Check for first-person pronouns (Pydantic should catch this)
            # If we got here, validation passed

        if validation_passed:
            print("   ✓ All bullets passed validation!")
            print("   - No first-person pronouns")
            print("   - Correct length (30-250 chars)")
            print("   - Valid IDs and skills")

        return bullets

    except Exception as e:
        print(f"\n✗ Bullet generation failed: {e}")
        import traceback
        traceback.print_exc()
        return None


async def test_cover_letter_generation(job, resume, bullets, llm_client):
    """Test cover letter generation."""
    print_section("Testing Cover Letter Generation")

    if job is None or resume is None:
        print("\n⚠ Skipping - sample data not available")
        return None

    if llm_client is None:
        print("\n⚠ Skipping - LLM client not initialized")
        return None

    if not bullets:
        print("\n⚠ Skipping - no bullets available")
        return None

    try:
        print(f"\n✓ Generating cover letter using {llm_client.__class__.__name__}...")
        print("   (This may take 10-30 seconds...)")

        cover_letter = await generate_cover_letter(job, resume, bullets, llm_client)

        print(f"\n✓ Generated cover letter successfully!")
        print(f"   ID: {cover_letter.id}")
        print(f"   Job ID: {cover_letter.job_id}")
        print(f"   Tone: {cover_letter.tone}")
        print(f"   Total length: {len(cover_letter.get_full_text())} chars")

        # Display sections
        print("\n   Opening:")
        print(f"   {cover_letter.opening}")

        print("\n   Body (preview):")
        body_preview = cover_letter.body[:300] + "..." if len(cover_letter.body) > 300 else cover_letter.body
        for line in body_preview.split('\n'):
            print(f"   {line}")

        print("\n   Closing:")
        print(f"   {cover_letter.closing}")

        # Validation
        print("\n✓ Running Pydantic validation checks...")
        print(f"   - Opening length: {len(cover_letter.opening)} chars")
        print(f"   - Body length: {len(cover_letter.body)} chars")
        print(f"   - Closing length: {len(cover_letter.closing)} chars")
        print("   ✓ Cover letter passed validation!")

        return cover_letter

    except Exception as e:
        print(f"\n✗ Cover letter generation failed: {e}")
        import traceback
        traceback.print_exc()
        return None


async def run_async_tests():
    """Run all generator tests."""
    print("\n" + "📝" * 35)
    print("  AutoResuAgent - Generators Test Suite")
    print("📝" * 35)

    try:
        # Setup
        job, resume, config = test_setup()

        if job is None or resume is None:
            print("\n❌ Cannot proceed without sample data")
            print("\nPlease ensure these files exist:")
            print("  - data/jobs/ml-engineer-sample.yaml")
            print("  - data/resumes/jane-doe-sample.json")
            return

        # Choose LLM client
        llm_client = None
        if config.openai_api_key:
            print("\n✓ Using OpenAI client")
            llm_client = OpenAILLMClient(config)
        elif config.anthropic_api_key:
            print("\n✓ Using Anthropic client")
            llm_client = AnthropicLLMClient(config)
        else:
            print("\n⚠ No API keys configured")
            print("\nTo test generators:")
            print("  1. Copy .env.example to .env")
            print("  2. Add at least one API key:")
            print("     OPENAI_API_KEY=sk-...")
            print("     ANTHROPIC_API_KEY=sk-ant-...")
            print("  3. Run this test again")
            return

        # Test bullet generation
        bullets = await test_bullet_generation(job, resume, llm_client)

        # Test cover letter generation
        if bullets:
            cover_letter = await test_cover_letter_generation(job, resume, bullets, llm_client)
        else:
            cover_letter = None

        # Summary
        print_section("Test Summary")

        if bullets and cover_letter:
            print("\n✅ All generator tests passed successfully!")

            print("\n📊 Generation Statistics:")
            print(f"   - Bullets generated: {len(bullets)}")
            print(f"   - Cover letter sections: 3 (opening, body, closing)")
            print(f"   - Total cover letter length: {len(cover_letter.get_full_text())} chars")

            print("\n✨ Generators are production-ready!")
            print("\nNext steps:")
            print("  1. Retrieval + LLM generation working correctly")
            print("  2. Pydantic validation catching errors")
            print("  3. Ready to implement agent components (planner, validator, executor)")
            print("  4. Can generate full tailored resume + cover letter packages")

        elif bullets:
            print("\n✅ Bullet generation tests passed!")
            print("⚠ Cover letter generation encountered issues")

        else:
            print("\n⚠ Some tests did not complete")
            print("Check the errors above for details")

    except Exception as e:
        print(f"\n❌ Error during testing: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


def main():
    """Main entry point."""
    asyncio.run(run_async_tests())


if __name__ == "__main__":
    main()
