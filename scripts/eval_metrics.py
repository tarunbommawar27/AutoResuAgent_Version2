#!/usr/bin/env python3
"""
Evaluation metrics script for AutoResuAgent.

Computes accuracy, precision, recall, F1, and other metrics comparing
baseline vs full (semantic retrieval) modes.

Usage:
    python scripts/eval_metrics.py --input outputs/eval/baseline_vs_full.jsonl --outdir outputs/eval/metrics --verbose
"""

import json
import logging
import argparse
from pathlib import Path
from typing import List, Dict, Any, Tuple, Optional
from collections import defaultdict
import sys

# Add helpful import error handling
try:
    import numpy as np
    import pandas as pd
    import matplotlib.pyplot as plt
    from sentence_transformers import SentenceTransformer
    from sklearn.metrics.pairwise import cosine_similarity
except ImportError as e:
    print(f"Error: Missing required package. Please install dependencies:")
    print(f"  pip install sentence-transformers scikit-learn pandas matplotlib numpy")
    print(f"\nOriginal error: {e}")
    sys.exit(1)


def setup_logging(verbose: bool = False) -> None:
    """Configure logging with appropriate level."""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        format='%(asctime)s - %(levelname)s - %(message)s',
        level=level
    )


def load_jsonl(filepath: Path) -> List[Dict[str, Any]]:
    """
    Load JSONL file and return list of records.

    Args:
        filepath: Path to JSONL file

    Returns:
        List of dictionaries, one per line

    Raises:
        FileNotFoundError: If file doesn't exist
        json.JSONDecodeError: If file contains invalid JSON
    """
    records = []
    with open(filepath, 'r', encoding='utf-8') as f:
        for line_num, line in enumerate(f, start=1):
            line = line.strip()
            if not line:
                continue
            try:
                record = json.loads(line)
                records.append(record)
            except json.JSONDecodeError as e:
                logging.warning(f"Skipping invalid JSON at line {line_num}: {e}")
                continue
    return records


def extract_bullets(mode_data: Dict[str, Any]) -> List[str]:
    """
    Extract bullet texts from baseline or full mode data.

    Handles both:
    - mode_data['package']['bullets']
    - mode_data['bullets']

    Bullets can be:
    - List of dicts with 'text' key
    - List of strings

    Args:
        mode_data: Dictionary containing bullet data

    Returns:
        List of bullet text strings
    """
    bullets = []

    # Try to find bullets in different locations
    bullet_data = None
    if 'package' in mode_data and isinstance(mode_data['package'], dict):
        if 'bullets' in mode_data['package']:
            bullet_data = mode_data['package']['bullets']
    elif 'bullets' in mode_data:
        bullet_data = mode_data['bullets']

    if bullet_data is None:
        return []

    # Extract text from bullet data
    for item in bullet_data:
        if isinstance(item, dict):
            # Bullet is a dict with 'text' key
            if 'text' in item:
                bullets.append(item['text'])
            elif 'content' in item:
                bullets.append(item['content'])
        elif isinstance(item, str):
            # Bullet is already a string
            bullets.append(item)

    return bullets


