"""
Dataset Evaluation Runner
Runs baseline vs full comparison on a dataset of job-resume pairs.
"""

import json
import logging
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..agent import AgentExecutor

from .metrics import compute_basic_metrics, compare_runs_metrics

logger = logging.getLogger(__name__)


async def run_dataset_eval(
    dataset_path: Path,
    executor: "AgentExecutor",
    output_dir: Path | None = None
) -> None:
    """
    Run baseline vs full evaluation on a dataset of job-resume pairs.

    This function:
    1. Loads the dataset from JSON file
    2. For each pair, runs both baseline and full modes
    3. Computes metrics and comparison deltas
    4. Saves results to JSONL file
    5. Prints summary statistics

    Args:
        dataset_path: Path to dataset JSON file (list of {id, job_path, resume_path})
        executor: AgentExecutor instance configured with LLM and encoder
        output_dir: Optional output directory (defaults to outputs/eval)

    Output Format:
        Each JSONL line contains:
        {
            "pair_id": "pair-001",
            "job_path": "...",
            "resume_path": "...",
            "baseline": {
                "metrics": {...},
                "errors": [...]
            },
            "full": {
                "metrics": {...},
                "errors": [...]
            },
            "comparison": {
                "delta_required_skill_coverage": 0.25,
                "delta_num_bullets": 2,
                ...
            }
        }

    Example:
        >>> from src.agent import AgentExecutor
        >>> from src.llm import OpenAIClient
        >>> from src.embeddings import SentenceBertEncoder
        >>>
        >>> llm = OpenAIClient()
        >>> encoder = SentenceBertEncoder()
        >>> executor = AgentExecutor(llm, encoder)
        >>>
        >>> await run_dataset_eval(
        ...     Path("data/eval/job_resume_pairs.json"),
        ...     executor
        ... )
    """
    logger.info(f"Starting dataset evaluation from {dataset_path}")

    # Load dataset
    try:
        with open(dataset_path, 'r', encoding='utf-8') as f:
            dataset = json.load(f)
    except Exception as e:
        logger.error(f"Failed to load dataset: {e}")
        return

    if not isinstance(dataset, list):
        logger.error("Dataset must be a JSON array")
        return

    logger.info(f"Loaded {len(dataset)} job-resume pairs")

    # Prepare output directory
    if output_dir is None:
        output_dir = Path("outputs/eval")
    output_dir.mkdir(parents=True, exist_ok=True)

    output_file = output_dir / "baseline_vs_full.jsonl"
    logger.info(f"Results will be saved to {output_file}")

    # Track statistics
    total_pairs = len(dataset)
    baseline_success = 0
    full_success = 0
    results = []

    # Process each pair
    for i, pair in enumerate(dataset, 1):
        pair_id = pair.get("id", f"pair-{i:03d}")
        job_path = Path(pair.get("job_path", ""))
        resume_path = Path(pair.get("resume_path", ""))

        logger.info(f"\n{'='*60}")
        logger.info(f"Processing pair {i}/{total_pairs}: {pair_id}")
        logger.info(f"  Job: {job_path}")
        logger.info(f"  Resume: {resume_path}")
        logger.info(f"{'='*60}")

        # Validate paths
        if not job_path.exists():
            logger.error(f"Job file not found: {job_path}")
            continue
        if not resume_path.exists():
            logger.error(f"Resume file not found: {resume_path}")
            continue

        result = {
            "pair_id": pair_id,
            "job_path": str(job_path),
            "resume_path": str(resume_path),
            "baseline": {},
            "full": {},
            "comparison": {}
        }

        # Run BASELINE mode
        logger.info(f"\n[{pair_id}] Running BASELINE mode...")
        try:
            baseline_pkg, baseline_errors, baseline_metrics = await executor.run_single_job(
                job_path,
                resume_path,
                mode="baseline"
            )

            if baseline_pkg:
                # Load job and resume for metrics computation
                from ..models import load_job_from_yaml, load_resume_from_json
                job = load_job_from_yaml(job_path)
                resume = load_resume_from_json(resume_path)

                # Compute basic metrics
                basic_metrics = compute_basic_metrics(baseline_pkg, job, resume)

                result["baseline"]["metrics"] = basic_metrics
                result["baseline"]["errors"] = baseline_errors if baseline_errors else []

                if not baseline_errors:
                    baseline_success += 1
                    logger.info(f"[{pair_id}] BASELINE succeeded")
                else:
                    logger.warning(f"[{pair_id}] BASELINE completed with {len(baseline_errors)} errors")
            else:
                logger.error(f"[{pair_id}] BASELINE failed to generate package")
                result["baseline"]["metrics"] = {}
                result["baseline"]["errors"] = baseline_errors if baseline_errors else ["Generation failed"]

        except Exception as e:
            logger.error(f"[{pair_id}] BASELINE exception: {e}")
            import traceback
            traceback.print_exc()
            result["baseline"]["metrics"] = {}
            result["baseline"]["errors"] = [str(e)]

        # Run FULL mode
        logger.info(f"\n[{pair_id}] Running FULL mode...")
        try:
            full_pkg, full_errors, full_metrics = await executor.run_single_job(
                job_path,
                resume_path,
                mode="full"
            )

            if full_pkg:
                # Load job and resume for metrics computation
                from ..models import load_job_from_yaml, load_resume_from_json
                job = load_job_from_yaml(job_path)
                resume = load_resume_from_json(resume_path)

                # Compute basic metrics
                basic_metrics = compute_basic_metrics(full_pkg, job, resume)

                result["full"]["metrics"] = basic_metrics
                result["full"]["errors"] = full_errors if full_errors else []

                if not full_errors:
                    full_success += 1
                    logger.info(f"[{pair_id}] FULL succeeded")
                else:
                    logger.warning(f"[{pair_id}] FULL completed with {len(full_errors)} errors")
            else:
                logger.error(f"[{pair_id}] FULL failed to generate package")
                result["full"]["metrics"] = {}
                result["full"]["errors"] = full_errors if full_errors else ["Generation failed"]

        except Exception as e:
            logger.error(f"[{pair_id}] FULL exception: {e}")
            import traceback
            traceback.print_exc()
            result["full"]["metrics"] = {}
            result["full"]["errors"] = [str(e)]

        # Compute comparison
        if result["full"]["metrics"] and result["baseline"]["metrics"]:
            try:
                comparison = compare_runs_metrics(
                    result["full"]["metrics"],
                    result["baseline"]["metrics"]
                )
                result["comparison"] = comparison

                logger.info(f"\n[{pair_id}] Comparison:")
                logger.info(f"  Δ Required Skill Coverage: {comparison.get('delta_required_skill_coverage', 0):.2%}")
                logger.info(f"  Δ Num Bullets: {comparison.get('delta_num_bullets', 0):+d}")
                logger.info(f"  Δ Avg Bullet Length: {comparison.get('delta_avg_bullet_length_chars', 0):+.1f} chars")

            except Exception as e:
                logger.error(f"[{pair_id}] Comparison failed: {e}")
                result["comparison"] = {}

        # Save result
        results.append(result)

        # Write to JSONL incrementally
        try:
            with open(output_file, 'a', encoding='utf-8') as f:
                f.write(json.dumps(result) + '\n')
            logger.info(f"[{pair_id}] Result saved to {output_file}")
        except Exception as e:
            logger.error(f"[{pair_id}] Failed to save result: {e}")

    # Print final summary
    logger.info(f"\n{'='*60}")
    logger.info("EVALUATION COMPLETE")
    logger.info(f"{'='*60}")
    logger.info(f"Evaluated {total_pairs} pairs:")
    logger.info(f"  Baseline success: {baseline_success}/{total_pairs}")
    logger.info(f"  Full success: {full_success}/{total_pairs}")
    logger.info(f"Results saved to {output_file}")
    logger.info(f"{'='*60}\n")

    # Print aggregate statistics if we have successful comparisons
    successful_comparisons = [r for r in results if r["comparison"]]
    if successful_comparisons:
        logger.info("\nAggregate Comparison Statistics:")

        avg_skill_delta = sum(
            r["comparison"].get("delta_required_skill_coverage", 0)
            for r in successful_comparisons
        ) / len(successful_comparisons)

        avg_bullet_delta = sum(
            r["comparison"].get("delta_num_bullets", 0)
            for r in successful_comparisons
        ) / len(successful_comparisons)

        avg_length_delta = sum(
            r["comparison"].get("delta_avg_bullet_length_chars", 0)
            for r in successful_comparisons
        ) / len(successful_comparisons)

        logger.info(f"  Avg Δ Required Skill Coverage: {avg_skill_delta:.2%}")
        logger.info(f"  Avg Δ Num Bullets: {avg_bullet_delta:+.1f}")
        logger.info(f"  Avg Δ Avg Bullet Length: {avg_length_delta:+.1f} chars")
        logger.info("")
