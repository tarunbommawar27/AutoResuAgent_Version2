"""Tests for evaluation metrics script."""

import json
import subprocess
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock
import pytest
import numpy as np


def test_eval_metrics_end_to_end(tmp_path):
    """Test full evaluation metrics pipeline with synthetic data."""

    # Create synthetic JSONL input
    input_file = tmp_path / "test_baseline_vs_full.jsonl"

    synthetic_data = [
        {
            "pair_id": "pair-001",
            "job_path": "data/jobs/test_job.yaml",
            "resume_path": "data/resumes/test_resume.json",
            "baseline": {
                "metrics": {
                    "num_bullets": 5,
                    "avg_bullet_length_chars": 120.0,
                    "required_skill_coverage": 0.6,
                    "nice_to_have_skill_coverage": 0.3,
                    "has_cover_letter": True,
                    "num_experiences_with_bullets": 0
                },
                "errors": [],
                "package": {
                    "bullets": [
                        {"id": "b1", "text": "Developed API using Python"},
                        {"id": "b2", "text": "Built ML model with TensorFlow"}
                    ]
                }
            },
            "full": {
                "metrics": {
                    "num_bullets": 6,
                    "avg_bullet_length_chars": 135.0,
                    "required_skill_coverage": 0.8,
                    "nice_to_have_skill_coverage": 0.5,
                    "has_cover_letter": True,
                    "num_experiences_with_bullets": 2
                },
                "errors": [],
                "package": {
                    "bullets": [
                        {"id": "b1", "text": "Developed REST API using Python and Flask"},
                        {"id": "b2", "text": "Built ML classification model with TensorFlow"}
                    ]
                }
            }
        },
        {
            "pair_id": "pair-002",
            "job_path": "data/jobs/test_job2.yaml",
            "resume_path": "data/resumes/test_resume2.json",
            "baseline": {
                "metrics": {
                    "num_bullets": 4,
                    "avg_bullet_length_chars": 110.0,
                    "required_skill_coverage": 0.5,
                    "nice_to_have_skill_coverage": 0.2,
                    "has_cover_letter": False,
                    "num_experiences_with_bullets": 0
                },
                "errors": ["Some error"],
                "bullets": [
                    "Simple bullet one",
                    "Simple bullet two"
                ]
            },
            "full": {
                "metrics": {
                    "num_bullets": 5,
                    "avg_bullet_length_chars": 125.0,
                    "required_skill_coverage": 0.9,
                    "nice_to_have_skill_coverage": 0.6,
                    "has_cover_letter": True,
                    "num_experiences_with_bullets": 3
                },
                "errors": [],
                "bullets": [
                    "Improved bullet one with details",
                    "Improved bullet two with metrics"
                ]
            }
        }
    ]

    with open(input_file, 'w') as f:
        for record in synthetic_data:
            f.write(json.dumps(record) + '\n')

    # Create output directory
    outdir = tmp_path / "metrics"

    # Run the script
    result = subprocess.run(
        [
            sys.executable,
            "scripts/eval_metrics.py",
            "--input", str(input_file),
            "--outdir", str(outdir),
            "--match_threshold", "0.5"
        ],
        capture_output=True,
        text=True
    )

    # Assert script ran successfully
    assert result.returncode == 0, f"Script failed: {result.stderr}"

    # Assert output files exist
    assert (outdir / "metrics_summary_per_pair.csv").exists()
    assert (outdir / "metrics_aggregate.csv").exists()
    assert (outdir / "num_bullets_per_pair.png").exists()
    assert (outdir / "req_skill_coverage_per_pair.png").exists()
    assert (outdir / "semantic_f1_per_pair.png").exists()

    # Read and verify per-pair CSV
    import pandas as pd
    per_pair_df = pd.read_csv(outdir / "metrics_summary_per_pair.csv")

    assert len(per_pair_df) == 2
    assert "pair_id" in per_pair_df.columns
    assert "baseline_num_bullets" in per_pair_df.columns
    assert "full_num_bullets" in per_pair_df.columns
    assert "semantic_f1" in per_pair_df.columns

    # Verify aggregate CSV exists and has expected structure
    aggregate_df = pd.read_csv(outdir / "metrics_aggregate.csv")
    assert len(aggregate_df) > 0


def test_extract_bullets_handles_different_formats():
    """Test that bullet extraction handles various input formats."""
    # Import the function from the script
    import sys
    from pathlib import Path
    script_dir = Path(__file__).parent.parent / "scripts"
    sys.path.insert(0, str(script_dir))
    from eval_metrics import extract_bullets

    # Format 1: package.bullets as list of dicts
    data1 = {
        "package": {
            "bullets": [
                {"id": "b1", "text": "First bullet"},
                {"id": "b2", "text": "Second bullet"}
            ]
        }
    }
    bullets1 = extract_bullets(data1)
    assert bullets1 == ["First bullet", "Second bullet"]

    # Format 2: bullets as list of strings
    data2 = {
        "bullets": ["Bullet one", "Bullet two", "Bullet three"]
    }
    bullets2 = extract_bullets(data2)
    assert bullets2 == ["Bullet one", "Bullet two", "Bullet three"]

    # Format 3: bullets as list of dicts (at top level)
    data3 = {
        "bullets": [
            {"text": "Dict bullet one"},
            {"text": "Dict bullet two"}
        ]
    }
    bullets3 = extract_bullets(data3)
    assert bullets3 == ["Dict bullet one", "Dict bullet two"]

    # Format 4: empty/missing
    data4 = {}
    bullets4 = extract_bullets(data4)
    assert bullets4 == []

    # Format 5: package exists but no bullets
    data5 = {"package": {}}
    bullets5 = extract_bullets(data5)
    assert bullets5 == []