def compute_semantic_matching(
    baseline_bullets: List[str],
    full_bullets: List[str],
    model: Optional[SentenceTransformer],
    threshold: float = 0.7
) -> Dict[str, float]:
    """
    Compute semantic matching metrics between baseline and full bullets.

    Uses greedy 1:1 matching with similarity threshold.

    Args:
        baseline_bullets: List of baseline bullet texts
        full_bullets: List of full mode bullet texts
        model: SentenceTransformer model (or None to skip)
        threshold: Minimum cosine similarity for a match (0.0-1.0)

    Returns:
        Dict with keys: precision, recall, f1, tp, fp, fn
    """
    # Handle edge cases - check empty lists BEFORE model check
    # This ensures correct metrics even when model is None

    if len(baseline_bullets) == 0 and len(full_bullets) == 0:
        # Both empty = perfect agreement on "nothing"
        return {
            'precision': 1.0,
            'recall': 1.0,
            'f1': 1.0,
            'tp': 0,
            'fp': 0,
            'fn': 0
        }

    if len(baseline_bullets) == 0:
        return {
            'precision': 0.0,
            'recall': 1.0,  # No baseline to recall
            'f1': 0.0,
            'tp': 0,
            'fp': len(full_bullets),
            'fn': 0
        }

    if len(full_bullets) == 0:
        return {
            'precision': 1.0,  # No false positives
            'recall': 0.0,
            'f1': 0.0,
            'tp': 0,
            'fp': 0,
            'fn': len(baseline_bullets)
        }

    # Now check if model is available (needed for non-empty bullets)
    if model is None:
        return {
            'precision': 0.0,
            'recall': 0.0,
            'f1': 0.0,
            'tp': 0,
            'fp': 0,
            'fn': 0
        }

    try:
        # Encode bullets
        baseline_embeddings = model.encode(baseline_bullets, convert_to_numpy=True)
        full_embeddings = model.encode(full_bullets, convert_to_numpy=True)

        # Compute cosine similarity matrix: [num_baseline x num_full]
        sim_matrix = cosine_similarity(baseline_embeddings, full_embeddings)

        # Greedy 1:1 matching
        matched_baseline = set()
        matched_full = set()

        # For each baseline bullet, find best matching full bullet
        for baseline_idx in range(len(baseline_bullets)):
            best_full_idx = np.argmax(sim_matrix[baseline_idx])
            best_similarity = sim_matrix[baseline_idx, best_full_idx]

            # Only match if similarity >= threshold and full bullet not already matched
            if best_similarity >= threshold and best_full_idx not in matched_full:
                matched_baseline.add(baseline_idx)
                matched_full.add(best_full_idx)

        # Count metrics
        tp = len(matched_baseline)  # Successfully matched baseline bullets
        fp = len(full_bullets) - len(matched_full)  # Unmatched full bullets
        fn = len(baseline_bullets) - len(matched_baseline)  # Unmatched baseline bullets

        # Compute precision, recall, F1
        precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
        recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
        f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0.0

        return {
            'precision': precision,
            'recall': recall,
            'f1': f1,
            'tp': tp,
            'fp': fp,
            'fn': fn
        }

    except Exception as e:
        logging.error(f"Error in semantic matching: {e}")
        return {
            'precision': 0.0,
            'recall': 0.0,
            'f1': 0.0,
            'tp': 0,
            'fp': 0,
            'fn': 0
        }


def compute_per_pair_metrics(
    record: Dict[str, Any],
    model: Optional[SentenceTransformer],
    threshold: float
) -> Dict[str, Any]:
    """
    Compute all metrics for a single job-resume pair.

    Args:
        record: Dictionary containing baseline and full mode results
        model: SentenceTransformer model for semantic matching
        threshold: Similarity threshold for matching

    Returns:
        Dictionary with all per-pair metrics
    """
    pair_id = record.get('pair_id', 'unknown')

    # Extract baseline metrics
    baseline = record.get('baseline', {})
    baseline_metrics = baseline.get('metrics', {})
    baseline_errors = baseline.get('errors', [])

    # Extract full metrics
    full = record.get('full', {})
    full_metrics = full.get('metrics', {})
    full_errors = full.get('errors', [])

    # Extract bullets
    baseline_bullets = extract_bullets(baseline)
    full_bullets = extract_bullets(full)

    # Compute semantic matching
    semantic_metrics = compute_semantic_matching(
        baseline_bullets,
        full_bullets,
        model,
        threshold
    )

    # Build metrics dictionary
    metrics = {
        'pair_id': pair_id,
        'baseline_success': len(baseline_errors) == 0,
        'full_success': len(full_errors) == 0,
        'baseline_has_cover_letter': baseline_metrics.get('has_cover_letter', False),
        'full_has_cover_letter': full_metrics.get('has_cover_letter', False),
        'baseline_num_bullets': baseline_metrics.get('num_bullets', 0),
        'full_num_bullets': full_metrics.get('num_bullets', 0),
        'baseline_required_coverage': baseline_metrics.get('required_skill_coverage', 0.0),
        'full_required_coverage': full_metrics.get('required_skill_coverage', 0.0),
        'baseline_nice_coverage': baseline_metrics.get('nice_to_have_skill_coverage', 0.0),
        'full_nice_coverage': full_metrics.get('nice_to_have_skill_coverage', 0.0),
        'baseline_avg_bullet_length': baseline_metrics.get('avg_bullet_length_chars', 0.0),
        'full_avg_bullet_length': full_metrics.get('avg_bullet_length_chars', 0.0),
        'delta_num_bullets': full_metrics.get('num_bullets', 0) - baseline_metrics.get('num_bullets', 0),
        'delta_required_coverage': round(full_metrics.get('required_skill_coverage', 0.0) - baseline_metrics.get('required_skill_coverage', 0.0), 10),
        'delta_nice_coverage': round(full_metrics.get('nice_to_have_skill_coverage', 0.0) - baseline_metrics.get('nice_to_have_skill_coverage', 0.0), 10),
        'semantic_precision': semantic_metrics['precision'],
        'semantic_recall': semantic_metrics['recall'],
        'semantic_f1': semantic_metrics['f1'],
        'semantic_tp': semantic_metrics['tp'],
        'semantic_fp': semantic_metrics['fp'],
        'semantic_fn': semantic_metrics['fn']
    }

    return metrics


