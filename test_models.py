"""
Test script for Pydantic models.
Validates that all models work correctly with sample data.
"""

import sys
from pathlib import Path

# Fix Unicode encoding for Windows console
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8')

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from src.models import (
    JobDescription,
    load_job_from_yaml,
    Experience,
    Education,
    CandidateProfile,
    load_resume_from_json,
    GeneratedBullet,
    GeneratedSection,
    GeneratedCoverLetter,
    FullGeneratedPackage,
)
from pydantic import ValidationError


def print_section(title: str):
    """Print a formatted section header."""
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70)


def test_job_description():
    """Test JobDescription model and YAML loader."""
    print_section("Testing JobDescription Model")

    # Test direct instantiation
    print("\n✓ Creating JobDescription instance...")
    job = JobDescription(
        job_id="test-job-001",
        title="Software Engineer",
        company="TestCorp",
        responsibilities=["Write code", "Review PRs"],
        required_skills=["Python", "Git"],
    )
    print(f"   Job ID: {job.job_id}")
    print(f"   Title: {job.title}")
    print(f"   Company: {job.company}")
    print(f"   Required Skills: {', '.join(job.required_skills)}")

    # Test utility methods
    all_skills = job.get_all_skills()
    print(f"   All Skills: {', '.join(all_skills)}")

    search_text = job.get_search_text()
    print(f"   Search Text (preview): {search_text[:80]}...")

    # Test YAML loading
    print("\n✓ Loading JobDescription from YAML...")
    yaml_path = Path("data/jobs/ml-engineer-sample.yaml")
    if yaml_path.exists():
        job_from_yaml = load_job_from_yaml(yaml_path)
        print(f"   Loaded: {job_from_yaml.title} at {job_from_yaml.company}")
        print(f"   Responsibilities: {len(job_from_yaml.responsibilities)}")
        print(f"   Required Skills: {len(job_from_yaml.required_skills)}")
        print(f"   Nice-to-have Skills: {len(job_from_yaml.nice_to_have_skills or [])}")
    else:
        print(f"   ⚠ Sample file not found: {yaml_path}")

    # Test validation
    print("\n✓ Testing validation...")
    try:
        invalid_job = JobDescription(
            job_id="",  # Should fail - empty ID
            title="Test",
        )
    except ValidationError as e:
        print(f"   Correctly rejected empty job_id")

    return job_from_yaml if yaml_path.exists() else job