def test_semantic_matching_edge_cases():
    """Test semantic matching handles edge cases correctly."""
    import sys
    from pathlib import Path
    script_dir = Path(__file__).parent.parent / "scripts"
    sys.path.insert(0, str(script_dir))
    from eval_metrics import compute_semantic_matching

    # Case 1: Both empty
    result = compute_semantic_matching([], [], None, 0.7)
    assert result['precision'] == 1.0
    assert result['recall'] == 1.0
    assert result['f1'] == 1.0

    # Case 2: Baseline empty
    result = compute_semantic_matching([], ["Some bullet"], None, 0.7)
    assert result['precision'] == 0.0
    assert result['recall'] == 1.0
    assert result['f1'] == 0.0

    # Case 3: Full empty
    result = compute_semantic_matching(["Some bullet"], [], None, 0.7)
    assert result['precision'] == 1.0
    assert result['recall'] == 0.0
    assert result['f1'] == 0.0

    # Case 4: Model is None
    result = compute_semantic_matching(["baseline"], ["full"], None, 0.7)
    assert result['precision'] == 0.0
    assert result['recall'] == 0.0
    assert result['f1'] == 0.0


def test_load_jsonl_handles_invalid_lines():
    """Test that load_jsonl skips invalid JSON lines gracefully."""
    import sys
    from pathlib import Path
    import tempfile
    script_dir = Path(__file__).parent.parent / "scripts"
    sys.path.insert(0, str(script_dir))
    from eval_metrics import load_jsonl

    with tempfile.NamedTemporaryFile(mode='w', suffix='.jsonl', delete=False) as f:
        f.write('{"valid": "json"}\n')
        f.write('invalid json line\n')
        f.write('{"another": "valid"}\n')
        f.write('\n')  # Empty line
        f.write('{"third": "valid"}\n')
        temp_path = Path(f.name)

    try:
        records = load_jsonl(temp_path)
        assert len(records) == 3
        assert records[0] == {"valid": "json"}
        assert records[1] == {"another": "valid"}
        assert records[2] == {"third": "valid"}
    finally:
        temp_path.unlink()


def test_compute_per_pair_metrics_complete():
    """Test compute_per_pair_metrics with complete record."""
    import sys
    from pathlib import Path
    script_dir = Path(__file__).parent.parent / "scripts"
    sys.path.insert(0, str(script_dir))
    from eval_metrics import compute_per_pair_metrics

    record = {
        "pair_id": "test-001",
        "baseline": {
            "metrics": {
                "num_bullets": 3,
                "avg_bullet_length_chars": 100.0,
                "required_skill_coverage": 0.5,
                "nice_to_have_skill_coverage": 0.2,
                "has_cover_letter": True
            },
            "errors": [],
            "package": {
                "bullets": [
                    {"text": "Bullet 1"},
                    {"text": "Bullet 2"},
                    {"text": "Bullet 3"}
                ]
            }
        },
        "full": {
            "metrics": {
                "num_bullets": 4,
                "avg_bullet_length_chars": 120.0,
                "required_skill_coverage": 0.7,
                "nice_to_have_skill_coverage": 0.4,
                "has_cover_letter": True
            },
            "errors": [],
            "package": {
                "bullets": [
                    {"text": "Improved bullet 1"},
                    {"text": "Improved bullet 2"},
                    {"text": "Improved bullet 3"},
                    {"text": "New bullet 4"}
                ]
            }
        }
    }

    # Test without model (semantic metrics should be 0)
    metrics = compute_per_pair_metrics(record, None, 0.7)

    assert metrics['pair_id'] == 'test-001'
    assert metrics['baseline_success'] == True
    assert metrics['full_success'] == True
    assert metrics['baseline_num_bullets'] == 3
    assert metrics['full_num_bullets'] == 4
    assert metrics['baseline_required_coverage'] == 0.5
    assert metrics['full_required_coverage'] == 0.7
    assert metrics['delta_num_bullets'] == 1
    assert metrics['delta_required_coverage'] == 0.2
    assert metrics['semantic_precision'] == 0.0  # No model
    assert metrics['semantic_recall'] == 0.0
    assert metrics['semantic_f1'] == 0.0


def test_compute_aggregate_metrics():
    """Test aggregate metrics computation."""
    import sys
    from pathlib import Path
    import pandas as pd
    script_dir = Path(__file__).parent.parent / "scripts"
    sys.path.insert(0, str(script_dir))
    from eval_metrics import compute_aggregate_metrics

    # Create sample per-pair DataFrame
    data = {
        'pair_id': ['pair-001', 'pair-002', 'pair-003'],
        'baseline_success': [True, True, False],
        'full_success': [True, True, True],
        'baseline_num_bullets': [3, 4, 5],
        'full_num_bullets': [5, 6, 7],
        'baseline_required_coverage': [0.5, 0.6, 0.4],
        'full_required_coverage': [0.7, 0.8, 0.9],
        'delta_num_bullets': [2, 2, 2],
        'delta_required_coverage': [0.2, 0.2, 0.5],
        'semantic_f1': [0.8, 0.7, 0.6]
    }
    per_pair_df = pd.DataFrame(data)

    aggregate_df = compute_aggregate_metrics(per_pair_df)

    # Check that aggregate DataFrame has expected structure
    assert 'mean' in aggregate_df.columns
    assert 'std' in aggregate_df.columns
    assert 'min' in aggregate_df.columns
    assert 'max' in aggregate_df.columns

    # Check specific values
    assert 'baseline_num_bullets' in aggregate_df.index
    assert aggregate_df.loc['baseline_num_bullets', 'mean'] == 4.0
    assert 'baseline_success_rate' in aggregate_df.index
    assert aggregate_df.loc['baseline_success_rate', 'mean'] == pytest.approx(2/3, rel=0.01)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