def compute_aggregate_metrics(per_pair_df: pd.DataFrame) -> pd.DataFrame:
    """
    Compute aggregate statistics across all pairs.

    Args:
        per_pair_df: DataFrame with per-pair metrics

    Returns:
        DataFrame with aggregate statistics
    """
    # Define metrics to aggregate
    numeric_metrics = [
        'baseline_num_bullets',
        'full_num_bullets',
        'baseline_required_coverage',
        'full_required_coverage',
        'baseline_nice_coverage',
        'full_nice_coverage',
        'baseline_avg_bullet_length',
        'full_avg_bullet_length',
        'delta_num_bullets',
        'delta_required_coverage',
        'delta_nice_coverage',
        'semantic_precision',
        'semantic_recall',
        'semantic_f1'
    ]

    # Compute statistics
    stats = []
    for metric in numeric_metrics:
        if metric in per_pair_df.columns:
            stats.append({
                'metric': metric,
                'mean': per_pair_df[metric].mean(),
                'std': per_pair_df[metric].std(),
                'min': per_pair_df[metric].min(),
                'max': per_pair_df[metric].max(),
                'median': per_pair_df[metric].median()
            })

    # Add success rates
    if 'baseline_success' in per_pair_df.columns:
        stats.append({
            'metric': 'baseline_success_rate',
            'mean': per_pair_df['baseline_success'].mean(),
            'std': 0.0,
            'min': 0.0,
            'max': 1.0,
            'median': per_pair_df['baseline_success'].median()
        })

    if 'full_success' in per_pair_df.columns:
        stats.append({
            'metric': 'full_success_rate',
            'mean': per_pair_df['full_success'].mean(),
            'std': 0.0,
            'min': 0.0,
            'max': 1.0,
            'median': per_pair_df['full_success'].median()
        })

    # Add cover letter percentages
    if 'baseline_has_cover_letter' in per_pair_df.columns:
        stats.append({
            'metric': 'baseline_cover_letter_pct',
            'mean': per_pair_df['baseline_has_cover_letter'].mean(),
            'std': 0.0,
            'min': 0.0,
            'max': 1.0,
            'median': per_pair_df['baseline_has_cover_letter'].median()
        })

    if 'full_has_cover_letter' in per_pair_df.columns:
        stats.append({
            'metric': 'full_cover_letter_pct',
            'mean': per_pair_df['full_has_cover_letter'].mean(),
            'std': 0.0,
            'min': 0.0,
            'max': 1.0,
            'median': per_pair_df['full_has_cover_letter'].median()
        })

    aggregate_df = pd.DataFrame(stats)
    aggregate_df.set_index('metric', inplace=True)

    return aggregate_df


