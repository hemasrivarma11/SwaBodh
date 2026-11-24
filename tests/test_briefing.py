import pandas as pd

from swabodh.briefing import experiment_script, full_briefing, trust_script
from swabodh.experiments import analyze_experiment, outcome_series
from swabodh.explain import explain_experiment, explain_trust
from swabodh.sample import generate_sample
from swabodh.trust import analyze_trust


def _setup():
    df, schedule, truth = generate_sample(seed=7)
    df["date"] = pd.to_datetime(df["date"])
    trust = analyze_trust(df)
    days = pd.DataFrame([(str(d), c) for d, c in schedule], columns=["date", "condition"])
    outcomes, excluded = outcome_series(trust, "sleep_minutes", True)
    return trust, analyze_experiment(outcomes, days), len(excluded), truth


def test_trust_script_mentions_the_real_drift():
    trust, _, _, truth = _setup()
    script = trust_script(trust)
    assert "Drift alert" in script
    assert truth["drift_start"] in script


def test_experiment_script_contains_calculated_numbers():
    trust, res, n_excl, _ = _setup()
    script = experiment_script("No caffeine", "sleep_minutes", res, n_excl)
    assert f"{res['diff']:+.1f}" in script
    assert "Likely higher on habit days" in script


def test_full_briefing_has_disclaimer():
    assert "not a medical device" in full_briefing(["Hello."])


def test_explanations_are_local_and_have_text():
    trust, res, n_excl, _ = _setup()
    assert explain_trust(trust)["source"] == "template"
    assert explain_experiment("N", "sleep_minutes", res, n_excl)["text"]
