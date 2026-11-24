"""SwaBodh look and feel: soft lavender background, cream cards, pastel tiles, pill buttons."""
from .db import get_setting
import html
import re

import streamlit as st

PASTEL = ["#a98bf5", "#fb8fb9", "#f9a65a", "#f7cd5a", "#7ed395", "#6aa6f5", "#8fdcd0"]
TINTS = ["blue", "pink", "yellow", "green", "lav"]

CSS = """
@import url('https://fonts.googleapis.com/css2?family=Nunito:wght@400;600;700;800&family=Plus+Jakarta+Sans:wght@600;700;800&display=swap');
:root{--navy:#1c1b4d;--muted:#6d6c93;--purple:#7c5cf0;--cream:#fdf6f1;--card:#fffaf7;--line:rgba(124,92,240,.10);--shadow:0 10px 28px rgba(110,90,200,.13);}
.stApp{background:linear-gradient(160deg,#b4b3f9 0%,#a2a1f4 55%,#9a98f0 100%) !important;font-family:'Nunito',sans-serif;color:var(--navy);}
header[data-testid="stHeader"]{background:transparent !important;}
[data-testid="stAppDeployButton"], [data-testid="stToolbarActions"]{display:none !important;}
[data-testid="stMainBlockContainer"], .block-container{background:var(--cream);border-radius:34px;max-width:1180px;width:calc(100% - 44px);margin:18px auto 28px auto;padding:2.2rem 2.4rem 2.6rem 2.4rem !important;box-shadow:0 18px 50px rgba(80,60,170,.22), inset 0 1px 0 rgba(255,255,255,.9);}
.stApp p, .stApp label, .stApp li, .stApp button, .stApp input, .stApp textarea,
.stApp [data-baseweb] *, .stApp [data-testid="stMarkdownContainer"] *{font-family:'Nunito',sans-serif;}
.stApp [data-testid="stIconMaterial"], .stApp .material-symbols-rounded{font-family:'Material Symbols Rounded' !important;}
h1,h2,h3,h4,.stApp h1,.stApp h2,.stApp h3{font-family:'Plus Jakarta Sans','Nunito',sans-serif !important;color:var(--navy) !important;letter-spacing:-.02em;}
h1{font-weight:800 !important;font-size:2.3rem !important;} h2,h3{font-weight:800 !important;}
.stApp [data-testid="stCaptionContainer"], .stApp small{color:var(--muted) !important;}
hr{border-color:var(--line) !important;}

/* sidebar */
section[data-testid="stSidebar"]{background:transparent !important;border:none !important;}
section[data-testid="stSidebar"] > div{background:linear-gradient(180deg,#9395f6 0%,#7f80ea 100%) !important;border-radius:32px;margin:18px 0 18px 14px;height:calc(100vh - 36px) !important;box-shadow:0 14px 36px rgba(70,60,170,.35), inset 0 1px 0 rgba(255,255,255,.45);}
section[data-testid="stSidebar"] *{color:#fff;}
[data-testid="stSidebarContent"]{display:flex;flex-direction:column;position:relative;}
[data-testid="stSidebarHeader"]{position:absolute;top:.5rem;right:.6rem;padding:0 !important;height:auto !important;z-index:5;width:auto;}
[data-testid="stLogoSpacer"], [data-testid="stSidebarNavSeparator"]{display:none !important;}
[data-testid="stSidebarUserContent"]{order:-1;padding:.6rem 1rem 0 1rem !important;}
[data-testid="stSidebarNav"]{order:0;margin-top:.4rem;}
a[data-testid="stSidebarNavLink"]{border-radius:18px !important;padding:.62rem .9rem !important;margin:3px 8px !important;font-weight:700;transition:all .18s ease;}
a[data-testid="stSidebarNavLink"], a[data-testid="stSidebarNavLink"] *{color:#fff !important;font-weight:700 !important;}
a[data-testid="stSidebarNavLink"]:hover{background:rgba(255,255,255,.18) !important;transform:translateX(3px);}
a[data-testid="stSidebarNavLink"][aria-current="page"]{background:#fffaf7 !important;box-shadow:0 6px 16px rgba(60,50,150,.25);}
a[data-testid="stSidebarNavLink"][aria-current="page"], a[data-testid="stSidebarNavLink"][aria-current="page"] *{color:var(--purple) !important;}
.sb-brand{text-align:center;padding:.6rem 0 .2rem 0;}
.sb-logo{width:74px;height:74px;margin:0 auto 6px auto;border-radius:50%;background:#fffaf7;display:flex;align-items:center;justify-content:center;font-size:2.2rem;box-shadow:0 8px 20px rgba(60,50,150,.3);}
.sb-brand b{display:block;font-family:'Plus Jakarta Sans',sans-serif;font-size:1.35rem;color:#fff;}
.sb-brand span{color:#e9e7ff;font-size:.95rem;}
.sb-privacy{margin:10px 12px 6px 12px;padding:14px 14px 12px 14px;border-radius:22px;background:linear-gradient(160deg,#ffd9e6,#ffc9dc);text-align:center;box-shadow:0 8px 18px rgba(60,50,150,.22);}
.sb-privacy, .sb-privacy *{color:#3d2a5a !important;}
.sb-privacy b{font-family:'Plus Jakarta Sans',sans-serif;font-size:1rem;}
.sb-privacy p{margin:.25rem 0 0 0;font-size:.82rem;line-height:1.35;}

/* buttons */
.stButton > button, .stDownloadButton > button, [data-testid="stFormSubmitButton"] > button, a[data-testid="stPageLink-NavLink"]{border-radius:999px !important;font-weight:800 !important;padding:.55rem 1.3rem !important;border:1.5px solid rgba(124,92,240,.25) !important;background:#fff !important;color:var(--purple) !important;box-shadow:0 5px 14px rgba(110,90,200,.12);transition:all .18s ease;}
.stButton > button:hover, .stDownloadButton > button:hover, a[data-testid="stPageLink-NavLink"]:hover{transform:translateY(-2px);box-shadow:0 9px 20px rgba(110,90,200,.22);border-color:var(--purple) !important;}
.stButton > button[kind="primary"], [data-testid="stBaseButton-primary"], [data-testid="stFormSubmitButton"] > button[kind="primaryFormSubmit"]{background:linear-gradient(135deg,#a07bf8,#7c5cf0) !important;color:#fff !important;border:none !important;box-shadow:0 9px 22px rgba(124,92,240,.42);}
.stButton > button[kind="primary"] *, [data-testid="stBaseButton-primary"] *{color:#fff !important;}
.stButton > button:disabled{opacity:.5;}
a[data-testid="stPageLink-NavLink"] p{color:var(--purple) !important;font-weight:800 !important;}

/* inputs, tabs, expanders */
[data-baseweb="select"] > div, .stTextArea textarea, .stDateInput input, .stTextInput input{border-radius:16px !important;background:#fff !important;border:1.5px solid var(--line) !important;}
[data-testid="stTab"], button[data-baseweb="tab"]{border-radius:999px !important;margin-right:6px;padding:.45rem 1.1rem !important;font-weight:800 !important;border-bottom:none !important;background:#fff;box-shadow:0 4px 10px rgba(110,90,200,.10);}
[data-testid="stTab"][aria-selected="true"], button[data-baseweb="tab"][aria-selected="true"]{background:linear-gradient(135deg,#a07bf8,#7c5cf0) !important;}
[data-testid="stTab"][aria-selected="true"] *, button[data-baseweb="tab"][aria-selected="true"] *{color:#fff !important;}
[data-testid="stTab"] > div[data-rac], [data-baseweb="tab-highlight"], [data-baseweb="tab-border"]{display:none !important;}
[role="tablist"]{border:none !important;box-shadow:none !important;gap:6px;padding-bottom:.5rem;}
[data-testid="stExpander"]{border-radius:20px !important;border:1.5px solid var(--line) !important;background:var(--card);}
[data-testid="stAlert"]{border-radius:20px !important;border:none !important;}
[data-testid="stDataFrame"]{border-radius:18px;overflow:hidden;}
[data-testid="stPills"] button, [data-testid="stButtonGroup"] button{border-radius:999px !important;font-weight:800 !important;}

/* cards: st.container(key="card-...") */
div[class*="st-key-card-"]{background:var(--card);border-radius:26px;padding:1.1rem 1.3rem 1.2rem 1.3rem;box-shadow:var(--shadow);border:1px solid rgba(255,255,255,.9);}
.sb-card-title{font-family:'Plus Jakarta Sans',sans-serif;font-weight:800;font-size:1.08rem;color:var(--navy);margin:0 0 .5rem 0;}
.sb-card-sub{color:var(--muted);font-size:.88rem;margin:-.3rem 0 .6rem 0;}

/* hero + banner */
.sb-hero{position:relative;overflow:hidden;border-radius:28px;padding:1.9rem 2rem;margin:.2rem 0 1.2rem 0;background:linear-gradient(120deg,#ffe3ee 0%,#f6dcf5 45%,#dcd2fb 100%);box-shadow:var(--shadow);display:flex;align-items:center;justify-content:space-between;gap:1rem;min-height:170px;}
.sb-hero h2{font-size:2.3rem !important;line-height:1.08;margin:0 0 .5rem 0 !important;}
.sb-hero p{color:#4b4a73;font-size:1.02rem;margin:0;max-width:430px;line-height:1.45;}
.sb-kicker{display:inline-block;background:rgba(255,255,255,.75);color:var(--purple);font-weight:800;font-size:.78rem;padding:.22rem .7rem;border-radius:999px;margin-bottom:.6rem;letter-spacing:.04em;}
.sb-hero-art{position:relative;min-width:230px;height:130px;}
.sb-hero-art .tile{position:absolute;width:78px;height:78px;border-radius:22px;display:flex;align-items:center;justify-content:center;font-size:2.3rem;box-shadow:0 12px 22px rgba(90,70,190,.28);animation:float 4s ease-in-out infinite;}
.sb-hero-art .t1{left:6px;top:36px;background:linear-gradient(145deg,#ffd27a,#ffb23f);transform:rotate(-9deg);}
.sb-hero-art .t2{left:68px;top:0;background:linear-gradient(145deg,#8fb8ff,#5f8cf5);transform:rotate(6deg);animation-delay:.6s;}
.sb-hero-art .t3{left:132px;top:30px;background:linear-gradient(145deg,#ff9fc2,#f56fa0);transform:rotate(-4deg);animation-delay:1.2s;}
.sb-hero-art .plant{position:absolute;right:-8px;top:-10px;font-size:3.6rem;filter:drop-shadow(0 8px 8px rgba(60,120,80,.3));}
.sb-hero-art .sp{position:absolute;color:#f7cd5a;font-size:1.5rem;animation:twinkle 2.4s ease-in-out infinite;}
.sb-hero-art .s1{left:112px;top:-6px;} .sb-hero-art .s2{left:210px;top:84px;font-size:1rem;animation-delay:.8s;}
@keyframes float{0%,100%{translate:0 0}50%{translate:0 -7px}}
@keyframes twinkle{0%,100%{opacity:.35;scale:.8}50%{opacity:1;scale:1.15}}
.sb-banner{border-radius:26px;padding:1.1rem 1.5rem;margin:1.1rem 0 .2rem 0;display:flex;align-items:center;gap:1rem;background:linear-gradient(120deg,#e4d9fd,#d4c7fb);box-shadow:var(--shadow);}
.sb-banner .big{font-size:2.4rem;}
.sb-banner b{font-family:'Plus Jakarta Sans',sans-serif;font-size:1.15rem;display:block;}
.sb-banner span{color:#4b4a73;font-size:.92rem;}

/* stat tiles */
.sb-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(168px,1fr));gap:14px;margin:.4rem 0 1.1rem 0;}
.sb-stat{border-radius:24px;padding:1rem 1.1rem;box-shadow:var(--shadow);border:1px solid rgba(255,255,255,.85);transition:transform .18s ease;}
.sb-stat:hover{transform:translateY(-3px);}
.sb-ico{width:44px;height:44px;border-radius:14px;display:flex;align-items:center;justify-content:center;font-size:1.35rem;margin-bottom:.55rem;box-shadow:0 6px 12px rgba(0,0,0,.12);}
.sb-stat-label{font-weight:700;color:#3c3b66;font-size:.92rem;}
.sb-stat-value{font-family:'Plus Jakarta Sans',sans-serif;font-weight:800;font-size:1.6rem;color:var(--navy);line-height:1.15;}
.sb-grid.compact .sb-stat-value{font-size:1.12rem;line-height:1.25;min-height:2.8rem;}
.sb-stat-delta{font-size:.8rem;font-weight:700;color:#5a45c8;margin-top:.15rem;}
.tint-blue{background:linear-gradient(160deg,#e3edff,#d6e5ff);} .ico-blue{background:linear-gradient(145deg,#6aa6f5,#4f8cf5);}
.tint-pink{background:linear-gradient(160deg,#ffe6ef,#ffd9e6);} .ico-pink{background:linear-gradient(145deg,#ff9fc2,#f56fa0);}
.tint-yellow{background:linear-gradient(160deg,#fff4d6,#ffeab8);} .ico-yellow{background:linear-gradient(145deg,#ffd27a,#f5b73c);}
.tint-green{background:linear-gradient(160deg,#ddf6e8,#cdf0dd);} .ico-green{background:linear-gradient(145deg,#5fd3a0,#34c08a);}
.tint-lav{background:linear-gradient(160deg,#ebe3fe,#ded2fc);} .ico-lav{background:linear-gradient(145deg,#b79bfa,#8b5cf6);}

/* pills, chips, rows */
.sb-pill{display:inline-block;padding:.2rem .7rem;border-radius:999px;font-size:.78rem;font-weight:800;margin-top:.4rem;}
.p-ok{background:#d4f1dc;color:#2e9d5b;} .p-warn{background:#ffe6b8;color:#b9770e;} .p-bad{background:#ffd8dc;color:#d6455d;} .p-info{background:#d6e5ff;color:#3b6fd8;} .p-gray{background:#e8e6f5;color:#6d6c93;}
.sb-chips{display:flex;flex-wrap:wrap;gap:8px;margin:.3rem 0;}
.sb-chip{padding:.35rem .8rem;border-radius:999px;font-size:.82rem;font-weight:700;background:#fff;border:1.5px solid var(--line);color:#4b4a73;}
.sb-chip.yes{background:#e6f7ec;color:#2e9d5b;border-color:#bfe8cd;} .sb-chip.no{background:#f1eefb;color:#6d6c93;}
.sb-row{display:flex;align-items:center;gap:.9rem;padding:.7rem .4rem;border-bottom:1px solid var(--line);}
.sb-row:last-child{border-bottom:none;}
.sb-row .rico{width:46px;height:46px;border-radius:15px;display:flex;align-items:center;justify-content:center;font-size:1.35rem;flex:none;}
.sb-row .rmain{flex:1;min-width:0;}
.sb-row .sb-pill{min-width:140px;text-align:center;flex:none;}
.sb-row .rtitle{font-weight:800;color:var(--navy);} .sb-row .rsub{font-size:.82rem;color:var(--muted);}
.sb-bar{height:9px;border-radius:99px;background:#ece8fb;overflow:hidden;margin-top:.35rem;}
.sb-bar > i{display:block;height:100%;border-radius:99px;background:linear-gradient(90deg,#a98bf5,#7c5cf0);}

/* insight cards */
.sb-insights{display:grid;grid-template-columns:repeat(auto-fit,minmax(250px,1fr));gap:14px;margin:.6rem 0 .8rem 0;}
.sb-insight{border-radius:22px;padding:.95rem 1.1rem;display:flex;gap:.85rem;align-items:flex-start;box-shadow:var(--shadow);border:1px solid rgba(255,255,255,.85);transition:transform .18s ease;}
.sb-insight:hover{transform:translateY(-3px);}
.sb-insight .iico{width:40px;height:40px;border-radius:13px;display:flex;align-items:center;justify-content:center;font-size:1.2rem;flex:none;box-shadow:0 5px 10px rgba(0,0,0,.1);}
.sb-insight .itag{font-size:.72rem;font-weight:800;text-transform:uppercase;letter-spacing:.07em;color:#5a45c8;}
.sb-insight .itext{font-weight:600;color:#2b2a58;line-height:1.4;font-size:.95rem;margin-top:.1rem;}
.sb-source{display:inline-block;font-size:.78rem;font-weight:800;padding:.2rem .7rem;border-radius:999px;background:#ece8fb;color:#5a45c8;margin-right:6px;}
.sb-verdict{border-radius:24px;padding:1.1rem 1.4rem;font-family:'Plus Jakarta Sans',sans-serif;font-weight:800;font-size:1.25rem;box-shadow:var(--shadow);margin:.4rem 0 1rem 0;display:flex;align-items:center;gap:.8rem;}
.v-good{background:linear-gradient(120deg,#d9f5e4,#c7efd9);color:#1f7a4a;} .v-neutral{background:linear-gradient(120deg,#e3edff,#d6e5ff);color:#2f5bb7;}
.sb-privcard{border-radius:24px;padding:1.1rem 1.2rem;box-shadow:var(--shadow);height:100%;}
.sb-privcard h4{margin:.3rem 0 .4rem 0 !important;font-size:1.05rem !important;}
.sb-privcard ul{margin:.2rem 0 0 1.1rem;padding:0;color:#3c3b66;font-size:.9rem;line-height:1.5;}
.sb-demo{display:inline-block;background:#fff1c9;color:#8a5a00;border:2px dashed #f5b73c;padding:.4rem 1rem;border-radius:999px;font-weight:800;letter-spacing:.05em;font-size:.85rem;margin:0 0 .9rem 0;}
@media (max-width:900px){ .sb-hero{flex-direction:column;align-items:flex-start;} [data-testid="stMainBlockContainer"]{padding:1.2rem !important;} }
"""

