"""Plain-language explanations.

Every number comes from trust.py and experiments.py, calculated on this device. If you switch
Google Gemini on (Privacy page), Gemini only REWORDS a short list of those finished facts into
friendlier sentences. We then check that Gemini did not invent any number; if it did, its answer
is thrown away and the built-in explanation is shown instead. Gemini never sees your raw readings.
"""
import re
import time

import requests

from .config import GEMINI_API_KEY, GEMINI_MODEL, label, unit

GEMINI_BACKUP_MODELS = ["gemini-3.6-flash"]  # tried if the main model is busy/unknown
GEMINI_URL = "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"

DISCLAIMER = (
    "SwaBodh is a self-awareness tool, not a medical device. It does not diagnose, treat or "
    "give medical advice. Talk to a qualified professional about health concerns."
)

SYSTEM_PROMPT = (
    "You are the explanation writer inside SwaBodh, a personal data-awareness app. "
    "Use ONLY the facts provided. Copy every number exactly as written; never add, round or "
    "calculate new numbers. Never mention causes, diagnoses, diseases, treatments or medical "
    "advice. If the facts show uncertainty, say so plainly. Write 3 to 5 short lines. Each line "
    "is ONE sentence of at most 20 words, in simple, calm language, separated by a line break. "
    "No bullet symbols, no numbering, no headings, no bold text."
)

STATUS_WORDS = {
    "reliable": "devices agree",
    "caution": "devices differ somewhat",
    "unreliable": "devices disagree strongly",
    "single_source": "only one device reported, so it cannot be cross-checked",
}

VERDICT_HEADLINE = {
    "likely_increase": "Likely higher on habit days",
    "likely_decrease": "Likely lower on habit days",
    "no_clear_effect": "No clear difference",
    "inconclusive": "Inconclusive so far",
    "insufficient": "Not enough data yet",
}

VERDICT_SENTENCE = {
    "likely_increase": (
        "The habit days were higher, and the gap is large compared with normal day-to-day ups and "
        "downs, so it is unlikely to be chance alone."
    ),
    "likely_decrease": (
        "The habit days were lower, and the gap is large compared with normal day-to-day ups and "
        "downs, so it is unlikely to be chance alone."
    ),
    "no_clear_effect": "There is no clear difference between habit days and usual days.",
    "inconclusive": (
        "There is a difference, but it is not yet strong enough to rule out chance. More days "
        "would make the answer clearer."
    ),
}
EXPERIMENT_CAVEAT = (
    "Days were assigned at random, which makes this a fair test for you personally, but it covers "
    "only a small number of days from one person."
)
TRUST_GUIDANCE = (
    "When devices disagree, treat that day's number as a rough guide and look at your own "
    "longer-term trend instead of a single reading."
)

DISAGREEMENT_NOTE = (
    "Disagreement between devices does not prove which device is wrong; any of them could be off."
)
_NUMBER = re.compile(r"\d+(?:\.\d+)?")


class GeminiError(Exception):
    """Raised with a message that is safe to show on screen (never contains the API key)."""


def is_gemini_configured() -> bool:
    return bool(GEMINI_API_KEY)

def run_gemini_check():
    """Sends a harmless fixed test sentence. Returns (ok, message)."""
    if not is_gemini_configured():
        return False, "No GEMINI_API_KEY found in .env."
    try:
        _call_gemini("Test: devices agreed on 90% of days.")
    except GeminiError as exc:
        return False, str(exc)
    return True, f"Gemini works. Key and model ({GEMINI_MODEL}) accepted."

def alert_sentence(a: dict) -> str:
    m = a["metric"]
    u = unit(m)
    direction = "higher" if a["raw_shift"] > 0 else "lower"
    size = abs(a["raw_shift"])
    if a["culprit"]:
        return (
            f"Drift alert for {label(m)}: your {a['culprit']} began reading differently from your "
            f"other devices around {a['start_date']}. It now reads about {size:.1f} {u} {direction} "
            f"than before, compared with the others."
        )
    x, y = a["sources"]
    return (
        f"Drift alert for {label(m)}: the relationship between your {x} and your {y} changed around "
        f"{a['start_date']}. The {x} now reads about {size:.1f} {u} {direction} than expected from "
        f"the {y}. It cannot be determined which device changed."
    )


def trust_facts(trust: dict) -> list:
    facts = []
    for _, r in trust["summary"].iterrows():
        if r["n_days"] > 0:
            facts.append(
                f"{label(r['metric'])}: devices were compared on {int(r['n_days'])} days and agreed on "
                f"{r['reliable_pct']:.0f}% of them. On the most recent day, {STATUS_WORDS[r['latest_status']]}."
            )
    for a in trust["alerts"]:
        facts.append(alert_sentence(a))
    bias = trust["bias"]
    for _, b in bias.iterrows():
        if abs(b["offset_pct"]) >= 5 and abs(b["offset"]) >= 1:
            facts.append(
                f"{label(b['metric'])}: your {b['source']} typically reads {abs(b['offset']):.0f} "
                f"{unit(b['metric'])} {'above' if b['offset'] > 0 else 'below'} the average of your devices."
            )
    return facts


