"""
System Comparison Framework
Compares three systems: Original Resume, LLM Baseline, and AutoResuAgent.

This module provides comprehensive evaluation of different resume generation
approaches to demonstrate the value of the full AutoResuAgent system.
"""

import logging
import asyncio
from pathlib import Path
from typing import TYPE_CHECKING
import json

if TYPE_CHECKING:
    from ..models import JobDescription, CandidateProfile, FullGeneratedPackage, GeneratedBullet
    from ..llm import BaseLLMClient
    from ..embeddings import SentenceBertEncoder

logger = logging.getLogger(__name__)


def compute_system_metrics(
    bullets: list["GeneratedBullet"],
    job: "JobDescription",
    resume: "CandidateProfile",
    cover_letter_text: str | None = None
) -> dict:
    """
    Compute comprehensive metrics for a system's output.

    Args:
        bullets: Generated bullets
        job: Target job description
        resume: Candidate's resume
        cover_letter_text: Optional cover letter text

    Returns:
        Dictionary with metrics:
        - skill_coverage_ratio: Required skills covered (0.0-1.0)
        - hallucination_ratio: Skills not in resume (0.0-1.0)
        - avg_bullet_length: Average characters per bullet
        - num_bullets: Total bullets generated
    """
    metrics = {}

    # Basic counts
    metrics["num_bullets"] = len(bullets)

    if not bullets:
        # No bullets - return zero metrics
        return {
            "num_bullets": 0,
            "skill_coverage_ratio": 0.0,
            "hallucination_ratio": 0.0,
            "avg_bullet_length": 0.0,
            "resume_skill_usage_ratio": 0.0
        }

    # Bullet length metrics
    bullet_lengths = [len(b.text) for b in bullets]
    metrics["avg_bullet_length"] = sum(bullet_lengths) / len(bullet_lengths)

    # Collect all skills mentioned in bullets
    bullet_skills = set()
    for bullet in bullets:
        if hasattr(bullet, 'skills_covered') and bullet.skills_covered:
            bullet_skills.update(s.lower() for s in bullet.skills_covered)

    # Skill coverage (what % of required skills are covered)
    required_skills = job.required_skills if job.required_skills else []
    if required_skills:
        required_skills_lower = set(s.lower() for s in required_skills)
        covered = bullet_skills & required_skills_lower
        metrics["skill_coverage_ratio"] = len(covered) / len(required_skills)
    else:
        metrics["skill_coverage_ratio"] = 1.0  # No requirements means 100% coverage

    # Hallucination detection (skills in bullets but not in resume)
    resume_skills = resume.skills if resume.skills else []
    if resume_skills and bullet_skills:
        resume_skills_lower = set(s.lower() for s in resume_skills)
        hallucinated = bullet_skills - resume_skills_lower
        metrics["hallucination_ratio"] = len(hallucinated) / len(bullet_skills)
    else:
        metrics["hallucination_ratio"] = 0.0

    # Resume skill usage (what % of resume skills are used)
    if resume_skills:
        resume_skills_lower = set(s.lower() for s in resume_skills)
        used = bullet_skills & resume_skills_lower
        metrics["resume_skill_usage_ratio"] = len(used) / len(resume_skills)
    else:
        metrics["resume_skill_usage_ratio"] = 0.0

    return metrics


async def run_system_a(
    job: "JobDescription",
    resume: "CandidateProfile"
) -> tuple[list["GeneratedBullet"], str]:
    """
    System A: Original Resume (no LLM).

    Simply uses the resume's existing bullets as-is.

    Args:
        job: Target job description
        resume: Candidate's resume

    Returns:
        Tuple of (bullets, system_name)
    """
    from ..models import GeneratedBullet

    logger.info("Running System A: Original Resume")

    bullets = []
    bullet_id = 1

    # Extract all bullets from resume experiences
    for exp in resume.experiences:
        for bullet_text in exp.bullets:
            bullet = GeneratedBullet(
                id=f"original-{bullet_id:03d}",
                text=bullet_text,
                source_experience_id=exp.id,
                skills_covered=[]  # Original bullets don't tag skills
            )
            bullets.append(bullet)
            bullet_id += 1

    logger.info(f"System A: Using {len(bullets)} original bullets")
    return bullets, "Original Resume"


