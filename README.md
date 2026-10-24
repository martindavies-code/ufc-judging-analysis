# UFC Judging Disagreement & Dissent Analysis (1995–2026)

An empirical data science project analyzing every available UFC judge's scorecard in UFC history to determine **which judge disagrees with their other two colleagues the highest percentage of times**, evaluated directly at the **round scoring level** (each individual 5-minute round scored 10-9, 10-8, 10-10) and the overall fight decision level.

---

## Executive Summary: Round-by-Round Scoring Disagreements

Across **751 UFC events** from **1995 through 2026**, **4,010 UFC fights** went to a decision, yielding **31,881 individual 5-minute rounds scored** across **411 unique judges**.

A **Round Dissent** occurs when two cage-side colleagues agree on who won an individual round, while the third judge submits a dissenting score for the opposing fighter or a draw.

### Which judge disagrees with their other two colleagues the highest percentage of times on round scoring?

1. **UFC Veteran Mainstays (Minimum 250 Scored Rounds):**
   * 🥇 **Cardo Urso**: **9.32%** round dissent rate (29 dissents in 311 rounds)
   * 🥈 **Glenn Trowbridge**: **8.83%** (40 dissents in 453 rounds)
   * 🥉 **Rick Winter**: **8.75%** (30 dissents in 343 rounds)
   * 4️⃣ **Dave Tirelli**: **8.56%** (41 dissents in 479 rounds)
   * 5️⃣ **David Lethaby**: **8.50%** (54 dissents in 635 rounds)
   * 6️⃣ **Marcos Rosales**: **8.32%** (47 dissents in 565 rounds)
   * 7️⃣ **Paul Sutherland**: **8.16%** (23 dissents in 282 rounds)
   * 8️⃣ **Adalaide Byrd**: **8.14%** (55 dissents in 676 rounds)
   * 9️⃣ **Anders Ohlsson**: **7.80%** (23 dissents in 295 rounds)
   * 🔟 **Howard Hughes**: **7.63%** (27 dissents in 354 rounds)
   * 1️⃣1️⃣ **Eric Colón**: **7.61%** (98 dissents in 1,288 rounds)
   * 1️⃣2️⃣ **Derek Cleary**: **7.48%** (168 dissents in 2,246 rounds)
   * 1️⃣3️⃣ **Mark Collett**: **7.26%** (34 dissents in 468 rounds)
   * 1️⃣4️⃣ **Douglas Crosby**: **7.18%** (38 dissents in 529 rounds)
   * 1️⃣5️⃣ **Chris Lee**: **7.14%** (141 dissents in 1,974 rounds)
   * 1️⃣6️⃣ **Sal D'Amato**: **6.34%** (220 dissents in 3,468 rounds — highest absolute volume)

2. **Currently Active UFC Mainstays (2024–2026 Roster, Min 250 Rounds):**
   * 🥇 **Rick Winter**: **8.75%** round dissent rate (30 dissents in 343 rounds) — **#1 Active Dissenter in the UFC today**
   * 🥈 **Dave Tirelli**: **8.56%** (41 dissents in 479 rounds)
   * 🥉 **David Lethaby**: **8.50%** (54 dissents in 635 rounds)
   * 4️⃣ **Adalaide Byrd**: **8.14%** (55 dissents in 676 rounds)
   * 5️⃣ **Anders Ohlsson**: **7.80%** (23 dissents in 295 rounds)
   * 6️⃣ **Howard Hughes**: **7.63%** (27 dissents in 354 rounds)
   * 7️⃣ **Eric Colón**: **7.61%** (98 dissents in 1,288 rounds)
   * 8️⃣ **Derek Cleary**: **7.48%** (168 dissents in 2,246 rounds)
   * 9️⃣ **Chris Lee**: **7.14%** (141 dissents in 1,974 rounds)

