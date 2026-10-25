# UFC Judging Disagreement & Dissent Analysis (1995–2026)

An empirical data science project analyzing every available UFC judge's scorecard in UFC history to determine **which judge disagrees with their other two colleagues the highest percentage of times**, evaluated directly at the **round scoring level** (each individual 5-minute round scored 10-9, 10-8, 10-10) and the overall fight decision level.

---

## Executive Summary: Round-by-Round Scoring Disagreements

Across **751 UFC events** from **1995 through 2026**, this investigation analyzes **every fight where official scorecards exist** — encompassing **4,010 UFC decisions** plus **48 bouts that ended inside the distance** where judges' scorecards were officially submitted (e.g., Rounds 1–3 of a bout stopped in Round 4, or Rounds 1–4 of a bout stopped in Round 5). In total, **32,876 individual 5-minute rounds scored** across **411 unique judges** were evaluated.

A **Round Dissent** occurs when two cage-side colleagues agree on who won an individual round, while the third judge submits a dissenting score for the opposing fighter or a draw.

### Which judge disagrees with their other two colleagues the highest percentage of times on round scoring?

1. **UFC Veteran Mainstays (Minimum 250 Scored Rounds):**
   * 🥇 **Cardo Urso**: **9.01%** round dissent rate (29 dissents in 322 rounds)
   * 🥈 **Rick Winter**: **8.75%** (30 dissents in 343 rounds)
   * 🥉 **David Lethaby**: **8.62%** (55 dissents in 638 rounds)
   * 4️⃣ **Dave Tirelli**: **8.54%** (41 dissents in 480 rounds)
   * 5️⃣ **Glenn Trowbridge**: **8.37%** (41 dissents in 490 rounds)
   * 6️⃣ **Marcos Rosales**: **7.97%** (47 dissents in 590 rounds)
   * 7️⃣ **Adalaide Byrd**: **7.87%** (55 dissents in 699 rounds)
   * 8️⃣ **Anders Ohlsson**: **7.80%** (23 dissents in 295 rounds)
   * 9️⃣ **Howard Hughes**: **7.63%** (27 dissents in 354 rounds)
   * 🔟 **Eric Colón**: **7.60%** (99 dissents in 1,302 rounds)
   * 1️⃣1️⃣ **Derek Cleary**: **7.44%** (170 dissents in 2,284 rounds)
   * 1️⃣2️⃣ **Mark Collett**: **7.26%** (34 dissents in 468 rounds)
   * 1️⃣3️⃣ **Douglas Crosby**: **7.18%** (38 dissents in 529 rounds)
   * 1️⃣4️⃣ **Chris Lee**: **7.08%** (142 dissents in 2,007 rounds)
   * 1️⃣5️⃣ **Ben Cartlidge**: **6.87%** (58 dissents in 844 rounds)
   * 1️⃣6️⃣ **Sal D'Amato**: **6.24%** (223 dissents in 3,573 rounds — highest absolute volume)

2. **Currently Active UFC Mainstays (2024–2026 Roster, Min 250 Rounds):**
   * 🥇 **Rick Winter**: **8.75%** round dissent rate (30 dissents in 343 rounds) — **#1 Active Dissenter in the UFC today**
   * 🥈 **David Lethaby**: **8.62%** (55 dissents in 638 rounds)
   * 🥉 **Dave Tirelli**: **8.54%** (41 dissents in 480 rounds)
   * 4️⃣ **Adalaide Byrd**: **7.87%** (55 dissents in 699 rounds)
   * 5️⃣ **Anders Ohlsson**: **7.80%** (23 dissents in 295 rounds)
   * 6️⃣ **Howard Hughes**: **7.63%** (27 dissents in 354 rounds)
   * 7️⃣ **Eric Colón**: **7.60%** (99 dissents in 1,302 rounds)
   * 8️⃣ **Derek Cleary**: **7.44%** (170 dissents in 2,284 rounds)
   * 9️⃣ **Chris Lee**: **7.08%** (142 dissents in 2,007 rounds)
   * 🔟 **Ben Cartlidge**: **6.87%** (58 dissents in 844 rounds)