async def run_system_b(
    job: "JobDescription",
    resume: "CandidateProfile",
    llm: "BaseLLMClient"
) -> tuple[list["GeneratedBullet"], str]:
    """
    System B: LLM Baseline (one-shot, no retrieval).

    Simple one-shot generation:
    - No SentenceBERT
    - No FAISS retrieval
    - No validation or retry loop

    Args:
        job: Target job description
        resume: Candidate's resume
        llm: LLM client

    Returns:
        Tuple of (bullets, system_name)
    """
    from ..generators.baseline_generator import generate_bullets_baseline

    logger.info("Running System B: LLM Baseline")

    bullets = await generate_bullets_baseline(job, resume, llm)

    logger.info(f"System B: Generated {len(bullets)} baseline bullets")
    return bullets, "LLM Baseline"


async def run_system_c(
    job: "JobDescription",
    resume: "CandidateProfile",
    llm: "BaseLLMClient",
    encoder: "SentenceBertEncoder"
) -> tuple[list["GeneratedBullet"], str]:
    """
    System C: AutoResuAgent (full system).

    Complete pipeline:
    - SentenceBERT embeddings
    - FAISS retrieval
    - Validation
    - Retry loop
    - Hallucination detection

    Args:
        job: Target job description
        resume: Candidate's resume
        llm: LLM client
        encoder: SentenceBERT encoder

    Returns:
        Tuple of (bullets, system_name)
    """
    from ..agent import AgentExecutor
    from ..embeddings import ResumeFaissIndex, retrieve_relevant_experiences
    from ..generators import generate_bullets_for_job

    logger.info("Running System C: AutoResuAgent")

    # Build FAISS index
    index = ResumeFaissIndex(encoder)
    index.build_from_experiences(resume.experiences)

    # Retrieve relevant experiences
    retrieved = retrieve_relevant_experiences(job, resume, encoder, index, top_k=5)

    # Generate with full system (includes validation and retry)
    executor = AgentExecutor(llm, encoder, max_retries=3)
    bullets = await executor._generate_bullets_with_retry(job, resume, retrieved)

    if not bullets:
        logger.warning("System C: Failed to generate bullets, returning empty list")
        bullets = []

    logger.info(f"System C: Generated {len(bullets)} bullets with full pipeline")
    return bullets, "AutoResuAgent"


def compute_alignment_score(
    bullets: list["GeneratedBullet"],
    job: "JobDescription",
    encoder: "SentenceBertEncoder"
) -> float:
    """
    Compute semantic alignment between bullets and job description.

    Uses cosine similarity between bullet embeddings and job embedding.

    Args:
        bullets: Generated bullets
        job: Target job description
        encoder: SentenceBERT encoder

    Returns:
        Average alignment score (0.0-1.0)
    """
    if not bullets:
        return 0.0

    # Get job embedding
    job_text = job.get_search_text()
    job_embedding = encoder.encode([job_text])[0]

    # Get bullet embeddings
    bullet_texts = [b.text for b in bullets]
    bullet_embeddings = encoder.encode(bullet_texts)

    # Compute cosine similarities
    from numpy import dot
    from numpy.linalg import norm

    similarities = []
    for bullet_emb in bullet_embeddings:
        similarity = dot(job_embedding, bullet_emb) / (norm(job_embedding) * norm(bullet_emb))
        similarities.append(float(similarity))

    # Return average similarity
    return sum(similarities) / len(similarities) if similarities else 0.0


def compute_gold_similarity(
    bullets: list["GeneratedBullet"],
    gold_bullets: list[str],
    encoder: "SentenceBertEncoder"
) -> float:
    """
    Compute similarity to gold-standard bullets (if available).

    Args:
        bullets: Generated bullets
        gold_bullets: Gold-standard bullets
        encoder: SentenceBERT encoder

    Returns:
        Average similarity score (0.0-1.0)
    """
    if not bullets or not gold_bullets:
        return 0.0

    # Get embeddings
    bullet_texts = [b.text for b in bullets]
    bullet_embeddings = encoder.encode(bullet_texts)
    gold_embeddings = encoder.encode(gold_bullets)

    # Compute pairwise similarities and take max for each generated bullet
    from numpy import dot
    from numpy.linalg import norm

    similarities = []
    for bullet_emb in bullet_embeddings:
        # Find best match in gold set
        best_sim = 0.0
        for gold_emb in gold_embeddings:
            sim = dot(bullet_emb, gold_emb) / (norm(bullet_emb) * norm(gold_emb))
            best_sim = max(best_sim, float(sim))
        similarities.append(best_sim)

    return sum(similarities) / len(similarities) if similarities else 0.0


