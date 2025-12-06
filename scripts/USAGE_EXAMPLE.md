# Quick Start Guide for Evaluation Metrics

## Installation

First, install the required dependencies:

```bash
pip install sentence-transformers scikit-learn pandas matplotlib numpy
```

## Step-by-Step Usage

### 1. Generate Evaluation Data

Run the evaluation pipeline on your dataset:

```bash
python main.py --eval-dataset data/eval/job_resume_pairs.json --provider openai
```

This creates: `outputs/eval/baseline_vs_full.jsonl`

### 2. Compute Metrics

Run the metrics script:

```bash
python scripts/eval_metrics.py \
  --input outputs/eval/baseline_vs_full.jsonl \
  --outdir outputs/eval/metrics \
  --verbose
```

### 3. View Results

Check the output directory:

```bash
# View per-pair metrics
cat outputs/eval/metrics/metrics_summary_per_pair.csv

# View aggregate statistics
cat outputs/eval/metrics/metrics_aggregate.csv

# Open the plots (on Windows)
start outputs/eval/metrics/num_bullets_per_pair.png
start outputs/eval/metrics/req_skill_coverage_per_pair.png
start outputs/eval/metrics/semantic_f1_per_pair.png
```

## Expected Output Structure

```
outputs/eval/metrics/
├── metrics_summary_per_pair.csv      # Detailed per-pair metrics
├── metrics_aggregate.csv             # Summary statistics
├── num_bullets_per_pair.png          # Bullet count comparison chart
├── req_skill_coverage_per_pair.png   # Skill coverage comparison chart
└── semantic_f1_per_pair.png          # Semantic similarity chart
```

## Testing the Installation

Run the test suite to verify everything works:

```bash
pytest tests/test_eval_metrics.py -v
```

Expected output:
```
tests/test_eval_metrics.py::test_eval_metrics_end_to_end PASSED
tests/test_eval_metrics.py::test_extract_bullets_handles_different_formats PASSED
tests/test_eval_metrics.py::test_semantic_matching_edge_cases PASSED
tests/test_eval_metrics.py::test_load_jsonl_handles_invalid_lines PASSED
tests/test_eval_metrics.py::test_compute_per_pair_metrics_complete PASSED
tests/test_eval_metrics.py::test_compute_aggregate_metrics PASSED
```

## Common Issues

### Issue: "No module named 'sentence_transformers'"

**Solution**: Install dependencies
```bash
pip install sentence-transformers scikit-learn pandas matplotlib numpy
```

### Issue: "Input file not found"

**Solution**: Run the evaluation pipeline first
```bash
python main.py --eval-dataset data/eval/job_resume_pairs.json --provider openai
```

### Issue: Model download is slow

**Solution**: The first run downloads the Sentence-BERT model (~90MB). Subsequent runs will be faster as the model is cached.

## Advanced Options

### Custom Similarity Threshold

```bash
# Stricter matching (only very similar bullets match)
python scripts/eval_metrics.py --match_threshold 0.9

# Lenient matching (loosely related bullets match)
python scripts/eval_metrics.py --match_threshold 0.5
```

### Different SBERT Model

```bash
# Use a different sentence embedding model
python scripts/eval_metrics.py --sbert_model paraphrase-MiniLM-L6-v2
```

## Interpreting Results

### Key Metrics to Watch

1. **Full Success Rate**: Should be ≥ baseline success rate
   - Target: >90%

2. **Delta Required Coverage**: Should be positive
   - Target: +10% to +30%

3. **Semantic F1**: Shows content retention
   - Target: 0.6-0.8 (balanced improvement)

4. **Delta Num Bullets**: Full mode should generate more
   - Target: +2 to +5 bullets

### What Good Results Look Like

```
Full mode success rate: 96.7%
Avg delta required coverage: +26.2%
Avg semantic F1: 0.807
Avg delta num bullets: +2.6
```

### What to Investigate

- **Low F1 (<0.5)**: Full mode may be hallucinating
- **Negative skill coverage delta**: Full mode is worse
- **Very high F1 (>0.9)**: Full mode isn't improving much

## Next Steps

After running metrics:

1. Review the CSV files for detailed analysis
2. Check plots to identify outlier pairs
3. Investigate failing pairs in the JSONL
4. Adjust prompts/retrieval if needed
5. Re-run evaluation pipeline
6. Compare metrics across iterations

## Support

For detailed documentation, see: [README_EVAL_METRICS.md](../README_EVAL_METRICS.md)
