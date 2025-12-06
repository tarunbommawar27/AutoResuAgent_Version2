# Evaluation Metrics for AutoResuAgent

This script computes comprehensive metrics comparing baseline vs. full (semantic retrieval) modes.

## Overview

The evaluation metrics script analyzes the output of AutoResuAgent's baseline vs. full mode comparison and provides detailed quantitative insights including:

- Success rates for both modes
- Bullet point counts and quality metrics
- Required skill coverage comparison
- Semantic similarity matching using Sentence-BERT embeddings
- Cover letter generation rates
- Aggregate statistics across all job-resume pairs

## Installation

Install required dependencies:

```bash
pip install sentence-transformers scikit-learn pandas matplotlib numpy
```

Or install all AutoResuAgent dependencies at once:

```bash
pip install -r requirements.txt
```

## Usage

### Step 1: Generate Evaluation Data

First, run your evaluation pipeline to generate the baseline vs. full comparison:

```bash
python main.py --eval-dataset data/eval/job_resume_pairs.json --provider openai
```

This will create `outputs/eval/baseline_vs_full.jsonl` with results for each job-resume pair.

### Step 2: Compute Metrics

Run the evaluation metrics script:

```bash
python scripts/eval_metrics.py \
  --input outputs/eval/baseline_vs_full.jsonl \
  --outdir outputs/eval/metrics \
  --match_threshold 0.7 \
  --verbose
```

### Command-Line Arguments

- `--input`: Path to baseline_vs_full.jsonl (default: `outputs/eval/baseline_vs_full.jsonl`)
- `--outdir`: Output directory for results (default: `outputs/eval/metrics`)
- `--sbert_model`: Sentence-BERT model name (default: `all-MiniLM-L6-v2`)
- `--match_threshold`: Similarity threshold for semantic matching (default: `0.7`, range: 0.0-1.0)
- `--verbose`: Enable debug logging

## Outputs

The script generates the following files in the output directory:

### 1. metrics_summary_per_pair.csv

Detailed metrics for each job-resume pair with columns:

- `pair_id`: Unique identifier for the pair
- `baseline_success`: Whether baseline mode completed without errors
- `full_success`: Whether full mode completed without errors
- `baseline_num_bullets`: Number of bullets generated in baseline mode
- `full_num_bullets`: Number of bullets generated in full mode
- `delta_num_bullets`: Difference (full - baseline)
- `baseline_required_coverage`: Fraction of required skills covered (baseline)
- `full_required_coverage`: Fraction of required skills covered (full)
- `delta_required_coverage`: Improvement in skill coverage
- `baseline_has_cover_letter`: Whether baseline generated a cover letter
- `full_has_cover_letter`: Whether full mode generated a cover letter
- `semantic_precision`: Fraction of full bullets matching baseline (≥ threshold)
- `semantic_recall`: Fraction of baseline bullets matched in full mode
- `semantic_f1`: Harmonic mean of precision and recall

### 2. metrics_aggregate.csv

Summary statistics across all pairs including:

- Mean, standard deviation, min, max, and median for each numeric metric
- Success rates for both modes
- Cover letter generation rates

### 3. Visualizations (PNG files)

- **num_bullets_per_pair.png**: Bar chart comparing bullet counts (baseline vs. full)
- **req_skill_coverage_per_pair.png**: Bar chart comparing required skill coverage
- **semantic_f1_per_pair.png**: Bar chart showing semantic F1 scores per pair

## Metrics Explained

### Success Metrics

- **Success Rate**: Percentage of pairs that completed without validation errors
- Higher success rate indicates more robust generation

### Bullet Quality Metrics

- **Number of Bullets**: Count of tailored resume bullets generated
- **Average Bullet Length**: Mean character length (longer bullets often contain more detail)
- **Skill Coverage**: Fraction of job's required/nice-to-have skills mentioned in bullets

### Semantic Matching

The script uses **Sentence-BERT embeddings** to compare bullets between baseline and full modes:

1. Each bullet is encoded into a 384-dimensional semantic vector
2. Cosine similarity is computed between all baseline-full bullet pairs
3. Greedy 1:1 matching pairs each baseline bullet with its most similar full bullet
4. A match is counted if similarity ≥ threshold (default 0.7)

**Semantic Metrics**:
- **Precision**: Fraction of full-mode bullets that match baseline bullets (above threshold)
  - High precision = full mode retains baseline content
- **Recall**: Fraction of baseline bullets matched in full mode
  - High recall = full mode covers all baseline points
