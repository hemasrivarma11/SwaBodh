"""Simulated 3-device health data, so the app works without real devices.

Hidden truths built into the data (so we can check the app finds them):
  * The 'ring' resting heart rate / HRV shift part-way through (like a firmware change).
  * On one night the ring slipped off and reported far too little sleep.
  * In the last 28 days, 'avoiding late caffeine' really adds ~28 minutes of sleep.
"""
from datetime import date, timedelta

import numpy as np
import pandas as pd

from .experiments import make_schedule

N_DAYS = 60
EXPERIMENT_DAYS = 28
LAST_DAY = date(2026, 11, 21)  # fixed, so the demo gives the same results every time you run it


def generate_sample(n_days=N_DAYS, seed=7):
    rng = np.random.default_rng(seed)
    end = LAST_DAY
    dates = [end - timedelta(days=n_days - 1 - i) for i in range(n_days)]

    exp_dates = dates[-EXPERIMENT_DAYS:]
    schedule = make_schedule(exp_dates[0], EXPERIMENT_DAYS, seed=seed)
    condition = {d: c for d, c in schedule}

    drift_idx = n_days - 18
    bad_night_idx = n_days - 9

    rows = []

    def add(d, source, metric, value):
        if rng.random() < 0.03:  # a few missing readings, like real life
            return
        rows.append((d.isoformat(), source, metric, round(float(max(value, 0)), 1)))

    for i, d in enumerate(dates):
        avoid = condition.get(d) == "treatment"
        true_sleep = 420 + rng.normal(0, 14) + (28 if avoid else 0) + (15 if d.weekday() >= 5 else 0)
        true_deep = 0.11 * true_sleep + rng.normal(0, 4)
        true_rhr = 58 + rng.normal(0, 1.5)
        true_hrv = 52 + rng.normal(0, 4) + (3 if avoid else 0)
        true_steps = 8000 + rng.normal(0, 1800)

        ring_sleep = true_sleep - 5 + rng.normal(0, 8)
        ring_deep = true_deep + rng.normal(0, 3)
        if i == bad_night_idx:  # ring slipped off
            ring_sleep -= 110
            ring_deep -= 30
        ring_rhr = true_rhr - 1 + rng.normal(0, 0.8)
        ring_hrv = true_hrv + rng.normal(0, 2)
        if i >= drift_idx:  # firmware-style shift
            ring_rhr += 6
            ring_hrv -= 7

        add(d, "watch", "sleep_minutes", true_sleep + 10 + rng.normal(0, 10))
        add(d, "watch", "deep_sleep_min", true_deep * 1.6 + rng.normal(0, 5))
        add(d, "watch", "resting_hr", true_rhr + 1 + rng.normal(0, 1))
        add(d, "watch", "hrv_ms", 0.85 * true_hrv + rng.normal(0, 2.5))
        add(d, "watch", "steps", true_steps + rng.normal(0, 150))

        add(d, "ring", "sleep_minutes", ring_sleep)
        add(d, "ring", "deep_sleep_min", ring_deep)
        add(d, "ring", "resting_hr", ring_rhr)
        add(d, "ring", "hrv_ms", ring_hrv)

        add(d, "phone", "sleep_minutes", true_sleep + 25 + rng.normal(0, 35))
        add(d, "phone", "steps", true_steps * 1.08 + rng.normal(0, 400))

    df = pd.DataFrame(rows, columns=["date", "source", "metric", "value"])
    truth = {
        "drift_start": dates[drift_idx].isoformat(),
        "bad_night": dates[bad_night_idx].isoformat(),
        "true_sleep_effect_min": 28,
    }
    return df, schedule, truth