def experiment_facts(name: str, metric: str, res: dict, n_excluded: int) -> list:
    u = unit(metric)
    return [
        f"Experiment: {name}. Outcome measured: {label(metric)} ({u}).",
        f"Days with the habit: {res['n_treatment']}. Usual days: {res['n_control']}.",
        f"Average on habit days: {res['mean_treatment']:.1f} {u}. Average on usual days: "
        f"{res['mean_control']:.1f} {u}. Difference: {res['diff']:+.1f} {u}.",
        f"95% interval for the difference: {res['ci_low']:+.1f} to {res['ci_high']:+.1f} {u}.",
        f"Estimated chance that the habit days were higher: {res['prob_positive'] * 100:.0f}%.",
        f"Days left out because devices strongly disagreed: {n_excluded}.",
        f"Result category: {VERDICT_HEADLINE[res['verdict']]}.",
    ]



def _gemini_status_message(status: int, detail: str = "") -> str:
    if status in (401, 403):
        base = "Gemini refused the API key. Check GEMINI_API_KEY in your .env file."
    elif status == 400:
        base = "Gemini rejected the request. Check GEMINI_API_KEY and GEMINI_MODEL in your .env file."
    elif status == 404:
        base = "Gemini does not recognise the model in GEMINI_MODEL. Set GEMINI_MODEL=gemini-3.8-flash in your .env file."
    elif status == 429:
        base = "Gemini's rate limit or free quota was reached. Try again in a minute."
    elif status >= 500:
        base = f"Gemini is busy or down right now (status {status}). Try again in a minute."
    else:
        base = f"Gemini returned an error (status {status})."
    return base + (f" Google says: {detail[:140]}" if detail else "")


def _google_detail(response) -> str:
    """Google's own error text (never contains your key)."""
    try:
        return str(response.json()["error"]["message"])
    except Exception:
        return ""


def _post_gemini(model: str, facts_text: str):
    return requests.post(
        GEMINI_URL.format(model=model),
        headers={"x-goog-api-key": GEMINI_API_KEY, "Content-Type": "application/json"},
        json={
            "systemInstruction": {"parts": [{"text": SYSTEM_PROMPT}]},
            "contents": [
                {"role": "user", "parts": [{"text": "FACTS:\n" + facts_text + "\n\nWrite the explanation now."}]}
            ],
            "generationConfig": {"temperature": 0.2, "maxOutputTokens": 2048},
        },
        timeout=30,
    )


def _call_gemini(facts_text: str) -> str:
    """Sends ONLY the calculated facts to Gemini. Retries busy errors, then tries backup models."""
    models = [GEMINI_MODEL] + [m for m in GEMINI_BACKUP_MODELS if m != GEMINI_MODEL]
    response = None
    for model in models:
        for attempt in range(3):
            try:
                response = _post_gemini(model, facts_text)
            except requests.RequestException as exc:
                raise GeminiError(f"Could not reach Gemini ({type(exc).__name__}). Check your internet connection.")
            if response.status_code == 200:
                break
            if response.status_code not in (404, 429, 500, 502, 503, 504):
                raise GeminiError(_gemini_status_message(response.status_code, _google_detail(response)))
            if attempt < 2:
                time.sleep(2 * (attempt + 1))  # briefly retry busy or unavailable models
        if response.status_code == 200:
            break
    if response is None or response.status_code != 200:
        raise GeminiError(_gemini_status_message(response.status_code, _google_detail(response)))
    try:
        parts = response.json()["candidates"][0]["content"]["parts"]
        text = "".join(p.get("text", "") for p in parts if not p.get("thought")).strip()
    except (KeyError, IndexError, TypeError, ValueError):
        raise GeminiError("Gemini returned an empty or blocked answer.")
    if not text:
        raise GeminiError("Gemini returned an empty or blocked answer.")
    return text


def _explain(facts: list, fallback: str, use_ai: bool) -> dict:
    def template(note):
        return {"text": fallback, "source": "template", "note": note}

    if not use_ai:
        return template("Gemini is switched off (Privacy page), so this is the built-in explanation.")
    if not is_gemini_configured():
        return template("No GEMINI_API_KEY is set in .env, so this is the built-in explanation.")
    facts_text = "\n".join(facts)
    try:
        text = _call_gemini(facts_text)
    except GeminiError as exc:
        return template(f"{exc} Showing the built-in explanation instead.")
    invented = set(_NUMBER.findall(text)) - (set(_NUMBER.findall(facts_text)) | {"95"})
    if invented:
        shown = ", ".join(sorted(invented)[:3])
        return template(f"Gemini wrote numbers that are not in your results ({shown}), so its answer was discarded.")
    return {"text": text, "source": "ai", "note": "Checked: every number comes from your calculated results."}


def explain_trust(trust: dict, use_ai: bool = False) -> dict:
    facts = trust_facts(trust) + [DISAGREEMENT_NOTE]
    fallback = " ".join(facts) + " " + TRUST_GUIDANCE
    res = _explain(facts, fallback, use_ai)
    if "does not prove which device" not in res["text"]:
        res["text"] += "\n" + DISAGREEMENT_NOTE  # always shown, even if Gemini leaves it out
    return res


def explain_experiment(name: str, metric: str, res: dict, n_excluded: int, use_ai: bool = False) -> dict:
    if res["status"] != "ok":
        text = (
            "There are not enough days with data yet. Each group (habit days and usual days) "
            "needs at least 3 days with readings before SwaBodh can compare them."
        )
        return {"text": text, "source": "template", "note": ""}
    facts = experiment_facts(name, metric, res, n_excluded)
    fallback = " ".join(facts[2:5]) + " " + VERDICT_SENTENCE[res["verdict"]] + " " + EXPERIMENT_CAVEAT
    return _explain(facts, fallback, use_ai)
