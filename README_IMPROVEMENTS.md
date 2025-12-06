# Skill Coverage Improvement Guide

## Problem Identified

Initial evaluation showed:
- ✅ Full mode generates 49% more bullets
- ⚠️ But skill coverage drops by 4% on average
- ⚠️ 6 pairs show >30% coverage drop
- ⚠️ Semantic F1 = 1.0 (too perfect, suggests insufficient differentiation)

## Root Causes

1. **Semantic retrieval finds similar experiences but they don't always contain required skills**
   - Retrieval was based purely on responsibility similarity, not skill presence
   - top_k=5 was too small, limiting skill diversity in retrieved experiences

2. **LLM prompt didn't emphasize required skills strongly enough**
   - No explicit instruction to cover ALL required skills
   - No verification step before finalizing bullets
   - Missing emphasis on skills_covered field

3. **No validation preventing bullets that miss required skills**
   - Validation only checked individual bullet properties (length, hallucinations)
   - No collective validation across all bullets for skill coverage
   - Missing skills didn't trigger retry

## Fixes Applied

### 1. Strengthened Bullet Generation Prompt
**File:** `src/generators/bullet_generator.py`

**Changes:**
- Added "**CRITICAL REQUIREMENT:**" banner at the start of the prompt
- Required skills section moved to top with "**MUST COVER ALL OF THESE:**" header
- Task instructions now include: "1. **COVER ALL REQUIRED SKILLS**" as first priority
- Added "**SKILL COVERAGE CHECK:**" reminder before output format
- Final reminder: "Every required skill must appear in at least one bullet's skills_covered field"
- Added validation_feedback parameter to inject error messages from failed attempts

**Impact:** LLM now receives 4+ explicit reminders to cover all required skills

### 2. Added Skill Coverage Validation
**File:** `src/agent/validator.py`

**New Function:** `validate_skill_coverage_strict(bullets, job, minimum_coverage=0.8)`

**Logic:**
- Collects all skills mentioned across all bullets
- Checks each required skill for coverage (exact match or substring match)
- Calculates coverage percentage: `1.0 - (missing / total)`
- Returns errors if coverage < 80% or if any skills are missing
- Lists specific missing skills in error message

**Integration:** Added to `validate_bullets_only()` so it runs on every validation pass

**Impact:** Missing skills now trigger validation failure and retry with feedback

### 3. Increased Retrieval Diversity
**File:** `src/embeddings/retriever.py`

**Change:** Increased default `top_k` from 5 to 10 in `retrieve_relevant_experiences()`

**Rationale:**
- More retrieved experiences = higher chance of finding all required skills
- Gives LLM more diverse context to draw from
- Minimal performance impact (still fast FAISS search)

**Impact:** 100% more context per responsibility, better skill coverage

### 4. Added Validation Feedback Loop
**File:** `src/agent/executor.py`

**Changes to `_generate_bullets_with_retry()`:**
- Added `validation_feedback` variable to track errors across attempts
- First attempt: No feedback (clean slate)
- Subsequent attempts: Include validation errors in prompt
- Feedback includes: specific missing skills, hallucination warnings, length issues
- LLM receives explicit instructions to "fix these issues in your new generation"

**Flow:**
```
Attempt 1: Generate bullets → Validate → FAIL (missing Python, AWS)
Attempt 2: Generate with feedback "Missing: Python, AWS" → Validate → SUCCESS
```

**Impact:** LLM learns from mistakes and corrects skill coverage on retry

### 5. Created Analysis Tool
**File:** `scripts/analyze_problem_pairs.py`

**Purpose:** Identify and analyze pairs with skill coverage degradation

**Usage:**
```bash
python scripts/analyze_problem_pairs.py --input outputs/eval/baseline_vs_full.jsonl --threshold -0.2
```

**Output:**
- Lists problem pairs sorted by delta (worst first)
- Shows baseline vs. full coverage for each
- Provides summary statistics
- Offers recommendations for further improvements

**Impact:** Easy identification of problematic job-resume combinations

## Expected Improvements

After re-running evaluation with these fixes:

### Metrics to Watch

