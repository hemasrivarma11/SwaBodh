import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from swabodh.config import label, unit
from swabodh.explain import explain_trust
from swabodh.privacy import ai_enabled
from swabodh.theme import (
    METRIC_STYLE, PASTEL, STATUS_PILL, banner, card, card_title, hero, stat_cards, style_fig,demo_badge
)
from swabodh.ui import STATUS_TEXT, explanation_block, require_data, sidebar_note

st.set_page_config(page_title="Dashboard · SwaBodh", page_icon="📊", layout="wide")
sidebar_note()
hero("Dashboard", "Your devices combined into one view, with a data-quality flag on every metric.", kicker="OVERVIEW")

df, trust = require_data()
cons, summary, daily = trust["consensus"], trust["summary"], trust["daily"]
metrics = summary["metric"].tolist()

tiles = []
for m in metrics:
    series = cons[cons["metric"] == m].sort_values("date")["value"].reset_index(drop=True)
    latest = series.iloc[-1]
    prior = series.iloc[-8:-1].mean() if len(series) > 1 else float("nan")
    arrow = "" if pd.isna(prior) else ("↗ " if latest >= prior else "↘ ") + f"{latest - prior:+.1f} vs prior 7 days"
    status = summary.loc[summary["metric"] == m, "latest_status"].iloc[0]
    icon, tint = METRIC_STYLE.get(m, ("📊", "lav"))
    tiles.append(
        {"icon": icon, "label": label(m), "value": f"{latest:,.0f} {unit(m)}", "tint": tint,
         "delta": arrow, "pill": (STATUS_TEXT[status], STATUS_PILL[status])}
    )
stat_cards(tiles)

choice = st.pills("Pick a metric", metrics, format_func=label, default=metrics[0], key="dash_metric")
choice = choice or metrics[0]
series = cons[cons["metric"] == choice].copy()
series["date"] = pd.to_datetime(series["date"])
series = series.sort_values("date")

left, right = st.columns([3, 2])
with left:
    with card("last7"):
        card_title(f"{label(choice)} · last 7 days", "Devices combined, bias removed")
        last7 = series.tail(7).copy()
        last7["day"] = last7["date"].dt.strftime("%a")
        fig = go.Figure(go.Bar(x=last7["day"], y=last7["value"], marker=dict(color=PASTEL[: len(last7)], cornerradius=10),
                               hovertemplate="%{x}: %{y:,.0f}<extra></extra>"))
        st.plotly_chart(style_fig(fig, 280), width="stretch")
with right:
    with card("donut"):
        card_title("How often devices agreed", label(choice))
        counts = daily[daily["metric"] == choice]["status"].value_counts()
        names = [STATUS_TEXT[s] for s in counts.index]
        colors = {"reliable": "#7ed395", "caution": "#f7cd5a", "unreliable": "#fb8fb9", "single_source": "#c9c6e6"}
        fig = go.Figure(go.Pie(labels=names, values=counts.values, hole=0.64, sort=False, textinfo="none",
                               hovertemplate="%{label}: %{value} days (%{percent})<extra></extra>",
                               marker=dict(colors=[colors[s] for s in counts.index], line=dict(color="#fffaf7", width=3))))
        agree = 100 * counts.get("reliable", 0) / max(int(counts.sum()), 1)
        fig.add_annotation(text=f"<b>{agree:.0f}%</b><br>agree", x=0.5, y=0.5, showarrow=False, font=dict(size=22, color="#1c1b4d"))
        st_fig = style_fig(fig, 300)
        st_fig.update_layout(legend=dict(orientation="h", x=0.5, xanchor="center", y=-0.05, yanchor="top", font=dict(size=11)))
        st.plotly_chart(st_fig, width="stretch")

with card("trend"):
    card_title(f"{label(choice)} · full trend", "Red x = a day to treat with caution")
    fig = px.line(series, x="date", y="value", labels={"value": f"{label(choice)} ({unit(choice)})", "date": ""})
    fig.update_traces(line=dict(color="#7c5cf0", width=3, shape="spline"), fill="tozeroy", fillcolor="rgba(167,139,250,.10)")
    bad_dates = pd.to_datetime(daily[(daily["metric"] == choice) & (daily["status"] == "unreliable")]["date"])
    marks = series[series["date"].isin(bad_dates)]
    fig.add_scatter(x=marks["date"], y=marks["value"], mode="markers",
                    marker=dict(size=11, color="#f56fa0", symbol="x"), name="Devices strongly disagreed")
    st.plotly_chart(style_fig(fig, 340), width="stretch")

with card("explain"):
    card_title("💬 In plain language", "Short points, easy to scan")
    explanation_block("dashboard", lambda: explain_trust(trust, ai_enabled()))

banner("🧪", "Try a personal experiment", "Test a habit with randomised days and see what the data can honestly say.")
st.page_link("pages/3_Experiments.py", label="Start an experiment", icon="🧪")