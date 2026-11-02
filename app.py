import html
from pathlib import Path

import pandas as pd
import streamlit as st

st.set_page_config(
    page_title="Toxiscope | YouTube Comment Analyzer",
    page_icon="🫧",
    layout="wide",
)

DATA = Path("data")
REPORTS = DATA / "reports"

# ----------------------------------------------------------------------------
# THEME: "Bottle-glass + Clay"
# Deep bottle-green night, frosted glass panels, puffy clay buttons.
# Accents: lime (safe / primary) and coral-rose (toxic / alert).
# ----------------------------------------------------------------------------
CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Bricolage+Grotesque:opsz,wght@12..96,500;12..96,700;12..96,800&family=Figtree:wght@400;500;600&display=swap');

:root{
  --bg:#0b1713;
  --bg2:#10241d;
  --ink:#e4efe8;
  --ink-soft:#9db5a9;
  --lime:#c6f26b;
  --lime-deep:#8fc23a;
  --coral:#ff7b86;
  --coral-deep:#e4525f;
  --amber:#f2c14e;
  --glass:rgba(214,240,226,0.07);
  --glass-strong:rgba(214,240,226,0.12);
  --glass-line:rgba(214,240,226,0.18);
  --r:26px;
}

html, body, .stApp{
  background: radial-gradient(1200px 700px at 12% -10%, #17372c 0%, transparent 60%),
              radial-gradient(900px 600px at 105% 10%, #2b1c24 0%, transparent 55%),
              linear-gradient(180deg, var(--bg) 0%, var(--bg2) 100%) !important;
  color: var(--ink);
  font-family: 'Figtree', sans-serif;
}
[data-testid="stHeader"]{ background: transparent; }
#MainMenu, footer{ visibility:hidden; }
.block-container{ padding-top: 2.2rem; padding-bottom: 4rem; max-width: 1180px; }

h1,h2,h3,h4{ font-family:'Bricolage Grotesque', sans-serif !important; color: var(--ink) !important; letter-spacing:-0.02em; }

/* floating blurred orbs behind everything */
.orb{ position:fixed; border-radius:50%; filter: blur(70px); opacity:.45; z-index:0; pointer-events:none; }
.orb.o1{ width:340px; height:340px; background:#2f7a5a; top:6%; left:-80px; animation: drift1 18s ease-in-out infinite; }
.orb.o2{ width:300px; height:300px; background:#a8404f; top:48%; right:-90px; animation: drift2 22s ease-in-out infinite; }
.orb.o3{ width:240px; height:240px; background:#8aa83a; bottom:-60px; left:38%; animation: drift3 26s ease-in-out infinite; opacity:.3; }
@keyframes drift1{ 0%,100%{ transform:translate(0,0) } 50%{ transform:translate(90px,70px) } }
@keyframes drift2{ 0%,100%{ transform:translate(0,0) } 50%{ transform:translate(-80px,-60px) } }
@keyframes drift3{ 0%,100%{ transform:translate(0,0) } 50%{ transform:translate(60px,-80px) } }

@keyframes riseIn{ from{ opacity:0; transform: translateY(22px) scale(.98) } to{ opacity:1; transform:none } }
@keyframes growX{ from{ width:0 } to{ width:var(--w) } }
@keyframes pulseDot{ 0%,100%{ box-shadow:0 0 0 0 rgba(198,242,107,.55) } 70%{ box-shadow:0 0 0 10px rgba(198,242,107,0) } }
@keyframes sheen{ from{ transform: translateX(-120%) } to{ transform: translateX(220%) } }

/* ---------- glass panel ---------- */
.glass{
  position:relative; z-index:1;
  background: linear-gradient(145deg, var(--glass-strong), var(--glass));
  border: 1px solid var(--glass-line);
  border-radius: var(--r);
  backdrop-filter: blur(18px) saturate(140%);
  -webkit-backdrop-filter: blur(18px) saturate(140%);
  box-shadow: 0 18px 40px rgba(0,0,0,.35), inset 0 1px 0 rgba(255,255,255,.12);
  padding: 1.4rem 1.6rem;
  animation: riseIn .7s cubic-bezier(.2,.8,.2,1) both;
}

/* ---------- hero ---------- */
.hero{ display:grid; grid-template-columns: 1.5fr 1fr; gap:1.4rem; align-items:center; }
.badge{ display:inline-flex; align-items:center; gap:.55rem; font-size:.78rem; font-weight:600; letter-spacing:.08em; text-transform:uppercase;
        color: var(--lime); background: rgba(198,242,107,.1); border:1px solid rgba(198,242,107,.3); padding:.35rem .8rem; border-radius:999px; }
.badge i{ width:8px; height:8px; border-radius:50%; background:var(--lime); animation: pulseDot 2s infinite; }
.hero h1{ font-size: clamp(2.1rem, 4.2vw, 3.4rem); line-height:1.05; margin:.9rem 0 .6rem 0; font-weight:800; }
.hero h1 em{ font-style:normal; background: linear-gradient(95deg, var(--lime), #f3e58a 55%, var(--coral)); -webkit-background-clip:text; background-clip:text; color:transparent; }
.hero p{ color: var(--ink-soft); font-size:1.02rem; max-width: 46ch; margin:0; }

/* ring gauge (clay) */
.ring-wrap{ display:flex; justify-content:center; }
.ring{
  --p: 10;
  width: 190px; height:190px; border-radius:50%;
  background: conic-gradient(var(--coral) calc(var(--p) * 1%), rgba(255,255,255,.07) 0);
  display:grid; place-items:center;
  box-shadow: 14px 14px 30px rgba(0,0,0,.45), -8px -8px 22px rgba(214,240,226,.06), inset 0 0 0 1px rgba(255,255,255,.1);
  animation: riseIn .9s .15s cubic-bezier(.2,.8,.2,1) both;
}
.ring .core{
  width: 146px; height:146px; border-radius:50%;
  background: linear-gradient(145deg, #1b3a2f, #0f2119);
  box-shadow: inset 8px 8px 16px rgba(0,0,0,.5), inset -6px -6px 14px rgba(214,240,226,.07);
  display:flex; flex-direction:column; align-items:center; justify-content:center;
}
.ring .num{ font-family:'Bricolage Grotesque'; font-weight:800; font-size:2.1rem; color:var(--ink); }
.ring .cap{ font-size:.72rem; letter-spacing:.12em; text-transform:uppercase; color:var(--ink-soft); }

/* ---------- clay stat tiles ---------- */
.tiles{ display:grid; grid-template-columns: repeat(3, 1fr); gap:1.1rem; margin-top:1.2rem; }
.clay{
  position:relative; z-index:1; overflow:hidden;
  border-radius: 30px; padding: 1.3rem 1.4rem;
  background: linear-gradient(150deg, var(--c1), var(--c2));
  box-shadow: 12px 14px 28px rgba(0,0,0,.42), -6px -6px 18px rgba(214,240,226,.05),
              inset 5px 5px 10px rgba(255,255,255,.22), inset -8px -8px 14px rgba(0,0,0,.22);
  transition: transform .35s cubic-bezier(.2,.8,.2,1), box-shadow .35s;
  animation: riseIn .8s both;
}
.clay:nth-child(1){ animation-delay:.1s } .clay:nth-child(2){ animation-delay:.2s } .clay:nth-child(3){ animation-delay:.3s }
.clay:hover{ transform: translateY(-8px) rotate(-.6deg);
  box-shadow: 16px 24px 38px rgba(0,0,0,.5), -6px -6px 18px rgba(214,240,226,.07),
              inset 5px 5px 10px rgba(255,255,255,.28), inset -8px -8px 14px rgba(0,0,0,.2); }
.clay::after{ content:""; position:absolute; top:0; left:0; width:40%; height:100%;
  background: linear-gradient(100deg, transparent, rgba(255,255,255,.22), transparent); transform: translateX(-120%); }
.clay:hover::after{ animation: sheen .9s ease; }
.clay .lbl{ font-size:.8rem; font-weight:600; letter-spacing:.09em; text-transform:uppercase; color: var(--t2); }
.clay .val{ font-family:'Bricolage Grotesque'; font-size:2.5rem; font-weight:800; color: var(--t1); line-height:1.1; margin-top:.35rem; }
.clay .sub{ font-size:.86rem; color: var(--t2); margin-top:.2rem; }
.clay.lime{ --c1:#d4f77f; --c2:#9ccc43; --t1:#16260c; --t2:#37501a; }
.clay.coral{ --c1:#ff9aa2; --c2:#e85a68; --t1:#3a0c13; --t2:#6e1f2a; }
.clay.moss{ --c1:#3f8a6a; --c2:#26604a; --t1:#effaf3; --t2:#bfe3d0; }

/* ---------- section heading ---------- */
.sec{ display:flex; align-items:center; gap:.8rem; margin: 2.4rem 0 1rem 0; position:relative; z-index:1; }
.sec h2{ margin:0; font-size:1.5rem; }
.sec .line{ flex:1; height:1px; background: linear-gradient(90deg, var(--glass-line), transparent); }

/* ---------- bars ---------- */
.bar-row{ display:grid; grid-template-columns: 150px 1fr 70px; gap:1rem; align-items:center; padding:.55rem 0; animation: riseIn .6s both; }
.bar-label{ color:var(--ink); font-weight:500; white-space:nowrap; overflow:hidden; text-overflow:ellipsis; }
.bar-track{ height:18px; border-radius:999px; background: rgba(0,0,0,.28); box-shadow: inset 3px 3px 7px rgba(0,0,0,.5), inset -2px -2px 5px rgba(214,240,226,.06); overflow:hidden; }
.bar-fill{ height:100%; border-radius:999px; width:var(--w); animation: growX 1.2s cubic-bezier(.2,.8,.2,1) both;
  background: linear-gradient(90deg, var(--lime-deep), var(--lime) 45%, var(--amber) 75%, var(--coral));
  box-shadow: inset 0 2px 3px rgba(255,255,255,.4); }
.bar-val{ text-align:right; font-weight:700; color:var(--lime); font-variant-numeric: tabular-nums; }

/* ---------- comment cards ---------- */
.cm{ position:relative; z-index:1; display:grid; grid-template-columns: 6px 1fr auto; gap:1rem; align-items:center;
  padding: 1rem 1.2rem; margin-bottom:.8rem; border-radius:22px;
  background: var(--glass); border:1px solid var(--glass-line); backdrop-filter: blur(10px);
  transition: transform .3s cubic-bezier(.2,.8,.2,1), background .3s, border-color .3s; animation: riseIn .5s both; }
.cm:hover{ transform: translateX(8px); background: var(--glass-strong); border-color: rgba(255,255,255,.3); }
.cm .stripe{ align-self:stretch; border-radius:6px; background: var(--sev); }
.cm .txt{ color:var(--ink); line-height:1.5; word-break:break-word; }
.cm .chip{ font-family:'Bricolage Grotesque'; font-weight:700; padding:.4rem .9rem; border-radius:999px; color:#1a0b0e; background: var(--sev);
  box-shadow: inset 2px 2px 4px rgba(255,255,255,.35), inset -3px -3px 6px rgba(0,0,0,.18), 4px 6px 12px rgba(0,0,0,.3); }
.cm.hi{ --sev: var(--coral); } .cm.mid{ --sev: var(--amber); } .cm.lo{ --sev: var(--lime); }

/* ---------- tabs ---------- */
.stTabs [data-baseweb="tab-list"]{ gap:.6rem; background: var(--glass); padding:.45rem; border-radius:999px; border:1px solid var(--glass-line); width:fit-content; backdrop-filter: blur(12px); }
.stTabs [data-baseweb="tab"]{ height:46px; padding: 0 1.4rem; border-radius:999px; color: var(--ink-soft); font-weight:600; transition: all .3s; background: transparent; }
.stTabs [data-baseweb="tab"]:hover{ color: var(--ink); background: rgba(214,240,226,.08); }
.stTabs [aria-selected="true"]{ color:#16260c !important;
  background: linear-gradient(150deg, #d4f77f, #9ccc43) !important;
  box-shadow: 5px 6px 14px rgba(0,0,0,.4), inset 2px 2px 4px rgba(255,255,255,.45), inset -3px -3px 6px rgba(0,0,0,.15); }
.stTabs [data-baseweb="tab-highlight"], .stTabs [data-baseweb="tab-border"]{ display:none; }

/* ---------- clay buttons ---------- */
.stButton > button, .stDownloadButton > button{
  width:100%; min-height:3.1rem; border:none; border-radius:20px; font-weight:700; font-size:1rem; letter-spacing:.02em;
  color:#3a0c13; background: linear-gradient(150deg, #ff9aa2, #e85a68);
  box-shadow: 8px 10px 20px rgba(0,0,0,.4), inset 3px 3px 7px rgba(255,255,255,.4), inset -5px -5px 10px rgba(0,0,0,.2);
  transition: transform .25s cubic-bezier(.2,.8,.2,1), box-shadow .25s, filter .25s;
}
.stDownloadButton > button{ color:#16260c; background: linear-gradient(150deg, #d4f77f, #9ccc43); }
.stButton > button:hover, .stDownloadButton > button:hover{ transform: translateY(-4px) scale(1.015); filter: brightness(1.06);
  box-shadow: 10px 18px 28px rgba(0,0,0,.45), inset 3px 3px 7px rgba(255,255,255,.45), inset -5px -5px 10px rgba(0,0,0,.2); }
.stButton > button:active, .stDownloadButton > button:active{ transform: translateY(1px) scale(.985);
  box-shadow: 3px 4px 8px rgba(0,0,0,.4), inset 4px 4px 9px rgba(0,0,0,.25); }
.stButton > button p, .stDownloadButton > button p{ color: inherit; font-weight:700; }

/* ---------- inputs ---------- */
[data-baseweb="input"], [data-baseweb="select"] > div{ background: rgba(0,0,0,.28) !important; border-radius:16px !important; border:1px solid var(--glass-line) !important;
  box-shadow: inset 3px 3px 8px rgba(0,0,0,.45); transition: border-color .25s, box-shadow .25s; }
[data-baseweb="input"]:focus-within, [data-baseweb="select"] > div:hover{ border-color: var(--lime) !important; box-shadow: inset 3px 3px 8px rgba(0,0,0,.45), 0 0 0 3px rgba(198,242,107,.18); }
input{ color: var(--ink) !important; }
label, [data-testid="stWidgetLabel"] p{ color: var(--ink-soft) !important; font-weight:600 !important; }
[data-testid="stSlider"] [role="slider"]{ background: var(--lime) !important; box-shadow: 0 0 0 5px rgba(198,242,107,.25), 3px 4px 8px rgba(0,0,0,.4); }

/* ---------- dataframe / image / expander ---------- */
[data-testid="stDataFrame"]{ border-radius:20px; overflow:hidden; border:1px solid var(--glass-line); box-shadow: 0 14px 30px rgba(0,0,0,.35); }
[data-testid="stImage"] img{ border-radius:22px; border:1px solid var(--glass-line); box-shadow: 0 18px 40px rgba(0,0,0,.4); transition: transform .4s; }
[data-testid="stImage"] img:hover{ transform: scale(1.012); }
[data-testid="stExpander"]{ background: var(--glass); border:1px solid var(--glass-line) !important; border-radius:20px; backdrop-filter: blur(10px); }
[data-testid="stExpander"] summary:hover{ color: var(--lime); }

.empty{ text-align:center; color:var(--ink-soft); padding:2.2rem 1rem; }
.foot{ text-align:center; color: var(--ink-soft); font-size:.85rem; margin-top:3rem; position:relative; z-index:1; }

@media (max-width: 820px){
  .hero{ grid-template-columns:1fr; } .tiles{ grid-template-columns:1fr; }
  .bar-row{ grid-template-columns: 100px 1fr 56px; }
  .cm{ grid-template-columns: 6px 1fr; } .cm .chip{ grid-column:2; justify-self:start; }
}
</style>
<div class="orb o1"></div><div class="orb o2"></div><div class="orb o3"></div>
"""
st.markdown(CSS, unsafe_allow_html=True)


# ----------------------------------------------------------------------------
# Helpers
# ----------------------------------------------------------------------------
@st.cache_data
def load(path):
    return pd.read_csv(path) if Path(path).exists() else None


def section(title: str):
    st.markdown(f'<div class="sec"><h2>{title}</h2><div class="line"></div></div>', unsafe_allow_html=True)


def bars_html(df: pd.DataFrame) -> str:
    """Render a breakdown table (label column + a toxicity-rate-like column) as clay bars."""
    label_col = df.columns[0]
    num_cols = [c for c in df.columns[1:] if pd.api.types.is_numeric_dtype(df[c])]
    if not num_cols:
        return ""
    prefer = [c for c in num_cols if "rate" in c.lower()] or [c for c in num_cols if "toxic" in c.lower()] or num_cols
    val_col = prefer[0]
    data = df[[label_col, val_col]].dropna().sort_values(val_col, ascending=False).head(12)
    vmax = float(data[val_col].max()) or 1.0
    as_pct = vmax <= 1.0
    rows = []
    for i, (name, v) in enumerate(zip(data[label_col], data[val_col])):
        width = max(3.0, float(v) / vmax * 100)
        shown = f"{v:.1%}" if as_pct else f"{v:,.2f}"
        rows.append(
            f'<div class="bar-row" style="animation-delay:{i * 0.06:.2f}s">'
            f'<div class="bar-label" title="{html.escape(str(name))}">{html.escape(str(name))}</div>'
            f'<div class="bar-track"><div class="bar-fill" style="--w:{width:.1f}%"></div></div>'
            f'<div class="bar-val">{shown}</div></div>'
        )
    return f'<div class="glass">{"".join(rows)}</div>'


def comment_cards(df: pd.DataFrame) -> str:
    out = []
    for i, (txt, sc) in enumerate(zip(df["text_clean"], df["toxicity_score"])):
        sev = "hi" if sc >= 0.7 else "mid" if sc >= 0.4 else "lo"
        out.append(
            f'<div class="cm {sev}" style="animation-delay:{min(i, 15) * 0.04:.2f}s">'
            f'<div class="stripe"></div><div class="txt">{html.escape(str(txt))}</div>'
            f'<div class="chip">{sc:.2f}</div></div>'
        )
    return "".join(out)


# ----------------------------------------------------------------------------
# Data
# ----------------------------------------------------------------------------
comments = load(DATA / "comments_clean.csv")
if comments is None:
    st.markdown(
        '<div class="glass empty"><h3>No data yet 🫧</h3>'
        "<p><code>data/comments_clean.csv</code> nahi mili. Pehle pipeline chalao:<br>"
        "<code>python main.py all</code></p></div>",
        unsafe_allow_html=True,
    )
    st.stop()

total = len(comments)
rate = float(comments["is_toxic"].mean()) if "is_toxic" in comments else 0.0
avg = float(comments["toxicity_score"].mean()) if "toxicity_score" in comments else 0.0
n_toxic = int(comments["is_toxic"].sum()) if "is_toxic" in comments else 0

# ----------------------------------------------------------------------------
# Hero + stat tiles
# ----------------------------------------------------------------------------
st.markdown(
    f"""
<div class="glass hero">
  <div>
    <span class="badge"><i></i>Live analysis</span>
    <h1>Read the room,<br><em>comment by comment.</em></h1>
    <p>YouTube comment toxicity, broken down by channel, topic and reach, scored and ready to explore.</p>
  </div>
  <div class="ring-wrap">
    <div class="ring" style="--p:{rate * 100:.1f}">
      <div class="core"><div class="num">{rate:.1%}</div><div class="cap">toxic</div></div>
    </div>
  </div>
</div>
<div class="tiles">
  <div class="clay lime"><div class="lbl">Comments analyzed</div><div class="val">{total:,}</div><div class="sub">rows in the clean dataset</div></div>
  <div class="clay coral"><div class="lbl">Flagged toxic</div><div class="val">{n_toxic:,}</div><div class="sub">{rate:.1%} of all comments</div></div>
  <div class="clay moss"><div class="lbl">Avg toxicity score</div><div class="val">{avg:.3f}</div><div class="sub">0 = calm, 1 = harsh</div></div>
</div>
""",
    unsafe_allow_html=True,
)

# ----------------------------------------------------------------------------
# Tabs
# ----------------------------------------------------------------------------
tab1, tab2, tab3 = st.tabs(["Breakdown", "Explorer", "Charts"])

with tab1:
    for name, title in [("by_channel.csv", "Toxicity by channel"), ("by_topic.csv", "Toxicity by topic")]:
        df = load(REPORTS / name)
        if df is not None:
            section(title)
            html_bars = bars_html(df)
            if html_bars:
                st.markdown(html_bars, unsafe_allow_html=True)
            with st.expander("View raw table"):
                st.dataframe(df, use_container_width=True)

    vs = load(REPORTS / "toxicity_vs_views.csv")
    if vs is not None:
        section("Toxicity vs. views")
        st.dataframe(vs, use_container_width=True)

    if load(REPORTS / "by_channel.csv") is None and load(REPORTS / "by_topic.csv") is None and vs is None:
        st.markdown('<div class="glass empty">EDA reports nahi mile. <code>python main.py eda</code> chalao.</div>', unsafe_allow_html=True)

with tab2:
    section("Most toxic comments")
    if {"text_clean", "toxicity_score"} <= set(comments.columns):
        f1, f2, f3 = st.columns([2, 1, 1])
        query = f1.text_input("Search inside comments", placeholder="type a word...")
        min_score = f2.slider("Min score", 0.0, 1.0, 0.0, 0.05)
        n = f3.slider("How many", 5, 50, 15)

        view = comments
        chan_cols = [c for c in comments.columns if "channel" in c.lower()]
        if chan_cols:
            options = sorted(comments[chan_cols[0]].dropna().astype(str).unique())
            picked = st.multiselect("Channels", options, placeholder="All channels")
            if picked:
                view = view[view[chan_cols[0]].astype(str).isin(picked)]
        if query:
            view = view[view["text_clean"].astype(str).str.contains(query, case=False, na=False, regex=False)]
        view = view[view["toxicity_score"] >= min_score].nlargest(n, "toxicity_score")

        if view.empty:
            st.markdown('<div class="glass empty">Koi comment match nahi hua 🫧 filters thode loose karo.</div>', unsafe_allow_html=True)
        else:
            st.markdown(comment_cards(view), unsafe_allow_html=True)
            st.download_button(
                "Download these comments (CSV)",
                view.to_csv(index=False).encode("utf-8"),
                file_name="top_toxic_comments.csv",
                mime="text/csv",
            )
    else:
        st.markdown('<div class="glass empty">Columns <code>text_clean</code> / <code>toxicity_score</code> missing hain.</div>', unsafe_allow_html=True)

with tab3:
    section("EDA charts")
    chart = REPORTS / "toxicity_eda.png"
    if chart.exists():
        st.image(str(chart), use_container_width=True)
    else:
        st.markdown('<div class="glass empty">Chart nahi mila. <code>python main.py eda</code> chalao.</div>', unsafe_allow_html=True)

st.markdown('<div class="foot">Toxiscope · built with Streamlit · UET Lahore project</div>', unsafe_allow_html=True)