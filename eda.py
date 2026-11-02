"""EDA: toxicity rate by channel / topic, and toxicity vs. view-count relationship."""
import os, sqlite3
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from scipy import stats
import config


def load_frames():
    con = sqlite3.connect(config.DB_PATH)
    comments = pd.read_sql("SELECT * FROM comments", con)
    videos   = pd.read_sql("SELECT * FROM videos",   con)
    con.close()
    df = comments.merge(videos[["video_id", "channel", "view_count", "video_title"]],
                        on="video_id", how="left")
    return df


def by_channel(df: pd.DataFrame) -> pd.DataFrame:
    g = (df.groupby("channel")
           .agg(comments=("is_toxic", "size"),
                toxic=("is_toxic", "sum"),
                mean_toxicity=("toxicity_score", "mean"),
                median_views=("view_count", "median"))
           .assign(toxicity_rate=lambda x: x["toxic"] / x["comments"])
           .sort_values("toxicity_rate", ascending=False))
    return g.round(4)


def by_topic(df: pd.DataFrame) -> pd.DataFrame:
    g = (df.groupby("topic")
           .agg(comments=("is_toxic", "size"), toxic=("is_toxic", "sum"))
           .assign(toxicity_rate=lambda x: x["toxic"] / x["comments"])
           .query("comments >= 5")                      # filter tiny samples
           .sort_values("toxicity_rate", ascending=False))
    return g.round(4)


def toxicity_vs_views(df: pd.DataFrame) -> dict:
    """Two lenses: per-video rate vs. video views; per-comment score vs. views."""
    per_video = (df.groupby(["video_id", "channel"])
                   .agg(view_count=("view_count", "first"),
                        toxicity_rate=("is_toxic", "mean"),
                        n_comments=("is_toxic", "size"))
                   .reset_index())
    pv = per_video[per_video["n_comments"] >= 10]      # rate needs enough comments
    res = {}
    if len(pv) >= 3:
        rho, p = stats.spearmanr(np.log1p(pv["view_count"]), pv["toxicity_rate"])
        res["video_level"] = {"spearman_rho": round(rho, 3), "p_value": round(p, 4),
                              "n_videos": len(pv)}
    rho2, p2 = stats.spearmanr(np.log1p(df["view_count"]), df["toxicity_score"])
    res["comment_level"] = {"spearman_rho": round(rho2, 3), "p_value": round(p2, 4),
                            "n_comments": len(df)}
    return res, per_video


def make_plots(df, chan, pv, outdir):
    os.makedirs(outdir, exist_ok=True)
    fig, axes = plt.subplots(1, 3, figsize=(17, 5))

    chan["toxicity_rate"].plot.bar(ax=axes[0], color="#e4572e")
    axes[0].set_title("Toxicity rate by channel"); axes[0].set_ylabel("rate")
    axes[0].tick_params(axis="x", rotation=20)

    ax = axes[1]
    for ch, sub in pv.groupby("channel"):
        ax.scatter(np.log1p(sub["view_count"]), sub["toxicity_rate"],
                   label=ch, alpha=0.7)
    z = np.polyfit(np.log1p(pv["view_count"]), pv["toxicity_rate"], 1)
    xs = np.linspace(np.log1p(pv["view_count"]).min(), np.log1p(pv["view_count"]).max(), 50)
    ax.plot(xs, np.polyval(z, xs), "k--", alpha=0.6)
    ax.set_title("Video views (log) vs. comment toxicity rate")
    ax.set_xlabel("log(1 + views)"); ax.set_ylabel("toxicity rate"); ax.legend(fontsize=8)

    top = df.groupby("topic")["toxicity_score"].mean().nlargest(10).sort_values()
    top.plot.barh(ax=axes[2], color="#2e86ab")
    axes[2].set_title("Mean toxicity score by topic (top 10)")

    fig.tight_layout()
    path = os.path.join(outdir, "toxicity_eda.png")
    fig.savefig(path, dpi=120); plt.close(fig)
    return path


def run():
    df = load_frames()
    chan = by_channel(df);            print("\n=== TOXICITY BY CHANNEL ===\n", chan)
    top  = by_topic(df);              print("\n=== TOXICITY BY TOPIC (n>=5) ===\n", top.head(10))
    res, pv = toxicity_vs_views(df)
    print("\n=== TOXICITY vs VIEWS (Spearman, views log-transformed) ===")
    for lvl, r in res.items():
        print(f"  {lvl}: rho={r['spearman_rho']}  p={r['p_value']}  n={list(r.values())[-1]}")

    chan.to_csv(os.path.join(config.REPORT_DIR, "..", "by_channel.csv")) if os.path.isdir(config.REPORT_DIR) else None
    os.makedirs(config.REPORT_DIR, exist_ok=True)
    chan.to_csv(os.path.join(config.REPORT_DIR, "by_channel.csv"))
    top.to_csv(os.path.join(config.REPORT_DIR, "by_topic.csv"))
    pd.DataFrame(res).T.to_csv(os.path.join(config.REPORT_DIR, "toxicity_vs_views.csv"))
    path = make_plots(df, chan, pv, config.REPORT_DIR)
    print(f"\nEDA reports -> {config.REPORT_DIR} (chart: {path})")


if __name__ == "__main__":
    run()
