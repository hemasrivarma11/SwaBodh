import pandas as pd
import plotly.express as px
import streamlit as st

from swabodh.config import label, unit
from swabodh.explain import DISAGREEMENT_NOTE, alert_sentence, explain_trust
from swabodh.privacy import ai_enabled
from swabodh.theme import (
    METRIC_STYLE, PASTEL, STATUS_PILL, card, card_title, chips, esc, hero, list_rows, style_fig, demo_badge
)
from swabodh.ui import STATUS_TEXT, explanation_block, require_data, sidebar_note

st.set_page_config(page_title="Trust Layer · SwaBodh", page_icon="🛡️", layout="wide")
sidebar_note()
hero("Trust Layer", "Do your devices agree? Has one quietly changed? Which readings can you rely on?", kicker="DATA QUALITY")

df, trust = require_data()
daily, summary, bias, alerts = trust["daily"], trust["summary"], trust["bias"], trust["alerts"]

with card("overview"):
    card_title("Overview", "How much your devices agreed, per metric")
    rows = []
    for _, r in summary.iterrows():
        icon, tint = METRIC_STYLE.get(r["metric"], ("📊", "lav"))
        pct = None if pd.isna(r["reliable_pct"]) else float(r["reliable_pct"])
        sub = f"{int(r['n_sources'])} devices · {int(r['n_days'])} days compared"
        if pct is not None:
            sub += f" · agreed on {pct:.0f}% of days"
        rows.append({"icon": icon, "tint": tint, "title": label(r["metric"]), "sub": sub, "pct": pct,
                     "pill": (STATUS_TEXT[r["latest_status"]], STATUS_PILL[r["latest_status"]])})
    list_rows(rows)
    st.caption("ℹ️ " + DISAGREEMENT_NOTE)

if alerts:
    st.subheader("⚠️ Drift alerts")
    cells = "".join(
        f"<div class='sb-insight tint-yellow'><div class='iico ico-yellow'>⚠️</div>"
        f"<div><div class='itag'>{esc(label(a['metric']))}</div><div class='itext'>{esc(alert_sentence(a))}</div></div></div>"
        for a in alerts
    )
    st.markdown(f"<div class='sb-insights'>{cells}</div>", unsafe_allow_html=True)
else:
    st.success("✅ No lasting drift detected between your devices.")

metric_list = summary["metric"].tolist()
metric = st.pills("Look closer at one metric", metric_list, format_func=label, default=metric_list[0], key="trust_metric") or metric_list[0]

with card("lines"):
    card_title(f"{label(metric)} · every device", "Red bands = days devices strongly disagreed")
    sub = df[df["metric"] == metric]
    fig = px.line(sub, x="date", y="value", color="source", color_discrete_sequence=PASTEL, labels={"value": f"{label(metric)} ({unit(metric)})", "date": ""})
    fig.update_traces(line=dict(width=2.6))
    flagged = daily[(daily["metric"] == metric) & (daily["status"] == "unreliable")]["date"].tolist()
    for d in flagged[:40]:
        day = pd.to_datetime(d)
        fig.add_vrect(x0=day - pd.Timedelta(hours=12), x1=day + pd.Timedelta(hours=12), fillcolor="#fb8fb9", opacity=0.22, line_width=0)
    st.plotly_chart(style_fig(fig, 360), width="stretch")

left, right = st.columns(2)
with left:
    with card("agree"):
        card_title("How often did devices agree?")
        counts = daily[daily["metric"] == metric]["status"].value_counts()
        total = max(int(counts.sum()), 1)
        list_rows([
            {"icon": {"reliable": "🟢", "caution": "🟡", "unreliable": "🔴", "single_source": "⚪"}[s], "tint": "lav",
             "title": STATUS_TEXT[s], "sub": f"{int(n)} day{'s' if int(n) != 1 else ''}", "pct": 100 * n / total}
            for s, n in counts.items()
        ])
with right:
    with card("bias"):
        card_title("Typical bias of each device", "Compared with the average of your devices")
        b = bias[bias["metric"] == metric]
        list_rows([
            {"icon": "📟", "tint": "blue", "title": str(r["source"]),
             "sub": f"Usually reads {r['offset']:+.1f} {unit(metric)} vs average"}
            for _, r in b.iterrows()
        ])

if flagged:
    with st.expander(f"📅 Days to treat with caution ({len(flagged)})"):
        chips([(d, "no") for d in flagged])

with card("explain"):
    card_title("💬 In plain language", "Short points, easy to scan")
    explanation_block("trust", lambda: explain_trust(trust, ai_enabled()))