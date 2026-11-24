# SwaBodh (Know Thyself)

🌐 Live Demo: https://swabodh-6zzuwkgrqkrps9mdlvwnxk.streamlit.app/

💻 Source Code: https://github.com/hemasrivarma11/SwaBodh

A privacy-first personal health intelligence app (hackathon MVP).

- **Trust Layer:** compares readings from several devices, flags unreliable days, detects device drift.
- **Personal Experiments:** randomised self-experiments (e.g. no caffeine after 2 PM) with honest uncertainty.
- **Plain-language insights:** every number is calculated on your computer. Optionally, Google Gemini rewords those finished facts; any answer containing a number not in your results is rejected and replaced by a built-in explanation.
- **Listen:** a spoken briefing of your insights, voiced by ElevenLabs. Optional and off by default.
- **Privacy:** local SQLite storage, consent switch, export and delete.

SwaBodh is a self-awareness tool, not a medical device. It does not diagnose or give medical advice.

## Architecture
Deployment architecture: SwaBodh runs as a Python Streamlit application, hosted on Streamlit Community Cloud. Its SQLite storage runs in the hosted application environment, not on each visitor's personal device. Google Gemini and ElevenLabs are optional external integrations requiring user consent. The only external services are Google Gemini
(optional, sends only calculated facts) and ElevenLabs (optional, sends only briefing text). Both are
off by default and need a consent switch on the Privacy page. API keys are read from `.env` on the
server side, sent only in request headers, and never reach the browser.

    CSV / simulated data -> SQLite (local) -> trust.py -> experiments.py -> explain.py / briefing.py -> pages
                                                      |                              |
                                              Gemini (optional)        voice.py -> ElevenLabs (optional)

## Setup
Run these commands from the project directory (the folder containing `Home.py`):

    python -m venv .venv
    .\.venv\Scripts\Activate.ps1
    pip install -r requirements.txt
    Copy-Item .env.example .env      # then add GEMINI_API_KEY (and optionally ElevenLabs key + voice ID)
    python -m streamlit run Home.py

On macOS or Linux, activate the environment with `source .venv/bin/activate` instead of the
PowerShell command above. The app stores its local database in `data/swabodh.db`. Loading demo data
replaces the currently stored readings and experiments; CSV imports add or update readings using
the `(date, source, metric)` key. Invalid and duplicate rows in a CSV are skipped.

## Test
    python -m pytest -q

Note: with a free Gemini key, Google may use submitted content to improve its products. Demo data only.

### Optional ElevenLabs voice setup

For a free ElevenLabs account, community Voice Library voices are not available through the API.
Create and save a voice under **Voices → My Voices → Add a new voice → Voice Design**, then copy
that saved voice's ID. Put the ID in `ELEVENLABS_VOICE_ID` in `.env` and set
`ELEVENLABS_MODEL_ID=eleven_v3`. Add your API key to `ELEVENLABS_API_KEY`, save the file, restart
the app, and use **Test my voice** on the Privacy page. Voice Design preview and speech generation
use your ElevenLabs credits.