METRIC_STYLE = {
    "sleep_minutes": ("😴", "blue"),
    "deep_sleep_min": ("🌙", "lav"),
    "resting_hr": ("❤️", "pink"),
    "hrv_ms": ("📈", "green"),
    "steps": ("👟", "yellow"),
}
STATUS_PILL = {"reliable": "p-ok", "caution": "p-warn", "unreliable": "p-bad", "single_source": "p-gray"}


def inject_css() -> None:
    st.markdown(f"<style>{CSS}</style>", unsafe_allow_html=True)


def esc(text) -> str:
    return html.escape(str(text))


def card(name: str):
    """A rounded cream card. Use as:  with card('trend'): ..."""
    return st.container(key=f"card-{name}")


def card_title(title: str, sub: str = "") -> None:
    st.markdown(
        f"<div class='sb-card-title'>{esc(title)}</div>" + (f"<div class='sb-card-sub'>{esc(sub)}</div>" if sub else ""),
        unsafe_allow_html=True,
    )


def hero(title: str, subtitle: str, kicker: str = "", art: bool = True, big: bool = False) -> None:
    art_html = (
        "<div class='sb-hero-art'><span class='sp s1'>✦</span><span class='sp s2'>✦</span>"
        "<div class='tile t1'>😴</div><div class='tile t2'>💓</div><div class='tile t3'>👟</div>"
        "<span class='plant'>🌿</span></div>"
        if art else ""
    )
    k = f"<span class='sb-kicker'>{esc(kicker)}</span><br>" if kicker else ""
    size = "" if big else " style='font-size:1.9rem !important'"
    st.markdown(
        f"<div class='sb-hero'><div>{k}<h2{size}>{title}</h2><p>{esc(subtitle)}</p></div>{art_html}</div>",
        unsafe_allow_html=True,
    )


