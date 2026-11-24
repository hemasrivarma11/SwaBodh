import pandas as pd

from swabodh.sample import generate_sample
from swabodh.trust import analyze_trust


def _run():
    df, schedule, truth = generate_sample(seed=7)
    df["date"] = pd.to_datetime(df["date"])
    return analyze_trust(df), truth


def test_finds_the_hidden_drift():
    trust, truth = _run()
    drifted = {a["metric"] for a in trust["alerts"]}
    assert "resting_hr" in drifted
    alert = next(a for a in trust["alerts"] if a["metric"] == "resting_hr")
    start = pd.Timestamp(alert["start_date"])
    assert abs((start - pd.Timestamp(truth["drift_start"])).days) <= 3
    assert alert["raw_shift"] > 3  # the ring reads several bpm higher


def test_no_false_alarm_on_steps():
    trust, _ = _run()
    assert "steps" not in {a["metric"] for a in trust["alerts"]}


def test_flags_the_night_the_ring_slipped_off():
    trust, truth = _run()
    daily = trust["daily"]
    row = daily[(daily["metric"] == "sleep_minutes") & (daily["date"] == truth["bad_night"])]
    assert row["status"].iloc[0] == "unreliable"


def test_consensus_exists_for_every_metric():
    trust, _ = _run()
    assert set(trust["consensus"]["metric"]) == {"sleep_minutes", "deep_sleep_min", "resting_hr", "hrv_ms", "steps"}
