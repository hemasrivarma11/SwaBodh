"""Small helpers shared by every Streamlit page."""
import hashlib

import streamlit as st

from . import voice
from .db import init_db, load_measurements
from .explain import DISCLAIMER, is_gemini_configured
from .privacy import ai_enabled, set_voice_enabled, voice_enabled
from .theme import esc, inject_css, insight_cards
from .trust import analyze_trust

STATUS_EMOJI = {"reliable": "🟢", "caution": "🟡", "unreliable": "🔴", "single_source": "⚪"}
STATUS_TEXT = {
    "reliable": "Devices agree",
    "caution": "Devices differ a bit",
    "unreliable": "Devices disagree",
    "single_source": "One device only",
}


@st.cache_data(show_spinner=False)
def _cached_trust(df):
    return analyze_trust(df)


def load_all():
    init_db()
    df = load_measurements()
    if df.empty:
        return df, None
    return df, _cached_trust(df)


def require_data():
    df, trust = load_all()
    if trust is None:
        st.info("No data yet. Open the **Home** page in the left sidebar and click **Load demo data**.")
        st.stop()
    return df, trust


def sidebar_note():
    """Applies the theme (on every page) and draws the brand + privacy card in the sidebar."""
    inject_css()
    init_db()
    on = []
    if ai_enabled() and is_gemini_configured():
        on.append("Gemini")
    if voice_enabled() and voice.is_configured():
        on.append("ElevenLabs")
    if on:
        note = f"Sending text to {' and '.join(on)}. Never raw readings."
    else:
        note = "Online services are OFF. Nothing leaves this device."
    st.sidebar.markdown(
        "<div class='sb-brand'><div class='sb-logo'>🧭</div><b>SwaBodh</b><span>Know thyself 👋</span></div>"
        f"<div class='sb-privacy'><div style='font-size:1.6rem'>🔒</div><b>Private by default</b><p>{esc(note)}</p></div>",
        unsafe_allow_html=True,
    )


def voice_controls(key: str, text: str) -> None:
    """One 'Read aloud' control that always tells you what is missing instead of hiding."""
    if not voice.is_configured():
        st.caption("🔇 Voice is not set up yet.")
        if st.button("🩺 Why is there no voice?", key=f"vdiag_{key}"):
            for ok, title, hint in voice.setup_report():
                st.write(("✅ " if ok else "❌ ") + title + ("" if ok or not hint else f" — {hint}"))
            st.caption("After fixing .env, fully stop the app (Ctrl+C) and run `python -m streamlit run Home.py` again.")
        return
    if not voice_enabled():
        if st.button("🎙️ I agree: send this text to ElevenLabs", key=f"von_{key}", help="Sends only this short text to ElevenLabs."):
            set_voice_enabled(True)
            st.rerun()
        return

    audio_key = "audio_" + key + "_" + hashlib.sha1(text.encode("utf-8")).hexdigest()[:8]
    st.caption("Only the explanation text above is sent to ElevenLabs. No readings, no name.")
    clicked = st.button("🔊 Read aloud", key=f"voice_{key}")
    if clicked:
        with st.spinner("Creating the voice..."):
            audio, err = voice.speak(voice.to_speech_text(text))
        if err:
            st.error(err)
            st.session_state.pop(audio_key, None)
        else:
            st.session_state[audio_key] = audio
    audio = st.session_state.get(audio_key)
    if audio:
        st.audio(audio, format="audio/mp3", autoplay=clicked)


def explanation_block(key, build):
    """Button -> short coloured point cards (not a paragraph) + refresh + read aloud."""
    result_key = f"result_{key}"
    c1, c2, _ = st.columns([2, 1, 3], vertical_alignment="center")
    if c1.button("✨ Explain in plain language", key=f"explain_{key}", type="primary"):
        with st.spinner("Writing short points..."):
            st.session_state[result_key] = build()
    res = st.session_state.get(result_key)
    if res and c2.button("🔄 Refresh", key=f"refresh_{key}"):
        with st.spinner("Writing short points..."):
            res = st.session_state[result_key] = build()
    if not res:
        st.caption("Tap the button to get 3 to 5 short, easy points.")
        return

    points = insight_cards(res["text"])
    source = "✨ Written by Google Gemini" if res["source"] == "ai" else "🧩 Built-in explanation"
    st.markdown(f"<span class='sb-source'>{source}</span>", unsafe_allow_html=True)
    if res.get("note"):
        st.caption(res["note"])

    voice_controls(str(key), " ".join(points))

    with st.expander("📄 Show as plain text"):
        st.code(res["text"], language=None, wrap_lines=True)
    st.caption(DISCLAIMER)
