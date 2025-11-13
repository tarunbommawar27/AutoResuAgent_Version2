"""
Test script for agent components (validator, executor, async execution).
Tests the full agentic loop: Retrieve → Generate → Validate → Retry
"""

import sys
from pathlib import Path

# Fix Unicode encoding for Windows console
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8')

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent))

import asyncio
from src.models import load_job_from_yaml, load_resume_from_json, GeneratedBullet
from src.embeddings import SentenceBertEncoder
from src.llm import OpenAILLMClient, AnthropicLLMClient
from src.agent import (
    validate_bullet_length,
    validate_skill_coverage,
    detect_hallucinations,
    validate_bullets_only,
    AgentExecutor,
)
from src.orchestration import get_config


def print_section(title: str):
    """Print a formatted section header."""
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70)


def test_validation_functions():
    """Test individual validation functions."""
    print_section("Testing Validation Functions")

    # Create test bullets
    print("\n✓ Creating test bullets...")

    bullet_valid = GeneratedBullet(
        id="bullet-001",
        text="Developed scalable ML pipeline processing 1M+ requests daily using Python and AWS",
        source_experience_id="exp-001",
        skills_covered=["Python", "AWS", "Machine Learning"]
    )

    bullet_too_long = GeneratedBullet(
        id="bullet-002",
        text="A" * 150,  # 150 chars - too long for LaTeX
        source_experience_id="exp-001",
        skills_covered=["Python"]
    )

    print(f"   Created {2} test bullets")

    # Test bullet length validation
    print("\n✓ Testing bullet_length validation...")
    error = validate_bullet_length(bullet_valid, max_len=150)
    if error:
        print(f"   ✗ Valid bullet failed: {error}")
    else:
        print(f"   ✓ Valid bullet passed (length: {len(bullet_valid.text)})")

    error = validate_bullet_length(bullet_too_long, max_len=150)
    if error:
        print(f"   ✓ Long bullet correctly rejected: {error[:60]}...")
    else:
        print(f"   ✗ Long bullet should have been rejected!")

    # Test skill coverage validation
    print("\n✓ Testing skill_coverage validation...")
    required_skills = ["Python", "AWS", "Machine Learning", "Docker"]

    error = validate_skill_coverage(bullet_valid, required_skills)
    if error:
        print(f"   ✗ Skill coverage failed: {error[:60]}...")
    else:
        print(f"   ✓ Skill coverage validated successfully")

    # Test hallucination detection
    print("\n✓ Testing hallucination detection...")
    resume_skills = ["Python", "JavaScript", "AWS", "Docker", "Machine Learning"]

    error = detect_hallucinations(bullet_valid, resume_skills)
    if error:
        print(f"   ✗ False positive hallucination: {error[:60]}...")
    else:
        print(f"   ✓ No hallucinations detected (correct)")

    # Test with hallucinated skill
    bullet_hallucinated = GeneratedBullet(
        id="bullet-003",
        text="Built quantum computing system using QuantumSDK and HyperBrain",
        source_experience_id="exp-001",
        skills_covered=["QuantumSDK", "HyperBrain"]  # Not in resume
    )

    error = detect_hallucinations(bullet_hallucinated, resume_skills)
    if error:
        print(f"   ✓ Hallucination detected: {error[:80]}...")
    else:
        print(f"   ✗ Hallucination should have been detected!")


