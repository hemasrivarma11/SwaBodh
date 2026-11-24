import streamlit as st

from swabodh import ingest
from swabodh.db import init_db, set_setting, table_counts
from swabodh.ui import sidebar_note

st.set_page_config(page_title="SwaBodh", page_icon="🧭", layout="wide")
init_db()
sidebar_note()

st.title("🧭 SwaBodh · Know Thyself")
st.caption("Your data. Your intelligence. Built to be honest about what it does not know.")

st.markdown(
    """
**1. Trust Layer.** Combines your devices, checks whether they agree, and warns you when a reading
(or a device) cannot be trusted.

**2. Personal Experiments.** Test a habit, such as no caffeine after 2 PM, using randomised days, and
see whether it made a difference for you, with honest uncertainty.

**3. Plain-language insights.** Numbers are calculated here; Google Gemini can optionally reword them (never your raw readings).

**4. Listen.** Hear your insights as a short spoken briefing, voiced by ElevenLabs (optional, and
only after you switch it on in the Privacy page).

Use the pages in the left sidebar. Start by loading data below.
"""
)

st.subheader("Get data in")
left, right = st.columns(2)

with left:
    st.markdown("**Option A: simulated demo data** (3 devices, 60 days)")
    st.caption("Replaces the data currently stored in this app. Simulated, not real health data.")
    if st.button("Load demo data", type="primary"):
        ingest.load_demo()
        set_setting("data_mode", "demo")
        st.cache_data.clear()
        st.success("Demo data loaded. Open Dashboard, Trust Layer or Experiments in the sidebar.")

with right:
    st.markdown("**Option B: your own CSV**")
    st.caption("Columns: date, source, metric, value. One row per reading.")
    uploaded = st.file_uploader("Choose a CSV file", type=["csv"])
    if uploaded is not None and st.button("Import this file"):
        try:
            saved, skipped = ingest.import_csv(uploaded)
            set_setting("data_mode", "csv")
            st.cache_data.clear()
            st.success(f"Imported {saved} readings ({skipped} invalid or duplicate rows skipped).")
        except ValueError as exc:
            st.error(str(exc))

with st.expander("CSV format example"):
    st.code(
        "date,source,metric,value\n"
        "2026-11-01,watch,sleep_minutes,431\n"
        "2026-11-01,ring,sleep_minutes,418\n"
        "2026-11-01,watch,resting_hr,59\n"
        "2026-11-01,ring,resting_hr,57\n",
        language="text",
    )
    st.caption("Known metrics: sleep_minutes, deep_sleep_min, resting_hr, hrv_ms, steps.")

counts = table_counts()
st.divider()
c1, c2, c3 = st.columns(3)
c1.metric("Readings stored", f"{counts['measurements']:,}")
c2.metric("Experiments", counts["experiments"])
c3.metric("Experiment days", counts["experiment_days"])
