from datetime import date, timedelta

import plotly.express as px
import streamlit as st

from swabodh.config import METRIC_LABELS, label, unit
from swabodh.db import create_experiment, get_experiment_days, list_experiments
from swabodh.experiments import analyze_experiment, make_schedule, outcome_series
from swabodh.explain import VERDICT_HEADLINE, explain_experiment
from swabodh.privacy import ai_enabled
from swabodh.theme import card, card_title, chips, hero, stat_cards, style_fig, verdict
from swabodh.ui import explanation_block, require_data, sidebar_note

st.set_page_config(page_title="Experiments · SwaBodh", page_icon="🧪", layout="wide")
sidebar_note()
hero("Personal Experiments", "Test a habit on yourself with randomised days, and see what the data can honestly say.", kicker="SELF-TESTS")

df, trust = require_data()

HABITS = {
    "No caffeine after 2 PM": "sleep_minutes",
    "Screens off 60 minutes before bed": "sleep_minutes",
    "20-minute evening walk": "hrv_ms",
    "Consistent bedtime": "deep_sleep_min",
}

tab_run, tab_analyze = st.tabs(["🚀 Start a new experiment", "📊 See results"])

with tab_run:
    with card("new"):
        card_title("Pick a habit", "We randomise the days so the test is fair.")
        with st.form("new_experiment", border=False):
            habit = st.selectbox("Habit to test", list(HABITS))
            metric = st.selectbox(
                "What should be measured?", list(METRIC_LABELS), format_func=label,
                index=list(METRIC_LABELS).index("sleep_minutes"),
            )
            nights = st.slider("How many days?", 10, 28, 14, step=2)
            start = st.date_input("Start date", value=date.today() + timedelta(days=1))
            submitted = st.form_submit_button("🎲 Create my randomised schedule", type="primary")
    if submitted:
        schedule = make_schedule(start, nights)
        create_experiment(habit, metric, schedule)
        st.toast("Experiment created!", icon="🧪")
        with card("plan"):
            card_title("Your plan", "Follow it, then import your device data to see results.")
            chips([
                (f"{d.strftime('%b %d')} · {'✅ Do it' if c == 'treatment' else '➖ Normal'}", "yes" if c == "treatment" else "no")
                for d, c in schedule
            ])
            st.caption("Days are randomised in pairs, so habit days and normal days are balanced.")

with tab_analyze:
    exps = list_experiments()
    if exps.empty:
        st.info("No experiments yet. Load the demo data on the app page, or start one in the first tab.")
        st.stop()
    names = {int(r["id"]): f"{r['name']} · {label(r['metric'])}" for _, r in exps.iterrows()}
    exp_id = st.selectbox("Experiment", list(names), format_func=lambda i: names[i])
    row = exps[exps["id"] == exp_id].iloc[0]
    metric = row["metric"]

    exclude = st.toggle("Ignore days when my devices strongly disagreed (recommended)", value=True)
    days = get_experiment_days(exp_id)
    outcomes, excluded = outcome_series(trust, metric, exclude)
    res = analyze_experiment(outcomes, days)

    if res["status"] != "ok":
        st.warning(
            f"Not enough data yet: {res['n_treatment']} habit days and {res['n_control']} usual days "
            "have readings. Each group needs at least 3."
        )
    else:
        headline = VERDICT_HEADLINE[res["verdict"]]
        verdict(headline, res["verdict"] in ("likely_increase", "likely_decrease"))

        u = unit(metric)
        stat_cards([
            {"icon": "✅", "label": "Habit days (average)", "value": f"{res['mean_treatment']:.1f} {u}", "tint": "green"},
            {"icon": "➖", "label": "Usual days (average)", "value": f"{res['mean_control']:.1f} {u}", "tint": "blue"},
            {"icon": "↔️", "label": "Difference", "value": f"{res['diff']:+.1f} {u}", "tint": "lav",
             "delta": f"95% range {res['ci_low']:+.1f} to {res['ci_high']:+.1f}"},
            {"icon": "🎲", "label": "Chance habit days were higher", "value": f"{res['prob_positive'] * 100:.0f}%", "tint": "yellow",
             "delta": f"{len(excluded)} day(s) left out"},
        ])

        with card("box"):
            card_title("Habit days vs usual days")
            merged = days.merge(outcomes, on="date")
            merged["Group"] = merged["condition"].map({"treatment": "Habit days", "control": "Usual days"})
            fig = px.box(merged, x="Group", y="value", color="Group", points="all",
                         color_discrete_map={"Habit days": "#7ed395", "Usual days": "#6aa6f5"},
                         labels={"value": f"{label(metric)} ({u})", "Group": ""})
            fig.update_layout(showlegend=False)
            st.plotly_chart(style_fig(fig, 340), width="stretch")

    with st.expander("📅 Show the schedule"):
        st.dataframe(days.rename(columns={"date": "Date", "condition": "Group"}), hide_index=True, width="stretch")

    with card("explain"):
        card_title("💬 In plain language", "Short points, easy to scan")
        explanation_block(
            f"exp_{exp_id}_{int(exclude)}",
            lambda: explain_experiment(row["name"], metric, res, len(excluded), ai_enabled()),
        )