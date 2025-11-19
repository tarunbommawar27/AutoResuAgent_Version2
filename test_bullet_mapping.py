"""
Quick test to verify bullet-to-experience mapping logic.
"""
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from models.resume import load_resume_from_json
from models.job_description import load_job_from_yaml
from models.output import GeneratedBullet, FullGeneratedPackage

# Load test data
resume = load_resume_from_json(Path("data/resumes/sample_resume.json"))
job = load_job_from_yaml(Path("data/jobs/sample_job.yaml"))

print("=" * 70)
print("RESUME EXPERIENCES:")
print("=" * 70)
for exp in resume.experiences:
    print(f"  ID: {exp.id}")
    print(f"  Role: {exp.role} at {exp.company}")
    print(f"  Bullets: {len(exp.bullets)}")
    print()

print("=" * 70)
print("CREATING TEST BULLETS:")
print("=" * 70)

# Create test bullets with source_experience_id
test_bullets = [
    GeneratedBullet(
        id="bullet-001",
        text="Built machine learning pipelines using Python and scikit-learn to automate data processing workflows",
        source_experience_id="exp-1",
        skills_covered=["Python", "Machine Learning", "scikit-learn"]
    ),
    GeneratedBullet(
        id="bullet-002",
        text="Developed REST APIs with Flask and integrated Docker containers for microservices architecture",
        source_experience_id="exp-2",
        skills_covered=["Python", "Docker", "REST API"]
    ),
    GeneratedBullet(
        id="bullet-003",
        text="Analyzed customer support tickets using NLP techniques and created SQL dashboards for insights",
        source_experience_id="exp-1",
        skills_covered=["NLP", "SQL", "Python"]
    ),
]

for bullet in test_bullets:
    print(f"  {bullet.id}: source_experience_id={bullet.source_experience_id}")
    print(f"    Text: {bullet.text[:60]}...")
    print()

print("=" * 70)
print("GROUPING BULLETS BY EXPERIENCE:")
print("=" * 70)

# Group bullets by source_experience_id
experience_bullets = {}
for bullet in test_bullets:
    exp_id = bullet.source_experience_id
    if exp_id:
        if exp_id not in experience_bullets:
            experience_bullets[exp_id] = []
        experience_bullets[exp_id].append(bullet)

print(f"Grouped {len(test_bullets)} bullets into {len(experience_bullets)} experience buckets")
print(f"Buckets: {list(experience_bullets.keys())}")
print()

# Match with resume experiences
print("=" * 70)
print("MATCHING WITH RESUME EXPERIENCES:")
print("=" * 70)

experiences_with_bullets = []
for exp in resume.experiences:
    exp_id = exp.id
    tailored_bullets = experience_bullets.get(exp_id, [])

    print(f"\nExperience {exp_id} ({exp.role} at {exp.company}):")
    print(f"  Matched bullets: {len(tailored_bullets)}")

    if tailored_bullets:
        experiences_with_bullets.append({
            "id": exp_id,
            "role": exp.role,
            "company": exp.company,
            "bullets": tailored_bullets
        })
        for bullet in tailored_bullets:
            print(f"    - {bullet.id}: {bullet.text[:50]}...")

print()
print("=" * 70)
print(f"✓ Built {len(experiences_with_bullets)} experiences with generated bullets")
print("=" * 70)

if len(experiences_with_bullets) > 0:
    print("\n✅ SUCCESS: Bullets are being matched to experiences!")
else:
    print("\n❌ FAILURE: No experiences with bullets!")