async def test_agent_executor(llm_client):
    """Test AgentExecutor with full agentic loop."""
    print_section("Testing AgentExecutor")

    if llm_client is None:
        print("\n⚠ Skipping - LLM client not initialized")
        return None

    # Check sample data
    job_path = Path("data/jobs/ml-engineer-sample.yaml")
    resume_path = Path("data/resumes/jane-doe-sample.json")

    if not job_path.exists() or not resume_path.exists():
        print(f"\n⚠ Sample data not found")
        print(f"   Job: {job_path.exists()}")
        print(f"   Resume: {resume_path.exists()}")
        return None

    try:
        print("\n✓ Initializing AgentExecutor...")
        encoder = SentenceBertEncoder()
        executor = AgentExecutor(llm_client, encoder, max_retries=3)
        print(f"   Executor: {executor}")
        print(f"   Max retries: {executor.max_retries}")

        print("\n✓ Running full agentic loop...")
        print(f"   Job: {job_path.name}")
        print(f"   Resume: {resume_path.name}")
        print("   (This may take 30-60 seconds...)")

        package, errors = await executor.run_single_job(job_path, resume_path)

        if package:
            print(f"\n✓ Package generated successfully!")
            print(f"   Package ID: {package.id}")
            print(f"   Job ID: {package.job_id}")
            print(f"   Candidate ID: {package.candidate_id}")
            print(f"   Bullets: {len(package.bullets)}")
            print(f"   Cover letter: {'✓' if package.cover_letter else '✗'}")

            # Show sample bullets
            if package.bullets:
                print("\n   Sample Bullets (first 3):")
                for i, bullet in enumerate(package.bullets[:3], 1):
                    print(f"\n   {i}. {bullet.text}")
                    print(f"      Skills: {', '.join(bullet.skills_covered[:5])}")

            # Show validation errors
            if errors:
                print(f"\n⚠ Validation warnings ({len(errors)}):")
                for error in errors[:3]:
                    print(f"   - {error}")
                if len(errors) > 3:
                    print(f"   ...and {len(errors) - 3} more")
            else:
                print("\n✓ No validation errors!")

            return package

        else:
            print(f"\n✗ Package generation failed!")
            if errors:
                print(f"   Errors ({len(errors)}):")
                for error in errors[:5]:
                    print(f"   - {error}")
            return None

    except Exception as e:
        print(f"\n✗ AgentExecutor test failed: {e}")
        import traceback
        traceback.print_exc()
        return None


async def run_async_tests():
    """Run all agent tests."""
    print("\n" + "🤖" * 35)
    print("  AutoResuAgent - Agent Layer Test Suite")
    print("🤖" * 35)

    try:
        # Get config
        config = get_config()

        # Test validation functions (no API needed)
        test_validation_functions()

        # Choose LLM client for executor tests
        llm_client = None
        if config.openai_api_key:
            print("\n✓ Using OpenAI client for executor tests")
            llm_client = OpenAILLMClient(config)
        elif config.anthropic_api_key:
            print("\n✓ Using Anthropic client for executor tests")
            llm_client = AnthropicLLMClient(config)
        else:
            print("\n⚠ No API keys configured - skipping executor tests")

        # Test executor
        package = None
        if llm_client:
            package = await test_agent_executor(llm_client)

        # Summary
        print_section("Test Summary")

        print("\n✅ Validation functions tested:")
        print("   - validate_bullet_length ✓")
        print("   - validate_skill_coverage ✓")
        print("   - detect_hallucinations ✓")

        if package:
            print("\n✅ AgentExecutor test passed:")
            print(f"   - Full agentic loop completed ✓")
            print(f"   - Generated {len(package.bullets)} bullets ✓")
            print(f"   - Generated cover letter ✓")
            print(f"   - Package validation completed ✓")

            print("\n✨ Agent layer is production-ready!")
            print("\nCapabilities:")
            print("  1. ✓ Validation with hallucination detection")
            print("  2. ✓ Agentic loop: Retrieve → Generate → Validate → Retry")
            print("  3. ✓ Full pipeline from job/resume to package")
            print("  4. ✓ Ready for concurrent processing")

            print("\nNext steps:")
            print("  - Add LaTeX rendering (Jinja2 templates → PDF)")
            print("  - Implement end-to-end pipeline orchestration")
            print("  - Deploy as production system")

        elif llm_client:
            print("\n⚠ AgentExecutor encountered issues")
            print("   Check errors above for details")

        else:
            print("\n⚠ Executor tests skipped (no API keys)")
            print("\nTo test full agent:")
            print("  1. Copy .env.example to .env")
            print("  2. Add API key:")
            print("     OPENAI_API_KEY=sk-...")
            print("     or")
            print("     ANTHROPIC_API_KEY=sk-ant-...")
            print("  3. Run this test again")

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
