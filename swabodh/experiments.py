"""Personal Experiments: randomise days, then measure whether a habit made a difference."""
import random
from datetime import timedelta

import numpy as np
import pandas as pd
from scipy import stats

MIN_PER_GROUP = 3


def make_schedule(start, n_days, seed=None):
    """Randomised schedule in pairs of consecutive days: in each pair one day gets the
    habit ('treatment') and the other is a normal day ('control'). Pairing keeps the two
    groups balanced across the calendar. Returns a list of (date, condition)."""
    rng = random.Random(seed)
    schedule = []
    day = start
    remaining = n_days
    while remaining > 0:
        if remaining >= 2:
            pair = ["treatment", "control"]
            rng.shuffle(pair)
            schedule.append((day, pair[0]))
            schedule.append((day + timedelta(days=1), pair[1]))
            day += timedelta(days=2)
            remaining -= 2
        else:
            schedule.append((day, rng.choice(["treatment", "control"])))
            remaining -= 1
    return schedule


def outcome_series(trust, metric, exclude_unreliable=True):
    """Pulls the outcome from the Trust Layer's consensus values. Days where the devices
    strongly disagree can be left out, so the experiment is not fooled by bad readings."""
    cons = trust["consensus"]
    cons = cons[cons["metric"] == metric][["date", "value"]]
    excluded = []
    if exclude_unreliable:
        daily = trust["daily"]
        bad = daily[(daily["metric"] == metric) & (daily["status"] == "unreliable")]["date"]
        bad = set(bad.tolist())
        excluded = sorted(d for d in cons["date"] if d in bad)
        cons = cons[~cons["date"].isin(bad)]
    return cons.reset_index(drop=True), excluded


def analyze_experiment(outcomes, days):
    """outcomes: DataFrame[date, value]; days: DataFrame[date, condition].
    Returns a dictionary of calculated results (difference, 95% interval, verdict)."""
    merged = days.merge(outcomes, on="date", how="inner").dropna(subset=["value"])
    t = merged.loc[merged["condition"] == "treatment", "value"].to_numpy(float)
    c = merged.loc[merged["condition"] == "control", "value"].to_numpy(float)
    result = {"n_treatment": len(t), "n_control": len(c), "status": "ok"}
    if len(t) < MIN_PER_GROUP or len(c) < MIN_PER_GROUP:
        result["status"] = "insufficient"
        result["verdict"] = "insufficient"
        return result

    diff = float(t.mean() - c.mean())
    v_t = t.var(ddof=1) / len(t)
    v_c = c.var(ddof=1) / len(c)
    se = float(np.sqrt(v_t + v_c))
    if se < 1e-9:
        # With constant outcomes, Welch's degrees of freedom is undefined. Return
        # a finite degenerate interval and direction probability instead of NaNs.
        ci_low = ci_high = diff
        prob_positive = 0.5 if diff == 0 else (1.0 if diff > 0 else 0.0)
    else:
        dof = (v_t + v_c) ** 2 / ((v_t**2) / (len(t) - 1) + (v_c**2) / (len(c) - 1))
        tcrit = float(stats.t.ppf(0.975, dof))
        ci_low, ci_high = diff - tcrit * se, diff + tcrit * se
        prob_positive = float(stats.t.cdf(diff / se, dof))
    pooled_sd = float(np.sqrt((t.var(ddof=1) + c.var(ddof=1)) / 2))

    if ci_low > 0:
        verdict = "likely_increase"
    elif ci_high < 0:
        verdict = "likely_decrease"
    elif abs(diff) < se:
        verdict = "no_clear_effect"
    else:
        verdict = "inconclusive"

    result.update(
        mean_treatment=float(t.mean()),
        mean_control=float(c.mean()),
        diff=diff,
        ci_low=float(ci_low),
        ci_high=float(ci_high),
        prob_positive=prob_positive,
        cohens_d=diff / pooled_sd if pooled_sd > 0 else 0.0,
        verdict=verdict,
    )
    return result
