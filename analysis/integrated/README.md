# Integrated Individual-Differences Analysis

This module crosses the participant-text comprehension/fixation counts with
participant-level individual-difference measures. It is intentionally separate
from the standalone comprehension and individual-differences analyses.

Run the integrated moderation analysis with:

```bash
python analysis/integrated/run_analysis.py --wave both
```

The primary question is whether language skill changes the relationship between
comprehension and fixation rate. Wave-specific models are fitted first because
the waves have different participant and language compositions.

The interaction term is the main test:

```text
comprehension_score x language_skill_composite
```

The analysis uses standardized predictors within wave and does not sum raw test
scores. Generated cross-dataset outputs are written to `output/`.