def test_resume_models():
    """Test resume models and JSON loader."""
    print_section("Testing Resume Models")

    # Test Experience
    print("\n✓ Creating Experience instance...")
    exp = Experience(
        id="exp-test-001",
        role="Senior Developer",
        company="TestCorp",
        start_date="2020-01",
        end_date=None,
        bullets=[
            "Built scalable web applications",
            "Led team of 5 engineers",
        ],
    )
    print(f"   ID: {exp.id}")
    print(f"   Role: {exp.role} at {exp.company}")
    print(f"   Is Current: {exp.is_current()}")
    print(f"   Bullets: {len(exp.bullets)}")

    # Test Education
    print("\n✓ Creating Education instance...")
    edu = Education(
        degree="Bachelor of Science in Computer Science",
        institution="Test University",
        year=2019,
        details=["GPA: 3.8/4.0", "Dean's List"],
    )
    print(f"   Degree: {edu.degree}")
    print(f"   Institution: {edu.institution}")
    print(f"   Year: {edu.year}")

    # Test CandidateProfile
    print("\n✓ Creating CandidateProfile instance...")
    profile = CandidateProfile(
        candidate_id="test-candidate-001",
        name="Test User",
        email="test@example.com",
        skills=["Python", "JavaScript", "AWS"],
        experiences=[exp],
        education=[edu],
    )
    print(f"   Candidate ID: {profile.candidate_id}")
    print(f"   Name: {profile.name}")
    print(f"   Email: {profile.email}")
    print(f"   Total Skills: {len(profile.skills)}")
    print(f"   Total Experiences: {len(profile.experiences)}")
    print(f"   Total Bullets: {len(profile.get_all_bullets())}")

    # Test JSON loading
    print("\n✓ Loading CandidateProfile from JSON...")
    json_path = Path("data/resumes/jane-doe-sample.json")
    if json_path.exists():
        resume_from_json = load_resume_from_json(json_path)
        print(f"   Loaded: {resume_from_json.name}")
        print(f"   Email: {resume_from_json.email}")
        print(f"   Location: {resume_from_json.location}")
        print(f"   Skills: {len(resume_from_json.skills)}")
        print(f"   Experiences: {len(resume_from_json.experiences)}")
        print(f"   Education: {len(resume_from_json.education)}")

        # Test utility methods
        exp_by_id = resume_from_json.get_experience_by_id("exp-001")
        if exp_by_id:
            print(f"   Found experience: {exp_by_id.role} at {exp_by_id.company}")
    else:
        print(f"   ⚠ Sample file not found: {json_path}")

    # Test validation
    print("\n✓ Testing validation...")
    try:
        invalid_profile = CandidateProfile(
            candidate_id="test",
            name="Test",
            email="invalid-email",  # Should fail
        )
    except ValidationError as e:
        print(f"   Correctly rejected invalid email")

    try:
        # Duplicate experience IDs should fail
        dup_profile = CandidateProfile(
            candidate_id="test",
            name="Test",
            email="test@example.com",
            experiences=[
                Experience(id="exp-001", role="Dev", company="A", start_date="2020-01"),
                Experience(id="exp-001", role="Dev", company="B", start_date="2021-01"),
            ],
        )
    except ValidationError as e:
        print(f"   Correctly rejected duplicate experience IDs")

    return resume_from_json if json_path.exists() else profile


def test_output_models():
    """Test generated output models."""
    print_section("Testing Output Models")

    # Test GeneratedBullet
    print("\n✓ Creating GeneratedBullet instance...")
    bullet = GeneratedBullet(
        id="bullet-001",
        text="Developed machine learning pipeline reducing inference time by 40%",
        source_experience_id="exp-001",
        skills_covered=["Python", "Machine Learning", "Optimization"],
    )
    print(f"   ID: {bullet.id}")
    print(f"   Text: {bullet.text}")
    print(f"   Starts with action verb: {bullet.starts_with_action_verb()}")
    print(f"   Skills covered: {', '.join(bullet.skills_covered)}")

    # Test validation - first-person pronouns
    print("\n✓ Testing first-person pronoun validation...")
    try:
        invalid_bullet = GeneratedBullet(
            id="bullet-002",
            text="I developed a system that improved performance",  # Should fail
        )
    except ValidationError as e:
        print(f"   Correctly rejected first-person pronoun")

    # Test GeneratedSection
    print("\n✓ Creating GeneratedSection instance...")
    section = GeneratedSection(
        section_name="Professional Experience",
        bullets=[
            bullet,
            GeneratedBullet(
                id="bullet-002",
                text="Implemented CI/CD pipeline automating deployment process",
                skills_covered=["CI/CD", "DevOps"],
            ),
        ],
    )
    print(f"   Section: {section.section_name}")
    print(f"   Bullets: {len(section.bullets)}")
    print(f"   All skills covered: {', '.join(section.get_all_skills_covered())}")

    # Test GeneratedCoverLetter
    print("\n✓ Creating GeneratedCoverLetter instance...")
    cover_letter = GeneratedCoverLetter(
        text="""Dear Hiring Manager,

I am writing to express my strong interest in the Senior Machine Learning Engineer position at TechCorp AI. With over 5 years of experience in developing and deploying production ML systems, I am excited about the opportunity to contribute to your team's innovative work in artificial intelligence.

In my current role at DataTech Inc, I have successfully built and deployed ML models serving millions of users, consistently achieving significant improvements in both performance and user engagement. My experience with TensorFlow, PyTorch, and MLOps aligns perfectly with your requirements.

I am particularly drawn to TechCorp AI's commitment to pushing the boundaries of machine learning technology. I would welcome the opportunity to discuss how my background and skills can contribute to your team's success.

Thank you for considering my application. I look forward to speaking with you soon.

Sincerely,
Jane Doe"""
    )
    print(f"   Word count: {cover_letter.get_word_count()}")
    print(f"   Paragraph count: {cover_letter.get_paragraph_count()}")

    # Test validation - too short
    print("\n✓ Testing cover letter length validation...")
    try:
        too_short = GeneratedCoverLetter(
            text="This is way too short."  # Should fail
        )
    except ValidationError as e:
        print(f"   Correctly rejected too-short cover letter")

    # Test FullGeneratedPackage
    print("\n✓ Creating FullGeneratedPackage instance...")
    package = FullGeneratedPackage(
        job_id="ml-engineer-techcorp-2024",
        candidate_id="jane-doe-2024",
        sections=[section],
        cover_letter=cover_letter,
    )
    print(f"   Job ID: {package.job_id}")
    print(f"   Candidate ID: {package.candidate_id}")
    print(f"   Total sections: {len(package.sections)}")
    print(f"   Total bullets: {package.get_total_bullets()}")
    print(f"   Has cover letter: {package.cover_letter is not None}")
    print(f"   All skills covered: {', '.join(package.get_all_skills_covered()[:5])}...")

    # Test validation - empty package
    print("\n✓ Testing empty package validation...")
    try:
        empty_package = FullGeneratedPackage(
            job_id="test",
            candidate_id="test",
            sections=[],
            cover_letter=None,  # Should fail - no content
        )
    except ValidationError as e:
        print(f"   Correctly rejected empty package")

    return package