def banner(emoji: str, title: str, subtitle: str) -> None:
    st.markdown(
        f"<div class='sb-banner'><div class='big'>{emoji}</div><div><b>{esc(title)}</b><span>{esc(subtitle)}</span></div></div>",
        unsafe_allow_html=True,
    )


def stat_cards(items: list, compact: bool = False) -> None:
    """items: dicts with icon, label, value, tint, optional delta and pill=(text, css_class)."""
    cells = []
    for it in items:
        tint = it.get("tint", "lav")
        delta = f"<div class='sb-stat-delta'>{esc(it['delta'])}</div>" if it.get("delta") else ""
        pill = f"<span class='sb-pill {it['pill'][1]}'>{esc(it['pill'][0])}</span>" if it.get("pill") else ""
        cells.append(
            f"<div class='sb-stat tint-{tint}'><div class='sb-ico ico-{tint}'>{it['icon']}</div>"
            f"<div class='sb-stat-label'>{esc(it['label'])}</div>"
            f"<div class='sb-stat-value'>{esc(it['value'])}</div>{delta}{pill}</div>"
        )
    st.markdown(f"<div class='sb-grid{' compact' if compact else ''}'>" + "".join(cells) + "</div>", unsafe_allow_html=True)


def list_rows(rows: list) -> None:
    """rows: dicts with icon, tint, title, sub, optional pill=(text, css) and pct (0-100 progress bar)."""
    out = []
    for r in rows:
        bar = ""
        if r.get("pct") is not None:
            bar = f"<div class='sb-bar'><i style='width:{max(0, min(100, r['pct'])):.0f}%'></i></div>"
        pill = f"<span class='sb-pill {r['pill'][1]}' style='margin:0'>{esc(r['pill'][0])}</span>" if r.get("pill") else ""
        out.append(
            f"<div class='sb-row'><div class='rico tint-{r.get('tint', 'lav')}'>{r['icon']}</div>"
            f"<div class='rmain'><div class='rtitle'>{esc(r['title'])}</div><div class='rsub'>{esc(r.get('sub', ''))}</div>{bar}</div>{pill}</div>"
        )
    st.markdown("".join(out), unsafe_allow_html=True)


