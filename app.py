from __future__ import annotations

import html
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

st.set_page_config(page_title="Toxiscope | YouTube Comment Analyzer", page_icon="🫧", layout="wide")

DATA_DIR = Path("data")
REPORT_DIR = DATA_DIR / "reports"

LIME, CORAL, AMBER, BLUE, TEXT, MUTED, GRID = "#c8ef75", "#ff8791", "#f3c76c", "#7ec7df", "#e8f2ec", "#abc1b4", "rgba(232,242,236,.12)"
PALETTE = [LIME, BLUE, CORAL, AMBER, "#b79cff", "#7be0b0"]

# Native widgets are themed through .streamlit/config.toml (base="dark"). The CSS below
# only styles our own HTML, plus the tab bar, which Streamlit leaves low-contrast.
st.markdown(
    """
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700;800&display=swap');
:root{--panel:rgba(22,43,35,.88);--line:rgba(220,244,230,.15);--text:#e8f2ec;--muted:#abc1b4;--lime:#c8ef75;--coral:#ff8791;--amber:#f3c76c}
html,body,.stApp{background:radial-gradient(900px 500px at 8% 0%,rgba(35,91,70,.42),transparent 65%),linear-gradient(180deg,#0b1713,#10221b)!important;color:var(--text);font-family:'DM Sans',sans-serif}
[data-testid="stHeader"]{background:transparent}#MainMenu,footer{visibility:hidden}
.block-container{max-width:1240px;padding-top:1.6rem;padding-bottom:3rem}
h1,h2,h3,h4,label,p,span{font-family:'DM Sans',sans-serif}
.panel{background:var(--panel);border:1px solid var(--line);border-radius:20px;padding:1.2rem 1.4rem;box-shadow:0 14px 34px rgba(0,0,0,.18)}
.hero h1{margin:.7rem 0 .4rem;font-size:clamp(2rem,4vw,3.1rem);line-height:1.06;color:var(--text)}
.hero h1 span{color:var(--lime)}.hero p{max-width:62ch;margin:0;color:var(--muted);line-height:1.6}
.badge{display:inline-block;padding:.3rem .7rem;color:var(--lime);background:rgba(200,239,117,.1);border:1px solid rgba(200,239,117,.28);border-radius:999px;font-size:.72rem;font-weight:700;letter-spacing:.1em;text-transform:uppercase}
.metric{padding:1rem 1.15rem;min-height:112px;border-radius:18px;border:1px solid rgba(255,255,255,.1);box-shadow:0 12px 26px rgba(0,0,0,.16)}
.metric.lime{color:#17260e;background:linear-gradient(135deg,#d7f68b,#a9d55b)}
.metric.coral{color:#381016;background:linear-gradient(135deg,#ffa1a8,#e96773)}
.metric.green{color:#effaf4;background:linear-gradient(135deg,#45896e,#286049)}
.metric-label{font-size:.72rem;font-weight:700;letter-spacing:.09em;text-transform:uppercase;opacity:.85}
.metric-value{margin-top:.3rem;font-size:2rem;font-weight:800;line-height:1.1}.metric-note{margin-top:.2rem;font-size:.78rem;opacity:.85}
.section-heading{display:flex;align-items:center;gap:.9rem;margin:1.4rem 0 .6rem}.section-heading h2{margin:0;font-size:1.35rem;color:var(--text)}
.section-rule{flex:1;height:1px;background:var(--line)}
.stat{padding:1rem 1.2rem;border:1px solid var(--line);border-radius:16px;background:rgba(255,255,255,.03)}
.stat b{display:block;font-size:1.7rem;color:var(--lime)}.stat small{color:var(--muted)}
.comment-card{display:grid;grid-template-columns:5px minmax(0,1fr) auto;align-items:center;gap:.85rem;margin-bottom:.6rem;padding:.8rem 1rem;border:1px solid var(--line);border-radius:14px;background:rgba(255,255,255,.03)}
.comment-stripe{align-self:stretch;min-height:36px;border-radius:99px;background:var(--sev)}
.comment-text{color:var(--text);line-height:1.5;overflow-wrap:anywhere}
.comment-score{padding:.3rem .65rem;border-radius:99px;background:var(--sev);color:#241216;font-weight:800;font-size:.82rem}
.sev-high{--sev:var(--coral)}.sev-mid{--sev:var(--amber)}.sev-low{--sev:var(--lime)}
.empty-state{padding:1.3rem;border:1px dashed var(--line);border-radius:16px;color:var(--muted);text-align:center}
/* tab bar: inactive tabs were nearly invisible */
button[data-baseweb="tab"]{color:var(--muted)!important;font-weight:600;font-size:1rem}
button[data-baseweb="tab"][aria-selected="true"]{color:var(--lime)!important}
div[data-baseweb="tab-highlight"]{background:var(--lime)!important}
div[data-baseweb="tab-border"]{background:var(--line)!important}
[data-testid="stExpander"],[data-testid="stDataFrame"]{border:1px solid var(--line);border-radius:14px}
.footer{margin-top:2.5rem;color:var(--muted);font-size:.8rem;text-align:center}
/* widgets: readable on dark background regardless of Streamlit theme */
[data-testid="stWidgetLabel"] p,[data-testid="stWidgetLabel"] label,[data-testid="stWidgetLabel"] span{color:#e8f2ec!important;font-weight:600;font-size:.92rem}
[data-testid="stCaptionContainer"] p,[data-testid="stCaptionContainer"] span{color:#abc1b4!important}
[data-testid="stRadio"] label p,[data-testid="stRadio"] label span{color:#e8f2ec!important;font-weight:500}
div[data-baseweb="select"]>div,div[data-baseweb="input"]>div,input,textarea{background:#14281f!important;color:#e8f2ec!important;border:1px solid rgba(220,244,230,.28)!important;border-radius:12px!important}
div[data-baseweb="select"] *{color:#e8f2ec!important}
div[data-baseweb="select"] svg{fill:#c8ef75!important}
div[data-baseweb="popover"] ul,div[data-baseweb="popover"] li{background:#14281f!important;color:#e8f2ec!important}
div[data-baseweb="popover"] li:hover{background:#235b46!important}
input::placeholder{color:#8fa89a!important}
[data-baseweb="tag"]{background:#235b46!important}[data-baseweb="tag"] *{color:#e8f2ec!important}
[data-testid="stSlider"] *{color:#e8f2ec!important}
[data-testid="stSlider"] [role="slider"]{background:#c8ef75!important}
[data-testid="stExpander"] summary,[data-testid="stExpander"] summary *{color:#e8f2ec!important}
[data-testid="stDownloadButton"] button,.stButton button{background:#c8ef75!important;color:#17260e!important;border:0;border-radius:12px;font-weight:700}
[data-testid="stDownloadButton"] button *{color:#17260e!important}
[data-testid="stAlert"] *{color:#e8f2ec!important}
.js-plotly-plot .legend text,.js-plotly-plot .legendtext{fill:#e8f2ec!important}
@media(max-width:760px){.comment-card{grid-template-columns:5px minmax(0,1fr)}.comment-score{grid-column:2;justify-self:start}}
</style>
""",
    unsafe_allow_html=True,
)


