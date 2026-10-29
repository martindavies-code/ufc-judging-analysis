"""Visualizer for UFC judging analysis: generates publication-quality charts.

Plots round-level and fight-level disagreement rates, veteran rankings,
scatter distributions, and historical trends over time.
"""

import logging
import sqlite3
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import matplotlib.pyplot as plt
import pandas as pd
from matplotlib import ticker

logger = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"
OUTPUT_DIR = PROJECT_ROOT / "output"
DB_PATH = DATA_DIR / "ufc_judging.db"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Set clean aesthetic styling
plt.rcParams["font.family"] = "sans-serif"
plt.rcParams["font.sans-serif"] = ["DejaVu Sans", "Arial", "Helvetica"]
plt.rcParams["axes.edgecolor"] = "#cccccc"
plt.rcParams["axes.linewidth"] = 0.8


def generate_visualizations(db_path: Path = DB_PATH) -> None:
    """Generate all analytical visualizations for the web dashboard and report."""
    if not db_path.exists():
        logger.warning("Database %s not found.", db_path)
        return

    conn = sqlite3.connect(db_path)
    try:
        conn.execute("PRAGMA busy_timeout = 5000")
        df_fights = pd.read_sql("SELECT * FROM fights", conn)
        df_judges = pd.read_sql("SELECT * FROM judge_appearances", conn)
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='round_scores'")
        has_rounds = cursor.fetchone() is not None
        df_rounds = pd.read_sql("SELECT * FROM round_scores", conn) if has_rounds else pd.DataFrame()
    finally:
        conn.close()

    # ========================================================
    # 1. ROUND-LEVEL VISUALIZATIONS (PRIMARY)
    # ========================================================
    if not df_rounds.empty:
        from src.analyzer import calculate_judge_round_metrics

        round_stats = calculate_judge_round_metrics(df_rounds)

        # Chart R1: Round Disagreement Rate - Min 50 Rounds
        plt.figure(figsize=(10, 6), dpi=300)
        top_50_rounds = (
            round_stats[round_stats["total_rounds"] >= 50].sort_values(by="round_dissent_pct", ascending=True).tail(12)
        )
        colors_r50 = [
            "#e74c3c" if x >= 8.5 else "#e67e22" if x >= 7.0 else "#3498db" for x in top_50_rounds["round_dissent_pct"]
        ]
        bars_r50 = plt.barh(
            top_50_rounds["judge_name"], top_50_rounds["round_dissent_pct"], color=colors_r50, height=0.65
        )

        for bar in bars_r50:
            w = bar.get_width()
            plt.text(
                w + 0.15,
                bar.get_y() + bar.get_height() / 2,
                f"{w:.1f}%",
                va="center",
                ha="left",
                fontsize=9,
                fontweight="bold",
                color="#2c3e50",
            )

        plt.title(
            "UFC Judges with Highest Round Disagreement Rate\n(Minimum 50 Rounds Judged, 1995–2026)",
            fontsize=13,
            fontweight="bold",
            pad=15,
        )
        plt.xlabel("Round Disagreement Rate (% of Rounds Dissented from Both Colleagues)", fontsize=10, labelpad=10)
        plt.xlim(0, max(14, top_50_rounds["round_dissent_pct"].max() + 2))
        plt.grid(axis="x", linestyle="--", alpha=0.5)
        plt.tight_layout()
        plt.savefig(OUTPUT_DIR / "round_dissent_rate_min_50.png")
        plt.close()

        # Chart R2: Round Disagreement Rate - Veteran Judges (Min 250 Rounds)
        plt.figure(figsize=(10, 6), dpi=300)
        top_vet_rounds = (
            round_stats[round_stats["total_rounds"] >= 250].sort_values(by="round_dissent_pct", ascending=True).tail(12)
        )
        colors_vet = [
            "#e74c3c" if x >= 8.0 else "#e67e22" if x >= 6.5 else "#3498db" for x in top_vet_rounds["round_dissent_pct"]
        ]
        bars_vet = plt.barh(
            top_vet_rounds["judge_name"], top_vet_rounds["round_dissent_pct"], color=colors_vet, height=0.65
        )

        for bar in bars_vet:
            w = bar.get_width()
            plt.text(
                w + 0.12,
                bar.get_y() + bar.get_height() / 2,
                f"{w:.2f}%",
                va="center",
                ha="left",
                fontsize=9,
                fontweight="bold",
                color="#2c3e50",
            )

        plt.title(
            "Top Veteran UFC Judges by Round Disagreement Rate\n(Minimum 250 Rounds Judged)",
            fontsize=13,
            fontweight="bold",
            pad=15,
        )
        plt.xlabel("Round Disagreement Rate (%)", fontsize=10, labelpad=10)
        plt.xlim(0, max(12, top_vet_rounds["round_dissent_pct"].max() + 2))
        plt.grid(axis="x", linestyle="--", alpha=0.5)
        plt.tight_layout()
        plt.savefig(OUTPUT_DIR / "round_dissent_rate_min_250.png")
        plt.close()

        # Chart R3: Scatter Plot - Total Rounds vs Round Dissent Rate
        plt.figure(figsize=(11, 7), dpi=300)
        active_round_judges = round_stats[round_stats["total_rounds"] >= 50].copy()

        plt.scatter(
            active_round_judges["total_rounds"],
            active_round_judges["round_dissent_pct"],
            alpha=0.65,
            s=active_round_judges["total_rounds"] * 0.15 + 40,
            c=active_round_judges["round_dissent_pct"],
            cmap="plasma",
            edgecolor="k",
            linewidth=0.5,
        )

        notable_round = [
            "Ben Cartlidge",
            "Eric Colón",
            "Derek Cleary",
            "Chris Lee",
            "Sal D'Amato",
            "Michael Bell",
            "Tony Weeks",
            "Adalaide Byrd",
            "Junichiro Kamijo",
            "Ron McCarthy",
            "Dave Tirelli",
        ]

        for name in notable_round:
            match = active_round_judges[active_round_judges["judge_name"] == name]
            if not match.empty:
                r = match.iloc[0]
                plt.annotate(
                    f"{name}\n({r['round_dissent_pct']:.1f}%, {int(r['total_rounds'])} rds)",
                    (r["total_rounds"], r["round_dissent_pct"]),
                    textcoords="offset points",
                    xytext=(0, 10),
                    ha="center",
                    fontsize=8,
                    fontweight="semibold",
                    bbox={"boxstyle": "round,pad=0.2", "fc": "white", "ec": "#888888", "alpha": 0.85},
                )

        plt.title("UFC Judging: Total Rounds Judged vs Round Disagreement Rate", fontsize=13, fontweight="bold", pad=15)
        plt.xlabel("Total UFC Rounds Judged", fontsize=10, labelpad=10)
        plt.ylabel("Round Disagreement Rate (%)", fontsize=10, labelpad=10)
        plt.grid(True, linestyle="--", alpha=0.5)
        plt.tight_layout()
        plt.savefig(OUTPUT_DIR / "scatter_rounds_vs_dissent.png")
        plt.close()

        # Chart R4: Round Disagreement Rate Trend Over Time
        df_rounds["year_num"] = pd.to_numeric(df_rounds["event_year"], errors="coerce")
        valid_rounds = df_rounds.dropna(subset=["year_num"])
        valid_rounds = valid_rounds[valid_rounds["year_num"] >= 2005]
        if not valid_rounds.empty:
            yearly_rounds = (
                valid_rounds.groupby("year_num")
                .agg(total=("round_num", "count"), dissents=("round_dissented", "sum"))
                .reset_index()
            )
            yearly_rounds["dissent_pct"] = (yearly_rounds["dissents"] / yearly_rounds["total"]) * 100

            plt.figure(figsize=(10, 5), dpi=300)
            plt.plot(
                yearly_rounds["year_num"],
                yearly_rounds["dissent_pct"],
                marker="s",
                color="#2980b9",
                linewidth=2.5,
                markersize=6,
            )
            mean_rd = yearly_rounds["dissent_pct"].mean()
            plt.axhline(mean_rd, color="#e74c3c", linestyle=":", label=f"Historical Average ({mean_rd:.1f}%)")
            plt.title(
                "UFC Round Disagreement Rate Over Time (2005–2026)\nPercentage of Scored Rounds Where a Judge Dissented",
                fontsize=13,
                fontweight="bold",
                pad=15,
            )
            plt.xlabel("Year", fontsize=10, labelpad=10)
            plt.ylabel("Round Disagreement Rate (%)", fontsize=10, labelpad=10)
            plt.gca().xaxis.set_major_locator(ticker.MultipleLocator(2))
            plt.legend(frameon=True, facecolor="white", framealpha=0.9)
            plt.grid(True, linestyle="--", alpha=0.5)
            plt.tight_layout()
            plt.savefig(OUTPUT_DIR / "round_disagreement_trend.png")
            plt.close()

    # ========================================================
    # 2. FIGHT-LEVEL VISUALIZATIONS (HISTORICAL COMPARISON)
    # ========================================================
    if not df_judges.empty:
        fight_stats = (
            df_judges.groupby("judge_name")
            .agg(total_fights=("fight", "count"), dissents=("disagreed_with_both", "sum"))
            .reset_index()
        )
        fight_stats["dissent_pct"] = (fight_stats["dissents"] / fight_stats["total_fights"]) * 100

        # Chart F1: Min 50 Fights
        plt.figure(figsize=(10, 6), dpi=300)
        top_50 = fight_stats[fight_stats["total_fights"] >= 50].sort_values(by="dissent_pct", ascending=True).tail(12)
        colors = ["#e74c3c" if x >= 12 else "#e67e22" if x >= 9 else "#3498db" for x in top_50["dissent_pct"]]
        bars = plt.barh(top_50["judge_name"], top_50["dissent_pct"], color=colors, height=0.65)
        for bar in bars:
            w = bar.get_width()
            plt.text(
                w + 0.3,
                bar.get_y() + bar.get_height() / 2,
                f"{w:.1f}%",
                va="center",
                ha="left",
                fontsize=9,
                fontweight="bold",
                color="#2c3e50",
            )
        plt.title(
            "UFC Judges with Highest Fight Decision Disagreement Rate\n(Minimum 50 Fights Judged, 1995–2026)",
            fontsize=13,
            fontweight="bold",
            pad=15,
        )
        plt.xlabel("Disagreement Percentage (% of Split Decisions Dissented)", fontsize=10, labelpad=10)
        plt.xlim(0, 26)
        plt.grid(axis="x", linestyle="--", alpha=0.5)
        plt.tight_layout()
        plt.savefig(OUTPUT_DIR / "dissent_rate_min_50.png")
        plt.close()

        # Chart F2: Min 100 Fights
        plt.figure(figsize=(10, 6), dpi=300)
        top_100 = fight_stats[fight_stats["total_fights"] >= 100].sort_values(by="dissent_pct", ascending=True).tail(12)
        colors_100 = ["#e74c3c" if x >= 10 else "#e67e22" if x >= 8 else "#3498db" for x in top_100["dissent_pct"]]
        bars_100 = plt.barh(top_100["judge_name"], top_100["dissent_pct"], color=colors_100, height=0.65)
        for bar in bars_100:
            w = bar.get_width()
            plt.text(
                w + 0.15,
                bar.get_y() + bar.get_height() / 2,
                f"{w:.2f}%",
                va="center",
                ha="left",
                fontsize=9,
                fontweight="bold",
                color="#2c3e50",
            )
        plt.title(
            "Top Veteran UFC Judges by Fight Decision Disagreement Rate\n(Minimum 100 Fights Judged)",
            fontsize=13,
            fontweight="bold",
            pad=15,
        )
        plt.xlabel("Disagreement Percentage (%)", fontsize=10, labelpad=10)
        plt.xlim(0, 15)
        plt.grid(axis="x", linestyle="--", alpha=0.5)
        plt.tight_layout()
        plt.savefig(OUTPUT_DIR / "dissent_rate_min_100.png")
        plt.close()

        # Chart F3: Scatter Fights vs Dissent
        plt.figure(figsize=(11, 7), dpi=300)
        active_fights = fight_stats[fight_stats["total_fights"] >= 25].copy()
        plt.scatter(
            active_fights["total_fights"],
            active_fights["dissent_pct"],
            alpha=0.6,
            s=active_fights["total_fights"] * 0.4 + 40,
            c=active_fights["dissent_pct"],
            cmap="viridis",
            edgecolor="k",
            linewidth=0.5,
        )
        plt.title(
            "UFC Judging: Total Decisions Judged vs Fight Decision Dissent Rate", fontsize=13, fontweight="bold", pad=15
        )
        plt.xlabel("Total UFC Decisions Judged", fontsize=10, labelpad=10)
        plt.ylabel("Decision Dissent Percentage (%)", fontsize=10, labelpad=10)
        plt.grid(True, linestyle="--", alpha=0.5)
        plt.tight_layout()
        plt.savefig(OUTPUT_DIR / "scatter_fights_vs_dissent.png")
        plt.close()

    # Chart F4: Split Decision Trend
    if not df_fights.empty:
        df_fights["year_int"] = pd.to_numeric(df_fights["event_year"], errors="coerce")
        yearly = (
            df_fights.groupby("year_int")
            .agg(
                total=("decision_type", "count"),
                split=("decision_type", lambda s: s.str.contains("Split", case=False, na=False).sum()),
            )
            .reset_index()
        )
        yearly["split_pct"] = (yearly["split"] / yearly["total"]) * 100
        yearly = yearly[yearly["year_int"] >= 2004]

        plt.figure(figsize=(10, 5), dpi=300)
        plt.plot(yearly["year_int"], yearly["split_pct"], marker="o", color="#8e44ad", linewidth=2.5, markersize=6)
        plt.axhline(
            yearly["split_pct"].mean(),
            color="#e74c3c",
            linestyle=":",
            label=f"Historical Average ({yearly['split_pct'].mean():.1f}%)",
        )
        plt.title(
            "UFC Split Decision Rate Over Time (2004–2026)\nPercentage of Decisions with a Dissenting Judge",
            fontsize=13,
            fontweight="bold",
            pad=15,
        )
        plt.xlabel("Year", fontsize=10, labelpad=10)
        plt.ylabel("Split Decisions (%)", fontsize=10, labelpad=10)
        plt.gca().xaxis.set_major_locator(ticker.MultipleLocator(2))
        plt.legend(frameon=True, facecolor="white", framealpha=0.9)
        plt.grid(True, linestyle="--", alpha=0.5)
        plt.tight_layout()
        plt.savefig(OUTPUT_DIR / "split_decision_trend.png")
        plt.close()

    logger.info("All visualizations successfully updated in %s", OUTPUT_DIR)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    generate_visualizations()