3. **Most Consensual Judges (Highest Colleague Agreement Rate, Min 250 Rounds):**
   * 🥇 **Clemens Werner**: **95.01% agreement rate** (4.99% dissent, 24 dissents in 481 rounds; -2.24% below avg) — **#1 Most Consensual Active Judge in UFC history**
   * 🥈 **Jeff Mullen** *(Historical)*: **94.64% agreement rate** (5.36% dissent, 15 dissents in 280 rounds)
   * 🥉 **Ron McCarthy**: **94.24% agreement rate** (5.76% dissent, 52 dissents in 902 rounds)
   * 4️⃣ **Michael Bell**: **94.21% agreement rate** (5.79% dissent, 106 dissents in 1,830 rounds)
   * 5️⃣ **Junichiro Kamijo**: **94.04% agreement rate** (5.96% dissent, 91 dissents in 1,528 rounds)
   * 6️⃣ **Tony Weeks**: **93.86% agreement rate** (6.14% dissent, 61 dissents in 993 rounds)
   * 7️⃣ **Sal D'Amato**: **93.76% agreement rate** (6.24% dissent, 223 dissents in 3,573 rounds)
   * 8️⃣ **Ben Cartlidge**: **93.13% agreement rate** (6.87% dissent, 58 dissents in 844 rounds)

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
| **Unique UFC Fighters Analyzed** | 2,093 fighters | — |

---

## Fighter Controversy & Disagreement Index

Which UFC fighters find themselves in razor-thin, split-call contests most frequently? Who has been historically "unlucky" on the wrong side of split decisions, and who has been the most fortunate?

Across 4,010 UFC decisions, exactly **20.05% (1 in 5 bouts)** ended in a split decision.

### 1. Highest Split Decision Rate (Min 6 Decision Bouts)
1. 🥇 **Zubaira Tukhugov**: **83.33%** (5 split decisions in 6 bouts) — **#1 All-Time Most Contested Fighter**
2. 🥈 **Paul Felder**: **66.67%** (6 splits in 9 bouts; 48.39% of scored rounds had a judge dissent)
3. 🥉 **Joshua Culibao**: **66.67%** (4 splits in 6 bouts)
4. 4️⃣ **Brad Pickett**: **66.67%** (4 splits in 6 bouts)
5. 5️⃣ **Gian Villante**: **62.50%** (5 splits in 8 bouts)
6. 6️⃣ **Sean Woodson**: **57.14%** (4 splits in 7 bouts, 3W-0L in splits) — **#1 Active Split Rate**