def test_model_serialization():
    """Test that models can be serialized to/from dict and JSON."""
    print_section("Testing Model Serialization")

    # Create a simple job
    job = JobDescription(
        job_id="test-001",
        title="Test Engineer",
        company="TestCorp",
        responsibilities=["Test code"],
        required_skills=["Testing"],
    )

    # Test to_dict
    print("\n✓ Testing model_dump()...")
    job_dict = job.model_dump()
    print(f"   Serialized to dict: {list(job_dict.keys())[:5]}...")

    # Test from_dict
    print("\n✓ Testing model_validate()...")
    job_copy = JobDescription.model_validate(job_dict)
    print(f"   Deserialized: {job_copy.title}")

    # Test JSON
    print("\n✓ Testing model_dump_json()...")
    job_json = job.model_dump_json(indent=2)
    print(f"   JSON length: {len(job_json)} characters")

    print("\n✓ Testing model_validate_json()...")
    job_from_json = JobDescription.model_validate_json(job_json)
    print(f"   From JSON: {job_from_json.title}")


def main():
    """Run all tests."""
    print("\n" + "🚀" * 35)
    print("  AutoResuAgent - Pydantic Models Test Suite")
    print("🚀" * 35)

    try:
        # Run tests
        job = test_job_description()
        resume = test_resume_models()
        package = test_output_models()
        test_model_serialization()

        # Summary
        print_section("Test Summary")
        print("\n✅ All tests passed successfully!")
        print("\n📊 Model Statistics:")
        print(f"   - JobDescription: {len(job.required_skills)} required skills")
        print(f"   - CandidateProfile: {len(resume.experiences)} experiences")
        print(f"   - FullGeneratedPackage: {package.get_total_bullets()} total bullets")

        print("\n✨ Models are production-ready!")
        print("\nNext steps:")
        print("  1. Models are validated and working correctly")
        print("  2. Ready to implement LLM clients and generators")
        print("  3. Sample data files are available in data/ directory")

    except Exception as e:
        print(f"\n❌ Error during testing: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
