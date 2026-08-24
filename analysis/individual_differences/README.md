# Individual-Differences Analysis

This package audits and describes the MECO-L2 participant measures without
crossing them with comprehension, fixation, or reading-rate data.

Prepare the source tables with:

```bash
python scripts/preprocess_individual_differences.py --wave both
```

Run the standalone analysis with:

```bash
python analysis/individual_differences/run_analysis.py --wave both
```

The analysis preserves missing values and flags suspicious values instead of
deleting or imputing them. Standardized scores are calculated within wave.
The language-skill composite is the mean of standardized LexTALE, capped
vocabulary, and TOWRE scores. Raw measures are not summed because they use
different scales.