@st.cache_data(show_spinner=False)
def _read_csv(path: str, modified_ns: int) -> pd.DataFrame:
    del modified_ns  # only part of the cache key
    return pd.read_csv(path)


def load_csv(path: Path) -> pd.DataFrame | None:
    if not path.is_file():
        return None
    try:
        return _read_csv(str(path), path.stat().st_mtime_ns)
    except (OSError, pd.errors.EmptyDataError, pd.errors.ParserError) as exc:
        st.warning(f"Could not read `{path.as_posix()}`: {exc}")
        return None


def section(title: str, note: str = "") -> None:
    st.markdown(
        f'<div class="section-heading"><h2>{html.escape(title)}</h2><div class="section-rule"></div></div>',
        unsafe_allow_html=True,
    )
    if note:
        st.caption(note)


def show_df(df: pd.DataFrame) -> None:
    """Works on old and new Streamlit versions (use_container_width was deprecated)."""
    try:
        st.dataframe(df, width="stretch", hide_index=True)
    except TypeError:
        st.dataframe(df, use_container_width=True, hide_index=True)


def show_fig(fig: go.Figure) -> None:
    st.plotly_chart(fig, theme=None, config={"displaylogo": False, "modeBarButtonsToRemove": ["lasso2d", "select2d"]})


