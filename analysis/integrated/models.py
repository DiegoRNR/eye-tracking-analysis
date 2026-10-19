"""Wave-specific moderation models for integrated reader analyses."""

import numpy as np
import statsmodels.api as sm


def _term(column):
    return f'Q("{column}")' if "." in column else column


def fit_fixation_moderation(data, predictor="language_skill_composite"):
    data = data.dropna(subset=[predictor]).copy()
    predictor_term = _term(predictor)
    formula = (
        "valid_fixation_events ~ comprehension_score + "
        f"{predictor_term} + comprehension_score:{predictor_term} + "
        "C(text_id) + C(lang)"
    )
    if data["wave"].nunique() > 1:
        formula += " + C(wave)"
    model = sm.GEE.from_formula(
        formula,
        groups="participant_id",
        data=data,
        family=sm.families.NegativeBinomial(alpha=1.0),
        cov_struct=sm.cov_struct.Exchangeable(),
        offset=data["log_text_length"],
    )
    return model.fit(), data, formula


def fit_comprehension_moderation(data, predictor="language_skill_composite"):
    data = data.dropna(subset=[predictor]).copy()
    predictor_term = _term(predictor)
    formula = (
        "comprehension_success ~ fixations_per_word + "
        f"{predictor_term} + fixations_per_word:{predictor_term} + "
        "C(text_id) + C(lang)"
    )
    if data["wave"].nunique() > 1:
        formula += " + C(wave)"
    expanded = data.loc[data.index.repeat(2)].copy()
    question_number = expanded.groupby(level=0).cumcount()
    expanded["comprehension_success"] = (
        question_number < expanded["comprehension_score"].to_numpy()
    ).astype(int)
    model = sm.GEE.from_formula(
        formula,
        groups="participant_id",
        data=expanded,
        family=sm.families.Binomial(),
        cov_struct=sm.cov_struct.Exchangeable(),
    )
    return model.fit(), data, formula


def interaction_summary(result, predictor):
    term = f"comprehension_score:{_term(predictor)}"
    if term not in result.params:
        term = f"{_term(predictor)}:comprehension_score"
    low, high = result.conf_int().loc[term]
    return {
        "term": term,
        "estimate": float(result.params[term]),
        "std_error": float(result.bse[term]),
        "p_value": float(result.pvalues[term]),
        "ci_low": float(low),
        "ci_high": float(high),
        "exponentiated_effect": float(np.exp(result.params[term])),
    }
