"""Privacy controls: consent switches, export everything, delete everything."""
import json

from . import voice
from .db import (
    delete_all_data,
    get_experiment_days,
    get_setting,
    list_experiments,
    load_measurements,
    set_setting,
)

DATA_FLOW_TEXT = """
**What stays on this device:** all raw readings, experiment schedules and results (a local SQLite
file). All analysis (device agreement, drift detection, experiment statistics) is calculated on
this device.

**What can leave, only if you switch it on below:**
- **Google Gemini (AI explanations):** a short list of already-calculated facts (for example
  "ring heart rate shifted by about 6 bpm around 2026-11-04") so Gemini can reword them. Never your raw
  readings and never your name. SwaBodh rejects any Gemini answer containing a number that is not in
  your results. *Note: with a free Gemini API key, Google may use submitted content to improve its
  products. A key on a billed Google project is treated as a paid service.*
- **ElevenLabs (voice):** only the text of your spoken briefing, so it can be read aloud. You can read
  and edit that text before sending.

**Saved audio:** finished audio is cached in the `data/audio_cache` folder on this device so that
replaying costs nothing. "Delete everything" removes it.

**Always yours:** export everything or delete everything at any time.
"""


def ai_enabled() -> bool:
    return get_setting("ai_consent", "false") == "true"


def set_ai_enabled(value: bool) -> None:
    set_setting("ai_consent", "true" if value else "false")


def voice_enabled() -> bool:
    return get_setting("voice_consent", "false") == "true"


def set_voice_enabled(value: bool) -> None:
    set_setting("voice_consent", "true" if value else "false")


def export_measurements_csv() -> bytes:
    df = load_measurements()
    df["date"] = df["date"].dt.strftime("%Y-%m-%d")
    return df.to_csv(index=False).encode("utf-8")


def export_everything_json() -> bytes:
    df = load_measurements()
    df["date"] = df["date"].dt.strftime("%Y-%m-%d")
    experiments = []
    for _, row in list_experiments().iterrows():
        experiments.append(
            {
                "id": int(row["id"]),
                "name": row["name"],
                "metric": row["metric"],
                "days": get_experiment_days(int(row["id"])).to_dict(orient="records"),
            }
        )
    payload = {"measurements": df.to_dict(orient="records"), "experiments": experiments}
    return json.dumps(payload, indent=2).encode("utf-8")


def delete_everything() -> None:
    delete_all_data(keep_settings=False)
    voice.clear_audio_cache()