def style(fig: go.Figure, height: int = 380) -> go.Figure:
    fig.update_layout(
        height=height, paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(23,47,38,.55)",
        font=dict(family="DM Sans, sans-serif", color=TEXT, size=13),
        margin=dict(l=24, r=40, t=24, b=24), legend=dict(bgcolor="rgba(11,23,19,.7)", bordercolor="rgba(220,244,230,.25)", borderwidth=1, font=dict(color=TEXT, size=14), title_font=dict(color=TEXT)),
        hoverlabel=dict(bgcolor="#172f26", font_color=TEXT),
    )
    axis = dict(gridcolor=GRID, zeroline=False, linecolor=GRID, tickfont=dict(color=TEXT, size=13),
                title_font=dict(color=TEXT, size=13), title_standoff=18, automargin=True, ticks="outside",
                tickcolor=GRID)  # automargin = reserve room for tick labels so nothing is clipped
    fig.update_xaxes(**axis)
    fig.update_yaxes(**axis)
    return fig


METRIC_LABELS = {
    "toxicity_rate": "Toxicity rate",
    "mean_toxicity": "Mean toxicity score",
    "comments": "Comments",
    "toxic": "Toxic comments",
}


def bar_chart(df: pd.DataFrame, label_col: str, key: str, color: str) -> None:
    """Interactive bar chart with a metric picker and horizontal/vertical toggle."""
    metrics = [m for m in METRIC_LABELS if m in df.columns and pd.api.types.is_numeric_dtype(df[m])]
    if df.empty or not metrics:
        st.markdown('<div class="empty-state">No data available.</div>', unsafe_allow_html=True)
        return

    c1, c2 = st.columns([3, 2])
    metric = c1.selectbox("Metric", metrics, format_func=METRIC_LABELS.get, key=f"{key}_m")
    orient = c2.radio("Orientation", ["Horizontal", "Vertical"], horizontal=True, key=f"{key}_o")

    data = df[[label_col, metric] + [c for c in ("comments",) if c in df.columns and c != metric]].dropna(subset=[metric])
    data = data.sort_values(metric, ascending=False).head(12)
    is_pct = metric == "toxicity_rate"
    fmt = ".2%" if is_pct else (",.0f" if metric in ("comments", "toxic") else ".3f")
    horizontal = orient == "Horizontal"

    fig = go.Figure(go.Bar(
        x=data[metric] if horizontal else data[label_col].astype(str),
        y=data[label_col].astype(str) if horizontal else data[metric],
        orientation="h" if horizontal else "v",
        marker=dict(color=color, line=dict(width=0)),
        text=[format(v, fmt) for v in data[metric]], textposition="outside", cliponaxis=False,
        textfont=dict(color=TEXT, size=12),
        customdata=data["comments"] if "comments" in data.columns else None,
        hovertemplate=f"<b>%{{{'y' if horizontal else 'x'}}}</b><br>{METRIC_LABELS[metric]}: %{{{'x' if horizontal else 'y'}:{fmt}}}"
                      + ("<br>Comments: %{customdata:,}" if "comments" in data.columns else "") + "<extra></extra>",
    ))
    value_axis = dict(title=METRIC_LABELS[metric], tickformat=".1%" if is_pct else None,
                      range=[0, float(data[metric].max()) * 1.25 or 1])
    if horizontal:
        fig.update_layout(xaxis=value_axis, yaxis=dict(autorange="reversed", title=""))
    else:
        fig.update_layout(yaxis=value_axis, xaxis=dict(title=""))
    show_fig(style(fig, max(340, 150 + 58 * len(data)) if horizontal else 460))


def strength(rho: float) -> str:
    a = abs(rho)
    word = "very weak" if a < .1 else "weak" if a < .3 else "moderate" if a < .5 else "strong"
    return f"{word} {'negative' if rho < 0 else 'positive'}"


def comment_cards(df: pd.DataFrame) -> str:
    cards = []
    for _, row in df.iterrows():
        score = float(row["toxicity_score"])
        sev = "high" if score >= 0.7 else "mid" if score >= 0.4 else "low"
        cards.append(
            f'<div class="comment-card sev-{sev}"><div class="comment-stripe"></div>'
            f'<div class="comment-text">{html.escape(str(row["text_clean"]))}</div>'
            f'<div class="comment-score">{score:.2f}</div></div>'
        )
    return "".join(cards)


