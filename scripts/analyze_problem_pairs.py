#!/usr/bin/env python3
"""
Analyze pairs with low skill coverage to identify root causes.

Usage:
    python scripts/analyze_problem_pairs.py --input outputs/eval/baseline_vs_full.jsonl
"""

import json
import argparse
from pathlib import Path
from typing import List, Dict, Any, Optional
import sys


def inspect_structure(pair: Dict[str, Any]) -> None:
    """Print the structure of a pair to debug."""
    print("JSONL Structure Inspection:")
    print("="*80)
    print(f"Top-level keys: {list(pair.keys())}")

    if 'baseline' in pair:
        print(f"\nbaseline keys: {list(pair['baseline'].keys())}")
        if 'metrics' in pair['baseline']:
            print(f"baseline.metrics keys: {list(pair['baseline']['metrics'].keys())}")

    if 'full' in pair:
        print(f"\nfull keys: {list(pair['full'].keys())}")
        if 'metrics' in pair['full']:
            print(f"full.metrics keys: {list(pair['full']['metrics'].keys())}")

    if 'comparison' in pair:
        print(f"\ncomparison keys: {list(pair['comparison'].keys())}")

    print("="*80)
    print()


def find_coverage_value(data: Dict[str, Any]) -> Optional[float]:
    """
    Recursively search for skill coverage value in nested dict.

    Tries multiple possible locations and key names.
    """
    # Try direct metrics access
    if 'metrics' in data:
        metrics = data['metrics']
        for key in ['required_skill_coverage', 'required_coverage', 'skill_coverage', 'coverage']:
            if key in metrics:
                return metrics[key]

    # Try direct access (metrics might be at top level)
    for key in ['required_skill_coverage', 'required_coverage', 'skill_coverage', 'coverage']:
        if key in data:
            return data[key]

    # Try nested search
    for value in data.values():
        if isinstance(value, dict):
            result = find_coverage_value(value)
            if result is not None:
                return result

    return None


def extract_coverage(pair: Dict[str, Any], mode: str) -> Optional[float]:
    """
    Extract coverage value for baseline or full mode.

    Args:
        pair: The pair dictionary
        mode: 'baseline' or 'full'

    Returns:
        Coverage value (0.0-1.0) or None if not found
    """
    if mode not in pair:
        return None

    mode_data = pair[mode]

    # Try finding it recursively
    coverage = find_coverage_value(mode_data)

    # If still not found, try comparison section for computed values
    if coverage is None and 'comparison' in pair:
        comp = pair['comparison']
        if mode == 'baseline' and 'baseline_required_coverage' in comp:
            return comp['baseline_required_coverage']
        if mode == 'full' and 'full_required_coverage' in comp:
            return comp['full_required_coverage']

    return coverage


def analyze_pair(pair: Dict[str, Any], threshold: float) -> Optional[Dict[str, Any]]:
    """
    Analyze a single pair for coverage issues.

    Returns:
        Analysis dict if it's a problem pair, None otherwise
    """
    baseline_cov = extract_coverage(pair, 'baseline')
    full_cov = extract_coverage(pair, 'full')

    if baseline_cov is None or full_cov is None:
        return None

    delta = full_cov - baseline_cov

    if delta < threshold:
        return {
            'pair_id': pair.get('pair_id', 'unknown'),
            'baseline_coverage': baseline_cov,
            'full_coverage': full_cov,
            'delta': delta,
            'job_path': pair.get('job_path', 'N/A'),
            'resume_path': pair.get('resume_path', 'N/A')
        }

    return None


