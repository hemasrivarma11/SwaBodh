from datetime import date

import pandas as pd

from swabodh.experiments import analyze_experiment, make_schedule, outcome_series
from swabodh.sample import generate_sample
from swabodh.trust import analyze_trust


def test_schedule_is_balanced_and_complete():
    schedule = make_schedule(date(2026, 1, 1), 14, seed=1)
    assert len(schedule) == 14
    conditions = [c for _, c in schedule]
    assert conditions.count("treatment") == 7
    assert conditions.count("control") == 7


def test_finds_the_hidden_caffeine_effect():
    df, schedule, truth = generate_sample(seed=7)
    df["date"] = pd.to_datetime(df["date"])
    trust = analyze_trust(df)
    days = pd.DataFrame([(str(d), c) for d, c in schedule], columns=["date", "condition"])
    outcomes, _ = outcome_series(trust, "sleep_minutes", exclude_unreliable=True)
    result = analyze_experiment(outcomes, days)
    assert result["verdict"] == "likely_increase"
    assert 10 < result["diff"] < 50  # true effect is 28 minutes


def test_says_insufficient_when_too_little_data():
    days = pd.DataFrame({"date": ["2026-01-01", "2026-01-02"], "condition": ["treatment", "control"]})
    outcomes = pd.DataFrame({"date": ["2026-01-01", "2026-01-02"], "value": [400.0, 410.0]})
    assert analyze_experiment(outcomes, days)["status"] == "insufficient"
