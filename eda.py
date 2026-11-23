"""Generate toxicity summary reports and a dashboard-ready EDA chart."""
from __future__ import annotations

import os
import sqlite3

import matplotlib
matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.ticker import PercentFormatter
from scipy import stats

import config


def load_frames() -> pd.DataFrame:
    """Load comments and video metadata from the project's SQLite database."""
    with sqlite3.connect(config.DB_PATH) as connection:
        comments = pd.read_sql_query("SELECT * FROM comments", connection)
        videos = pd.read_sql_query("SELECT * FROM videos", connection)

    if comments.empty:
        raise ValueError(f"No comments found in database: {config.DB_PATH}")

    video_columns = [
        column for column in ("video_id", "channel", "view_count", "video_title")
        if column in videos.columns
    ]
    if "video_id" not in video_columns:
        raise ValueError("The videos table must contain a video_id column.")

    return comments.merge(
        videos[video_columns].drop_duplicates("video_id"),
        on="video_id",
        how="left",
        suffixes=("", "_video"),
    )


def by_channel(df: pd.DataFrame) -> pd.DataFrame:
    """Summarize comment counts and toxicity rate for each channel."""
    if "channel" not in df.columns:
        return pd.DataFrame(
            columns=["comments", "toxic", "mean_toxicity", "median_views", "toxicity_rate"]
        )

    work = df.copy()
    work["is_toxic"] = pd.to_numeric(work["is_toxic"], errors="coerce").fillna(0)
    if "toxicity_score" in work:
        work["toxicity_score"] = pd.to_numeric(work["toxicity_score"], errors="coerce")
    if "view_count" in work:
        work["view_count"] = pd.to_numeric(work["view_count"], errors="coerce")
    else:
        work["view_count"] = np.nan

    result = (
        work.dropna(subset=["channel"])
        .groupby("channel")
        .agg(
            comments=("is_toxic", "size"),
            toxic=("is_toxic", "sum"),
            mean_toxicity=("toxicity_score", "mean"),
            median_views=("view_count", "median"),
        )
    )
    result["toxicity_rate"] = result["toxic"] / result["comments"]
    return result.sort_values("toxicity_rate", ascending=False).round(6)


def by_topic(df: pd.DataFrame) -> pd.DataFrame:
    """Summarize toxicity by topic; omit groups with fewer than five comments."""
    if not {"topic", "is_toxic"}.issubset(df.columns):
        return pd.DataFrame(columns=["comments", "toxic", "toxicity_rate"])

    work = df[["topic", "is_toxic"]].copy()
    work["is_toxic"] = pd.to_numeric(work["is_toxic"], errors="coerce").fillna(0)
    result = (
        work.dropna(subset=["topic"])
        .groupby("topic")
        .agg(comments=("is_toxic", "size"), toxic=("is_toxic", "sum"))
    )
    result["toxicity_rate"] = result["toxic"] / result["comments"]
    result = result[result["comments"] >= 5]
    return result.sort_values("toxicity_rate", ascending=False).round(6)


def toxicity_vs_views(df: pd.DataFrame):
    """Calculate Spearman correlations using valid, non-negative view counts."""
    needed = {"video_id", "channel", "view_count", "is_toxic", "toxicity_score"}
    if not needed.issubset(df.columns):
        return {}, pd.DataFrame()

    work = df.copy()
    for column in ("view_count", "is_toxic", "toxicity_score"):
        work[column] = pd.to_numeric(work[column], errors="coerce")
    work = work.dropna(subset=["video_id", "channel", "view_count", "is_toxic"])
    work = work[work["view_count"] >= 0]

    per_video = (
        work.groupby(["video_id", "channel"], dropna=True)
        .agg(
            view_count=("view_count", "first"),
            toxicity_rate=("is_toxic", "mean"),
            n_comments=("is_toxic", "size"),
            **({"video_title": ("video_title", "first")} if "video_title" in work.columns else {}),
        )
        .reset_index()
    )
    qualified = per_video[per_video["n_comments"] >= 10]
    results = {}

    if len(qualified) >= 3 and qualified["toxicity_rate"].nunique() > 1:
        rho, p_value = stats.spearmanr(
            np.log1p(qualified["view_count"]),
            qualified["toxicity_rate"],
            nan_policy="omit",
        )
        if np.isfinite(rho) and np.isfinite(p_value):
            results["video_level"] = {
                "spearman_rho": round(float(rho), 3),
                "p_value": round(float(p_value), 4),
                "n_videos": int(len(qualified)),
            }

    comment_data = work.dropna(subset=["toxicity_score"])
    if (
        len(comment_data) >= 3
        and comment_data["toxicity_score"].nunique() > 1
        and comment_data["view_count"].nunique() > 1
    ):
        rho, p_value = stats.spearmanr(
            np.log1p(comment_data["view_count"]),
            comment_data["toxicity_score"],
            nan_policy="omit",
        )
        if np.isfinite(rho) and np.isfinite(p_value):
            results["comment_level"] = {
                "spearman_rho": round(float(rho), 3),
                "p_value": round(float(p_value), 4),
                "n_comments": int(len(comment_data)),
            }

    return results, per_video