# ───────────────────────────── data ─────────────────────────────
comments = load_csv(DATA_DIR / "comments_clean.csv")
if comments is None:
    st.markdown('<div class="empty-state"><h3>No dashboard data found</h3>'
                "<p>Make sure <code>data/comments_clean.csv</code> exists.</p></div>", unsafe_allow_html=True)
    st.stop()
comments = comments.copy()
if "toxicity_score" in comments:
    comments["toxicity_score"] = pd.to_numeric(comments["toxicity_score"], errors="coerce")
if "is_toxic" in comments:
    comments["is_toxic"] = pd.to_numeric(comments["is_toxic"], errors="coerce").fillna(0)

total = len(comments)
toxic_count = int(comments["is_toxic"].sum()) if "is_toxic" in comments else 0
toxic_rate = toxic_count / total if total else 0.0
avg_score = float(comments["toxicity_score"].mean()) if "toxicity_score" in comments and comments["toxicity_score"].notna().any() else 0.0

# ───────────────────────────── header ─────────────────────────────
st.markdown(
    """<div class="panel hero"><span class="badge">YouTube comment analysis</span>
    <h1>Read the room,<br><span>comment by comment.</span></h1>
    <p>Explore estimated comment toxicity by channel, topic and video reach.
    Scores are model estimates, not judgments about individual people.</p></div>""",
    unsafe_allow_html=True,
)
st.write("")
m1, m2, m3 = st.columns(3)
for col, cls, label, value, note in (
    (m1, "lime", "Comments analyzed", f"{total:,}", "Rows in the cleaned dataset"),
    (m2, "coral", "Flagged toxic", f"{toxic_count:,}", f"{toxic_rate:.2%} of analyzed comments"),
    (m3, "green", "Average toxicity score", f"{avg_score:.3f}", "Scores range from 0 to 1"),
):
    col.markdown(f'<div class="metric {cls}"><div class="metric-label">{label}</div>'
                 f'<div class="metric-value">{value}</div><div class="metric-note">{note}</div></div>',
                 unsafe_allow_html=True)

overview_tab, reach_tab, explorer_tab, data_tab = st.tabs(["Overview", "Reach vs. toxicity", "Comment explorer", "Data & downloads"])

# ───────────────────────────── overview ─────────────────────────────
with overview_tab:
    by_channel = load_csv(REPORT_DIR / "by_channel.csv")
    by_topic = load_csv(REPORT_DIR / "by_topic.csv")

    section("Toxicity by channel", "Rates are shares of comments flagged toxic; hover a bar for comment counts.")
    if by_channel is not None:
        bar_chart(by_channel, "channel" if "channel" in by_channel else by_channel.columns[0], "ch", LIME)
    else:
        st.info("Run `python main.py eda` to generate `by_channel.csv`.")

    if by_topic is not None and len(by_topic) >= 2:
        section("Toxicity by topic")
        bar_chart(by_topic, "topic" if "topic" in by_topic else by_topic.columns[0], "tp", BLUE)

