# Baseline Comparison Module - Testing Instructions

## Overview
The baseline comparison module has been implemented to compare:
- **Baseline mode**: No FAISS, no semantic search, minimal validation
- **Full Agent mode**: Complete pipeline with retrieval, validation, and retry

## What Was Implemented

### 1. Evaluation Dataset Format
**File**: `data/eval/job_resume_pairs.json`

Contains pairs of job descriptions and resumes for evaluation:
```json
[
  {
    "id": "pair-001",
    "job_path": "data/jobs/sample_job.yaml",
    "resume_path": "data/resumes/sample_resume.json"
  },
  {
    "id": "pair-002",
    "job_path": "data/jobs/cisco_ml_engineer.yaml",
    "resume_path": "data/resumes/tarun_resume.json"
  }
]
```

### 2. Extended AgentExecutor with Baseline Mode
**File**: `src/agent/executor.py`

Updated `run_single_job()` signature:
```python
async def run_single_job(
    self,
    job_path: Path,
    resume_path: Path,
    mode: str = "full"  # "full" | "baseline"
) -> tuple["FullGeneratedPackage | None", list[str], dict | None]:
```

**Baseline mode behavior**:
- Uses `generate_bullets_baseline()` - no FAISS retrieval
- Uses `generate_cover_letter_baseline()` - simple LLM prompt
- Minimal validation: only checks bullet length >= 30 chars
- No retry loops
- Returns same structure as full mode

**Full mode behavior**:
- Unchanged - FAISS retrieval, validation, retry loops
- Complete metrics computation

### 3. Metrics Helper Module
**File**: `src/evaluation/metrics.py`

Added two new functions:

#### `compute_basic_metrics(pkg, job, resume) -> dict`
Returns simplified metrics:
- `num_bullets`
- `avg_bullet_length_chars`
- `required_skill_coverage`
- `nice_to_have_skill_coverage`
- `has_cover_letter`
- `num_experiences_with_bullets`

#### `compare_runs_metrics(full, baseline) -> dict`
Computes deltas between full and baseline:
- `delta_required_skill_coverage`
- `delta_num_bullets`
- `delta_avg_bullet_length_chars`
- `delta_nice_to_have_skill_coverage`
- `delta_num_experiences_with_bullets`

### 4. Dataset Evaluation Runner
**File**: `src/evaluation/run_dataset_eval.py`

Main function: `run_dataset_eval(dataset_path, executor, output_dir=None)`

**Process**:
1. Loads dataset JSON file
2. For each pair:
   - Runs baseline mode
   - Runs full mode
   - Computes comparison metrics
3. Saves results to `outputs/eval/baseline_vs_full.jsonl`
4. Prints summary statistics

**Output Format** (JSONL - one line per pair):
```json
{
  "pair_id": "pair-001",
  "job_path": "data/jobs/sample_job.yaml",
  "resume_path": "data/resumes/sample_resume.json",
  "baseline": {
    "metrics": {
      "num_bullets": 8,
      "avg_bullet_length_chars": 92.5,
      "required_skill_coverage": 0.6,
      "nice_to_have_skill_coverage": 0.4,
      "has_cover_letter": true,
      "num_experiences_with_bullets": 0
    },
    "errors": []
  },
  "full": {
    "metrics": {
      "num_bullets": 10,
      "avg_bullet_length_chars": 105.3,
      "required_skill_coverage": 0.85,
      "nice_to_have_skill_coverage": 0.7,
      "has_cover_letter": true,
      "num_experiences_with_bullets": 3
    },
    "errors": []
  },
  "comparison": {
    "delta_required_skill_coverage": 0.25,
    "delta_num_bullets": 2,
    "delta_avg_bullet_length_chars": 12.8,
    "delta_nice_to_have_skill_coverage": 0.3,
    "delta_num_experiences_with_bullets": 3
  }
}
```

### 5. CLI Entry Point
**File**: `main.py`

Added `--eval-dataset` argument:
```bash
python main.py --eval-dataset data/eval/job_resume_pairs.json [--provider openai|anthropic]
```

## Testing Instructions

### Test 1: Verify Dataset Format
```bash
# Check that dataset file exists and is valid JSON
cat data/eval/job_resume_pairs.json
```

Expected: Valid JSON with 2 pairs

### Test 2: Run Evaluation on Dataset
```bash
# Run with OpenAI (default)
python main.py --eval-dataset data/eval/job_resume_pairs.json --verbose

# Or with Anthropic
python main.py --eval-dataset data/eval/job_resume_pairs.json --provider anthropic --verbose
```