- **F1 Score**: Harmonic mean of precision and recall
  - Balanced measure of content overlap

### Match Threshold

The `--match_threshold` parameter controls how strict the semantic matching is:

- **0.9**: Very strict - only nearly identical bullets match
- **0.7**: Moderate (default) - bullets with similar meaning match
- **0.5**: Lenient - loosely related bullets match

**Interpretation**:
- **High F1 (>0.7)**: Full mode retains and improves baseline content
- **Medium F1 (0.5-0.7)**: Full mode makes moderate changes
- **Low F1 (<0.5)**: Full mode generates substantially different content

## Example Output

When the script completes, you'll see a summary like:

```
============================================================
KEY FINDINGS
============================================================
Total pairs evaluated: 30
Baseline success rate: 73.3%
Full mode success rate: 96.7%
Avg baseline bullets: 4.2
Avg full mode bullets: 6.8
Avg delta num bullets: +2.6
Avg baseline required coverage: 52.3%
Avg full mode required coverage: 78.5%
Avg delta required coverage: +26.2%
Baseline cover letter rate: 73.3%
Full mode cover letter rate: 96.7%
Avg semantic precision: 0.823
Avg semantic recall: 0.791
Avg semantic F1: 0.807
============================================================
```

## Interpretation Guide

### What to Look For

**Good Results**:
- Full mode success rate > baseline success rate
- Positive delta in required skill coverage (full mode covers more skills)
- Semantic F1 > 0.7 (full mode retains baseline content while improving it)
- Full mode generates more bullets (delta > 0)

**Potential Issues**:
- Low semantic F1 (<0.5) may indicate full mode is hallucinating or diverging too much
- Negative delta in skill coverage suggests full mode is worse
- Lower success rate in full mode indicates validation/generation issues

### Trade-offs

- **Higher bullet count** isn't always better - quality matters more than quantity
- **Very high semantic F1 (>0.9)** might mean full mode isn't improving much over baseline
- **Moderate F1 (0.6-0.8)** is often ideal - shows improvement while retaining key points

## Running Tests

To verify the script works correctly:

```bash
pytest tests/test_eval_metrics.py -v
```

The tests create synthetic data and verify:
- JSONL loading and parsing
- Bullet extraction from different formats
- Semantic matching edge cases
- CSV and plot generation
- End-to-end pipeline

## Troubleshooting

### "Model download failed"

If the Sentence-BERT model fails to download:
- Ensure you have internet access
- Try a different model: `--sbert_model paraphrase-MiniLM-L6-v2`
- The script will continue without semantic metrics if model loading fails

### "No records found"

If the input JSONL is empty:
- Verify the evaluation pipeline completed successfully
- Check that `outputs/eval/baseline_vs_full.jsonl` exists and has content
- Ensure the file is valid JSONL (one JSON object per line)

### Missing columns in CSV

If expected columns are missing:
- Verify your JSONL has both `baseline` and `full` sections with `metrics` subdicts
- Check that bullet data is in the expected format (see bullet extraction tests)

## Advanced Usage

### Custom Threshold Analysis

To see how threshold affects results, run multiple times with different thresholds:

```bash
for threshold in 0.5 0.6 0.7 0.8 0.9; do
  python scripts/eval_metrics.py \
    --input outputs/eval/baseline_vs_full.jsonl \
    --outdir "outputs/eval/metrics_threshold_${threshold}" \
    --match_threshold "$threshold"
done
```

### Analyzing Specific Pairs

To analyze only certain pairs, filter the JSONL first:

```bash
# Extract only "good match" pairs (pair-001 through pair-010)
head -10 outputs/eval/baseline_vs_full.jsonl > outputs/eval/good_matches.jsonl
python scripts/eval_metrics.py --input outputs/eval/good_matches.jsonl --outdir outputs/eval/good_matches_metrics
```

## Integration with Research

This metrics script is designed for research and evaluation of LLM-based resume generation systems. Key features:

- **Reproducible**: Fixed random seeds in Sentence-BERT encoding
- **Extensible**: Easy to add new metrics in `compute_per_pair_metrics()`
- **Publication-ready**: High-DPI PNG plots (150 DPI) suitable for papers
- **Statistical rigor**: Reports mean, std, min, max, median for all metrics

## Citation

If you use this evaluation framework in your research, please cite the AutoResuAgent project.

## Support

For issues or questions:
- Check the test file `tests/test_eval_metrics.py` for usage examples
- Review the main AutoResuAgent documentation
- Open an issue on the project repository