def main():
    parser = argparse.ArgumentParser(description="Analyze problem pairs with low skill coverage")
    parser.add_argument(
        '--input',
        type=Path,
        default=Path('outputs/eval/baseline_vs_full.jsonl'),
        help='Path to baseline_vs_full.jsonl'
    )
    parser.add_argument(
        '--threshold',
        type=float,
        default=-0.2,
        help='Coverage drop threshold to flag as problem (default: -0.2 = -20%%)'
    )
    parser.add_argument(
        '--inspect',
        action='store_true',
        help='Print structure of first pair and exit'
    )

    args = parser.parse_args()

    if not args.input.exists():
        print(f"ERROR: Input file not found: {args.input}")
        sys.exit(1)

    # Load pairs
    pairs = []
    with open(args.input, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line:
                pairs.append(json.loads(line))

    if not pairs:
        print("ERROR: No pairs found in input file")
        sys.exit(1)

    # Inspection mode
    if args.inspect:
        inspect_structure(pairs[0])
        sys.exit(0)

    print('='*80)
    print('SKILL COVERAGE ANALYSIS')
    print('='*80)
    print(f'Total pairs analyzed: {len(pairs)}')
    print(f'Problem threshold: {args.threshold:.1%} coverage drop\n')

    # Analyze all pairs
    problem_pairs = []
    all_deltas = []
    failed_pairs = []

    for pair in pairs:
        baseline_cov = extract_coverage(pair, 'baseline')
        full_cov = extract_coverage(pair, 'full')

        if baseline_cov is None or full_cov is None:
            failed_pairs.append(pair.get('pair_id', 'unknown'))
            continue

        delta = full_cov - baseline_cov
        all_deltas.append({
            'pair_id': pair.get('pair_id', 'unknown'),
            'baseline': baseline_cov,
            'full': full_cov,
            'delta': delta
        })

        if delta < args.threshold:
            problem_pairs.append({
                'pair_id': pair.get('pair_id', 'unknown'),
                'baseline_coverage': baseline_cov,
                'full_coverage': full_cov,
                'delta': delta,
                'job_path': pair.get('job_path', 'N/A'),
                'resume_path': pair.get('resume_path', 'N/A')
            })

    # Report failed extractions
    if failed_pairs:
        print(f"WARNING: Could not extract coverage for {len(failed_pairs)} pairs:")
        for pid in failed_pairs[:5]:
            print(f"  - {pid}")
        if len(failed_pairs) > 5:
            print(f"  ... and {len(failed_pairs)-5} more")
        print("\nRun with --inspect to see the structure.\n")

    # Report problem pairs
    print(f'Problem pairs (>{abs(args.threshold):.0%} drop): {len(problem_pairs)}\n')

    if problem_pairs:
        problem_pairs.sort(key=lambda x: x['delta'])
        print('-'*80)
        for i, p in enumerate(problem_pairs, 1):
            print(f"{i}. {p['pair_id']}")
            print(f"   Baseline coverage: {p['baseline_coverage']:.1%}")
            print(f"   Full coverage: {p['full_coverage']:.1%}")
            print(f"   Delta: {p['delta']:+.1%} [!]")
            print(f"   Job: {Path(p['job_path']).name if p['job_path'] != 'N/A' else 'N/A'}")
            print(f"   Resume: {Path(p['resume_path']).name if p['resume_path'] != 'N/A' else 'N/A'}")
            print()
    else:
        print('SUCCESS: No problem pairs! All pairs maintain good skill coverage.\n')

    # Overall statistics
    if all_deltas:
        print('='*80)
        print('OVERALL STATISTICS')
        print('='*80)

        deltas_only = [d['delta'] for d in all_deltas]
        avg_delta = sum(deltas_only) / len(deltas_only)
        positive = sum(1 for d in deltas_only if d > 0.01)
        negative = sum(1 for d in deltas_only if d < -0.01)
        unchanged = len(deltas_only) - positive - negative

        print(f'Pairs analyzed: {len(all_deltas)}/{len(pairs)}')
        print(f'Average delta: {avg_delta:+.2%}')
        print(f'Pairs with improvement (>1%): {positive} ({positive/len(all_deltas)*100:.1f}%)')
        print(f'Pairs with degradation (<-1%): {negative} ({negative/len(all_deltas)*100:.1f}%)')
        print(f'Pairs essentially unchanged (±1%): {unchanged} ({unchanged/len(all_deltas)*100:.1f}%)')

        # Distribution
        import statistics
        if len(deltas_only) > 1:
            print(f'\nDelta distribution:')
            print(f'  Min: {min(deltas_only):+.1%}')
            print(f'  Max: {max(deltas_only):+.1%}')
            print(f'  Median: {statistics.median(deltas_only):+.1%}')
            print(f'  Std Dev: {statistics.stdev(deltas_only):.2%}')

        print('='*80)

        # Recommendations
        if problem_pairs:
            print('\nRECOMMENDATIONS:')
            print('='*80)
            print('1. Inspect job descriptions for problem pairs - do they have many required skills?')
            print('2. Check if retrieved experiences lack these specific skills')
            print('3. Consider strengthening skill coverage emphasis in prompts')
            print('4. Review validation thresholds and retry logic')
            print()


if __name__ == "__main__":
    main()