def make_plots(
    df: pd.DataFrame,
    channel_report: pd.DataFrame,
    per_video: pd.DataFrame,
    output_dir: str,
) -> str:
    """Create the two-panel dark-theme report chart (channel rate, reach vs. toxicity)."""
    os.makedirs(output_dir, exist_ok=True)

    background = "#10221b"
    panel = "#172f26"
    text = "#e8f2ec"
    muted = "#abc1b4"
    grid = "#365247"
    lime = "#c8ef75"
    coral = "#ff8791"
    blue = "#7ec7df"

    plt.rcParams["axes.titlecolor"] = text  # set_title(loc="left") ignores ax.title.set_color
    fig, axes = plt.subplots(
        1, 2, figsize=(12.5, 5.8), facecolor=background, constrained_layout=True
    )

    for ax in axes:
        ax.set_facecolor(panel)
        ax.tick_params(colors=muted, labelsize=9)
        ax.xaxis.label.set_color(muted)
        ax.yaxis.label.set_color(muted)
        for spine in ax.spines.values():
            spine.set_color(grid)
        ax.grid(axis="x", color=grid, linestyle="--", linewidth=0.6, alpha=0.55)
        ax.set_axisbelow(True)

    # Channel toxicity rate
    ax = axes[0]
    rates = (
        pd.to_numeric(channel_report.get("toxicity_rate", pd.Series(dtype=float)), errors="coerce")
        .dropna()
        .sort_values()
    )
    if not rates.empty:
        bars = ax.barh(rates.index.astype(str), rates.values, color=lime, height=0.62)
        ax.set_title("Toxicity rate by channel", loc="left", fontweight="bold")
        ax.set_xlabel("Share of comments flagged toxic")
        ax.xaxis.set_major_formatter(PercentFormatter(xmax=1))
        max_rate = float(rates.max())
        right = max(max_rate * 1.35, 0.01)
        ax.set_xlim(0, right)
        for bar, value in zip(bars, rates.values):
            ax.text(
                value + right * 0.025,
                bar.get_y() + bar.get_height() / 2,
                f"{value:.2%}",
                va="center",
                color=text,
                fontsize=8,
            )
    else:
        ax.set_title("Toxicity rate by channel", loc="left", fontweight="bold")
        ax.text(.5, .5, "No channel data", ha="center", va="center", color=muted, transform=ax.transAxes)

    # Video views vs. toxicity rate
    ax = axes[1]
    plot_data = per_video.copy()
    required = {"view_count", "toxicity_rate", "channel"}
    if required.issubset(plot_data.columns):
        plot_data["view_count"] = pd.to_numeric(plot_data["view_count"], errors="coerce")
        plot_data["toxicity_rate"] = pd.to_numeric(plot_data["toxicity_rate"], errors="coerce")
        plot_data = plot_data.dropna(subset=["view_count", "toxicity_rate"])
        plot_data = plot_data[plot_data["view_count"] >= 0]
        plot_data["log_views"] = np.log1p(plot_data["view_count"])
    else:
        plot_data = pd.DataFrame()

    ax.set_title("Video reach vs. toxicity", loc="left", fontweight="bold")
    if not plot_data.empty:
        for index, (channel, group) in enumerate(plot_data.groupby("channel")):
            ax.scatter(
                group["log_views"],
                group["toxicity_rate"],
                label=str(channel),
                s=38,
                alpha=.82,
                color=[lime, blue, coral, "#f3c76c", "#b79cff", "#7be0b0"][index % 6],
                edgecolors=background,
                linewidths=.45,
            )

        x_values = plot_data["log_views"].to_numpy(dtype=float)
        y_values = plot_data["toxicity_rate"].to_numpy(dtype=float)
        if len(x_values) >= 2 and np.unique(x_values).size >= 2:
            slope, intercept = np.polyfit(x_values, y_values, 1)
            line_x = np.linspace(x_values.min(), x_values.max(), 100)
            ax.plot(line_x, slope * line_x + intercept, color=coral, linestyle="--", linewidth=1.5)

        ax.set_xlabel("log(1 + video views)")
        ax.set_ylabel("Toxicity rate")
        ax.yaxis.set_major_formatter(PercentFormatter(xmax=1))
        if plot_data["channel"].nunique() <= 6:
            legend = ax.legend(fontsize=8, frameon=True)
            if legend:
                legend.get_frame().set_facecolor(panel)
                legend.get_frame().set_edgecolor(grid)
                for label in legend.get_texts():
                    label.set_color(text)
    else:
        ax.text(.5, .5, "Not enough video data", ha="center", va="center", color=muted, transform=ax.transAxes)

    output_path = os.path.join(output_dir, "toxicity_eda.png")
    fig.savefig(
        output_path,
        dpi=180,
        facecolor=fig.get_facecolor(),
        bbox_inches="tight",
    )
    plt.close(fig)
    return output_path


def run() -> None:
    df = load_frames()
    channel_report = by_channel(df)
    topic_report = by_topic(df)
    results, per_video = toxicity_vs_views(df)

    os.makedirs(config.REPORT_DIR, exist_ok=True)
    channel_report.to_csv(os.path.join(config.REPORT_DIR, "by_channel.csv"))
    topic_report.to_csv(os.path.join(config.REPORT_DIR, "by_topic.csv"))
    pd.DataFrame(results).T.to_csv(
        os.path.join(config.REPORT_DIR, "toxicity_vs_views.csv"), index_label="level"
    )
    per_video.to_csv(os.path.join(config.REPORT_DIR, "per_video.csv"), index=False)

    chart_path = make_plots(df, channel_report, per_video, config.REPORT_DIR)

    print("\n=== TOXICITY BY CHANNEL ===\n", channel_report)
    print("\n=== TOXICITY BY TOPIC ===\n", topic_report.head(10))
    print("\n=== TOXICITY VS. VIEWS ===\n", pd.DataFrame(results).T)
    print(f"\nEDA reports written to {config.REPORT_DIR}; chart: {chart_path}")


if __name__ == "__main__":
    run()
