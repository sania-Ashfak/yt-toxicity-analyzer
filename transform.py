"""TRANSFORM: validate raw fields, clean text, run the toxicity classifier.

Input : data/raw_comments.jsonl   (from extract.py, or your own source)
Output: in-memory pandas DataFrame handed to load.py
"""
import json, html, re
import pandas as pd
import config, toxicity

REQUIRED = ["comment_id", "video_id", "text", "author", "like_count", "published_at"]
URL_RE  = re.compile(r"https?://\S+|www\.\S+")
WS_RE   = re.compile(r"\s+")


def validate(df: pd.DataFrame) -> pd.DataFrame:
    """Drop rows missing required fields; coerce dtypes; drop exact dupes."""
    before = len(df)
    df = df.dropna(subset=REQUIRED)
    df = df[df["text"].astype(str).str.strip().str.len() > 0]   # empty comments
    df = df.drop_duplicates(subset=["comment_id"])               # API double-pull
    df["like_count"] = pd.to_numeric(df["like_count"], errors="coerce").fillna(0).astype(int)
    df["published_at"] = pd.to_datetime(df["published_at"], errors="coerce", utc=True)
    print(f"VALIDATE: {before} -> {len(df)} rows "
          f"({before - len(df)} invalid/duplicated removed)")
    return df.reset_index(drop=True)


def clean_text(s: str) -> str:
    s = html.unescape(str(s))
    s = URL_RE.sub("[URL]", s)
    return WS_RE.sub(" ", s).strip()


def run(raw_path: str = config.RAW_PATH) -> pd.DataFrame:
    records = []
    with open(raw_path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                records.append(json.loads(line))
    df = validate(pd.DataFrame(records))

    df["text_clean"] = df["text"].map(clean_text)
    df["text_len"]   = df["text_clean"].str.len()

    print(f"CLASSIFY: scoring {len(df)} comments "
          f"(backend={config.TOXICITY_BACKEND}) ...")
    preds = df["text_clean"].map(toxicity.predict)
    df["toxicity_score"] = preds.map(lambda p: p["toxicity"])
    df["is_toxic"]       = preds.map(lambda p: p["is_toxic"])
    for cat in ["profanity", "insult", "threat", "hate", "spam"]:
        df[f"cat_{cat}"] = preds.map(
            lambda p, c=cat: p["categories"].get(c, p["categories"].get(c.replace("_", " "), 0.0)))

    df["topic"] = (df.get("video_title", "")
                     .str.lower()
                     .str.extract(r"#(\w+)", expand=False)      # hashtag = topic
                     .fillna("general"))
    print(f"TRANSFORM done: toxicity rate = {df['is_toxic'].mean():.2%}")
    return df


if __name__ == "__main__":
    run()