def chips(items: list) -> None:
    """items: (text, css_class) pairs, css_class '' / 'yes' / 'no'."""
    st.markdown(
        "<div class='sb-chips'>" + "".join(f"<span class='sb-chip {c}'>{esc(t)}</span>" for t, c in items) + "</div>",
        unsafe_allow_html=True,
    )


def verdict(text: str, good: bool) -> None:
    st.markdown(
        f"<div class='sb-verdict {'v-good' if good else 'v-neutral'}'><span>{'🎉' if good else '🔎'}</span>{esc(text)}</div>",
        unsafe_allow_html=True,
    )


def privacy_card(emoji: str, title: str, points: list, tint: str) -> str:
    lis = "".join(f"<li>{esc(p)}</li>" for p in points)
    return f"<div class='sb-privcard tint-{tint}'><div style='font-size:1.8rem'>{emoji}</div><h4>{esc(title)}</h4><ul>{lis}</ul></div>"

def demo_badge() -> None:
    """Shows the DEMO label unless real CSV data was imported."""
    if get_setting("data_mode", "demo") == "demo":
        st.markdown("<span class='sb-demo'>🧪 DEMO MODE – SIMULATED HEALTH DATA</span>", unsafe_allow_html=True)

# ---- short insight cards (instead of paragraphs) ----
_TAGS = [
    ("drift alert", "🌊", "Drift"),
    ("typically reads", "⚖️", "Device bias"),
    ("agreed on", "🤝", "Agreement"),
    ("interval", "📏", "Range"),
    ("chance that", "🎲", "Chance"),
    ("average on", "📊", "Averages"),
    ("random", "🎯", "Fair test"),
    ("rough guide", "💡", "Tip"),
    ("not enough", "⏳", "Need more data"),
    ("no clear difference", "🤷", "No clear effect"),
    ("habit days were", "🧪", "Verdict"),
    ("not yet strong", "🧪", "Verdict"),
    ("cannot be cross-checked", "🔍", "One device"),
]
_SPLIT = re.compile(r"(?<=[.!?])\s+(?=[A-Z0-9])")


