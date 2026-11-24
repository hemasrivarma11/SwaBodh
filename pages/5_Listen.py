import hashlib

import streamlit as st

from swabodh import voice
from swabodh.briefing import experiment_script, full_briefing, trust_script
from swabodh.config import label
from swabodh.db import get_experiment_days, list_experiments
from swabodh.experiments import analyze_experiment, outcome_series
from swabodh.explain import DISCLAIMER
from swabodh.privacy import voice_enabled
from swabodh.ui import require_data, sidebar_note

st.set_page_config(page_title="Listen · SwaBodh", page_icon="🎧", layout="wide")
sidebar_note()
st.title("🎧 Listen to your insights")
st.caption("A short spoken briefing built only from your calculated results, voiced by ElevenLabs.")

df, trust = require_data()

include_trust = st.checkbox("Data trust and drift alerts", value=True)
exps = list_experiments()
chosen = []
if not exps.empty:
    names = {int(r["id"]): f"{r['name']} · {label(r['metric'])}" for _, r in exps.iterrows()}
    chosen = st.multiselect(
        "Experiments to include", list(names), default=list(names)[:1], format_func=lambda i: names[i]
    )

parts = []
if include_trust:
    parts.append(trust_script(trust))
for exp_id in chosen:
    row = exps[exps["id"] == exp_id].iloc[0]
    outcomes, excluded = outcome_series(trust, row["metric"], True)
    res = analyze_experiment(outcomes, get_experiment_days(exp_id))
    parts.append(experiment_script(row["name"], row["metric"], res, len(excluded)))

if not parts:
    st.info("Pick at least one thing to include in your briefing.")
    st.stop()

script = full_briefing(parts)
st.subheader("What will be read aloud")
st.caption("This is the text that gets sent to ElevenLabs. You can edit or delete anything before creating the audio.")
digest = hashlib.sha1(script.encode("utf-8")).hexdigest()[:10]
text = st.text_area("Script", value=script, height=260, key=f"script_{digest}", label_visibility="collapsed")
spoken = voice.to_speech_text(text)
spoken_id = hashlib.sha1(spoken.encode("utf-8")).hexdigest()

if voice.is_cached(spoken):
    st.caption(f"{len(spoken)} characters. Already created before, so replaying it uses no ElevenLabs credits.")
else:
    st.caption(f"{len(spoken)} characters. Creating new audio uses ElevenLabs credits.")

if not voice.is_configured():
    st.warning("ElevenLabs is not set up yet. Add ELEVENLABS_API_KEY and ELEVENLABS_VOICE_ID to your .env file, then restart the app.")
elif not voice_enabled():
    st.warning("Voice is switched off. Turn it on in the **Privacy** page to create audio.")
else:
    if st.button("🔊 Create audio", type="primary"):
        with st.spinner("Asking ElevenLabs to read this aloud..."):
            audio, err = voice.speak(spoken)
        if err:
            st.error(err)
        else:
            st.session_state["listen_audio"] = (spoken_id, audio)

saved = st.session_state.get("listen_audio")
if saved and saved[0] == spoken_id:
    st.audio(saved[1], format="audio/mp3")
    st.download_button("⬇️ Download MP3", saved[1], "swabodh_briefing.mp3", "audio/mpeg")

st.caption(DISCLAIMER)