def plot_comparison_bars(
    per_pair_df: pd.DataFrame,
    metric_name: str,
    ylabel: str,
    output_path: Path,
    baseline_col: str,
    full_col: str
) -> None:
    """
    Create bar chart comparing baseline vs full for a metric.

    Args:
        per_pair_df: DataFrame with per-pair metrics
        metric_name: Name for the plot title
        ylabel: Label for y-axis
        output_path: Path to save PNG
        baseline_col: Column name for baseline values
        full_col: Column name for full values
    """
    fig, ax = plt.subplots(figsize=(12, 6))

    x = np.arange(len(per_pair_df))
    width = 0.35

    baseline_vals = per_pair_df[baseline_col].values
    full_vals = per_pair_df[full_col].values

    bars1 = ax.bar(x - width/2, baseline_vals, width, label='Baseline', color='#3498db', alpha=0.8)
    bars2 = ax.bar(x + width/2, full_vals, width, label='Full (Semantic)', color='#e67e22', alpha=0.8)

    ax.set_xlabel('Pair ID', fontsize=12)
    ax.set_ylabel(ylabel, fontsize=12)
    ax.set_title(f'{metric_name}: Baseline vs Full Mode', fontsize=14, fontweight='bold')
    ax.set_xticks(x)
    ax.set_xticklabels(per_pair_df['pair_id'].values, rotation=45, ha='right', fontsize=9)
    ax.legend(fontsize=11)
    ax.grid(axis='y', alpha=0.3, linestyle='--')

    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    plt.close()


def plot_single_metric(
    per_pair_df: pd.DataFrame,
    metric_col: str,
    ylabel: str,
    output_path: Path
) -> None:
    """
    Create bar chart for a single metric per pair.

    Args:
        per_pair_df: DataFrame with per-pair metrics
        metric_col: Column name for the metric
        ylabel: Label for y-axis
        output_path: Path to save PNG
    """
    fig, ax = plt.subplots(figsize=(12, 6))

    x = np.arange(len(per_pair_df))
    values = per_pair_df[metric_col].values

    bars = ax.bar(x, values, color='#2ecc71', alpha=0.8, edgecolor='black', linewidth=0.5)

    # Color bars based on value (green=good, yellow=medium, red=low)
    for i, (bar, val) in enumerate(zip(bars, values)):
        if val >= 0.7:
            bar.set_color('#2ecc71')  # Green
        elif val >= 0.5:
            bar.set_color('#f39c12')  # Orange
        else:
            bar.set_color('#e74c3c')  # Red

    ax.set_xlabel('Pair ID', fontsize=12)
    ax.set_ylabel(ylabel, fontsize=12)
    ax.set_title(f'{ylabel} per Pair', fontsize=14, fontweight='bold')
    ax.set_xticks(x)
    ax.set_xticklabels(per_pair_df['pair_id'].values, rotation=45, ha='right', fontsize=9)
    ax.set_ylim(0, 1.0)
    ax.axhline(y=0.7, color='gray', linestyle='--', linewidth=1, alpha=0.5, label='Good threshold (0.7)')
    ax.axhline(y=0.5, color='gray', linestyle=':', linewidth=1, alpha=0.5, label='Medium threshold (0.5)')
    ax.legend(fontsize=10)
    ax.grid(axis='y', alpha=0.3, linestyle='--')

    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    plt.close()


