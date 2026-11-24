import streamlit as st

from swabodh import voice
from swabodh.db import init_db, table_counts
from swabodh.explain import is_gemini_configured, run_gemini_check
from swabodh.privacy import (
    ai_enabled,
    delete_everything,
    export_everything_json,
    export_measurements_csv,
    set_ai_enabled,
    set_voice_enabled,
    voice_enabled,
)
from swabodh.theme import card, card_title, hero, privacy_card
from swabodh.ui import sidebar_note

st.set_page_config(page_title="Privacy · SwaBodh", page_icon="🔒", layout="wide")
init_db()
sidebar_note()
hero("Privacy & data ownership", "You decide what stays here and what can leave. Everything is off by default.", kicker="YOUR DATA")

c1, c2 = st.columns(2)
c1.markdown(privacy_card("🔒", "Stays on this device", [
    "All raw readings and experiment results (local SQLite file)",
    "All analysis: agreement, drift, experiment statistics",
], "blue"), unsafe_allow_html=True)
c2.markdown(privacy_card("☁️", "Leaves only if you switch it on", [
    "Gemini: a few already-calculated facts, never raw readings or your name",
    "ElevenLabs: only the briefing text you can read and edit first",
], "pink"), unsafe_allow_html=True)
st.markdown("&nbsp;", unsafe_allow_html=True)
c3, c4 = st.columns(2)
c3.markdown(privacy_card("🎵", "Saved audio", [
    "Finished audio is cached in data/audio_cache so replaying is free",
    "Delete everything removes it",
], "yellow"), unsafe_allow_html=True)
c4.markdown(privacy_card("🔑", "Always yours", [
    "Export everything or delete everything at any time",
    "With a free Gemini key, Google may use submitted text to improve its products",
], "green"), unsafe_allow_html=True)

st.subheader("Your choices")
left, right = st.columns(2)
with left:
    with card("gemini"):
        card_title("✨ AI explanations (Google Gemini)")
        ai_on = st.toggle("Allow AI explanations", value=ai_enabled())
        set_ai_enabled(ai_on)
        if is_gemini_configured():
            st.success("Gemini is set up. The key is never shown or sent to your browser.")
        else:
            st.info("Gemini is not set up yet. Add GEMINI_API_KEY to .env and restart. Built-in explanations are used until then.")
        if st.button("✨ Test Gemini", key="gemini_test", disabled=not (ai_on and is_gemini_configured())):
            ok, message = run_gemini_check()
            (st.success if ok else st.error)(message)
with right:
    with card("voice"):
        card_title("🎙️ Voice briefings (ElevenLabs)")
        voice_on = st.toggle("Allow voice briefings", value=voice_enabled())
        set_voice_enabled(voice_on)
        if voice.is_configured():
            st.success("ElevenLabs key and voice ID found.")
        else:
            st.warning("ElevenLabs is not set up yet. See the checklist below.")

        with st.expander("🩺 Voice setup check", expanded=not voice.is_configured()):
            for ok, title, hint in voice.setup_report():
                st.write(("✅ " if ok else "❌ ") + title + ("" if ok or not hint else f" — {hint}"))
            st.write(("✅ " if voice_on else "❌ ") + "Voice switch above is ON")
            if st.button("🔊 Test my voice", key="voice_test", type="primary", disabled=not voice_on):
                with st.spinner("Asking ElevenLabs..."):
                    ok, message = voice.run_voice_check()
                (st.success if ok else st.error)(message)
                if ok:
                    audio, _ = voice.speak("SwaBodh voice is working.")
                    st.audio(audio, format="audio/mp3", autoplay=True)
            st.caption("After editing .env, stop the app (Ctrl+C) and run `python -m streamlit run Home.py` again.")

st.subheader("Take your data with you")
counts = table_counts()
if counts["measurements"] == 0:
    st.info("There is no data stored yet.")
else:
    d1, d2, _ = st.columns([1, 1, 2])
    d1.download_button("⬇️ Readings (CSV)", export_measurements_csv(), "swabodh_readings.csv", "text/csv", width="stretch")
    d2.download_button("⬇️ Everything (JSON)", export_everything_json(), "swabodh_export.json", "application/json", width="stretch")

st.subheader("Delete everything")
with card("delete"):
    st.caption("Removes all readings, experiments, settings and saved audio from this app. This cannot be undone.")
    confirm = st.toggle("I understand this permanently deletes my data")
    if st.button("🗑️ Delete all my data", disabled=not confirm):
        delete_everything()
        st.cache_data.clear()
        st.success("All data deleted.")