# ───────────────────────────── reach ─────────────────────────────
with reach_tab:
    per_video = load_csv(REPORT_DIR / "per_video.csv")
    stats = load_csv(REPORT_DIR / "toxicity_vs_views.csv")

    section("Do bigger videos attract more toxicity?", "Spearman rank correlation between log views and toxicity.")
    if stats is not None and not stats.empty:
        stats = stats.rename(columns={stats.columns[0]: "level"})
        cols = st.columns(len(stats))
        for col, (_, r) in zip(cols, stats.iterrows()):
            p = r.get("p_value")
            p_txt = "p < 0.0001" if pd.notna(p) and p < 0.0001 else f"p = {p:.4f}" if pd.notna(p) else ""
            n = r.get("n_videos") if pd.notna(r.get("n_videos")) else r.get("n_comments")
            unit = "videos" if pd.notna(r.get("n_videos")) else "comments"
            col.markdown(
                f'<div class="stat"><small>{html.escape(str(r["level"]).replace("_", " ").title())}</small>'
                f'<b>ρ = {r["spearman_rho"]:.3f}</b><small>{strength(r["spearman_rho"])} · {p_txt} · n = {int(n):,} {unit}</small></div>',
                unsafe_allow_html=True)
        st.write("")

    if per_video is not None and {"view_count", "toxicity_rate", "channel"}.issubset(per_video.columns):
        pv = per_video.dropna(subset=["view_count", "toxicity_rate"]).copy()
        pv["log_views"] = np.log1p(pv["view_count"])
        pv["toxicity_pct"] = pv["toxicity_rate"] * 100
        hover = [c for c in ("video_title", "view_count", "n_comments") if c in pv.columns]
        fig = px.scatter(pv, x="log_views", y="toxicity_pct", color="channel", symbol="channel", color_discrete_sequence=PALETTE,
                         symbol_sequence=["circle", "diamond", "square", "triangle-up", "x", "star"],
                         hover_data={c: True for c in hover} | {"log_views": False, "toxicity_pct": ":.2f"},
                         labels={"log_views": "log(1 + video views)", "toxicity_pct": "Toxicity rate (%)"})
        fig.update_traces(marker=dict(size=13, line=dict(width=1, color="#10221b"), opacity=.9))
        if len(pv) >= 2 and pv["log_views"].nunique() >= 2:
            k, b = np.polyfit(pv["log_views"], pv["toxicity_pct"], 1)
            xs = np.linspace(pv["log_views"].min(), pv["log_views"].max(), 50)
            fig.add_trace(go.Scatter(x=xs, y=k * xs + b, mode="lines", name="Linear trend",
                                     line=dict(color=CORAL, dash="dash", width=2), hoverinfo="skip"))
        fig.update_layout(yaxis=dict(ticksuffix="%", rangemode="tozero"), legend_title_text="")
        show_fig(style(fig, 540))
        st.caption("Each dot is one video. The dashed line is a simple linear trend for orientation; "
                   "the statistics above use rank correlation and are less sensitive to outliers.")
    else:
        st.info("Run `python main.py eda` to generate `per_video.csv`.")

# ───────────────────────────── explorer ─────────────────────────────
with explorer_tab:
    section("Explore higher-scoring comments")
    if not {"text_clean", "toxicity_score"}.issubset(comments.columns):
        st.warning("The cleaned CSV needs `text_clean` and `toxicity_score` columns.")
    else:
        a, b, c = st.columns([2, 1, 1])
        query = a.text_input("Search comment text", placeholder="Enter a word or phrase")
        min_score = b.slider("Minimum score", 0.0, 1.0, 0.0, 0.05)
        n_results = c.selectbox("Results", [10, 15, 25, 50], index=1)

        filtered = comments
        ch_cols = [x for x in filtered.columns if "channel" in x.lower()]
        if ch_cols:
            opts = sorted(filtered[ch_cols[0]].dropna().astype(str).unique())
            chosen = st.multiselect("Filter channels", opts)
            if chosen:
                filtered = filtered[filtered[ch_cols[0]].astype(str).isin(chosen)]
        if query:
            filtered = filtered[filtered["text_clean"].astype(str).str.contains(query, case=False, na=False, regex=False)]
        filtered = filtered[filtered["toxicity_score"].notna() & (filtered["toxicity_score"] >= min_score)].nlargest(n_results, "toxicity_score")

        if filtered.empty:
            st.info("No comments match these filters.")
        else:
            st.markdown(comment_cards(filtered), unsafe_allow_html=True)
            st.download_button("Download filtered comments", filtered.to_csv(index=False).encode("utf-8"),
                               "filtered_toxic_comments.csv", "text/csv")

# ───────────────────────────── data ─────────────────────────────
with data_tab:
    section("Report tables")
    found = False
    for fname, title in (("by_channel.csv", "Toxicity by channel"), ("by_topic.csv", "Toxicity by topic"),
                         ("toxicity_vs_views.csv", "Toxicity vs. views"), ("per_video.csv", "Per-video summary")):
        df = load_csv(REPORT_DIR / fname)
        if df is None:
            continue
        found = True
        with st.expander(title):
            show_df(df)
            st.download_button(f"Download {fname}", df.to_csv(index=False).encode("utf-8"), fname, "text/csv", key=f"dl_{fname}")
    png = REPORT_DIR / "toxicity_eda.png"
    if png.is_file():
        found = True
        with st.expander("Static EDA image (for reports)"):
            st.image(str(png))
    if not found:
        st.markdown('<div class="empty-state">No reports yet. Run <code>python main.py eda</code>.</div>', unsafe_allow_html=True)

st.markdown('<div class="footer">Toxiscope · YouTube comment analysis</div>', unsafe_allow_html=True)
