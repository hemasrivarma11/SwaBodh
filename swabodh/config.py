"""Central place for settings. Secrets are read from the .env file (or, when deployed, from the
host's secret store), never written in code."""
import os
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent.parent
ENV_PATH = ROOT / ".env"
ENV_FILE_FOUND = ENV_PATH.exists()
# override=True -> .env wins over stale variables set on your PC.
# utf-8-sig     -> survives the invisible BOM that Windows Notepad adds.
load_dotenv(ENV_PATH, override=True, encoding="utf-8-sig")
DATA_DIR = ROOT / "data"
DB_PATH = DATA_DIR / "swabodh.db"
AUDIO_CACHE_DIR = DATA_DIR / "audio_cache"


def _setting(name: str, default: str = "") -> str:
    """Environment variable first; then Streamlit's secret store (only exists when deployed)."""
    value = os.getenv(name)
    if value is None:
        try:
            import streamlit as st

            value = st.secrets.get(name)
        except Exception:
            value = None
    text = str(value if value is not None else default)
    # Remove spaces and any quote marks accidentally pasted around a key or ID.
    return text.strip().strip('"').strip("'").strip()


GEMINI_API_KEY = _setting("GEMINI_API_KEY")
GEMINI_MODEL = _setting("GEMINI_MODEL", "gemini-3.8-flash")

ELEVENLABS_API_KEY = _setting("ELEVENLABS_API_KEY")
ELEVENLABS_VOICE_ID = _setting("ELEVENLABS_VOICE_ID")
ELEVENLABS_MODEL_ID = _setting("ELEVENLABS_MODEL_ID", "eleven_multilingual_v2")

METRIC_LABELS = {
    "sleep_minutes": "Sleep duration",
    "deep_sleep_min": "Deep sleep",
    "resting_hr": "Resting heart rate",
    "hrv_ms": "Heart rate variability",
    "steps": "Steps",
}
METRIC_UNITS = {
    "sleep_minutes": "min",
    "deep_sleep_min": "min",
    "resting_hr": "bpm",
    "hrv_ms": "ms",
    "steps": "steps",
}


def label(metric: str) -> str:
    return METRIC_LABELS.get(metric, metric)


def unit(metric: str) -> str:
    return METRIC_UNITS.get(metric, "")