| Metric | Before | Target After |
|--------|--------|--------------|
| Avg skill coverage delta | -4% | **+5% to +15%** |
| Number of problem pairs (>20% drop) | 6 | **<3** |
| Avg bullets generated | +49% | **Maintained (+40% to +60%)** |
| Semantic F1 | 1.0 (too perfect) | **0.6-0.8 (healthy)** |
| Full mode success rate | ~97% | **>95% (maintained)** |

### Success Criteria

✅ **Primary Goal:** Full mode should have HIGHER skill coverage than baseline
✅ **Secondary Goal:** Maintain or improve bullet quantity
✅ **Tertiary Goal:** Semantic F1 shows differentiation (not just copying baseline)

## How to Verify

### Step 1: Re-run Evaluation
```bash
python main.py --eval-dataset data/eval/job_resume_pairs.json --provider openai
```

This will regenerate `outputs/eval/baseline_vs_full.jsonl` with the improved system.

### Step 2: Compute New Metrics
```bash
python scripts/eval_metrics.py \
  --input outputs/eval/baseline_vs_full.jsonl \
  --outdir outputs/eval/metrics_v2 \
  --verbose
```

### Step 3: Analyze Problem Pairs
```bash
python scripts/analyze_problem_pairs.py --input outputs/eval/baseline_vs_full.jsonl
```

### Step 4: Compare Results

**Before (v1):**
```
Avg baseline required coverage: 52.3%
Avg full mode required coverage: 48.1%  ❌
Avg delta required coverage: -4.2%      ❌
Semantic F1: 1.00                       ⚠️
```

**Expected After (v2):**
```
Avg baseline required coverage: 52.3%
Avg full mode required coverage: 62.0%  ✅
Avg delta required coverage: +9.7%      ✅
Semantic F1: 0.75                       ✅
```

## Monitoring

Track these metrics before/after:

### Coverage Metrics
- `baseline_required_coverage`: Should stay similar (~50-55%)
- `full_required_coverage`: Should INCREASE to 60-70%
- `delta_required_coverage`: Should be POSITIVE (+5% to +15%)

### Quality Metrics
- `baseline_num_bullets`: Baseline (~4-5 bullets)
- `full_num_bullets`: Should maintain increase (~6-8 bullets)
- `delta_num_bullets`: Keep positive (+2 to +4)

### Consistency Metrics
- `semantic_precision`: Should be 0.6-0.8 (not 1.0)
- `semantic_recall`: Should be 0.6-0.8 (not 1.0)
- `semantic_f1`: Should be 0.6-0.8 (healthy differentiation)

### Error Metrics
- `baseline_success`: ~70-80% (baseline has weaker validation)
- `full_success`: Should maintain >95%
- Problem pairs with >20% drop: Should be <3

## Debugging Tips

### If skill coverage is still low:

1. **Check the prompt is being used**
   - Add logging to `_build_bullet_generation_prompt()` to print the prompt
   - Verify "CRITICAL REQUIREMENT" and "MUST COVER ALL" appear

2. **Check validation is running**
   - Look for "Missing required skills" in logs
   - Verify `validate_skill_coverage_strict()` is being called

3. **Check retry is working**
   - Look for "Retrying with validation feedback..." in logs
   - Verify validation_feedback contains specific skill names

4. **Check retrieval has skills**
   - Manually inspect retrieved experiences for a problem pair
   - Verify they contain the required skills from job description

### If semantic F1 is still 1.0:

This means full mode is just copying baseline bullets exactly. Check:
1. Is retrieval actually using FAISS? (top_k=10 should fetch more diverse bullets)
2. Is the prompt emphasizing quantifiable results and metrics?
3. Are we using the right mode? ("full" vs "baseline")

### If validation is too strict (all retries failing):

1. Lower the threshold: `validate_skill_coverage_strict(..., minimum_coverage=0.7)`
2. Check if job descriptions have too many required skills (>10 is hard to cover)
3. Check if resume actually contains those skills

## Next Steps if Issues Persist

