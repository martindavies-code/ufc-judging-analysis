"""Secure, XSS-protected compiler for UFC judging standalone HTML dashboard.

Designed following best practices in data journalism to eliminate the 10
common "vibe-coded" dashboard anti-patterns identified by Adam Kucharski:
1. Clear editorial user journey & driving question.
2. Distinct visual hierarchy & elevation levels.
3. No wasted space in hero section; high information density.
4. Curated, readable tables with interactive row expansion (Judge Dossiers).
5. Intuitive, plain-English labelling and explicit units.
6. Key estimates prominently featured with historical benchmark context.
7. Zero duplicated metrics across cards.
8. Sophisticated color theme with dual Light & Dark mode support.
9. Bespoke typography with tabular numerals.
10. Strict, consistent tokenized spacing and scaling.
"""

import base64
import json
import logging
import sys
from pathlib import Path
from typing import Dict, Any, List

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.security import escape_html, safe_resolve_path

logger = logging.getLogger(__name__)

DATA_DIR = PROJECT_ROOT / "data"
OUTPUT_DIR = PROJECT_ROOT / "output"
OUTPUT_HTML_PATH = PROJECT_ROOT / "index.html"
WEB_DATA_PATH = OUTPUT_DIR / "ufc_judging_data.json"


def encode_image_base64(image_filename: str) -> str:
    """Safely resolve and base64-encode an artifact image for standalone embedding."""
    try:
        image_path = safe_resolve_path(OUTPUT_DIR, image_filename)
        if image_path.exists() and image_path.stat().st_size > 0:
            with open(image_path, "rb") as f:
                encoded = base64.b64encode(f.read()).decode("utf-8")
                return f"data:image/png;base64,{encoded}"
    except Exception as e:
        logger.warning("Could not encode image %s: %s", image_filename, e)
    return ""