3. **Most Consensual Judges (Highest Colleague Agreement Rate, Min 250 Rounds):**
   * 🥇 **Clemens Werner**: **94.94% agreement rate** (5.06% dissent, 24 dissents in 474 rounds; -2.35% below avg) — **#1 Most Consensual Judge in UFC history**
   * 🥈 **Jeff Mullen** *(Historical)*: **94.58% agreement rate** (5.42% dissent, 15 dissents in 277 rounds)
   * 🥉 **Ron McCarthy**: **94.36% agreement rate** (5.64% dissent, 50 dissents in 886 rounds)
   * 4️⃣ **Michael Bell**: **94.16% agreement rate** (5.84% dissent, 106 dissents in 1,814 rounds)
   * 5️⃣ **Junichiro Kamijo**: **94.08% agreement rate** (5.92% dissent, 90 dissents in 1,519 rounds)
   * 6️⃣ **Tony Weeks**: **93.86% agreement rate** (6.14% dissent, 61 dissents in 993 rounds)
   * 7️⃣ **Sal D'Amato**: **93.66% agreement rate** (6.34% dissent, 220 dissents in 3,468 rounds)
   * 8️⃣ **Ben Cartlidge**: **93.11% agreement rate** (6.89% dissent, 58 dissents in 842 rounds)

4. **Emerging & Regular Judges (Minimum 50 Scored Rounds):**
   * 🥇 **Barry Luxenberg**: **20.63%** (13 dissents in 63 rounds)
   * 🥈 **Albert Shen**: **15.12%** (13 dissents in 86 rounds)
   * 🥉 **Howie Booth**: **14.93%** (10 dissents in 67 rounds)
   * 4️⃣ **Jerin Valel**: **14.29%** (9 dissents in 63 rounds)
   * 5️⃣ **Barry Foley**: **13.48%** (19 dissents in 141 rounds)

5. **Pairwise Round Clashes (Co-Judges Seated Together, Min 100 Rounds):**
   * **Eric Colón & Michael Bell**: Disagreed on **19.74%** of rounds (46 round disagreements out of 233 rounds together).
   * **Glenn Trowbridge & Sal D'Amato**: Disagreed on **18.85%** of rounds (23 disagreements out of 122 rounds).
   * **Derek Cleary & Eric Colón**: Disagreed on **18.55%** of rounds (46 disagreements out of 248 rounds).

6. **Overall Fight Decision Disagreements (Secondary Mode):**
   * **Barry Foley** holds the #1 fight-level dissent rate at **22.64%** (12 dissents in 53 fights).
   * **Adalaide Byrd** holds the #1 fight-level dissent rate among 250+ fight veterans at **9.29%** (25 dissents in 269 fights).

---

## Dataset Overview

| Metric | Count | Percentage |
| :--- | :--- | :--- |
| **Total UFC Events Scraped** | 751 events | 100% |
| **Total Fights Decided by Judges** | 4,010 fights | 100% |
| **Total Individual Scorecards** | 12,030 scorecards | 100% |
| **Unanimous Decisions** | 3,102 fights | 77.36% |
| **Split Decisions** | 804 fights | 20.05% |
| **Majority Decisions** | 101 fights | 2.52% |
| **Draw Decisions** | 3 fights | 0.07% |
| **Unique Judges in History** | 491 judges | — |

---

## Top Disagreement Tables

### Tier 1: Veterans (Min 100 Fights)
| Rank | Judge Name | Total Fights | Dissents | Disagreement % | Unanimous % | Era |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| 1 | **Rick Winter** | 122 | 15 | **12.30%** | 77.0% | 2011–2026 |
| 2 | **Patricia Morse Jarman** | 111 | 11 | **9.91%** | 80.2% | 2002–2021 |
| 3 | **Adalaide Byrd** | 269 | 25 | **9.29%** | 76.2% | 2006–2025 |
| 4 | **Cardo Urso** | 119 | 11 | **9.24%** | 77.3% | 2006–2019 |
| 5 | **Dave Tirelli** | 159 | 14 | **8.81%** | 78.6% | 2011–2025 |
| 6 | **Marcos Rosales** | 233 | 20 | **8.58%** | 78.1% | 2006–2021 |
| 7 | **Dave Hagen** | 175 | 15 | **8.57%** | 78.3% | 2013–2025 |
| 8 | **Paul Sutherland** | 108 | 9 | **8.33%** | 80.6% | 2014–2025 |
| 9 | **Glenn Trowbridge** | 218 | 18 | **8.26%** | 79.4% | 2008–2019 |
| 10 | **Tony Weeks** | 403 | 33 | **8.19%** | 78.4% | 2006–2026 |
| 11 | **Chris Lee** | 685 | 56 | **8.18%** | 77.1% | 2009–2026 |
| 12 | **Douglas Crosby** | 268 | 21 | **7.84%** | 81.0% | 2000–2024 |
| 13 | **Derek Cleary** | 706 | 48 | **6.80%** | 78.3% | 2011–2026 |
| 14 | **Michael Bell** | 567 | 38 | **6.70%** | 78.8% | 2013–2026 |
| 15 | **Sal D'Amato** | 1,151 | 75 | **6.52%** | 79.8% | 2006–2026 |

