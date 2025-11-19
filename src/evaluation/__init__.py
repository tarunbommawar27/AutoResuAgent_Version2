"""
Evaluation Package
Metrics and evaluation utilities.
"""

from .metrics import ResumeMetrics, compute_package_metrics
from .comparison import (
    compare_systems,
    compute_system_metrics,
    compute_alignment_score,
    compute_gold_similarity,
    print_comparison_table,
    save_comparison_results,
)

__all__ = [
    "ResumeMetrics",
    "compute_package_metrics",
    "compare_systems",
    "compute_system_metrics",
    "compute_alignment_score",
    "compute_gold_similarity",
    "print_comparison_table",
    "save_comparison_results",
]