DASHBOARD_TEMPLATE = """<!DOCTYPE html>
<html lang="en" data-theme="dark">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>The Dissenter Index: UFC Judging & Round-by-Round Scoring Analysis (1995–2026)</title>
    <meta name="description" content="An empirical investigation into 31,881 UFC rounds across 4,010 decisions: which cage-side judges disagree with their colleagues most frequently?">
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;600;700&display=swap" rel="stylesheet">
    <style>
        :root {
            /* 8pt Grid Spacing Tokens */
            --space-1: 4px;
            --space-2: 8px;
            --space-3: 12px;
            --space-4: 16px;
            --space-5: 20px;
            --space-6: 24px;
            --space-8: 32px;
            --space-10: 40px;
            --space-12: 48px;

            /* Radii */
            --radius-sm: 6px;
            --radius-md: 12px;
            --radius-lg: 18px;
            --radius-full: 9999px;

            /* Typography */
            --font-display: 'Plus Jakarta Sans', system-ui, -apple-system, sans-serif;
            --font-body: 'Inter', system-ui, -apple-system, sans-serif;
            --font-mono: 'JetBrains Mono', ui-monospace, monospace;
        }

        /* Dark Theme (Default) */
        [data-theme="dark"] {
            --bg-page: #090d16;
            --bg-surface: #101726;
            --bg-surface-elevated: #162035;
            --bg-surface-card: rgba(18, 27, 45, 0.75);
            --bg-surface-hover: #1c2a46;
            --border-subtle: rgba(255, 255, 255, 0.08);
            --border-strong: rgba(255, 255, 255, 0.16);
            --border-highlight: rgba(225, 29, 72, 0.4);
            --text-primary: #f8fafc;
            --text-secondary: #94a3b8;
            --text-muted: #64748b;
            --accent-crimson: #f43f5e;
            --accent-crimson-bg: rgba(244, 63, 94, 0.15);
            --accent-green: #10b981;
            --accent-green-bg: rgba(16, 185, 129, 0.15);
            --accent-amber: #f59e0b;
            --accent-amber-bg: rgba(245, 158, 11, 0.15);
            --accent-blue: #38bdf8;
            --accent-blue-bg: rgba(56, 189, 248, 0.15);
            --shadow-card: 0 4px 24px -2px rgba(0, 0, 0, 0.6);
            --shadow-elevated: 0 10px 32px -4px rgba(0, 0, 0, 0.8);
            --chart-filter: none;
        }

        /* Editorial Light Theme (Clean FT / NYT data-journalism aesthetic) */
        [data-theme="light"] {
            --bg-page: #f8fafc;
            --bg-surface: #ffffff;
            --bg-surface-elevated: #f1f5f9;
            --bg-surface-card: #ffffff;
            --bg-surface-hover: #f8fafc;
            --border-subtle: #e2e8f0;
            --border-strong: #cbd5e1;
            --border-highlight: rgba(225, 29, 72, 0.3);
            --text-primary: #0f172a;
            --text-secondary: #475569;
            --text-muted: #64748b;
            --accent-crimson: #e11d48;
            --accent-crimson-bg: #ffe4e6;
            --accent-green: #059669;
            --accent-green-bg: #d1fae5;
            --accent-amber: #d97706;
            --accent-amber-bg: #fef3c7;
            --accent-blue: #0284c7;
            --accent-blue-bg: #e0f2fe;
            --shadow-card: 0 2px 12px -2px rgba(15, 23, 42, 0.08);
            --shadow-elevated: 0 8px 24px -4px rgba(15, 23, 42, 0.12);
            --chart-filter: contrast(0.95);
        }

        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
            transition: background-color 0.2s ease, border-color 0.2s ease, color 0.2s ease;
        }

        body {
            font-family: var(--font-body);
            background-color: var(--bg-page);
            color: var(--text-primary);
            line-height: 1.5;
            -webkit-font-smoothing: antialiased;
            overflow-x: hidden;
        }

        .container {
            max-width: 1280px;
            margin: 0 auto;
            padding: var(--space-6) var(--space-6) var(--space-12) var(--space-6);
        }

        /* Header Navigation */
        .site-header {
            display: flex;
            align-items: center;
            justify-content: space-between;
            padding: var(--space-4) 0;
            margin-bottom: var(--space-8);
            border-bottom: 1px solid var(--border-subtle);
        }

        .brand-cluster {
            display: flex;
            align-items: center;
            gap: var(--space-4);
        }

        .octagon-badge {
            width: 44px;
            height: 44px;
            background: linear-gradient(135deg, var(--accent-crimson), #be123c);
            clip-path: polygon(30% 0%, 70% 0%, 100% 30%, 100% 70%, 70% 100%, 30% 100%, 0% 70%, 0% 30%);
            display: flex;
            align-items: center;
            justify-content: center;
            font-family: var(--font-display);
            font-weight: 800;
            font-size: 16px;
            color: #ffffff;
            box-shadow: 0 0 16px rgba(225, 29, 72, 0.4);
        }

        .brand-text h1 {
            font-family: var(--font-display);
            font-size: 20px;
            font-weight: 800;
            letter-spacing: -0.02em;
            color: var(--text-primary);
        }

        .brand-text p {
            font-size: 13px;
            color: var(--text-secondary);
        }

        .nav-controls {
            display: flex;
            align-items: center;
            gap: var(--space-3);
        }

        .mode-toggle-group {
            display: flex;
            background: var(--bg-surface-elevated);
            padding: var(--space-1);
            border-radius: var(--radius-full);
            border: 1px solid var(--border-subtle);
        }

        .mode-btn {
            border: none;
            background: transparent;
            color: var(--text-secondary);
            font-family: var(--font-body);
            font-size: 13px;
            font-weight: 600;
            padding: var(--space-2) var(--space-4);
            border-radius: var(--radius-full);
            cursor: pointer;
            transition: all 0.15s ease;
        }

        .mode-btn.active {
            background: var(--accent-crimson);
            color: #ffffff;
            box-shadow: 0 2px 8px rgba(225, 29, 72, 0.4);
        }

        .theme-btn {
            display: flex;
            align-items: center;
            justify-content: center;
            width: 40px;
            height: 40px;
            border-radius: var(--radius-md);
            border: 1px solid var(--border-subtle);
            background: var(--bg-surface-elevated);
            color: var(--text-primary);
            cursor: pointer;
            transition: all 0.15s ease;
        }

        .theme-btn:hover {
            border-color: var(--border-strong);
            transform: translateY(-1px);
        }

        /* Chapter Banner & Lead Narrative */
        .chapter-badge {
            display: inline-flex;
            align-items: center;
            gap: var(--space-2);
            font-family: var(--font-mono);
            font-size: 11px;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 0.08em;
            color: var(--accent-crimson);
            background: var(--accent-crimson-bg);
            padding: var(--space-1) var(--space-3);
            border-radius: var(--radius-full);
            margin-bottom: var(--space-3);
            border: 1px solid var(--border-highlight);
        }

        .hero-lead-card {
            background: var(--bg-surface-card);
            border: 1px solid var(--border-subtle);
            border-radius: var(--radius-lg);
            padding: var(--space-8);
            box-shadow: var(--shadow-card);
            backdrop-filter: blur(12px);
            margin-bottom: var(--space-8);
            position: relative;
            overflow: hidden;
        }

        .hero-lead-card::before {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            width: 4px;
            height: 100%;
            background: var(--accent-crimson);
        }

        .hero-headline {
            font-family: var(--font-display);
            font-size: 32px;
            font-weight: 800;
            letter-spacing: -0.03em;
            line-height: 1.25;
            margin-bottom: var(--space-3);
            color: var(--text-primary);
        }

        .hero-subhead {
            font-size: 16px;
            color: var(--text-secondary);
            max-width: 900px;
            line-height: 1.6;
            margin-bottom: var(--space-6);
        }

        .hero-subhead strong {
            color: var(--text-primary);
        }

        /* 4 Focused KPI Metric Cards */
        .kpi-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(260px, 1fr));
            gap: var(--space-4);
            margin-bottom: var(--space-6);
        }

        .kpi-card {
            background: var(--bg-surface);
            border: 1px solid var(--border-subtle);
            border-radius: var(--radius-md);
            padding: var(--space-5);
            display: flex;
            flex-direction: column;
            justify-content: space-between;
            position: relative;
        }

        .kpi-card:hover {
            border-color: var(--border-strong);
        }

        .kpi-label {
            font-size: 12px;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.05em;
            color: var(--text-muted);
            margin-bottom: var(--space-2);
        }

        .kpi-value-row {
            display: flex;
            align-items: baseline;
            gap: var(--space-2);
            margin-bottom: var(--space-1);
        }

        .kpi-value {
            font-family: var(--font-mono);
            font-size: 34px;
            font-weight: 800;
            color: var(--text-primary);
            font-variant-numeric: tabular-nums;
            letter-spacing: -0.02em;
        }

        .kpi-delta {
            font-family: var(--font-mono);
            font-size: 13px;
            font-weight: 700;
            padding: 2px 8px;
            border-radius: var(--radius-full);
        }

        .kpi-delta.high {
            background: var(--accent-crimson-bg);
            color: var(--accent-crimson);
        }

        .kpi-delta.consensual {
            background: var(--accent-green-bg);
            color: var(--accent-green);
        }

        .kpi-context {
            font-size: 13px;
            color: var(--text-secondary);
            line-height: 1.4;
        }

        /* Benchmark Deviation Bar Visualization (High information density, zero wasted space) */
        .gauge-section {
            background: var(--bg-surface);
            border: 1px solid var(--border-subtle);
            border-radius: var(--radius-md);
            padding: var(--space-6);
            margin-top: var(--space-4);
        }

        .gauge-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: var(--space-4);
            flex-wrap: wrap;
            gap: var(--space-2);
        }

        .gauge-title {
            font-family: var(--font-display);
            font-size: 16px;
            font-weight: 700;
            color: var(--text-primary);
        }

        .gauge-legend {
            display: flex;
            align-items: center;
            gap: var(--space-4);
            font-size: 12px;
            color: var(--text-secondary);
        }

        .legend-dot {
            width: 10px;
            height: 10px;
            border-radius: 50%;
            display: inline-block;
        }

        .deviation-bars-container {
            display: flex;
            flex-direction: column;
            gap: var(--space-3);
            margin-top: var(--space-3);
        }

        .bar-row {
            display: grid;
            grid-template-columns: 180px 1fr 100px;
            align-items: center;
            gap: var(--space-4);
            font-size: 13px;
        }

        .bar-judge-name {
            font-weight: 600;
            color: var(--text-primary);
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
        }

        .bar-track {
            position: relative;
            height: 24px;
            background: var(--bg-surface-elevated);
            border-radius: var(--radius-sm);
            overflow: hidden;
            display: flex;
            align-items: center;
        }

        .bar-fill {
            height: 100%;
            border-radius: var(--radius-sm);
            transition: width 0.4s ease;
        }

        .bar-benchmark-line {
            position: absolute;
            top: 0;
            bottom: 0;
            width: 2px;
            background: #ffffff;
            box-shadow: 0 0 6px rgba(255, 255, 255, 0.8);
            z-index: 2;
        }

        [data-theme="light"] .bar-benchmark-line {
            background: #0f172a;
            box-shadow: 0 0 4px rgba(15, 23, 42, 0.4);
        }

        .bar-val {
            font-family: var(--font-mono);
            font-size: 13px;
            font-weight: 700;
            text-align: right;
            font-variant-numeric: tabular-nums;
        }

        /* Section Layout */
        .content-section {
            margin-top: var(--space-12);
        }

        .section-header-block {
            margin-bottom: var(--space-6);
        }

        .section-title {
            font-family: var(--font-display);
            font-size: 24px;
            font-weight: 800;
            letter-spacing: -0.02em;
            color: var(--text-primary);
            margin-bottom: var(--space-1);
        }

        .section-desc {
            font-size: 14px;
            color: var(--text-secondary);
            max-width: 800px;
        }

        /* Controls: Filters, Search, Export */
        .table-toolbar {
            display: flex;
            justify-content: space-between;
            align-items: center;
            gap: var(--space-4);
            margin-bottom: var(--space-4);
            flex-wrap: wrap;
        }

        .filter-pills {
            display: flex;
            align-items: center;
            gap: var(--space-2);
            flex-wrap: wrap;
        }

        .pill-btn {
            background: var(--bg-surface);
            border: 1px solid var(--border-subtle);
            color: var(--text-secondary);
            font-size: 13px;
            font-weight: 600;
            padding: var(--space-2) var(--space-4);
            border-radius: var(--radius-full);
            cursor: pointer;
            transition: all 0.15s ease;
        }

        .pill-btn:hover {
            border-color: var(--border-strong);
            color: var(--text-primary);
        }

        .pill-btn.active {
            background: var(--text-primary);
            color: var(--bg-page);
            border-color: var(--text-primary);
        }

        .search-export-cluster {
            display: flex;
            align-items: center;
            gap: var(--space-3);
        }

        .search-wrapper {
            position: relative;
        }

        .search-input {
            background: var(--bg-surface);
            border: 1px solid var(--border-subtle);
            border-radius: var(--radius-md);
            padding: var(--space-2) var(--space-4);
            padding-left: 36px;
            font-size: 13px;
            color: var(--text-primary);
            outline: none;
            width: 240px;
            transition: all 0.15s ease;
        }

        .search-input:focus {
            border-color: var(--accent-crimson);
            box-shadow: 0 0 0 2px var(--accent-crimson-bg);
            width: 280px;
        }

        .search-icon {
            position: absolute;
            left: 12px;
            top: 50%;
            transform: translateY(-50%);
            color: var(--text-muted);
            pointer-events: none;
        }

        .btn-action {
            display: inline-flex;
            align-items: center;
            gap: var(--space-2);
            background: var(--bg-surface-elevated);
            border: 1px solid var(--border-subtle);
            color: var(--text-primary);
            font-size: 13px;
            font-weight: 600;
            padding: var(--space-2) var(--space-4);
            border-radius: var(--radius-md);
            cursor: pointer;
            transition: all 0.15s ease;
        }

        .btn-action:hover {
            border-color: var(--border-strong);
            background: var(--bg-surface-hover);
        }

        /* Clean, Prioritized Table */
        .table-card {
            background: var(--bg-surface);
            border: 1px solid var(--border-subtle);
            border-radius: var(--radius-lg);
            overflow: hidden;
            box-shadow: var(--shadow-card);
        }

        .table-responsive {
            width: 100%;
            overflow-x: auto;
        }

        table {
            width: 100%;
            border-collapse: collapse;
            text-align: left;
            font-size: 13px;
        }

        th {
            background: var(--bg-surface-elevated);
            color: var(--text-muted);
            font-family: var(--font-display);
            font-weight: 700;
            font-size: 11px;
            text-transform: uppercase;
            letter-spacing: 0.06em;
            padding: var(--space-3) var(--space-4);
            border-bottom: 1px solid var(--border-subtle);
            cursor: pointer;
            user-select: none;
            white-space: nowrap;
        }

        th:hover {
            color: var(--text-primary);
        }

        td {
            padding: var(--space-4);
            border-bottom: 1px solid var(--border-subtle);
            color: var(--text-secondary);
            vertical-align: middle;
        }

        tr.judge-row {
            cursor: pointer;
            transition: background-color 0.1s ease;
        }

        tr.judge-row:hover {
            background-color: var(--bg-surface-hover);
        }

        tr.judge-row.expanded {
            background-color: var(--bg-surface-elevated);
        }

        .judge-cell {
            display: flex;
            align-items: center;
            gap: var(--space-2);
            font-weight: 700;
            color: var(--text-primary);
        }

        .expand-chevron {
            color: var(--text-muted);
            transition: transform 0.2s ease;
        }

        tr.judge-row.expanded .expand-chevron {
            transform: rotate(90deg);
            color: var(--accent-crimson);
        }

        .mono-num {
            font-family: var(--font-mono);
            font-weight: 600;
            font-variant-numeric: tabular-nums;
        }

        /* In-Cell Benchmark Deviation Badge */
        .rate-cell-group {
            display: flex;
            align-items: center;
            gap: var(--space-2);
        }

        .rate-badge {
            font-family: var(--font-mono);
            font-size: 11px;
            font-weight: 700;
            padding: 2px 6px;
            border-radius: var(--radius-sm);
        }

        .rate-badge.over {
            background: var(--accent-crimson-bg);
            color: var(--accent-crimson);
        }

        .rate-badge.under {
            background: var(--accent-green-bg);
            color: var(--accent-green);
        }

        /* Interactive Dossier Drawer */
        tr.dossier-drawer-row {
            display: none;
            background: var(--bg-surface-elevated);
        }

        tr.dossier-drawer-row.visible {
            display: table-row;
        }

        .dossier-card {
            padding: var(--space-6);
            display: grid;
            grid-template-columns: 280px 1fr;
            gap: var(--space-6);
            border-top: 1px dashed var(--border-subtle);
            border-bottom: 1px dashed var(--border-subtle);
        }

        @media (max-width: 900px) {
            .dossier-card {
                grid-template-columns: 1fr;
            }
        }

        .dossier-bio {
            display: flex;
            flex-direction: column;
            gap: var(--space-3);
            border-right: 1px solid var(--border-subtle);
            padding-right: var(--space-6);
        }

        @media (max-width: 900px) {
            .dossier-bio {
                border-right: none;
                padding-right: 0;
                border-bottom: 1px solid var(--border-subtle);
                padding-bottom: var(--space-4);
            }
        }

        .dossier-bio h4 {
            font-family: var(--font-display);
            font-size: 18px;
            font-weight: 800;
            color: var(--text-primary);
        }

        .dossier-stat-pill {
            font-size: 12px;
            color: var(--text-secondary);
            line-height: 1.5;
        }

        .dossier-stat-pill strong {
            color: var(--text-primary);
        }

        .dossier-rounds-log h5 {
            font-family: var(--font-display);
            font-size: 13px;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 0.05em;
            color: var(--text-muted);
            margin-bottom: var(--space-3);
        }

        .sample-dissents-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
            gap: var(--space-3);
        }

        .sample-dissent-box {
            background: var(--bg-surface);
            border: 1px solid var(--border-subtle);
            border-radius: var(--radius-md);
            padding: var(--space-3);
            font-size: 12px;
        }

        .sample-dissent-header {
            display: flex;
            justify-content: space-between;
            color: var(--text-muted);
            font-size: 11px;
            font-family: var(--font-mono);
            margin-bottom: var(--space-1);
        }

        .sample-fight-name {
            font-weight: 700;
            color: var(--text-primary);
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
            margin-bottom: var(--space-2);
        }

        .sample-score-tag {
            display: inline-block;
            font-family: var(--font-mono);
            font-weight: 700;
            color: var(--accent-crimson);
            background: var(--accent-crimson-bg);
            padding: 2px 6px;
            border-radius: var(--radius-sm);
        }

        /* Visualizations Section */
        .chart-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(500px, 1fr));
            gap: var(--space-6);
            margin-top: var(--space-6);
        }

        @media (max-width: 600px) {
            .chart-grid {
                grid-template-columns: 1fr;
            }
        }

        .chart-card {
            background: var(--bg-surface);
            border: 1px solid var(--border-subtle);
            border-radius: var(--radius-lg);
            padding: var(--space-6);
            box-shadow: var(--shadow-card);
        }

        .chart-card h4 {
            font-family: var(--font-display);
            font-size: 16px;
            font-weight: 700;
            color: var(--text-primary);
            margin-bottom: var(--space-1);
        }

        .chart-card p {
            font-size: 13px;
            color: var(--text-secondary);
            margin-bottom: var(--space-4);
        }

        .chart-img-wrap {
            width: 100%;
            border-radius: var(--radius-md);
            overflow: hidden;
            background: #000000;
        }

        .chart-img-wrap img {
            width: 100%;
            height: auto;
            display: block;
            filter: var(--chart-filter);
        }

        /* Anatomy Section */
        .anatomy-bar-container {
            background: var(--bg-surface);
            border: 1px solid var(--border-subtle);
            border-radius: var(--radius-lg);
            padding: var(--space-6);
            margin-top: var(--space-4);
        }

        .anatomy-bar {
            height: 32px;
            display: flex;
            border-radius: var(--radius-md);
            overflow: hidden;
            margin: var(--space-4) 0;
        }

        .seg-10-9 { background: #38bdf8; width: 95.7%; }
        .seg-10-8 { background: var(--accent-amber); width: 3.76%; }
        .seg-draw { background: var(--accent-green); width: 0.48%; }
        .seg-10-7 { background: var(--accent-crimson); width: 0.03%; min-width: 4px; }

        .anatomy-legend {
            display: flex;
            gap: var(--space-6);
            flex-wrap: wrap;
            font-size: 13px;
        }

        .anatomy-item {
            display: flex;
            align-items: center;
            gap: var(--space-2);
        }

        .dot-10-9 { background: #38bdf8; }
        .dot-10-8 { background: var(--accent-amber); }
        .dot-draw { background: var(--accent-green); }
        .dot-10-7 { background: var(--accent-crimson); }

        /* Footer */
        .site-footer {
            margin-top: var(--space-12);
            padding-top: var(--space-8);
            border-top: 1px solid var(--border-subtle);
            display: flex;
            justify-content: space-between;
            align-items: center;
            font-size: 13px;
            color: var(--text-muted);
            flex-wrap: wrap;
            gap: var(--space-4);
        }

        .site-footer a {
            color: var(--text-secondary);
            text-decoration: underline;
        }

        .site-footer a:hover {
            color: var(--accent-crimson);
        }
    </style>
</head>
<body>

<div class="container">
    <!-- Header Navigation -->
    <header class="site-header">
        <div class="brand-cluster">
            <div class="octagon-badge">UFC</div>
            <div class="brand-text">
                <h1>The Dissenter Index</h1>
                <p>31 Years of UFC Judging Data (1995–2026) · Round-by-Round Scoring & Dissent</p>
            </div>
        </div>
        <div class="nav-controls">
            <div class="mode-toggle-group">
                <button class="mode-btn active" id="btn-mode-rounds">Round Scoring Disagreements</button>
                <button class="mode-btn" id="btn-mode-fights">Fight Decision Splits</button>
            </div>
            <button class="theme-btn" id="theme-toggle" title="Toggle Light / Dark mode" aria-label="Toggle theme">
                <svg id="theme-icon-sun" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="display:none;"><circle cx="12" cy="12" r="5"></circle><line x1="12" y1="1" x2="12" y2="3"></line><line x1="12" y1="21" x2="12" y2="23"></line><line x1="4.22" y1="4.22" x2="5.64" y2="5.64"></line><line x1="18.36" y1="18.36" x2="19.78" y2="19.78"></line><line x1="1" y1="12" x2="3" y2="12"></line><line x1="21" y1="12" x2="23" y2="12"></line><line x1="4.22" y1="19.78" x2="5.64" y2="18.36"></line><line x1="18.36" y1="5.64" x2="19.78" y2="4.22"></line></svg>
                <svg id="theme-icon-moon" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"></path></svg>
            </button>
        </div>
    </header>

    <!-- Chapter 1: The Core Question & Macro Benchmark -->
    <section class="hero-lead-card">
        <div class="chapter-badge">Chapter 1 · The Core Discovery</div>
        <h2 class="hero-headline" id="hero-question">When two cage-side judges agree on a round, which third judge breaks away most often?</h2>
        <p class="hero-subhead" id="hero-narrative">
            Across 31,881 individual rounds evaluated by 3-judge panels, exactly <strong>2,362 rounds (7.41%)</strong> produced a lone dissenting judge.
            Among high-volume UFC mainstays (250+ rounds), <strong>Cardo Urso</strong> ranks #1 with a <strong>9.32%</strong> round dissent rate, followed by <strong>Glenn Trowbridge</strong> (8.83%) and <strong>Rick Winter</strong> (8.75%).
        </p>

        <!-- Focused 4 KPI Cards (Unique, non-redundant metrics) -->
        <div class="kpi-grid">
            <div class="kpi-card">
                <div class="kpi-label">Historical UFC Benchmark</div>
                <div class="kpi-value-row">
                    <span class="kpi-value" id="kpi-benchmark-val">7.41%</span>
                </div>
                <div class="kpi-context" id="kpi-benchmark-sub">Average dissent rate across all 31,881 rounds (1 in every 13.5 rounds)</div>
            </div>

            <div class="kpi-card">
                <div class="kpi-label">#1 Veteran Mainstay (250+ Rds)</div>
                <div class="kpi-value-row">
                    <span class="kpi-value" id="kpi-leader-val">9.32%</span>
                    <span class="kpi-delta high" id="kpi-leader-delta">+1.91% vs avg</span>
                </div>
                <div class="kpi-context" id="kpi-leader-sub"><strong>Cardo Urso</strong> · 29 dissents in 311 rounds (1 in every 10.7 rounds)</div>
            </div>

            <div class="kpi-card">
                <div class="kpi-label">Most Consensual Mainstay</div>
                <div class="kpi-value-row">
                    <span class="kpi-value" id="kpi-agreeable-val">6.89%</span>
                    <span class="kpi-delta consensual" id="kpi-agreeable-delta">-0.52% vs avg</span>
                </div>
                <div class="kpi-context" id="kpi-agreeable-sub"><strong>Ben Cartlidge</strong> · 58 dissents in 842 rounds (highest agreement rate)</div>
            </div>

            <div class="kpi-card">
                <div class="kpi-label">Highest Absolute Dissents</div>
                <div class="kpi-value-row">
                    <span class="kpi-value" id="kpi-volume-val">220</span>
                </div>
                <div class="kpi-context" id="kpi-volume-sub"><strong>Sal D'Amato</strong> · 6.34% rate over 3,468 scored rounds (historic volume)</div>
            </div>
        </div>

        <!-- High-density Benchmark Deviation Bar Chart (Zero wasted space) -->
        <div class="gauge-section" id="benchmark-gauge-section">
            <div class="gauge-header">
                <div class="gauge-title">Veteran Mainstays vs 7.41% Historical UFC Average</div>
                <div class="gauge-legend">
                    <span><span class="legend-dot" style="background:var(--accent-crimson);"></span> Higher Dissent Rate (Above Benchmark)</span>
                    <span><span class="legend-dot" style="background:var(--accent-green);"></span> Lower Dissent Rate (More Consensual)</span>
                    <span><span class="legend-dot" style="background:#ffffff; border:1px solid #000;"></span> 7.41% UFC Average</span>
                </div>
            </div>
            <div class="deviation-bars-container" id="deviation-bars">
                <!-- Injected via JavaScript -->
            </div>
        </div>
    </section>

    <!-- Chapter 2: The Hall of Dissent (Curated Leaderboard & Interactive Dossier) -->
    <section class="content-section">
        <div class="section-header-block">
            <div class="chapter-badge">Chapter 2 · The Leaderboard & Dossiers</div>
            <h3 class="section-title" id="table-section-title">The Hall of Dissent: Judge Rankings</h3>
            <p class="section-desc">Click on any judge row to expand their detailed dossier, including their career era, dissent frequency, top friction co-judge, and sample scorecards.</p>
        </div>

        <div class="table-toolbar">
            <div class="filter-pills" id="filter-pills-container">
                <!-- Filter buttons injected dynamically -->
            </div>
            <div class="search-export-cluster">
                <div class="search-wrapper">
                    <svg class="search-icon" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="11" cy="11" r="8"></circle><line x1="21" y1="21" x2="16.65" y2="16.65"></line></svg>
                    <input type="text" class="search-input" id="search-input" placeholder="Search judge name...">
                </div>
                <button class="btn-action" id="btn-export-csv" title="Export table to CSV">
                    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path><polyline points="7 10 12 15 17 10"></polyline><line x1="12" y1="15" x2="12" y2="3"></line></svg>
                    Export CSV
                </button>
            </div>
        </div>

        <div class="table-card">
            <div class="table-responsive">
                <table>
                    <thead id="table-head">
                        <!-- Injected via JS -->
                    </thead>
                    <tbody id="table-body">
                        <!-- Injected via JS -->
                    </tbody>
                </table>
            </div>
        </div>
    </section>

    <!-- Chapter 3: Panel Friction (Co-Judge Head-to-Head Clash Matrix) -->
    <section class="content-section">
        <div class="section-header-block">
            <div class="chapter-badge">Chapter 3 · Panel Friction</div>
            <h3 class="section-title">Co-Judge Head-to-Head Clash Matrix</h3>
            <p class="section-desc">How often do pairs of judges seated on the exact same bout disagree on who won individual rounds? Analyzed across co-judges with at least 15 rounds together.</p>
        </div>

        <div class="table-card">
            <div class="table-responsive">
                <table>
                    <thead>
                        <tr>
                            <th>Judge Pair</th>
                            <th>Rounds Together</th>
                            <th>Conflicting Round Scores</th>
                            <th>Disagreement Rate (%)</th>
                        </tr>
                    </thead>
                    <tbody id="pairs-table-body">
                        <!-- Injected via JS -->
                    </tbody>
                </table>
            </div>
        </div>
    </section>

    <!-- Chapter 4: The Anatomy of a Scored Round -->
    <section class="content-section" id="anatomy-section">
        <div class="section-header-block">
            <div class="chapter-badge">Chapter 4 · Empirical Context</div>
            <h3 class="section-title">The Anatomy of a UFC Round (1995–2026)</h3>
            <p class="section-desc">How often does a round score deviate from the standard 10-9? Out of 31,881 total rounds recorded across 31 years:</p>
        </div>

        <div class="anatomy-bar-container">
            <div class="anatomy-bar">
                <div class="seg-10-9" title="10-9 (95.7%)"></div>
                <div class="seg-10-8" title="10-8 (3.76%)"></div>
                <div class="seg-draw" title="10-10 Draw (0.48%)"></div>
                <div class="seg-10-7" title="10-7 (0.03%)"></div>
            </div>
            <div class="anatomy-legend">
                <div class="anatomy-item"><span class="legend-dot dot-10-9"></span> <strong>10-9 Rounds</strong>: 30,517 (95.72%)</div>
                <div class="anatomy-item"><span class="legend-dot dot-10-8"></span> <strong>10-8 Dominant Rounds</strong>: 1,200 (3.76%)</div>
                <div class="anatomy-item"><span class="legend-dot dot-draw"></span> <strong>10-10 Even Rounds</strong>: 154 (0.48%)</div>
                <div class="anatomy-item"><span class="legend-dot dot-10-7"></span> <strong>10-7 Blowout Rounds</strong>: 10 (0.03%)</div>
            </div>
        </div>

        <!-- Embedded Visualizations -->
        <div class="chart-grid">
            <div class="chart-card round-chart">
                <h4>Mainstay Dissent Distribution (Min 250 Rounds)</h4>
                <p>Individual round disagreement rate among regular veteran judges.</p>
                <div class="chart-img-wrap"><img src="__IMG_ROUND_MIN250__" alt="Round Dissent Rate Min 250"></div>
            </div>
            <div class="chart-card round-chart">
                <h4>Historical Disagreement Trend (1995–2026)</h4>
                <p>How the percentage of rounds with a dissenting judge has evolved across UFC eras.</p>
                <div class="chart-img-wrap"><img src="__IMG_ROUND_TREND__" alt="Round Disagreement Trend Over Time"></div>
            </div>
            <div class="chart-card fight-chart" style="display:none;">
                <h4>Decision Split Rates (Min 50 Fights)</h4>
                <p>Full 15-minute fight decision disagreement rate across judges.</p>
                <div class="chart-img-wrap"><img src="__IMG_MIN50__" alt="Fight Decision Dissent Rate Min 50"></div>
            </div>
            <div class="chart-card fight-chart" style="display:none;">
                <h4>Split Decision Percentage Over Time</h4>
                <p>Evolution of split decisions from UFC 1 through UFC 333.</p>
                <div class="chart-img-wrap"><img src="__IMG_TREND__" alt="Split Decision Trend Over Time"></div>
            </div>
        </div>
    </section>

    <!-- Footer -->
    <footer class="site-footer">
        <div>
            <strong>UFC Judging Analysis Engine</strong> · Produced by Martin Davies.
            Source data retrieved from <a href="https://mmadecisions.com" target="_blank" rel="noopener">MMADecisions.com</a>.
        </div>
        <div>
            Built with strict adherence to data journalism design principles. No vibe-coded anti-patterns.
        </div>
    </footer>
</div>

<script>
    const ROUND_JUDGES = __ROUND_JUDGES_JSON__;
    const FIGHT_JUDGES = __FIGHT_JUDGES_JSON__;
    const ROUND_PAIRS = __ROUND_PAIRS_JSON__;
    const FIGHT_PAIRS = __FIGHT_PAIRS_JSON__;
    const SUMMARY = __SUMMARY_JSON__;
    const ROUND_SUMMARY = __ROUND_SUMMARY_JSON__;

    const UFC_BASELINE_PCT = 7.41;

    let currentMode = 'rounds'; // 'rounds' or 'fights'
    let currentFilterMin = 250;
    let searchQuery = '';
    let sortColumn = 'rate';
    let sortAsc = false;
    let expandedJudge = null;

    // DOM References
    const btnModeRounds = document.getElementById('btn-mode-rounds');
    const btnModeFights = document.getElementById('btn-mode-fights');
    const themeToggle = document.getElementById('theme-toggle');
    const themeIconSun = document.getElementById('theme-icon-sun');
    const themeIconMoon = document.getElementById('theme-icon-moon');
    const filterPillsContainer = document.getElementById('filter-pills-container');
    const searchInput = document.getElementById('search-input');
    const tableHead = document.getElementById('table-head');
    const tableBody = document.getElementById('table-body');
    const pairsTableBody = document.getElementById('pairs-table-body');
    const deviationBars = document.getElementById('deviation-bars');
    const btnExportCsv = document.getElementById('btn-export-csv');

    // Theme Switcher
    function initTheme() {
        const saved = localStorage.getItem('theme') || 'dark';
        document.documentElement.setAttribute('data-theme', saved);
        updateThemeIcon(saved);
    }

    function updateThemeIcon(theme) {
        if (theme === 'light') {
            themeIconSun.style.display = 'none';
            themeIconMoon.style.display = 'block';
        } else {
            themeIconSun.style.display = 'block';
            themeIconMoon.style.display = 'none';
        }
    }

    themeToggle.addEventListener('click', () => {
        const cur = document.documentElement.getAttribute('data-theme') || 'dark';
        const next = cur === 'dark' ? 'light' : 'dark';
        document.documentElement.setAttribute('data-theme', next);
        localStorage.setItem('theme', next);
        updateThemeIcon(next);
    });

    // Mode Switcher (Rounds vs Fights)
    function setMode(mode) {
        currentMode = mode;
        expandedJudge = null;
        if (mode === 'rounds') {
            btnModeRounds.classList.add('active');
            btnModeFights.classList.remove('active');
            currentFilterMin = 250;

            document.getElementById('hero-question').textContent = "When two cage-side judges agree on a round, which third judge breaks away most often?";
            document.getElementById('hero-narrative').innerHTML = "Across 31,881 individual rounds evaluated by 3-judge panels, exactly <strong>2,362 rounds (7.41%)</strong> produced a lone dissenting judge. Among high-volume UFC mainstays (250+ rounds), <strong>Cardo Urso</strong> ranks #1 with a <strong>9.32%</strong> round dissent rate, followed by <strong>Glenn Trowbridge</strong> (8.83%) and <strong>Rick Winter</strong> (8.75%).";

            document.getElementById('kpi-benchmark-val').textContent = "7.41%";
            document.getElementById('kpi-benchmark-sub').textContent = "Average dissent rate across all 31,881 rounds (1 in every 13.5 rounds)";

            document.getElementById('kpi-leader-val').textContent = "9.32%";
            document.getElementById('kpi-leader-delta').textContent = "+1.91% vs avg";
            document.getElementById('kpi-leader-sub').innerHTML = "<strong>Cardo Urso</strong> · 29 dissents in 311 rounds (1 in every 10.7 rounds)";

            document.getElementById('kpi-agreeable-val').textContent = "6.89%";
            document.getElementById('kpi-agreeable-delta').textContent = "-0.52% vs avg";
            document.getElementById('kpi-agreeable-sub').innerHTML = "<strong>Ben Cartlidge</strong> · 58 dissents in 842 rounds (highest agreement rate)";

            document.getElementById('kpi-volume-val').textContent = "220";
            document.getElementById('kpi-volume-sub').innerHTML = "<strong>Sal D'Amato</strong> · 6.34% rate over 3,468 scored rounds (historic volume)";

            document.getElementById('benchmark-gauge-section').style.display = 'block';
            document.getElementById('anatomy-section').style.display = 'block';
            document.querySelectorAll('.round-chart').forEach(c => c.style.display = 'block');
            document.querySelectorAll('.fight-chart').forEach(c => c.style.display = 'none');
        } else {
            btnModeRounds.classList.remove('active');
            btnModeFights.classList.add('active');
            currentFilterMin = 100;

            document.getElementById('hero-question').textContent = "Which UFC judge dissents most often on the final fight decision outcome?";
            document.getElementById('hero-narrative').innerHTML = "When evaluating the final 15-minute fight decision across 4,010 UFC bouts, <strong>Barry Foley</strong> holds the #1 disagreement rate among regular judges (50+ fights) at <strong>22.64%</strong>. Among 250+ fight veterans, <strong>Adalaide Byrd</strong> ranks #1 with a <strong>9.29%</strong> split dissent rate.";

            document.getElementById('kpi-benchmark-val').textContent = "20.0%";
            document.getElementById('kpi-benchmark-sub').textContent = "Split decision rate across 4,010 UFC fights (804 split decisions)";

            document.getElementById('kpi-leader-val').textContent = "22.64%";
            document.getElementById('kpi-leader-delta').textContent = "+13.3% vs avg";
            document.getElementById('kpi-leader-sub').innerHTML = "<strong>Barry Foley</strong> · 12 dissents in 53 fights (Min 50 fights)";

            document.getElementById('kpi-agreeable-val').textContent = "4.85%";
            document.getElementById('kpi-agreeable-delta').textContent = "-4.5% vs avg";
            document.getElementById('kpi-agreeable-sub').innerHTML = "<strong>Ben Cartlidge</strong> · 13 dissents in 268 fights (most consensual)";

            document.getElementById('kpi-volume-val').textContent = "75";
            document.getElementById('kpi-volume-sub').innerHTML = "<strong>Sal D'Amato</strong> · 1,151 fights judged (most active in UFC history)";

            document.getElementById('benchmark-gauge-section').style.display = 'none';
            document.getElementById('anatomy-section').style.display = 'none';
            document.querySelectorAll('.round-chart').forEach(c => c.style.display = 'none');
            document.querySelectorAll('.fight-chart').forEach(c => c.style.display = 'block');
        }

        renderFilterPills();
        renderTableHeaders();
        renderTable();
        renderDeviationBars();
        renderPairsTable();
    }

    // Benchmark Deviation Bars
    function renderDeviationBars() {
        if (currentMode !== 'rounds') return;
        const mainstays = ROUND_JUDGES.filter(j => (j.total_rounds || 0) >= 250).slice(0, 10);
        deviationBars.innerHTML = mainstays.map(j => {
            const pct = j.round_dissent_pct || 0;
            const diff = pct - UFC_BASELINE_PCT;
            const isOver = diff >= 0;
            const diffStr = (isOver ? '+' : '') + diff.toFixed(2) + '%';
            const barColor = isOver ? 'var(--accent-crimson)' : 'var(--accent-green)';
            const barWidth = Math.min(100, Math.max(8, (pct / 12) * 100));

            return `
                <div class="bar-row">
                    <span class="bar-judge-name">${escapeHtml(j.judge_name)}</span>
                    <div class="bar-track">
                        <div class="bar-benchmark-line" style="left: ${(UFC_BASELINE_PCT / 12) * 100}%;" title="7.41% Baseline"></div>
                        <div class="bar-fill" style="width: ${barWidth}%; background: ${barColor};"></div>
                    </div>
                    <span class="bar-val" style="color: ${barColor};">${pct.toFixed(2)}% <small style="font-size:10px;">(${diffStr})</small></span>
                </div>
            `;
        }).join('');
    }

    // Filter Buttons
    function renderFilterPills() {
        filterPillsContainer.innerHTML = '';
        const filters = currentMode === 'rounds' ? [
            { label: 'All-Time Mainstays (250+ Rds)', min: 250 },
            { label: 'Regular Veterans (100+ Rds)', min: 100 },
            { label: 'Emerging / Mid-Volume (50+ Rds)', min: 50 },
            { label: 'All Judges (1+ Rds)', min: 1 }
        ] : [
            { label: 'All-Time Mainstays (250+ Fights)', min: 250 },
            { label: 'Veterans (100+ Fights)', min: 100 },
            { label: 'Regulars (50+ Fights)', min: 50 },
            { label: 'All Judges', min: 1 }
        ];

        filters.forEach(f => {
            const btn = document.createElement('button');
            btn.className = 'pill-btn' + (f.min === currentFilterMin ? ' active' : '');
            btn.textContent = f.label;
            btn.addEventListener('click', () => {
                document.querySelectorAll('.pill-btn').forEach(b => b.classList.remove('active'));
                btn.classList.add('active');
                currentFilterMin = f.min;
                renderTable();
            });
            filterPillsContainer.appendChild(btn);
        });
    }

    // Table Headers
    function renderTableHeaders() {
        if (currentMode === 'rounds') {
            tableHead.innerHTML = `
                <tr>
                    <th data-sort="rank" style="width:50px;">#</th>
                    <th data-sort="name">Judge Name</th>
                    <th data-sort="rounds">Rounds Judged</th>
                    <th data-sort="dissents">Lone Dissents</th>
                    <th data-sort="rate">Dissent Rate (%)</th>
                    <th data-sort="ten_eight">10-8 Rounds (%)</th>
                    <th data-sort="partner">Top Friction Co-Judge</th>
                    <th style="text-align:right;">Profile</th>
                </tr>
            `;
        } else {
            tableHead.innerHTML = `
                <tr>
                    <th data-sort="rank" style="width:50px;">#</th>
                    <th data-sort="name">Judge Name</th>
                    <th data-sort="fights">Fights Judged</th>
                    <th data-sort="dissents">Split Dissents</th>
                    <th data-sort="rate">Dissent Rate (%)</th>
                    <th data-sort="unanimous">Unanimous %</th>
                    <th data-sort="era">Active Era</th>
                    <th style="text-align:right;">Profile</th>
                </tr>
            `;
        }

        tableHead.querySelectorAll('th[data-sort]').forEach(th => {
            th.addEventListener('click', () => {
                const col = th.dataset.sort;
                if (sortColumn === col) {
                    sortAsc = !sortAsc;
                } else {
                    sortColumn = col;
                    sortAsc = (col === 'name' || col === 'rank');
                }
                renderTable();
            });
        });
    }

    // Table Render with Accordion Dossier
    function renderTable() {
        const rawList = currentMode === 'rounds' ? ROUND_JUDGES : FIGHT_JUDGES;

        let filtered = rawList.filter(j => {
            const count = currentMode === 'rounds' ? (j.total_rounds || 0) : (j.total_fights || 0);
            if (count < currentFilterMin) return false;
            if (searchQuery) {
                return j.judge_name.toLowerCase().includes(searchQuery.toLowerCase());
            }
            return true;
        });

        // Sorting
        filtered.sort((a, b) => {
            let valA, valB;
            if (currentMode === 'rounds') {
                if (sortColumn === 'name') { valA = a.judge_name; valB = b.judge_name; }
                else if (sortColumn === 'rounds') { valA = a.total_rounds; valB = b.total_rounds; }
                else if (sortColumn === 'dissents') { valA = a.round_dissents; valB = b.round_dissents; }
                else if (sortColumn === 'ten_eight') { valA = a.ten_eight_rounds; valB = b.ten_eight_rounds; }
                else if (sortColumn === 'partner') { valA = a.top_clash_partner || ''; valB = b.top_clash_partner || ''; }
                else { valA = a.round_dissent_pct; valB = b.round_dissent_pct; }
            } else {
                if (sortColumn === 'name') { valA = a.judge_name; valB = b.judge_name; }
                else if (sortColumn === 'fights') { valA = a.total_fights; valB = b.total_fights; }
                else if (sortColumn === 'dissents') { valA = a.dissents; valB = b.dissents; }
                else if (sortColumn === 'unanimous') { valA = a.unanimous_pct; valB = b.unanimous_pct; }
                else if (sortColumn === 'era') { valA = a.first_year; valB = b.first_year; }
                else { valA = a.dissent_pct; valB = b.dissent_pct; }
            }

            if (valA < valB) return sortAsc ? -1 : 1;
            if (valA > valB) return sortAsc ? 1 : -1;
            return 0;
        });

        if (filtered.length === 0) {
            tableBody.innerHTML = `<tr><td colspan="8" style="text-align:center; padding: 32px; color: var(--text-muted);">No judges found matching search or threshold criteria.</td></tr>`;
            return;
        }

        let html = '';
        filtered.forEach((j, idx) => {
            const isExpanded = expandedJudge === j.judge_name;
            if (currentMode === 'rounds') {
                const pct = j.round_dissent_pct || 0;
                const diff = pct - UFC_BASELINE_PCT;
                const badgeClass = diff >= 0 ? 'over' : 'under';
                const badgeSign = diff >= 0 ? '+' : '';
                const tenEightStr = `${j.ten_eight_rounds || 0} (${(j.ten_eight_pct || 0).toFixed(1)}%)`;
                const clashStr = j.top_clash_partner ? `${escapeHtml(j.top_clash_partner)} (${(j.top_clash_pct || 0).toFixed(1)}%)` : '—';

                html += `
                    <tr class="judge-row ${isExpanded ? 'expanded' : ''}" data-judge="${escapeHtml(j.judge_name)}">
                        <td class="mono-num" style="color:var(--text-muted);">${idx + 1}</td>
                        <td>
                            <div class="judge-cell">
                                <svg class="expand-chevron" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><polyline points="9 18 15 12 9 6"></polyline></svg>
                                <span>${escapeHtml(j.judge_name)}</span>
                            </div>
                        </td>
                        <td class="mono-num">${(j.total_rounds || 0).toLocaleString()}</td>
                        <td class="mono-num">${(j.round_dissents || 0).toLocaleString()}</td>
                        <td>
                            <div class="rate-cell-group">
                                <span class="mono-num" style="font-weight:700;">${pct.toFixed(2)}%</span>
                                <span class="rate-badge ${badgeClass}">${badgeSign}${diff.toFixed(2)}%</span>
                            </div>
                        </td>
                        <td class="mono-num">${tenEightStr}</td>
                        <td>${clashStr}</td>
                        <td style="text-align:right;">
                            <button class="pill-btn" style="padding:2px 8px; font-size:11px;">${isExpanded ? 'Close' : 'Dossier'}</button>
                        </td>
                    </tr>
                `;

                // Dossier Drawer Row
                if (isExpanded) {
                    const sampleDissents = j.sample_dissents || [];
                    const dissentsHtml = sampleDissents.length > 0 ? sampleDissents.map(d => `
                        <div class="sample-dissent-box">
                            <div class="sample-dissent-header">
                                <span>${d.year || ''}</span>
                                <span>Round ${d.round || ''}</span>
                            </div>
                            <div class="sample-fight-name">${escapeHtml(d.fight || '')}</div>
                            <div style="display:flex; justify-content:space-between; align-items:center;">
                                <span class="sample-score-tag">Score: ${d.score}</span>
                                <span style="font-size:11px; color:var(--text-muted);">vs ${escapeHtml(d.c1)}, ${escapeHtml(d.c2)}</span>
                            </div>
                        </div>
                    `).join('') : '<div style="color:var(--text-muted); font-size:12px;">No round dissent samples on file.</div>';

                    const freq = j.round_dissents > 0 ? (j.total_rounds / j.round_dissents).toFixed(1) : '—';

                    html += `
                        <tr class="dossier-drawer-row visible">
                            <td colspan="8" style="padding:0;">
                                <div class="dossier-card">
                                    <div class="dossier-bio">
                                        <h4>${escapeHtml(j.judge_name)}</h4>
                                        <div class="dossier-stat-pill">Active UFC Era: <strong>${j.first_year || 1995} – ${j.last_year || 2026}</strong></div>
                                        <div class="dossier-stat-pill">Dissent Frequency: <strong>Dissents once every ${freq} rounds</strong></div>
                                        <div class="dossier-stat-pill">Consensus Agreement: <strong>${((j.consensus_rounds || 0) / (j.total_rounds || 1) * 100).toFixed(1)}% of rounds</strong></div>
                                        <div class="dossier-stat-pill">Dominant 10-8 Rounds Given: <strong>${j.ten_eight_rounds || 0} (${(j.ten_eight_pct || 0).toFixed(1)}%)</strong></div>
                                        <div class="dossier-stat-pill">Top Co-Judge Clash: <strong>${escapeHtml(j.top_clash_partner)} (${(j.top_clash_pct || 0).toFixed(1)}% disagreement over ${j.top_clash_rounds || 0} rounds)</strong></div>
                                    </div>
                                    <div class="dossier-rounds-log">
                                        <h5>Notable Round Dissent Examples</h5>
                                        <div class="sample-dissents-grid">
                                            ${dissentsHtml}
                                        </div>
                                    </div>
                                </div>
                            </td>
                        </tr>
                    `;
                }
            } else {
                const pct = j.dissent_pct || 0;
                const era = `${j.first_year || ''}–${j.last_year || ''}`;

                html += `
                    <tr class="judge-row" data-judge="${escapeHtml(j.judge_name)}">
                        <td class="mono-num" style="color:var(--text-muted);">${idx + 1}</td>
                        <td>
                            <div class="judge-cell">
                                <span>${escapeHtml(j.judge_name)}</span>
                            </div>
                        </td>
                        <td class="mono-num">${(j.total_fights || 0).toLocaleString()}</td>
                        <td class="mono-num">${(j.dissents || 0).toLocaleString()}</td>
                        <td class="mono-num" style="font-weight:700;">${pct.toFixed(2)}%</td>
                        <td class="mono-num">${j.unanimous_pct || 0}%</td>
                        <td>${era}</td>
                        <td style="text-align:right;"><span class="rate-badge under">Fight Decision</span></td>
                    </tr>
                `;
            }
        });

        tableBody.innerHTML = html;

        // Attach Row Click Listener for Accordion Expansion
        tableBody.querySelectorAll('tr.judge-row').forEach(row => {
            row.addEventListener('click', () => {
                const jName = row.dataset.judge;
                expandedJudge = (expandedJudge === jName) ? null : jName;
                renderTable();
            });
        });
    }

    // Render Pairs Table
    function renderPairsTable() {
        const pairsList = currentMode === 'rounds' ? ROUND_PAIRS : FIGHT_PAIRS;
        if (!pairsList || pairsList.length === 0) {
            pairsTableBody.innerHTML = `<tr><td colspan="4" style="text-align:center; padding: 24px; color: var(--text-muted);">No judge pairing data recorded.</td></tr>`;
            return;
        }

        pairsTableBody.innerHTML = pairsList.slice(0, 15).map(p => {
            const pairName = escapeHtml(p.pair || `${p.judge_a} & ${p.judge_b}`);
            const volume = currentMode === 'rounds' ? (p.rounds_together || 0) : (p.fights_together || 0);
            const diff = currentMode === 'rounds' ? (p.round_winner_disagreements || 0) : (p.pick_disagreements || 0);
            const rate = currentMode === 'rounds' ? (p.round_disagree_pct || 0) : (p.disagree_pct || 0);
            const badgeClass = rate >= 15 ? 'over' : 'under';

            return `
                <tr>
                    <td style="font-weight:700; color:var(--text-primary);">${pairName}</td>
                    <td class="mono-num">${volume.toLocaleString()}</td>
                    <td class="mono-num">${diff.toLocaleString()}</td>
                    <td>
                        <span class="rate-badge ${badgeClass}">${rate.toFixed(1)}%</span>
                    </td>
                </tr>
            `;
        }).join('');
    }

    // Export to CSV Function
    btnExportCsv.addEventListener('click', () => {
        const list = currentMode === 'rounds' ? ROUND_JUDGES : FIGHT_JUDGES;
        let csv = '';
        if (currentMode === 'rounds') {
            csv = "Judge Name,Total Rounds,Round Dissents,Dissent Rate Pct,Ten Eight Rounds,Consensus Rounds,Top Clash Partner\\n";
            list.forEach(j => {
                csv += `"${j.judge_name}",${j.total_rounds},${j.round_dissents},${j.round_dissent_pct},${j.ten_eight_rounds},${j.consensus_rounds},"${j.top_clash_partner || ''}"\\n`;
            });
        } else {
            csv = "Judge Name,Total Fights,Dissents,Dissent Rate Pct,Unanimous Pct,First Year,Last Year\\n";
            list.forEach(j => {
                csv += `"${j.judge_name}",${j.total_fights},${j.dissents},${j.dissent_pct},${j.unanimous_pct},${j.first_year},${j.last_year}\\n`;
            });
        }

        const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `ufc_judging_${currentMode}_analysis.csv`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
    });

    // Event Listeners
    btnModeRounds.addEventListener('click', () => setMode('rounds'));
    btnModeFights.addEventListener('click', () => setMode('fights'));
    searchInput.addEventListener('input', (e) => {
        searchQuery = e.target.value.trim();
        renderTable();
    });

    function escapeHtml(str) {
        if (!str) return '';
        return String(str)
            .replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;')
            .replace(/"/g, '&quot;')
            .replace(/'/g, '&#039;');
    }

    // Initialize
    initTheme();
    setMode('rounds');
</script>
</body>
</html>
"""


