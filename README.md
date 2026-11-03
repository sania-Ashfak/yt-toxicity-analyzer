<div align="center">

# YouTube Comment Toxicity Analyzer

**An end-to-end data pipeline and live dashboard that measures how toxic the comments on YouTube channels are.**

[![Live Demo](https://img.shields.io/badge/Live%20Demo-Streamlit-FF4B4B?logo=streamlit&logoColor=white)](https://yt-toxicity-analyzer-8vji7t6eeg833fjmz7oxjl.streamlit.app/)
![Python](https://img.shields.io/badge/Python-3.x-3776AB?logo=python&logoColor=white)
![YouTube Data API](https://img.shields.io/badge/YouTube%20Data%20API-v3-FF0000?logo=youtube&logoColor=white)
![SQLite](https://img.shields.io/badge/SQLite-003B57?logo=sqlite&logoColor=white)

[**Open the live dashboard**](https://yt-toxicity-analyzer-8vji7t6eeg833fjmz7oxjl.streamlit.app/)

</div>

---

## Overview

This project collects comments from YouTube channels or videos, cleans them, scores each comment for toxicity, stores the results, and then explores how toxicity varies across channels, topics and video reach (views).

It is split into two parts:

| Part | What it does | Where it runs |
|---|---|---|
| **Pipeline** | Extract, transform, load and analyze comments (`main.py`) | Your machine (needs a YouTube API key) |
| **Dashboard** | Shows the results as an interactive web app (`app.py`) | Locally or on Streamlit Community Cloud |

The dashboard only reads the result files in `data/`, so it does **not** need an API key to run or to be deployed.

---

## Features

- **Automated extraction** from the YouTube Data API v3: comments plus video statistics, for specific video IDs or for the recent videos of a channel (channel handles such as `@name` are supported).
- **Resilient collection**: videos with disabled comments and quota errors are handled per video, so one failure does not crash the whole run. Paging is capped per video.
- **Data cleaning and validation**: field validation, text cleaning and removal of invalid or duplicated rows.
- **Swappable toxicity classifier** (`toxicity.py`): an offline rule-based lexicon backend or a machine-learning transformer backend, selected with one environment variable.
- **Category-level scores**: the lexicon backend keeps a separate score per category (profanity, insult, threat, hate, spam) so each type can be analyzed on its own.
- **Exploratory analysis**: toxicity by channel, by topic, and against views, with a chart and CSV reports.
- **Two storage formats**: a flat CSV and a normalized SQLite database (separate `videos` and `comments` tables).
- **Interactive dashboard**: headline metrics, breakdown charts, a searchable and filterable list of the most toxic comments, CSV download, and a custom glassmorphism + claymorphism interface.

---

## Tech Stack

| Area | Technology |
|---|---|
| Language | Python |
| Data source | YouTube Data API v3 |
| Data processing | pandas |
| Storage | CSV, SQLite |
| Analysis and charts | EDA with Spearman rank correlation, charts saved as PNG |
| Toxicity scoring (default) | Custom weighted lexicon classifier (offline, no extra dependencies) |
| Toxicity scoring (optional) | `unitary/toxic-bert` via the `detoxify` package (PyTorch) |
| Dashboard | Streamlit, custom HTML and CSS |
| Configuration | Environment variables with `python-dotenv` (`.env`) |
| Hosting | Streamlit Community Cloud, source on GitHub |

---

## How It Works

```
extract.py    YouTube Data API v3  ->  data/raw_comments.jsonl
transform.py  validate, clean, score toxicity
load.py       writes CSV and SQLite
eda.py        toxicity by channel / topic / views, plus charts
toxicity.py   classifier used by transform.py (lexicon or transformer)
main.py       pipeline runner
app.py        Streamlit dashboard that reads the output files
```

### 1. Extract
Resolves the target channels (handle, then uploads playlist, then the most recent videos) or uses the video IDs you give it, then downloads comments and video statistics into `data/raw_comments.jsonl`.

### 2. Transform
Validates fields, cleans comment text, removes invalid and duplicated rows, and scores every comment for toxicity.

### 3. Load
Writes the cleaned dataset to `data/comments_clean.csv` and to a SQLite database, `data/youtube_toxicity.db`, with normalized `videos` and `comments` tables.

### 4. EDA
Produces the report tables and chart in `data/reports/`. Toxicity versus views is tested at two levels:

- **Video level**: per-video toxicity rate against log(views), using Spearman correlation (only videos with at least 10 comments are included).
- **Comment level**: raw toxicity score against views for all comments.

---

## Toxicity Classifiers

Switch backend with the `TOXICITY_BACKEND` environment variable.

| Backend | Value | Description |
|---|---|---|
| Lexicon (default) | `lexicon` | Five weighted category lexicons (profanity, insult, threat, hate, spam) plus text signals such as capital-letter ratio and exclamation spam. Works offline with no extra dependencies. Rule-based, so it misses subtle or sarcastic toxicity (recall is roughly 55% compared with the transformer). |
| Transformer | `transformer` | Uses `unitary/toxic-bert` through `detoxify`. Needs `pip install detoxify torch` and is better suited for real analysis. |

---

## Output Files

| File | Content |
|---|---|
| `data/raw_comments.jsonl` | Raw extracted comments (large, not tracked in Git) |
| `data/comments_clean.csv` | Cleaned and scored comments |
| `data/youtube_toxicity.db` | SQLite database with `videos` and `comments` tables |
| `data/reports/by_channel.csv` | Toxicity by channel |
| `data/reports/by_topic.csv` | Toxicity by topic |
| `data/reports/toxicity_vs_views.csv` | Toxicity versus views |
| `data/reports/toxicity_eda.png` | EDA chart |

The dashboard expects the cleaned CSV to contain the columns `text_clean`, `toxicity_score` and `is_toxic`.

---

## Dashboard

`app.py` is a Streamlit app (branded **Toxiscope**) with three tabs:

- **Breakdown**: animated bars for toxicity by channel and by topic, the toxicity-versus-views table, and raw tables on demand.
- **Explorer**: the most toxic comments as cards colored by severity, with text search, a minimum score filter, a result count, a channel filter (when the data has a channel column) and CSV download of the filtered results.
- **Charts**: the EDA chart produced by the pipeline.

The top of the page shows the total comments analyzed, the number of comments flagged toxic, the toxicity rate and the average toxicity score.

---

## Project Structure

```
yt-toxicity-analyzer/
├── app.py              # Streamlit dashboard
├── main.py             # Pipeline runner
├── config.py           # Settings (channels, videos, limits, API key from env)
├── extract.py          # YouTube API extraction
├── transform.py        # Validation, cleaning, scoring
├── toxicity.py         # Lexicon and transformer classifiers
├── load.py             # CSV and SQLite output
├── eda.py              # Analysis and charts
├── requirements.txt    # Python dependencies
├── .gitignore
└── data/
    ├── comments_clean.csv
    ├── youtube_toxicity.db
    └── reports/
```

---

## Getting Started

### Prerequisites
- Python 3 and Git
- A YouTube Data API v3 key (only needed to run the pipeline, not the dashboard)

### 1. Clone and create a virtual environment

```bash
git clone https://github.com/sania-Ashfak/yt-toxicity-analyzer.git
cd yt-toxicity-analyzer

# Windows
python -m venv .venv
.venv\Scripts\activate

# macOS / Linux
python3 -m venv .venv
source .venv/bin/activate
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Get a YouTube API key
1. Open the [Google Cloud Console](https://console.cloud.google.com/) and create a project.
2. Go to **APIs & Services -> Library**, search for **YouTube Data API v3** and enable it.
3. Go to **APIs & Services -> Credentials -> Create Credentials -> API key**.
4. Restrict the key to the YouTube Data API v3.

The free tier gives 10,000 quota units per day. Reading comments costs about 1 unit per 100 comments.

### 4. Add your key

Create a file named `.env` in the project root:

```
YOUTUBE_API_KEY=your_key_here
```

`.env` is listed in `.gitignore`. **Never commit your key.**

### 5. Choose what to analyze

Edit `config.py`:

```python
VIDEO_IDS = []                 # specific video IDs, or leave empty
CHANNELS = ["@channelname"]    # channel handles to analyze
MAX_COMMENTS_PER_VIDEO = 500
```

For a first run, use one small channel and `MAX_COMMENTS_PER_VIDEO = 100`.

### 6. Run the pipeline

```bash
python main.py all
```

You can also run a single stage:

```bash
python main.py extract
python main.py transform
python main.py load
python main.py eda
```

To use the ML classifier:

```bash
pip install torch transformers detoxify

# macOS / Linux
TOXICITY_BACKEND=transformer python main.py all

# Windows PowerShell
$env:TOXICITY_BACKEND="transformer"; python main.py all
```

### 7. Launch the dashboard

```bash
streamlit run app.py
```

It opens at `http://localhost:8501`.

---

## Deployment

The live dashboard runs on **Streamlit Community Cloud**, deployed from this repository:

- Branch: `main`
- Main file: `app.py`
- Dependencies: `requirements.txt`

Because the dashboard only reads `data/comments_clean.csv` and `data/reports/`, no API key or secret is configured on the server. To refresh the live data, run the pipeline locally and push the updated `data/` files; Streamlit redeploys on every push.

---

## Troubleshooting

| Problem | Fix |
|---|---|
| `Set YOUTUBE_API_KEY env var` | Check that `.env` exists in the project root, has no quotes or spaces around `=`, and is saved. |
| `403 quotaExceeded` | The daily quota is used up. Wait about 24 hours or lower `MAX_COMMENTS_PER_VIDEO`. |
| `python is not recognized` (Windows) | Use `py` instead of `python`, or reinstall Python with "Add to PATH" checked. |
| `pip install torch` fails | Use the command from [pytorch.org](https://pytorch.org/) matching your system. The CPU-only build is enough. |
| Dashboard says `comments_clean.csv not found` | Run `python main.py all` first, or make sure `data/` was pushed. |

---

## Limitations and Responsible Use

- Toxicity scores are produced by automated classifiers and are estimates, not judgments about people. The lexicon backend in particular misses context, sarcasm and new slang.
- Comments are public YouTube data. Do not publish personal identifiers such as author names or IDs.
- Use of the YouTube API is subject to the [YouTube API Services Terms of Service](https://developers.google.com/youtube/terms/api-services-terms-of-service), including limits on how long API data may be stored.

---

## Contributors

- [@sania-Ashfak](https://github.com/sania-Ashfak)
- [@minaheljaved007](https://github.com/minaheljaved007)
-  [@asma Mushtaq]( https://github.com/2025AI263)
-  [@ushna fatima](https://github.com/ushna-25)