def split_points(text: str) -> list:
    """Turns a paragraph (or Gemini's one-sentence lines) into short separate points."""
    points = []
    for line in re.split(r"\n+", text.strip()):
        line = re.sub(r"^[\-\*\u2022\d\.\)\s]+(?=[A-Z])", "", line.strip())
        for p in (x.strip() for x in _SPLIT.split(line) if x.strip()):
            if points and p.startswith("On the most recent day"):
                points[-1] += " " + p  # keep "latest day" notes with their metric
            else:
                points.append(p)
    return points


def _card_html(points: list, start: int = 0) -> str:
    cells = []
    for i, p in enumerate(points, start=start):
        low = p.lower()
        emoji, tag = next(((e, t) for k, e, t in _TAGS if k in low), ("✨", "Insight"))
        tint = TINTS[i % len(TINTS)]
        cells.append(
            f"<div class='sb-insight tint-{tint}'><div class='iico ico-{tint}'>{emoji}</div>"
            f"<div><div class='itag'>{esc(tag)}</div><div class='itext'>{esc(p)}</div></div></div>"
        )
    return "<div class='sb-insights'>" + "".join(cells) + "</div>"


def insight_cards(text: str, max_visible: int = 6) -> list:
    """Draws every sentence as its own small card (extras fold away). Returns ALL points."""
    points = split_points(text)
    if len(points) <= max_visible:
        st.markdown(_card_html(points), unsafe_allow_html=True)
        return points
    visible = points[: max_visible - 1] + points[-1:]  # closing tip always visible
    hidden = points[max_visible - 1 : -1]
    st.markdown(_card_html(visible), unsafe_allow_html=True)
    with st.expander(f"➕ Show {len(hidden)} more points"):
        st.markdown(_card_html(hidden, start=max_visible), unsafe_allow_html=True)
    return points


# ---- charts ----
def style_fig(fig, height: int = 330):
    """Makes any Plotly chart match the theme (transparent, soft grid, pastel colours)."""
    fig.update_layout(
        height=height,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Nunito, sans-serif", color="#4b4a73", size=13),
        colorway=PASTEL,
        margin=dict(l=8, r=8, t=18, b=8),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, x=0, title_text=""),
        hoverlabel=dict(bgcolor="#fffaf7", font_size=13, font_family="Nunito"),
    )
    fig.update_xaxes(showgrid=False, zeroline=False, linecolor="rgba(124,92,240,.15)")
    fig.update_yaxes(gridcolor="rgba(124,92,240,.10)", zeroline=False)
    return fig