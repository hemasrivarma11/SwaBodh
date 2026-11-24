"""Builds the short script that is read aloud. Every sentence comes from calculated results."""
from .config import label, unit
from .explain import (
    EXPERIMENT_CAVEAT,
    TRUST_GUIDANCE,
    VERDICT_HEADLINE,
    VERDICT_SENTENCE,
    DISAGREEMENT_NOTE,
    alert_sentence,
)

SPOKEN_DISCLAIMER = "SwaBodh is a self-awareness tool, not a medical device, and this is not medical advice."


def trust_script(trust: dict) -> str:
    parts = []
    summary = trust["summary"]
    compared = summary[summary["n_days"] > 0].sort_values("reliable_pct")
    if compared.empty:
        parts.append("Only one device is reporting, so your readings cannot be cross-checked yet.")
    else:
        worst, best = compared.iloc[0], compared.iloc[-1]
        parts.append(
            f"Your devices agreed most on {label(best['metric'])}, on {best['reliable_pct']:.0f}% of days, "
            f"and least on {label(worst['metric'])}, on {worst['reliable_pct']:.0f}% of days."
        )
        cautious = summary[summary["latest_status"] == "unreliable"]["metric"].tolist()
        if cautious:
            names = ", ".join(label(m) for m in cautious)
            parts.append(f"On the most recent day, treat these readings with caution: {names}.")
    alerts = trust["alerts"]
    if alerts:
        parts.extend(alert_sentence(a) for a in alerts[:3])
    else:
        parts.append("I found no lasting drift between your devices.")
    parts.append(DISAGREEMENT_NOTE)
    parts.append(TRUST_GUIDANCE)
    return " ".join(parts)


def experiment_script(name: str, metric: str, res: dict, n_excluded: int) -> str:
    if res["status"] != "ok":
        return (
            f"Your experiment, {name}, does not have enough days with data yet. "
            "Each group needs at least 3 days with readings."
        )
    u = unit(metric)
    return (
        f"Your experiment: {name}. Outcome: {label(metric)}. "
        f"On habit days the average was {res['mean_treatment']:.1f} {u}, and on usual days it was "
        f"{res['mean_control']:.1f} {u}, a difference of {res['diff']:+.1f} {u}. "
        f"The 95% range for that difference is {res['ci_low']:+.1f} to {res['ci_high']:+.1f} {u}. "
        f"Result: {VERDICT_HEADLINE[res['verdict']]}. {VERDICT_SENTENCE[res['verdict']]} "
        f"{EXPERIMENT_CAVEAT}"
    )


def full_briefing(parts: list) -> str:
    return "Here is your SwaBodh briefing. " + " ".join(parts) + " " + SPOKEN_DISCLAIMER