### 1. Skill-Weighted Retrieval
Modify `retrieve_relevant_experiences()` to:
- Boost scores of experiences that contain required skills
- Add explicit queries for each required skill
- Combine semantic similarity + skill matching

### 2. Two-Stage Generation
- Stage 1: Generate draft bullets
- Stage 2: LLM enriches bullets to cover missing skills

### 3. Skill-Specific Prompting
For each missing skill, generate a dedicated bullet:
```python
if missing_skills:
    for skill in missing_skills:
        prompt = f"Generate a bullet highlighting {skill} from these experiences: ..."
```

### 4. Retrieval Fallback
If semantic retrieval doesn't find skills:
- Fall back to keyword search for skill names
- Use all experiences (not just top-k) if skills are missing

## Technical Details

### Files Modified

1. **src/generators/bullet_generator.py** (Lines 17-299)
   - Added `validation_feedback` parameter to `generate_bullets_for_job()`
   - Completely rewrote `_build_bullet_generation_prompt()` with skill emphasis
   - Added feedback injection when validation fails

2. **src/agent/validator.py** (Lines 428-533)
   - Added `validate_skill_coverage_strict()` function (55 lines)
   - Updated `validate_bullets_only()` to call skill coverage validation
   - Returns specific missing skill names in error messages

3. **src/embeddings/retriever.py** (Lines 15-54)
   - Changed default `top_k` from 5 to 10
   - Updated docstring to explain the increase

4. **src/agent/executor.py** (Lines 234-301)
   - Added `validation_feedback` variable to retry loop
   - Pass feedback to `generate_bullets_for_job()` on retries
   - Collect errors into feedback string for next attempt

### Files Created

5. **scripts/analyze_problem_pairs.py** (133 lines)
   - Standalone analysis tool for coverage issues
   - Identifies pairs below threshold
   - Provides summary statistics and recommendations

6. **README_IMPROVEMENTS.md** (This file)
   - Complete documentation of the problem and solution
   - Before/after metrics comparison
   - Verification and debugging guide

## Testing

### Unit Tests (Optional)
To add tests for the new validation function:

```python
# tests/test_validator.py

def test_skill_coverage_strict():
    from src.agent.validator import validate_skill_coverage_strict
    from src.models import GeneratedBullet, JobDescription

    # Create test data
    bullets = [
        GeneratedBullet(id="b1", text="...", skills_covered=["Python", "AWS"]),
        GeneratedBullet(id="b2", text="...", skills_covered=["Docker"])
    ]

    job = JobDescription(
        job_id="test",
        title="SDE",
        company="Test Co",
        required_skills=["Python", "AWS", "Docker", "Kubernetes"],  # 4 skills
        responsibilities=["Build stuff"]
    )

    errors = validate_skill_coverage_strict(bullets, job, minimum_coverage=0.8)

    # Should fail: only 3/4 skills covered (75% < 80%)
    assert len(errors) > 0
    assert "Kubernetes" in errors[0]  # Missing skill

    # Should pass with 0.7 threshold
    errors = validate_skill_coverage_strict(bullets, job, minimum_coverage=0.7)
    assert len(errors) == 0
```

### Integration Test
Run on a single pair to verify end-to-end:

```bash
python main.py \
  --job data/jobs/google_ml_engineer.yaml \
  --resume data/resumes/mid_ml_engineer.json \
  --provider openai \
  --verbose
```

Check logs for:
- "CRITICAL REQUIREMENT" in prompt
- "Missing required skills" if validation fails
- "Retrying with validation feedback" if retry happens
- Final bullets cover all required skills

## Summary

The skill coverage degradation issue has been systematically addressed through:

1. ✅ **Prompt Engineering:** 4+ explicit skill coverage reminders
2. ✅ **Validation:** Strict 80% threshold with specific error messages
3. ✅ **Retrieval:** 2x more context (top_k=10)
4. ✅ **Feedback Loop:** Errors guide LLM corrections on retry
5. ✅ **Analysis Tools:** Easy problem identification

Expected outcome: **Full mode now OUTPERFORMS baseline on skill coverage** while maintaining higher bullet counts.

Re-run the evaluation and compare metrics to verify success! 🎯