async def compare_systems(
    job: "JobDescription",
    resume: "CandidateProfile",
    llm: "BaseLLMClient",
    encoder: "SentenceBertEncoder",
    gold_bullets: list[str] | None = None
) -> dict:
    """
    Compare all three systems and compute comprehensive metrics.

    Args:
        job: Target job description
        resume: Candidate's resume
        llm: LLM client
        encoder: SentenceBERT encoder
        gold_bullets: Optional gold-standard bullets for comparison

    Returns:
        Dictionary with results for each system:
        {
            "system_a": {
                "name": "Original Resume",
                "metrics": {...},
                "bullets": [...]
            },
            "system_b": {...},
            "system_c": {...}
        }
    """
    logger.info("Starting system comparison")
    logger.info(f"Job: {job.title} at {job.company}")
    logger.info(f"Candidate: {resume.name}")

    results = {}

    # Run all systems
    logger.info("=" * 60)
    bullets_a, name_a = await run_system_a(job, resume)
    metrics_a = compute_system_metrics(bullets_a, job, resume)
    metrics_a["alignment_score"] = compute_alignment_score(bullets_a, job, encoder)
    if gold_bullets:
        metrics_a["gold_similarity"] = compute_gold_similarity(bullets_a, gold_bullets, encoder)

    results["system_a"] = {
        "name": name_a,
        "metrics": metrics_a,
        "bullets": [{"id": b.id, "text": b.text} for b in bullets_a[:10]]  # Store first 10
    }

    logger.info("=" * 60)
    bullets_b, name_b = await run_system_b(job, resume, llm)
    metrics_b = compute_system_metrics(bullets_b, job, resume)
    metrics_b["alignment_score"] = compute_alignment_score(bullets_b, job, encoder)
    if gold_bullets:
        metrics_b["gold_similarity"] = compute_gold_similarity(bullets_b, gold_bullets, encoder)

    results["system_b"] = {
        "name": name_b,
        "metrics": metrics_b,
        "bullets": [{"id": b.id, "text": b.text} for b in bullets_b[:10]]
    }

    logger.info("=" * 60)
    bullets_c, name_c = await run_system_c(job, resume, llm, encoder)
    metrics_c = compute_system_metrics(bullets_c, job, resume)
    metrics_c["alignment_score"] = compute_alignment_score(bullets_c, job, encoder)
    if gold_bullets:
        metrics_c["gold_similarity"] = compute_gold_similarity(bullets_c, gold_bullets, encoder)

    results["system_c"] = {
        "name": name_c,
        "metrics": metrics_c,
        "bullets": [{"id": b.id, "text": b.text} for b in bullets_c[:10]]
    }

    logger.info("=" * 60)
    logger.info("Comparison complete")

    return results


def print_comparison_table(results: dict):
    """
    Print comparison results in a formatted table.

    Args:
        results: Results dictionary from compare_systems()
    """
    print("\n" + "=" * 90)
    print("SYSTEM COMPARISON RESULTS")
    print("=" * 90)

    # Print header
    has_gold = "gold_similarity" in results["system_a"]["metrics"]
    if has_gold:
        print(f"\n{'SYSTEM':<20} {'COVERAGE':<12} {'HALLUC.':<12} {'ALIGNMENT':<12} {'GOLD_SIM':<12}")
    else:
        print(f"\n{'SYSTEM':<20} {'COVERAGE':<12} {'HALLUC.':<12} {'ALIGNMENT':<12}")
    print("-" * 90)

    # Print each system
    for system_key in ["system_a", "system_b", "system_c"]:
        system_data = results[system_key]
        name = system_data["name"]
        metrics = system_data["metrics"]

        coverage = metrics.get("skill_coverage_ratio", 0.0)
        halluc = metrics.get("hallucination_ratio", 0.0)
        alignment = metrics.get("alignment_score", 0.0)

        if has_gold:
            gold_sim = metrics.get("gold_similarity", 0.0)
            print(f"{name:<20} {coverage:<12.2f} {halluc:<12.2f} {alignment:<12.2f} {gold_sim:<12.2f}")
        else:
            print(f"{name:<20} {coverage:<12.2f} {halluc:<12.2f} {alignment:<12.2f}")

    print("-" * 90)

    # Print summary
    print("\nMetric Definitions:")
    print("  COVERAGE:   % of required job skills covered in bullets")
    print("  HALLUC.:    % of mentioned skills not found in resume (lower is better)")
    print("  ALIGNMENT:  Semantic similarity to job description (0.0-1.0)")
    if has_gold:
        print("  GOLD_SIM:   Similarity to gold-standard bullets (0.0-1.0)")

    print("\n" + "=" * 90)


def save_comparison_results(results: dict, output_path: Path):
    """
    Save comparison results to JSON file.

    Args:
        results: Results dictionary from compare_systems()
        output_path: Path to save JSON file
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    logger.info(f"Comparison results saved to: {output_path}")
