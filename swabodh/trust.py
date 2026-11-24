"""Trust Layer: compare devices, flag unreliable days, detect drift, build a consensus.

Key idea: devices report different raw numbers (different bias and scale), so we learn how
the devices normally relate to each other during a reference period (the first 28 days) and then
watch for days or periods where that relationship breaks.
"""
import itertools

import numpy as np
import pandas as pd

REF_DAYS = 28          # days used as each device's personal reference
SPREAD_OK = 2.0        # devices within this many 'units' of each other -> reliable
SPREAD_CAUTION = 3.5   # above this -> unreliable; values between thresholds are caution
CUSUM_K = 0.75         # drift detector sensitivity
CUSUM_H = 6.0          # drift detector alarm threshold
MIN_DRIFT_DAYS = 14
MIN_SHIFT_SD = 1.5     # a drift must be at least this big (in normal-noise units)...
MIN_DAYS_AFTER = 5     # ...and must last at least this many days


def _wide(df, metric):
    sub = df[df["metric"] == metric]
    wide = sub.pivot_table(index="date", columns="source", values="value", aggfunc="mean")
    return wide.sort_index().dropna(axis=1, how="all")


def _reference(wide):
    ref = wide.iloc[:REF_DAYS]
    med = ref.median().fillna(wide.median())
    scale = (ref - med).abs().median() * 1.4826
    scale = scale.where(scale > 1e-9, ref.std())
    scale = scale.where(scale > 1e-9, 1.0).fillna(1.0)
    return med, scale


def _daily(z, metric):
    n = z.notna().sum(axis=1)
    spread = z.max(axis=1) - z.min(axis=1)
    status = pd.Series("single_source", index=z.index)
    multi = n >= 2
    status[multi & (spread <= SPREAD_OK)] = "reliable"
    status[multi & (spread > SPREAD_OK) & (spread <= SPREAD_CAUTION)] = "caution"
    status[multi & (spread > SPREAD_CAUTION)] = "unreliable"
    return pd.DataFrame(
        {
            "date": z.index.strftime("%Y-%m-%d"),
            "metric": metric,
            "n_sources": n.to_numpy(),
            "spread": spread.to_numpy(),
            "status": status.to_numpy(),
        }
    )


def _cusum(s):
    """Two-sided CUSUM. Returns (alarm_index, start_index, direction) or None."""
    pos = neg = 0.0
    zero_pos = zero_neg = -1
    for i, x in enumerate(s):
        if np.isnan(x):
            continue
        pos = max(0.0, pos + x - CUSUM_K)
        neg = max(0.0, neg - x - CUSUM_K)
        if pos == 0.0:
            zero_pos = i
        if neg == 0.0:
            zero_neg = i
        if pos > CUSUM_H:
            return i, zero_pos + 1, "up"
        if neg > CUSUM_H:
            return i, zero_neg + 1, "down"
    return None


def _residual_gap(y, x, ref_end):
    """How far is y from what we would predict from x? The prediction rule is learned on the
    reference period only, so it ignores each device's bias and scale."""
    pair = pd.DataFrame({"y": y, "x": x}).dropna()
    if len(pair) < MIN_DRIFT_DAYS:
        return None
    ref = pair[pair.index <= ref_end]
    if len(ref) < 10:
        return None
    slope, intercept = np.polyfit(ref["x"], ref["y"], 1)
    resid = pair["y"] - (intercept + slope * pair["x"])
    ref_resid = resid[ref.index]
    sd0 = float(np.sqrt((ref_resid**2).sum() / max(len(ref_resid) - 2, 1)))
    sd0 = max(sd0, 0.01 * abs(float(ref["y"].mean())), 1e-6)
    return resid, sd0


def _detect_shift(resid, sd0):
    """Runs the drift detector on a residual series. Returns a dict or None.
    Small or short-lived shifts are ignored, so we only warn about real, lasting changes."""
    s = np.clip(resid.to_numpy() / sd0, -3, 3)  # one odd day must not trigger an alarm
    offset = 0
    while offset < len(s):
        hit = _cusum(s[offset:])
        if hit is None:
            return None
        alarm_i, start_i, direction = hit[0] + offset, hit[1] + offset, hit[2]
        shift_sd = float(np.mean(s[start_i:]))
        if abs(shift_sd) >= MIN_SHIFT_SD and len(s) - start_i >= MIN_DAYS_AFTER:
            before, after = resid.iloc[:start_i], resid.iloc[start_i:]
            base = before.mean() if len(before) else 0.0
            return {
                "start": resid.index[start_i],
                "alarm": resid.index[alarm_i],
                "direction": direction,
                "raw_shift": float(after.mean() - base),
                "shift_sd": shift_sd,
            }
        offset = alarm_i + 1
    return None