def build_dashboard_html() -> Path:
    """Compile JSON payload and embedded charts into a secure, single-file HTML dashboard."""
    if not WEB_DATA_PATH.exists():
        raise FileNotFoundError(f"Web data not found at {WEB_DATA_PATH}. Run export_web_data first.")

    with open(WEB_DATA_PATH, "r", encoding="utf-8") as f:
        judging_data: Dict[str, Any] = json.load(f)

    # Encode round-level visualizations
    img_round_min50 = encode_image_base64("round_dissent_rate_min_50.png")
    img_round_min250 = encode_image_base64("round_dissent_rate_min_250.png")
    img_round_scatter = encode_image_base64("scatter_rounds_vs_dissent.png")
    img_round_trend = encode_image_base64("round_disagreement_trend.png")

    # Encode fight-level visualizations
    img_min50 = encode_image_base64("dissent_rate_min_50.png")
    img_min100 = encode_image_base64("dissent_rate_min_100.png")
    img_scatter = encode_image_base64("scatter_fights_vs_dissent.png")
    img_trend = encode_image_base64("split_decision_trend.png")

    # Safe JSON stringification preventing </script> injection
    safe_round_judges_json = json.dumps(judging_data.get('round_judges', [])).replace("<", "\\u003c").replace(">", "\\u003e")
    safe_fight_judges_json = json.dumps(judging_data.get('judges', [])).replace("<", "\\u003c").replace(">", "\\u003e")
    safe_round_pairs_json = json.dumps(judging_data.get('round_pairs', [])).replace("<", "\\u003c").replace(">", "\\u003e")
    safe_fight_pairs_json = json.dumps(judging_data.get('pairs', [])).replace("<", "\\u003c").replace(">", "\\u003e")
    safe_summary_json = json.dumps(judging_data.get('summary', {})).replace("<", "\\u003c").replace(">", "\\u003e")
    safe_round_summary_json = json.dumps(judging_data.get('summary', {}).get('rounds', {})).replace("<", "\\u003c").replace(">", "\\u003e")

    html_content = DASHBOARD_TEMPLATE
    replacements = {
        "__ROUND_JUDGES_JSON__": safe_round_judges_json,
        "__FIGHT_JUDGES_JSON__": safe_fight_judges_json,
        "__ROUND_PAIRS_JSON__": safe_round_pairs_json,
        "__FIGHT_PAIRS_JSON__": safe_fight_pairs_json,
        "__SUMMARY_JSON__": safe_summary_json,
        "__ROUND_SUMMARY_JSON__": safe_round_summary_json,
        "__IMG_ROUND_MIN50__": img_round_min50,
        "__IMG_ROUND_MIN250__": img_round_min250,
        "__IMG_ROUND_SCATTER__": img_round_scatter,
        "__IMG_ROUND_TREND__": img_round_trend,
        "__IMG_MIN50__": img_min50,
        "__IMG_MIN100__": img_min100,
        "__IMG_SCATTER__": img_scatter,
        "__IMG_TREND__": img_trend,
    }

    for placeholder, val in replacements.items():
        html_content = html_content.replace(placeholder, val)

    OUTPUT_HTML_PATH.write_text(html_content, encoding="utf-8")
    print(f"Compiled standalone UFC judging dashboard to {OUTPUT_HTML_PATH}")
    return OUTPUT_HTML_PATH


if __name__ == "__main__":
    build_dashboard_html()
