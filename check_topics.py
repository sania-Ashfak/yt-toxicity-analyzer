import pandas as pd

df = pd.read_csv("data/comments_clean.csv")
print("Columns:", df.columns.tolist())

if "video_title" in df.columns and "topic" in df.columns:
    print(df[["video_title", "topic"]].drop_duplicates().head(30).to_string(index=False))
    print("\nTopic counts:")
    print(df["topic"].value_counts(dropna=False))
else:
    print("The cleaned CSV is missing video_title or topic.")