def _pair_drift(wide, a, b, ref_end):
    out = _residual_gap(wide[a], wide[b], ref_end)
    if out is None:
        return None
    hit = _detect_shift(*out)
    if hit:
        hit["pair"] = (a, b)
    return hit


def _drift_alerts(wide, metric, ref_end):
    sources = list(wide.columns)
    hits = []
    for a, b in itertools.combinations(sources, 2):
        hit = _pair_drift(wide, a, b, ref_end)
        if hit:
            hits.append(hit)
    if not hits:
        return []

    culprit = None
    if len(sources) == 3 and len(hits) == 2:
        common = set(hits[0]["pair"]) & set(hits[1]["pair"])
        if len(common) == 1:
            culprit = common.pop()

    alerts = []
    if culprit:
        others = [s for s in sources if s != culprit]
        out = _residual_gap(wide[culprit], wide[others].mean(axis=1), ref_end)
        start = min(h["start"] for h in hits)
        raw_shift = float("nan")
        if out is not None:
            resid = out[0]
            before, after = resid[resid.index < start], resid[resid.index >= start]
            if len(before) and len(after):
                raw_shift = float(after.mean() - before.mean())
        alerts.append(
            {
                "metric": metric,
                "culprit": culprit,
                "sources": sources,
                "start_date": start.strftime("%Y-%m-%d"),
                "alarm_date": min(h["alarm"] for h in hits).strftime("%Y-%m-%d"),
                "raw_shift": raw_shift,
                "shift_sd": max(abs(h["shift_sd"]) for h in hits),
            }
        )
    else:
        for h in hits:
            alerts.append(
                {
                    "metric": metric,
                    "culprit": None,
                    "sources": list(h["pair"]),
                    "start_date": h["start"].strftime("%Y-%m-%d"),
                    "alarm_date": h["alarm"].strftime("%Y-%m-%d"),
                    "raw_shift": h["raw_shift"],
                    "shift_sd": abs(h["shift_sd"]),
                }
            )
    return alerts


def analyze_trust(df):
    """df columns: date (datetime), source, metric, value. Returns a dictionary of results."""
    daily_parts, alerts, bias_rows, cons_parts, summary_rows = [], [], [], [], []

    for metric in sorted(df["metric"].unique()):
        wide = _wide(df, metric)
        if wide.empty:
            continue
        med, scale = _reference(wide)
        z = (wide - med) / scale

        # Consensus: remove each device's typical bias, then average the devices.
        adjusted = wide - med + med.mean()
        cons = pd.DataFrame(
            {"date": wide.index.strftime("%Y-%m-%d"), "metric": metric, "value": adjusted.mean(axis=1).to_numpy()}
        )
        cons_parts.append(cons)

        for source in wide.columns:
            offset = float(med[source] - med.mean())
            bias_rows.append(
                {
                    "metric": metric,
                    "source": source,
                    "offset": offset,
                    "offset_pct": 100 * offset / abs(med.mean()) if med.mean() else 0.0,
                }
            )

        daily = _daily(z, metric)
        daily_parts.append(daily)

        if wide.shape[1] >= 2:
            ref_end = wide.index[min(REF_DAYS, len(wide)) - 1]
            alerts.extend(_drift_alerts(wide, metric, ref_end))

        compared = daily[daily["n_sources"] >= 2]
        reliable_pct = 100 * (compared["status"] == "reliable").mean() if len(compared) else float("nan")
        summary_rows.append(
            {
                "metric": metric,
                "n_sources": wide.shape[1],
                "n_days": len(compared),
                "reliable_pct": reliable_pct,
                "latest_date": daily["date"].iloc[-1],
                "latest_status": daily["status"].iloc[-1],
            }
        )

    return {
        "daily": pd.concat(daily_parts, ignore_index=True) if daily_parts else pd.DataFrame(),
        "consensus": pd.concat(cons_parts, ignore_index=True) if cons_parts else pd.DataFrame(),
        "alerts": alerts,
        "bias": pd.DataFrame(bias_rows),
        "summary": pd.DataFrame(summary_rows),
    }
