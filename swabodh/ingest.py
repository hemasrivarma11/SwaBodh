"""Getting data in: validate a CSV and save it, or load the simulated demo data."""
import pandas as pd
import numpy as np

from .db import create_experiment, delete_all_data, init_db, list_experiments, save_measurements
from .sample import generate_sample

REQUIRED_COLUMNS = ["date", "source", "metric", "value"]
DEMO_EXPERIMENT_NAME = "No caffeine after 2 PM (demo)"


def clean(df: pd.DataFrame):
    missing = [c for c in REQUIRED_COLUMNS if c not in df.columns]
    if missing:
        raise ValueError(f"Your CSV is missing these columns: {', '.join(missing)}")
    out = df[REQUIRED_COLUMNS].copy()
    out["date"] = pd.to_datetime(out["date"], errors="coerce").dt.strftime("%Y-%m-%d")
    out["value"] = pd.to_numeric(out["value"], errors="coerce")
    out["source"] = out["source"].astype(str).str.strip().str.lower()
    out["metric"] = out["metric"].astype(str).str.strip().str.lower()
    before = len(out)
    out = out.dropna(subset=REQUIRED_COLUMNS)
    out = out[(out["source"] != "") & (out["metric"] != "")]
    out = out[np.isfinite(out["value"])]
    skipped_invalid = before - len(out)
    # The database key is (date, source, metric); retain the last repeated row.
    duplicate_mask = out.duplicated(subset=["date", "source", "metric"], keep="last")
    skipped_duplicates = int(duplicate_mask.sum())
    out = out.loc[~duplicate_mask]
    return out, skipped_invalid + skipped_duplicates


def import_csv(file_like):
    """Returns (rows_saved, rows_skipped)."""
    init_db()
    df = pd.read_csv(file_like)
    cleaned, skipped = clean(df)
    if cleaned.empty:
        raise ValueError("No valid rows found in this file.")
    return save_measurements(cleaned), skipped


def load_demo():
    """Replaces current data with simulated data. Returns the hidden 'truth' for testing."""
    init_db()
    delete_all_data(keep_settings=True)
    df, schedule, truth = generate_sample()
    save_measurements(df)
    if DEMO_EXPERIMENT_NAME not in list_experiments()["name"].tolist():
        create_experiment(DEMO_EXPERIMENT_NAME, "sleep_minutes", schedule)
    return truth