def main() -> None:
    """Main entry point for evaluation metrics script."""
    parser = argparse.ArgumentParser(
        description="Compute evaluation metrics for AutoResuAgent baseline vs full comparison"
    )
    parser.add_argument(
        "--input",
        type=Path,
        default=Path("outputs/eval/baseline_vs_full.jsonl"),
        help="Path to baseline_vs_full.jsonl"
    )
    parser.add_argument(
        "--outdir",
        type=Path,
        default=Path("outputs/eval/metrics"),
        help="Output directory for metrics and plots"
    )
    parser.add_argument(
        "--sbert_model",
        type=str,
        default="all-MiniLM-L6-v2",
        help="Sentence-BERT model name"
    )
    parser.add_argument(
        "--match_threshold",
        type=float,
        default=0.7,
        help="Similarity threshold for semantic matching (0.0-1.0)"
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable debug logging"
    )

    args = parser.parse_args()

    setup_logging(args.verbose)
    logger = logging.getLogger(__name__)

    # Validate inputs
    if not args.input.exists():
        logger.error(f"Input file not found: {args.input}")
        sys.exit(1)

    # Create output directory
    args.outdir.mkdir(parents=True, exist_ok=True)
    logger.info(f"Output directory: {args.outdir}")

    # Load data
    logger.info(f"Loading data from {args.input}")
    records = load_jsonl(args.input)
    logger.info(f"Loaded {len(records)} pairs")

    if len(records) == 0:
        logger.error("No records found in input file")
        sys.exit(1)

    # Load Sentence-BERT model (with fallback)
    logger.info(f"Loading Sentence-BERT model: {args.sbert_model}")
    model = None
    try:
        model = SentenceTransformer(args.sbert_model)
        logger.info("Model loaded successfully")
    except Exception as e:
        logger.error(f"Failed to load SBERT model: {e}")
        logger.warning("Continuing without semantic matching metrics...")

    # Compute per-pair metrics
    logger.info("Computing per-pair metrics...")
    per_pair_metrics = []
    for i, record in enumerate(records, start=1):
        if args.verbose:
            logger.debug(f"Processing pair {i}/{len(records)}: {record.get('pair_id', 'unknown')}")
        metrics = compute_per_pair_metrics(record, model, args.match_threshold)
        per_pair_metrics.append(metrics)

    per_pair_df = pd.DataFrame(per_pair_metrics)

    # Save per-pair CSV
    per_pair_csv = args.outdir / "metrics_summary_per_pair.csv"
    per_pair_df.to_csv(per_pair_csv, index=False)
    logger.info(f"Saved per-pair metrics: {per_pair_csv}")

    # Compute aggregate metrics
    logger.info("Computing aggregate metrics...")
    aggregate_df = compute_aggregate_metrics(per_pair_df)

    # Save aggregate CSV
    aggregate_csv = args.outdir / "metrics_aggregate.csv"
    aggregate_df.to_csv(aggregate_csv, index=True)
    logger.info(f"Saved aggregate metrics: {aggregate_csv}")

    # Generate plots
    logger.info("Generating plots...")

    plot_comparison_bars(
        per_pair_df,
        "Number of Bullets",
        "Number of Bullets",
        args.outdir / "num_bullets_per_pair.png",
        "baseline_num_bullets",
        "full_num_bullets"
    )
    logger.info("Generated num_bullets_per_pair.png")

    plot_comparison_bars(
        per_pair_df,
        "Required Skill Coverage",
        "Required Skill Coverage (0.0-1.0)",
        args.outdir / "req_skill_coverage_per_pair.png",
        "baseline_required_coverage",
        "full_required_coverage"
    )
    logger.info("Generated req_skill_coverage_per_pair.png")

    if model is not None:
        plot_single_metric(
            per_pair_df,
            "semantic_f1",
            "Semantic F1 Score",
            args.outdir / "semantic_f1_per_pair.png"
        )
        logger.info("Generated semantic_f1_per_pair.png")

    logger.info("=" * 60)
    logger.info("EVALUATION COMPLETE")
    logger.info("=" * 60)
    logger.info(f"Per-pair metrics: {per_pair_csv}")
    logger.info(f"Aggregate metrics: {aggregate_csv}")
    logger.info(f"Plots saved to: {args.outdir}")

    # Print key findings
    print("\n" + "=" * 60)
    print("KEY FINDINGS")
    print("=" * 60)
    print(f"Total pairs evaluated: {len(records)}")
    print(f"Baseline success rate: {per_pair_df['baseline_success'].mean():.1%}")
    print(f"Full mode success rate: {per_pair_df['full_success'].mean():.1%}")
    print(f"Avg baseline bullets: {per_pair_df['baseline_num_bullets'].mean():.2f}")
    print(f"Avg full mode bullets: {per_pair_df['full_num_bullets'].mean():.2f}")
    print(f"Avg delta num bullets: {per_pair_df['delta_num_bullets'].mean():+.2f}")
    print(f"Avg baseline required coverage: {per_pair_df['baseline_required_coverage'].mean():.2%}")
    print(f"Avg full mode required coverage: {per_pair_df['full_required_coverage'].mean():.2%}")
    print(f"Avg delta required coverage: {per_pair_df['delta_required_coverage'].mean():+.2%}")
    print(f"Baseline cover letter rate: {per_pair_df['baseline_has_cover_letter'].mean():.1%}")
    print(f"Full mode cover letter rate: {per_pair_df['full_has_cover_letter'].mean():.1%}")
    if model is not None:
        print(f"Avg semantic precision: {per_pair_df['semantic_precision'].mean():.3f}")
        print(f"Avg semantic recall: {per_pair_df['semantic_recall'].mean():.3f}")
        print(f"Avg semantic F1: {per_pair_df['semantic_f1'].mean():.3f}")
    print("=" * 60)


if __name__ == "__main__":
    main()