---

## Most Frequent Judge Panel Clashes (Min 50 Fights Together)

When two judges sit on the same cage-side panel, how frequently do their picks diverge?

| Rank | Judge Pair | Fights Together | Disagreements | Disagreement % |
| :--- | :--- | :--- | :--- | :--- |
| 1 | **Dave Hagen & Sal D'Amato** | 56 | 11 | **19.64%** |
| 2 | **Glenn Trowbridge & Sal D'Amato** | 52 | 10 | **19.23%** |
| 3 | **Adalaide Byrd & Sal D'Amato** | 76 | 14 | **18.42%** |
| 4 | **Chris Lee & Derek Cleary** | 110 | 19 | **17.27%** |
| 5 | **Junichiro Kamijo & Michael Bell** | 98 | 16 | **16.33%** |
| 6 | **Chris Lee & Sal D'Amato** | 224 | 36 | **16.07%** |
| 7 | **Adalaide Byrd & Derek Cleary** | 51 | 8 | **15.69%** |
| 8 | **Derek Cleary & Michael Bell** | 134 | 21 | **15.67%** |
| 9 | **Eric Colón & Michael Bell** | 71 | 11 | **15.49%** |
| 10 | **Douglas Crosby & Sal D'Amato** | 53 | 8 | **15.09%** |

---

## Project Structure

```
ufc-judging-analysis/
├── .github/
│   └── workflows/
│       └── weekly_update.yml        # Automated Monday cron to ingest UFC events & redeploy Pages
├── data/
│   ├── ufc_round_scores.csv         # 31,881 individual 5-minute round scores (10-9, 10-8, 10-10)
│   ├── ufc_scorecards.csv           # 4,010 UFC fights with full scores and dissenter flags
│   ├── ufc_judge_appearances.csv    # 12,030 individual judge-fight scorecard records
│   ├── ufc_judging.db               # SQLite database with 'round_scores', 'fights', and 'judge_appearances'
│   ├── judge_round_dissent_rankings.csv # Round-level dissent rates, 10-8s, and era per judge
│   ├── judge_round_pair_disagreements.csv # Pairwise round disagreements between co-judges
│   ├── judge_dissent_rankings.csv   # Fight-level dissent rankings per judge
│   └── judge_pair_disagreements.csv # Fight-level pairwise disagreements
├── output/
│   ├── ufc_judging_data.json        # Unified JSON payload for dashboards & visualizations
│   ├── round_dissent_rate_min_50.png # Top judges by round dissent % (min 50 rounds)
│   ├── round_dissent_rate_min_250.png# Top veteran judges by round dissent % (min 250 rounds)
│   ├── scatter_rounds_vs_dissent.png# Round volume vs dissent rate scatter plot
│   ├── round_disagreement_trend.png # Historical round disagreement rate trend over time
│   ├── dissent_rate_min_50.png      # Fight decision dissent rate (min 50 fights)
│   ├── dissent_rate_min_100.png     # Fight decision dissent rate (min 100 fights)
│   ├── scatter_fights_vs_dissent.png# Fight volume vs dissent rate scatter plot
│   └── split_decision_trend.png     # Historical split decision rate over time
├── src/
│   ├── weekly_update.py             # Incremental weekly ingestion & recompile pipeline
│   ├── download_decisions.py        # Asynchronous parallel scraper for 4,010 decision pages
│   ├── round_parser.py              # Round-level scorecard table parser & SQLite loader
│   ├── parser.py                    # Fight-level HTML parser converting scorecards to CSV/SQLite
│   ├── analyzer.py                  # Vectorized statistical analysis of round & fight dissent
│   ├── visualizer.py                # Publication-grade chart generation
│   ├── export_web_data.py           # Web data enrichment pipeline & JSON compiler
│   ├── build_dashboard.py           # Standalone interactive dashboard compiler
│   └── security.py                  # Strict path resolution, SQL validation & XSS protection
├── tests/                           # 65 comprehensive unit tests with branch coverage
├── index.html                       # Standalone interactive HTML dashboard (GitHub Pages)
├── requirements.txt                 # Project dependencies
└── README.md                        # Project documentation & analysis report
```

