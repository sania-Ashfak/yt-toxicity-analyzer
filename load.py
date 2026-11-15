"""LOAD: persist the transformed DataFrame to CSV + SQLite.

Schema: two normalized tables (videos 1-N comments), plus indexes for EDA.
"""
import os, sqlite3
import pandas as pd
import config

DDL = """
CREATE TABLE IF NOT EXISTS videos (
    video_id      TEXT PRIMARY KEY,
    video_title   TEXT,
    channel       TEXT,
    published_at  TEXT,
    view_count    INTEGER,
    like_count    INTEGER,
    comment_count INTEGER
);
CREATE TABLE IF NOT EXISTS comments (
    comment_id     TEXT PRIMARY KEY,
    video_id       TEXT REFERENCES videos(video_id),
    author         TEXT,
    text           TEXT,
    text_clean     TEXT,
    like_count     INTEGER,
    reply_count    INTEGER,
    published_at   TEXT,
    toxicity_score REAL,
    is_toxic       INTEGER,
    topic          TEXT
);
CREATE INDEX IF NOT EXISTS idx_comments_video ON comments(video_id);
CREATE INDEX IF NOT EXISTS idx_comments_toxic ON comments(is_toxic);
"""

VIDEO_COLS = ["video_id", "video_title", "channel", "published_at",
              "view_count", "like_count", "comment_count"]
COMMENT_COLS = ["comment_id", "video_id", "author", "text", "text_clean",
                "like_count", "reply_count", "published_at",
                "toxicity_score", "is_toxic", "topic"]


def run(df: pd.DataFrame):
    os.makedirs(config.DATA_DIR, exist_ok=True)

    # ---- CSV ----
    df.to_csv(config.CLEAN_CSV, index=False)
    print(f"LOAD csv  -> {config.CLEAN_CSV} ({len(df)} rows)")

    # ---- SQLite ----
    if os.path.exists(config.DB_PATH):
        os.remove(config.DB_PATH)                    # idempotent rebuild
    con = sqlite3.connect(config.DB_PATH)
    con.executescript(DDL)
    vcols = [c for c in VIDEO_COLS if c in df.columns]
    df[vcols].drop_duplicates("video_id").to_sql("videos", con, if_exists="append", index=False)
    ccols = [c for c in COMMENT_COLS if c in df.columns]
    df[ccols].to_sql("comments", con, if_exists="append", index=False)
    con.commit()
    print(f"LOAD db   -> {config.DB_PATH}")
    print(pd.read_sql("SELECT COUNT(*) AS comments, SUM(is_toxic) AS toxic "
                      "FROM comments", con).to_string(index=False))
    con.close()


if __name__ == "__main__":
    from transform import run as transform_run
    run(transform_run())