**Expected output**:
1. Header showing evaluation configuration
2. Progress for each pair:
   - `[pair-001] Running BASELINE mode...`
   - `[pair-001] Running FULL mode...`
   - `[pair-001] Comparison:` with deltas
3. Final summary:
   - `Evaluated N pairs: full_success=X, baseline_success=Y`
   - `Results saved to outputs/eval/baseline_vs_full.jsonl`
4. Aggregate statistics showing average improvements

### Test 3: Verify Output File
```bash
# Check JSONL output file
cat outputs/eval/baseline_vs_full.jsonl
```

Expected:
- 2 lines (one per pair)
- Each line is valid JSON
- Contains `baseline`, `full`, and `comparison` sections

### Test 4: Parse and Analyze Results
```python
# Python script to analyze results
import json

results = []
with open('outputs/eval/baseline_vs_full.jsonl', 'r') as f:
    for line in f:
        results.append(json.loads(line))

# Print summary
for r in results:
    print(f"\nPair: {r['pair_id']}")
    print(f"  Baseline bullets: {r['baseline']['metrics']['num_bullets']}")
    print(f"  Full bullets: {r['full']['metrics']['num_bullets']}")
    print(f"  Δ Required skill coverage: {r['comparison']['delta_required_skill_coverage']:.2%}")
```

### Test 5: Test Individual Modes (Optional)
You can test baseline and full modes separately by modifying the executor directly:

```python
# Test in Python REPL or Jupyter
from pathlib import Path
from src.orchestration.config import get_config
from src.embeddings import SentenceBertEncoder
from src.agent import AgentExecutor

config = get_config()
llm = config.get_llm_client("openai")
encoder = SentenceBertEncoder()
executor = AgentExecutor(llm, encoder)

# Test baseline mode
pkg, errors, metrics = await executor.run_single_job(
    Path("data/jobs/sample_job.yaml"),
    Path("data/resumes/sample_resume.json"),
    mode="baseline"
)
print(f"Baseline: {len(pkg.bullets)} bullets, errors={len(errors)}")

# Test full mode
pkg, errors, metrics = await executor.run_single_job(
    Path("data/jobs/sample_job.yaml"),
    Path("data/resumes/sample_resume.json"),
    mode="full"
)
print(f"Full: {len(pkg.bullets)} bullets, errors={len(errors)}")
```

## Validation Checklist

- [ ] Dataset file exists at `data/eval/job_resume_pairs.json`
- [ ] All job and resume files in dataset exist
- [ ] `--eval-dataset` CLI argument works
- [ ] Baseline mode runs without FAISS indexing
- [ ] Full mode runs with FAISS indexing
- [ ] Output file created at `outputs/eval/baseline_vs_full.jsonl`
- [ ] JSONL format is valid
- [ ] Comparison metrics show expected deltas
- [ ] Aggregate statistics are printed
- [ ] No syntax errors or import errors

## Expected Improvements (Full vs Baseline)

Based on the system design, you should see:

1. **Higher required skill coverage** in full mode
   - Baseline: ~50-70% (guessing without context)
   - Full: ~70-90% (targeted retrieval)

2. **More unique source experiences** in full mode
   - Baseline: 0 (no source tracking)
   - Full: 2-5 (FAISS retrieval tracks sources)

3. **Better bullet quality** in full mode
   - More specific to job requirements
   - Less hallucination
   - Better validation scores

4. **Similar or slightly higher bullet count** in full mode
   - Baseline may generate bullets but miss the mark
   - Full mode targets exactly what's needed

## Troubleshooting

### Issue: "Job file not found" or "Resume file not found"
**Solution**: Verify paths in `data/eval/job_resume_pairs.json` are correct relative to project root

### Issue: API rate limits
**Solution**: Add delays between pairs or reduce dataset size temporarily

### Issue: JSONL parsing errors
**Solution**: Check that each line in output is valid JSON (no partial writes)

### Issue: "No module named 'src.evaluation.run_dataset_eval'"
**Solution**: Ensure you're running from project root and `src/` is in Python path

## Next Steps

After successful testing:

1. Add more job-resume pairs to dataset
2. Analyze aggregate metrics to quantify improvements
3. Use results for paper/presentation showing AutoResuAgent effectiveness
4. Consider adding more sophisticated metrics (BLEU, ROUGE, etc.)