### 2. The UFC "Luck Differential" (Net Split Wins vs Losses)
* **Most Unlucky (Worst Split Decision Records)**:
  * 💔 **Jorge Masvidal**: **0W – 4L** (net **-4** luck differential; 0% win rate in split decisions)
  * 💔 **Andrea Lee**: **0W – 4L** (net **-4**)
  * 💔 **Angela Hill**: **1W – 4L** (net **-3**; 4 split losses — #1 among active UFC fighters)
  * 💔 **Cortney Casey**: **1W – 4L** (net **-3**)
  * 💔 **Pedro Munhoz / Santiago Ponzinibbio / Gerald Meerschaert**: **0W – 3L** (net **-3**)
* **Most Fortunate (Best Split Decision Records)**:
  * 🍀 **Sean Strickland**: **5W – 2L** (net **+3**; 5 career split wins — tied for #1 all-time)
  * 🍀 **Andre Fili**: **5W – 2L** (net **+3**; 5 career split wins)
  * 🍀 **Gleison Tibau**: **5W – 2L** (net **+3**; 5 career split wins)
  * 🍀 **Neil Magny**: **4W – 0L** (net **+4**; undefeated in career split decisions)
  * 🍀 **Benson Henderson**: **4W – 0L** (net **+4**; undefeated in career split decisions)

### 3. Most Contested Scored Rounds (Min 25 Scored Rounds)
* 🥇 **Paul Felder**: **48.39%** of rounds contested (15 of 31 rounds produced a lone dissenting judge)
* 🥈 **Dominick Cruz**: **41.38%** (12 of 29 rounds contested)
* 🥉 **Alexander Hernandez**: **40.74%** (11 of 27 rounds contested) — **#1 Active**
* 4️⃣ **Ross Pearson / Benson Henderson**: **40.48%** (17 of 42 rounds contested)
* 5️⃣ **Cory Sandhagen**: **38.46%** (15 of 39 rounds contested)

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

```text
ufc-judging-analysis/
├── .github/
│   └── workflows/
│       └── weekly_update.yml        # Automated Monday cron to ingest UFC events & redeploy Pages
├── data/
│   ├── ufc_round_scores.csv         # 32,876 individual 5-minute round scores (10-9, 10-8, 10-10)
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
│   ├── fighter_analysis.py          # Fighter controversy metrics, luck index & split rates
│   ├── weekly_update.py             # Incremental weekly ingestion & recompile pipeline
│   ├── download_decisions.py        # Asynchronous parallel scraper for 4,010 decision pages
│   ├── round_parser.py              # Round-level scorecard table parser & SQLite loader
│   ├── parser.py                    # Fight-level HTML parser converting scorecards to CSV/SQLite
│   ├── analyzer.py                  # Vectorized statistical analysis of round & fight dissent
│   ├── visualizer.py                # Publication-grade chart generation
│   ├── export_web_data.py           # Web data enrichment pipeline & JSON compiler
│   ├── build_dashboard.py           # Standalone interactive dashboard compiler
│   └── security.py                  # Strict path resolution, SQL validation & XSS protection
├── tests/                           # 97+ comprehensive unit tests with branch coverage
├── index.html                       # Standalone interactive HTML dashboard (GitHub Pages)
├── requirements.txt                 # Project dependencies
└── README.md                        # Project documentation & analysis report
```

---

## Interactive Dashboard Design (Kucharski Framework)

The dashboard (`index.html`) is engineered according to the principles articulated in Adam Kucharski's critique [*Ten reasons your vibe-coded dashboard looks terrible*](https://kucharski.substack.com/p/ten-reasons-your-vibe-coded-dashboard):

1. **Clear Editorial User Journey**: Numbered chapters starting directly with the core question and immediately delivering the answer before deeper exploration.
2. **Seamless 3-Way Analysis Mode Switcher**:
   * **Round Scoring Disagreements**: Detailed round-by-round dissent (10-9, 10-8) across 32,876 rounds (including completed rounds from stoppage bouts).
   * **Fight Decision Splits**: Final 15-minute fight decision split disagreement rankings across 4,010 bouts.
   * **Fighter Controversy Index**: Deep-dive into which UFC fighters find themselves in razor-thin fights, who suffers the worst split decision luck (-4 net luck for Masvidal & Lee), who benefits most (+3 for Strickland & Fili), and who has the highest rate of contested rounds (48.39% for Paul Felder).
3. **Intentional Visual Hierarchy**: Primary lead cards, secondary comparative gauges, and tertiary supporting charts.
4. **Zero Wasted Hero Space**: Interactive **Benchmark Deviation Gauge** visualizing how each judge or fighter compares to historical UFC baselines (7.23% for rounds, 20.05% for split decisions), plus the **UFC Luck Differential** gauge.
5. **Curated Table with Interactive Row Expansion (Dossiers)**: No cluttered data dumps; clicking any judge or fighter expands an inline dossier showing active career eras, disagreement frequencies, colleague clash stats, and sample bout scorecards.
6. **Plain-English Plot Labelling**: Self-explanatory metric names, explicit units, and clear context.
7. **Prominent Key Estimates**: 4 high-contrast KPI cards showcasing benchmarks, leaders, volume records, and luck extremes.
8. **No Duplicated Metrics**: Every card provides distinct, complementary insight.
9. **Dual Theme Engine**: Instant switch between Dark Mode (`#090d16` slate) and Light Mode (`#f8fafc` editorial palette).
10. **Bespoke Modern Typography**: `Plus Jakarta Sans` for headlines, `Inter` for prose, and `JetBrains Mono` with `tabular-nums` for tabular alignment.

---

## How to Run & Explore

### 1. View the Live Web Dashboard

* **Live Website**: [https://martindavies-code.github.io/ufc-judging-analysis/](https://martindavies-code.github.io/ufc-judging-analysis/)
* **Offline Local**: Double-click `index.html` or open it in any modern browser. It is 100% self-contained with no external server required. You can toggle between **Round Scoring Disagreements**, **Fight Decision Splits**, and **Fighter Controversy Index**, filter by thresholds, search judges and fighters in real time, sort columns, view interactive dossiers, and export data directly to CSV (`ufc_fighter_controversy_index.csv` or `ufc_judging_*_analysis.csv`).

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