---

## Interactive Dashboard Design (Kucharski Framework)

The dashboard (`index.html`) is engineered according to the principles articulated in Adam Kucharski's critique [*Ten reasons your vibe-coded dashboard looks terrible*](https://kucharski.substack.com/p/ten-reasons-your-vibe-coded-dashboard):

1. **Clear Editorial User Journey**: Numbered chapters starting directly with the core question (*"When two cage-side judges agree on a round, which third judge breaks away most often?"*) and immediately delivering the answer before deeper exploration.
2. **Intentional Visual Hierarchy**: Primary lead cards, secondary comparative gauges, and tertiary supporting charts.
3. **Zero Wasted Hero Space**: Interactive **Benchmark Deviation Gauge** visualizing how each veteran compares to the 7.41% historical UFC baseline.
4. **Curated Table with Interactive Row Expansion (Dossiers)**: No cluttered data dumps; clicking any judge expands an inline dossier showing their career era, dissent frequency ("1 in every X rounds"), 10-8 volume, top clash co-judge, and sample round scorecards.
5. **Plain-English Plot Labelling**: Self-explanatory metric names, explicit units, and clear context.
6. **Prominent Key Estimates**: 4 high-contrast KPI cards showcasing the historical UFC average, the top dissenter, the most consensual mainstay, and the all-time volume record holder.
7. **No Duplicated Metrics**: Every card provides distinct, complementary insight.
8. **Dual Theme Engine**: Instant switch between Dark Mode (`#090d16` slate) and Light Mode (`#f8fafc` editorial palette).
9. **Bespoke Modern Typography**: `Plus Jakarta Sans` for headlines, `Inter` for prose, and `JetBrains Mono` with `tabular-nums` for tabular alignment.
10. **8pt Grid & Consistent Scales**: Standardized 8px spacing tokens, 12px radii, and synchronized axis benchmarks.

---

## How to Run & Explore

### 1. View the Live Web Dashboard
* **Live Website**: [https://martindavies-code.github.io/ufc-judging-analysis/](https://martindavies-code.github.io/ufc-judging-analysis/)
* **Offline Local**: Double-click `index.html` or open it in any modern browser. It is 100% self-contained with no external server required. You can toggle between **Round Scoring Disagreements** (primary) and **Fight Decision Splits** (secondary), filter by volume thresholds, search judges in real time, sort columns, view judge dossiers, and export filtered data to CSV.

### 2. Automated Weekly Updates (Every Monday)
The repository automatically checks for new weekend UFC events every Monday at 10:00 UTC via GitHub Actions:
* **Workflow**: [`.github/workflows/weekly_update.yml`](.github/workflows/weekly_update.yml)
* **Schedule**: Runs on cron `0 10 * * 1` (Mondays) and on manual `workflow_dispatch`.
* **Execution**:
  1. Checks mmadecisions.com for newly completed events.
  2. Ingests new fight and round scorecards into `data/ufc_judging.db` and CSV files.
  3. Re-runs statistical models, re-generates visualizations, and recompiles `index.html`.
  4. Automatically commits and pushes to `main`, instantly updating the live GitHub Pages site!

To run the weekly update pipeline locally:
```bash
python src/weekly_update.py
```

### 3. Query the SQLite Database
```bash
sqlite3 data/ufc_judging.db "SELECT judge_name, COUNT(*) as rounds, SUM(is_dissent) as dissents, ROUND(CAST(SUM(is_dissent) AS FLOAT) / COUNT(*) * 100, 2) as dissent_pct FROM round_scores WHERE consensus_winner != 'SPLIT_3WAY' GROUP BY judge_name HAVING rounds >= 250 ORDER BY dissent_pct DESC LIMIT 10;"
```

### 4. Run the Test Suite
```bash
pytest --cov=src
```
