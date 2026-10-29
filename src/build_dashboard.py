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
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.security import safe_json_embed, safe_resolve_path

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
    except (OSError, ValueError) as e:
        logger.warning("Could not encode image %s: %s", image_filename, e)
    return ""


DASHBOARD_TEMPLATE = """<!DOCTYPE html>
<html lang="en" data-theme="dark">
<head>
    <meta charset="UTF-8">
        <link rel="icon" type="image/svg+xml" href="data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'><polygon points='30,0 70,0 100,30 100,70 70,100 30,100 0,70 0,30' fill='%23e11d48'/><text x='50' y='65' font-size='38' font-family='sans-serif' font-weight='800' fill='white' text-anchor='middle'>UFC</text></svg>">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>The Dissenter Index: UFC Judging & Round-by-Round Scoring Analysis (1995–2026)</title>
    <meta name="description" content="An empirical investigation into 32,876 UFC rounds across 4,010 decisions and 48 stoppage bouts: which cage-side judges disagree with their colleagues most frequently?">
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
    <style>
        :root {
            /* Strict 4-Step Spacing Scale */
            --space-half: 4px;
            --space-1: 8px;
            --space-2: 16px;
            --space-3: 24px;
            --space-4: 32px;

            /* Consolidated Border Radii: 1 Container Radius (8px) + Pills (9999px) */
            --radius: 8px;
            --radius-pill: 9999px;

            /* Strict 4-Step Fluid Typography Scale (clamp() for smooth cross-device scaling) */
            --font-size-title: clamp(22px, 3.2vw, 28px);
            --font-size-header: clamp(16px, 2.2vw, 18px);
            --font-size-body: 14px;
            --font-size-caption: 12px;
            --font-size-stat: clamp(24px, 4vw, 32px);

            /* Typography Stacks: High-legibility proportional typefaces with tabular numerals */
            --font-display: 'Plus Jakarta Sans', system-ui, -apple-system, sans-serif;
            --font-body: 'Inter', system-ui, -apple-system, sans-serif;
            --font-mono: 'Inter', system-ui, -apple-system, sans-serif;
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


        /* Enforce tabular numerals across all numbers, tables, badges, and statistics */
        .tabular-nums,
        .mono-num,
        .kpi-value,
        .kpi-delta,
        .bar-val,
        .bar-delta,
        .rate-badge,
        .col-num,
        th.col-num,
        td.col-num,
        .stat-tile-value,
        .stat-tile-sub,
        .friction-rate,
        .score-badge-crimson,
        .dissent-year-round,
        .dossier-era-tag strong,
        .dossier-stat-pill strong,
        .anatomy-legend strong,
        .sample-score-tag {
            font-variant-numeric: tabular-nums;
            font-feature-settings: "tnum" 1;
        }

        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
            transition: background-color 0.2s ease, border-color 0.2s ease, color 0.2s ease;
            -webkit-tap-highlight-color: transparent;
        }

        html, body {
            max-width: 100%;
            overflow-x: hidden;
            width: 100%;
        }

        body {
            font-family: var(--font-body);
            font-size: var(--font-size-body);
            background-color: var(--bg-page);
            color: var(--text-primary);
            line-height: 1.5;
            -webkit-font-smoothing: antialiased;
        }

        .container {
            max-width: 1280px;
            margin: 0 auto;
            padding: var(--space-3) var(--space-3) var(--space-4) var(--space-3);
        }

        @media (max-width: 900px) {
            .container {
                padding: var(--space-2) var(--space-2) var(--space-3) var(--space-2);
            }
        }

        @media (max-width: 600px) {
            .container {
                padding: 12px 10px 24px 10px;
            }
        }

        /* Responsive Text Utilities */
        .label-full {
            display: inline;
        }

        .label-short {
            display: none;
        }

        @media (max-width: 720px) {
            .label-full {
                display: none;
            }
            .label-short {
                display: inline;
            }
        }

        /* Header Navigation */
        .site-header {
            display: flex;
            align-items: center;
            justify-content: space-between;
            padding: var(--space-2) 0;
            margin-bottom: var(--space-4);
            border-bottom: 1px solid var(--border-subtle);
            gap: var(--space-2);
        }

        @media (max-width: 920px) {
            .site-header {
                display: grid;
                grid-template-columns: 1fr auto;
                grid-template-areas:
                    "brand theme"
                    "nav nav";
                row-gap: 12px;
                column-gap: 12px;
                margin-bottom: var(--space-3);
            }
        }

        .brand-cluster {
            display: flex;
            align-items: center;
            gap: var(--space-2);
            min-width: 0;
        }

        @media (max-width: 920px) {
            .brand-cluster {
                grid-area: brand;
            }
        }

        .octagon-badge {
            width: 40px;
            height: 40px;
            min-width: 40px;
            background: linear-gradient(135deg, var(--accent-crimson), #be123c);
            clip-path: polygon(30% 0%, 70% 0%, 100% 30%, 100% 70%, 70% 100%, 30% 100%, 0% 70%, 0% 30%);
            display: flex;
            align-items: center;
            justify-content: center;
            font-family: var(--font-display);
            font-weight: 800;
            font-size: 15px;
            color: #ffffff;
            box-shadow: 0 0 16px rgba(225, 29, 72, 0.4);
            flex-shrink: 0;
        }

        .brand-text {
            min-width: 0;
        }

        .brand-text h1 {
            font-family: var(--font-display);
            font-size: clamp(16px, 4vw, var(--font-size-header));
            font-weight: 800;
            letter-spacing: -0.02em;
            color: var(--text-primary);
            line-height: 1.2;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
        }

        .brand-text p {
            font-size: clamp(11px, 2.5vw, var(--font-size-caption));
            color: var(--text-secondary);
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
        }

        .nav-controls {
            display: flex;
            align-items: center;
            gap: var(--space-2);
            min-width: 0;
        }

        @media (max-width: 920px) {
            .nav-controls {
                grid-area: nav;
                width: 100%;
                display: block;
            }
        }

        .mode-toggle-group {
            display: flex;
            background: var(--bg-surface-elevated);
            padding: 3px;
            border-radius: var(--radius-pill);
            border: 1px solid var(--border-subtle);
            gap: 2px;
            overflow-x: auto;
            max-width: 100%;
        }

        .mode-toggle-group::-webkit-scrollbar {
            display: none;
        }

        @media (max-width: 920px) {
            .mode-toggle-group {
                width: 100%;
            }
            .mode-btn {
                flex: 1;
                text-align: center;
                justify-content: center;
            }
        }

        .mode-btn {
            border: none;
            background: transparent;
            color: var(--text-secondary);
            font-family: var(--font-body);
            font-size: 13px;
            font-weight: 600;
            padding: 10px var(--space-2);
            min-height: 44px;
            border-radius: var(--radius-pill);
            cursor: pointer;
            transition: all 0.15s ease;
            white-space: nowrap;
            display: inline-flex;
            align-items: center;
            justify-content: center;
            box-sizing: border-box;
        }

        @media (max-width: 480px) {
            .mode-btn {
                padding: 6px 6px;
                font-size: 11px;
            }
        }

        .mode-btn:hover {
            color: var(--text-primary);
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
            width: 44px;
            height: 44px;
            min-width: 44px;
            min-height: 44px;
            border-radius: var(--radius);
            border: 1px solid var(--border-subtle);
            background: var(--bg-surface-elevated);
            color: var(--text-primary);
            cursor: pointer;
            transition: all 0.15s ease;
            flex-shrink: 0;
            box-sizing: border-box;
        }

        @media (max-width: 920px) {
            .theme-btn {
                grid-area: theme;
                justify-self: end;
            }
        }

        .theme-btn:hover {
            border-color: var(--border-strong);
            transform: translateY(-1px);
        }

        /* Chapter Banner & Lead Narrative */
        .chapter-badge {
            display: inline-flex;
            align-items: center;
            gap: var(--space-1);
            font-family: var(--font-mono);
            font-size: 11px;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 0.08em;
            color: var(--accent-crimson);
            background: var(--accent-crimson-bg);
            padding: var(--space-half) var(--space-1);
            border-radius: var(--radius-pill);
            margin-bottom: var(--space-1);
            border: 1px solid var(--border-highlight);
        }

        .hero-lead-card {
            background: var(--bg-surface-card);
            border: 1px solid var(--border-subtle);
            border-radius: var(--radius);
            padding: var(--space-4);
            box-shadow: var(--shadow-card);
            -webkit-backdrop-filter: blur(12px);
            backdrop-filter: blur(12px);
            margin-bottom: var(--space-4);
            position: relative;
            overflow: hidden;
        }

        @media (max-width: 900px) {
            .hero-lead-card {
                padding: var(--space-3);
                margin-bottom: var(--space-3);
            }
        }

        @media (max-width: 600px) {
            .hero-lead-card {
                padding: 16px 14px;
                margin-bottom: 16px;
            }
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
            font-size: clamp(20px, 4.5vw, var(--font-size-title));
            font-weight: 800;
            letter-spacing: -0.03em;
            line-height: 1.25;
            margin-bottom: var(--space-1);
            color: var(--text-primary);
        }

        .hero-subhead {
            font-size: clamp(13px, 3.2vw, var(--font-size-body));
            color: var(--text-secondary);
            max-width: 900px;
            line-height: 1.6;
            margin-bottom: var(--space-3);
        }

        .hero-subhead strong {
            color: var(--text-primary);
        }

        /* 4 Focused KPI Metric Cards */
        .kpi-grid {
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: var(--space-2);
            margin-bottom: var(--space-3);
        }

        @media (max-width: 1024px) {
            .kpi-grid {
                grid-template-columns: repeat(2, 1fr);
                gap: 12px;
            }
        }

        @media (max-width: 520px) {
            .kpi-grid {
                grid-template-columns: 1fr;
                gap: 10px;
            }
        }

        .kpi-card {
            background: var(--bg-surface);
            border: 1px solid var(--border-subtle);
            border-radius: var(--radius);
            padding: var(--space-2) var(--space-3);
            display: flex;
            flex-direction: column;
            justify-content: space-between;
            position: relative;
        }

        @media (max-width: 600px) {
            .kpi-card {
                padding: 12px 14px;
            }
        }

        .kpi-card:hover {
            border-color: var(--border-strong);
        }

        .kpi-label {
            font-size: 11px;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.05em;
            color: var(--text-muted);
            margin-bottom: var(--space-1);
        }

        .kpi-value-row {
            display: flex;
            align-items: baseline;
            justify-content: space-between;
            flex-wrap: wrap;
            gap: var(--space-1);
            margin-bottom: var(--space-half);
        }

        .kpi-value {
            font-family: var(--font-mono);
            font-size: clamp(24px, 5.5vw, var(--font-size-stat));
            font-weight: 800;
            color: var(--text-primary);
            font-variant-numeric: tabular-nums;
            font-feature-settings: "tnum" 1;
            letter-spacing: -0.02em;
        }

        .kpi-delta {
            font-family: var(--font-mono);
            font-size: var(--font-size-caption);
            font-weight: 700;
            padding: 2px 8px;
            border-radius: var(--radius-pill);
            font-variant-numeric: tabular-nums;
            white-space: nowrap;
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
            font-size: var(--font-size-caption);
            color: var(--text-secondary);
            line-height: 1.4;
        }

        /* Benchmark Deviation Bar Visualization */
        .gauge-section {
            background: var(--bg-surface);
            border: 1px solid var(--border-subtle);
            border-radius: var(--radius);
            padding: var(--space-3);
            margin-top: var(--space-2);
        }

        @media (max-width: 640px) {
            .gauge-section {
                padding: 14px 10px;
            }
        }

        .gauge-header {
            display: flex;
            justify-content: space-between;
            align-items: flex-start;
            margin-bottom: var(--space-2);
            flex-direction: column;
            gap: var(--space-2);
        }

        @media (min-width: 900px) {
            .gauge-header {
                flex-direction: row;
                align-items: center;
            }
        }

        .gauge-title {
            font-family: var(--font-display);
            font-size: clamp(15px, 3.5vw, var(--font-size-header));
            font-weight: 700;
            color: var(--text-primary);
        }

        .gauge-controls-cluster {
            display: flex;
            align-items: center;
            gap: var(--space-2);
            flex-wrap: wrap;
            width: 100%;
        }

        @media (min-width: 900px) {
            .gauge-controls-cluster {
                width: auto;
                justify-content: flex-end;
            }
        }

        @media (max-width: 640px) {
            .gauge-controls-cluster {
                flex-direction: column;
                align-items: stretch;
                gap: 8px;
            }
            .gauge-controls-cluster .segmented-group {
            display: inline-flex;
            background: var(--bg-surface-elevated);
            padding: 3px;
            border-radius: var(--radius-pill);
            border: 1px solid var(--border-subtle);
            gap: 3px;
            align-items: center;
            box-sizing: border-box;
        }
            .gauge-controls-cluster .seg-btn {
                flex: 1;
                justify-content: center;
                padding: 10px 12px;
                min-height: 44px;
                font-size: 12px;
            }
        }

        .gauge-legend {
            display: flex;
            align-items: center;
            gap: var(--space-2);
            font-size: var(--font-size-caption);
            color: var(--text-secondary);
            flex-wrap: wrap;
            margin-bottom: var(--space-1);
        }

        @media (max-width: 640px) {
            .gauge-legend {
                font-size: 11px;
                gap: 6px 10px;
            }
        }

        .gauge-subtitle {
            font-size: 12px;
            color: var(--text-secondary);
            margin-top: 2px;
        }

        .legend-dot {
            width: 10px;
            height: 10px;
            border-radius: 50%;
            display: inline-block;
            flex-shrink: 0;
        }

        .legend-dot.crimson {
            background: var(--accent-crimson);
        }

        .legend-dot.green {
            background: var(--accent-green);
        }

        .legend-dot.benchmark {
            background: #ffffff;
            border: 1px solid #000000;
        }

        .deviation-bars-container {
            display: flex;
            flex-direction: column;
            gap: var(--space-1);
            margin-top: var(--space-2);
        }

        .segmented-group {
            display: inline-flex;
            background: var(--bg-surface-elevated);
            padding: 3px;
            border-radius: var(--radius-pill);
            border: 1px solid var(--border-subtle);
            gap: 2px;
        }

        .seg-btn {
            border: none;
            background: transparent;
            color: var(--text-secondary);
            font-family: var(--font-body);
            font-size: 13px;
            font-weight: 600;
            padding: 10px 16px;
            min-height: 44px;
            border-radius: var(--radius-pill);
            cursor: pointer;
            transition: all 0.15s ease;
            display: inline-flex;
            align-items: center;
            justify-content: center;
            gap: 6px;
            white-space: nowrap;
            box-sizing: border-box;
        }

        .seg-btn:hover {
            color: var(--text-primary);
        }

        .seg-btn.active {
            background: var(--text-primary);
            color: var(--bg-page);
            box-shadow: 0 1px 4px rgba(0, 0, 0, 0.2);
        }

        [data-theme="dark"] .seg-btn.active {
            background: #f8fafc;
            color: #090d16;
        }

        [data-theme="light"] .seg-btn.active {
            background: #0f172a;
            color: #ffffff;
        }

        .status-dot {
            width: 7px;
            height: 7px;
            border-radius: 50%;
            display: inline-block;
            flex-shrink: 0;
        }

        .status-dot.active {
            background: #10b981;
            box-shadow: 0 0 6px #10b981;
        }

        .status-dot.historical {
            background: var(--text-muted);
        }

        .status-dot.crimson {
            background: var(--accent-crimson);
            box-shadow: 0 0 5px var(--accent-crimson);
        }

        .roster-badge {
            display: inline-flex;
            align-items: center;
            gap: 4px;
            font-size: 11px;
            font-weight: 600;
            padding: 1px 6px;
            border-radius: var(--radius-pill);
            letter-spacing: 0.02em;
            text-transform: uppercase;
            white-space: nowrap;
            flex-shrink: 0;
        }

        .roster-badge.active {
            background: var(--accent-green-bg);
            color: var(--accent-green);
            border: 1px solid rgba(16, 185, 129, 0.3);
        }

        .roster-badge.historical {
            background: var(--bg-surface-elevated);
            color: var(--text-muted);
            border: 1px solid var(--border-subtle);
        }

        .bar-row {
            display: grid;
            grid-template-columns: minmax(180px, 220px) 1fr minmax(90px, 140px);
            align-items: center;
            gap: var(--space-2);
            font-size: var(--font-size-body);
            padding: 4px 6px;
            border-radius: var(--radius);
            transition: background 0.15s ease;
        }

        .bar-row:hover {
            background: var(--bg-surface-hover);
        }

        @media (max-width: 768px) and (min-width: 641px) {
            .bar-row {
                grid-template-columns: 170px 1fr 100px;
                gap: var(--space-1);
            }
        }

        /* Mobile stacked bar card layout: names never truncated, bars get 100% width! */
        @media (max-width: 640px) {
            .bar-row {
                display: flex;
                flex-wrap: wrap;
                align-items: center;
                justify-content: space-between;
                padding: 8px 10px;
                background: var(--bg-surface-elevated);
                border-radius: var(--radius);
                border: 1px solid var(--border-subtle);
                margin-bottom: 6px;
                gap: 4px 8px;
            }

            .bar-judge-col {
                order: 1;
                flex: 1 1 auto;
                min-width: 0;
            }

            .bar-judge-name {
                font-size: 13px;
                white-space: nowrap;
                overflow: hidden;
                text-overflow: ellipsis;
            }

            .bar-val-col {
                order: 2;
                flex: 0 0 auto;
                flex-direction: row;
                align-items: baseline;
                gap: 6px;
            }

            .bar-val {
                font-size: 13px;
            }

            .bar-delta {
                font-size: 11px;
            }

            .bar-track {
                order: 3;
                width: 100%;
                flex-basis: 100%;
                height: 14px;
                margin-top: 4px;
            }
        }

        .bar-judge-col {
            display: flex;
            align-items: center;
            gap: var(--space-1);
            min-width: 0;
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
            height: 22px;
            background: var(--bg-surface-elevated);
            border-radius: var(--radius);
            overflow: hidden;
            display: flex;
            align-items: center;
            min-width: 40px;
        }

        .bar-fill {
            height: 100%;
            border-radius: var(--radius);
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

        .bar-val-col {
            display: flex;
            flex-direction: column;
            align-items: flex-end;
            font-variant-numeric: tabular-nums;
            font-feature-settings: "tnum" 1;
        }

        .bar-val {
            font-family: var(--font-mono);
            font-size: var(--font-size-body);
            font-weight: 700;
            text-align: right;
            font-variant-numeric: tabular-nums;
            font-feature-settings: "tnum" 1;
        }

        .bar-delta {
            font-size: var(--font-size-caption);
            color: var(--text-muted);
            font-family: var(--font-mono);
            font-variant-numeric: tabular-nums;
        }

        /* Section Layout */
        .content-section {
            margin-top: var(--space-4);
        }

        @media (max-width: 600px) {
            .content-section {
                margin-top: var(--space-3);
            }
        }

        .section-header-block {
            margin-bottom: var(--space-3);
        }

        .section-title {
            font-family: var(--font-display);
            font-size: clamp(17px, 4vw, var(--font-size-header));
            font-weight: 800;
            letter-spacing: -0.02em;
            color: var(--text-primary);
            margin-bottom: var(--space-half);
        }

        .section-desc {
            font-size: clamp(13px, 3.2vw, var(--font-size-body));
            color: var(--text-secondary);
            max-width: 800px;
            line-height: 1.5;
        }

        /* Controls: Filters, Search, Export */
        .table-toolbar {
            display: flex;
            justify-content: space-between;
            align-items: center;
            gap: var(--space-2);
            margin-bottom: var(--space-2);
            flex-wrap: wrap;
        }

        .toolbar-left-cluster {
            display: flex;
            align-items: center;
            gap: var(--space-2);
            flex-wrap: wrap;
            width: 100%;
        }

        @media (min-width: 960px) {
            .toolbar-left-cluster {
                width: auto;
            }
        }

        .filter-pills {
            display: flex;
            align-items: center;
            gap: 6px;
            overflow-x: auto;
            max-width: 100%;
            padding: 2px 0 4px 0;
        }

        .filter-pills::-webkit-scrollbar {
            display: none;
        }

        .pill-btn {
            background: var(--bg-surface);
            border: 1px solid var(--border-subtle);
            color: var(--text-secondary);
            font-size: 13px;
            font-weight: 600;
            padding: 10px 18px;
            min-height: 44px;
            border-radius: var(--radius-pill);
            cursor: pointer;
            transition: all 0.15s ease;
            white-space: nowrap;
            flex-shrink: 0;
            display: inline-flex;
            align-items: center;
            justify-content: center;
            box-sizing: border-box;
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

        #table-roster-segmented {
            width: 100%;
            display: flex;
        }

        @media (min-width: 960px) {
            #table-roster-segmented {
                width: auto;
                display: inline-flex;
            }
        }

        @media (max-width: 960px) {
            #table-roster-segmented .seg-btn {
                flex: 1;
                justify-content: center;
                text-align: center;
                padding: 10px 12px;
                min-height: 44px;
                font-size: 12px;
            }
        }

        .search-export-cluster {
            display: flex;
            align-items: center;
            gap: var(--space-2);
            width: 100%;
        }

        @media (min-width: 960px) {
            .search-export-cluster {
                width: auto;
            }
        }

        .search-wrapper {
            position: relative;
            flex: 1;
        }

        .search-input {
            background: var(--bg-surface);
            border: 1px solid var(--border-subtle);
            border-radius: var(--radius);
            padding: 10px var(--space-2);
            padding-left: 36px;
            font-size: var(--font-size-body);
            color: var(--text-primary);
            outline: none;
            width: 100%;
            min-height: 44px;
            transition: all 0.15s ease;
            box-sizing: border-box;
        }

        @media (min-width: 960px) {
            .search-wrapper {
                flex: none;
            }
            .search-input {
                width: 220px;
            }
            .search-input:focus {
                width: 260px;
            }
        }

        .search-input:focus {
            border-color: var(--accent-crimson);
            box-shadow: 0 0 0 2px var(--accent-crimson-bg);
        }

        .search-icon {
            position: absolute;
            left: 10px;
            top: 50%;
            transform: translateY(-50%);
            color: var(--text-muted);
            pointer-events: none;
        }

        .btn-action {
            display: inline-flex;
            align-items: center;
            gap: var(--space-1);
            background: var(--bg-surface-elevated);
            border: 1px solid var(--border-subtle);
            color: var(--text-primary);
            font-size: 13px;
            font-weight: 600;
            padding: 10px 18px;
            min-height: 44px;
            border-radius: var(--radius);
            cursor: pointer;
            transition: all 0.15s ease;
            white-space: nowrap;
            flex-shrink: 0;
            box-sizing: border-box;
        }

        .btn-action:hover {
            border-color: var(--border-strong);
            background: var(--bg-surface-hover);
        }

        /* Clean, Prioritized Table */
        .table-card {
            background: var(--bg-surface);
            border: 1px solid var(--border-subtle);
            border-radius: var(--radius);
            overflow: hidden;
            box-shadow: var(--shadow-card);
            position: relative;
        }

        .table-scroll-hint {
            display: none;
            align-items: center;
            justify-content: center;
            gap: 8px;
            padding: 6px 12px;
            font-size: 11px;
            font-weight: 700;
            color: var(--accent-blue);
            background: var(--accent-blue-bg);
            border-bottom: 1px solid var(--border-subtle);
            letter-spacing: 0.04em;
            text-transform: uppercase;
        }

        @media (max-width: 1024px) {
            .table-scroll-hint {
                display: flex;
            }
        }

        .table-responsive {
            width: 100%;
            overflow-x: auto;
        }

        table {
            width: 100%;
            border-collapse: separate;
            border-spacing: 0;
            font-size: var(--font-size-body);
        }

        /* Explicit Column Alignment Utilities */
        .col-text, th.col-text, td.col-text {
            text-align: left;
        }

        .col-num, th.col-num, td.col-num {
            text-align: right;
            font-variant-numeric: tabular-nums;
            font-feature-settings: "tnum" 1;
        }

        .col-center, th.col-center, td.col-center {
            text-align: center;
        }

        th {
            background: var(--bg-surface-elevated);
            color: var(--text-muted);
            font-family: var(--font-display);
            font-weight: 700;
            font-size: var(--font-size-caption);
            text-transform: uppercase;
            letter-spacing: 0.06em;
            padding: 12px 14px;
            min-height: 44px;
            border-bottom: 1px solid var(--border-subtle);
            cursor: pointer;
            -webkit-user-select: none;
            user-select: none;
            white-space: nowrap;
            position: sticky;
            top: 0;
            z-index: 10;
        }

        th:hover {
            color: var(--text-primary);
        }

        td {
            padding: 12px 14px;
            min-height: 44px;
            border-bottom: 1px solid var(--border-subtle);
            color: var(--text-secondary);
            vertical-align: middle;
            white-space: nowrap;
        }

        /* Sticky Columns on Horizontal Scroll for Mobile & Tablet */
        @media (max-width: 1024px) {
            thead th:first-child,
            tr.judge-row td:first-child {
                position: sticky;
                left: 0;
                z-index: 11;
                background: var(--bg-surface-elevated);
                width: 38px;
                min-width: 38px;
                max-width: 38px;
                text-align: center;
            }

            tr.judge-row td:first-child {
                background: var(--bg-surface);
            }

            thead th:nth-child(2),
            tr.judge-row td:nth-child(2) {
                position: sticky;
                left: 38px;
                z-index: 11;
                background: var(--bg-surface-elevated);
                min-width: 160px;
                border-right: 2px solid var(--border-strong);
                box-shadow: 4px 0 10px -2px rgba(0, 0, 0, 0.4);
            }

            tr.judge-row td:nth-child(2) {
                background: var(--bg-surface);
            }

            thead th:first-child,
            thead th:nth-child(2) {
                z-index: 15;
            }

            tr.judge-row:hover td:first-child,
            tr.judge-row:hover td:nth-child(2) {
                background: var(--bg-surface-hover);
            }

            tr.judge-row.expanded td:first-child,
            tr.judge-row.expanded td:nth-child(2) {
                background: var(--bg-surface-elevated);
            }

            [data-theme="light"] tr.judge-row td:first-child,
            [data-theme="light"] tr.judge-row td:nth-child(2) {
                background: #ffffff;
            }
            [data-theme="light"] thead th:first-child,
            [data-theme="light"] thead th:nth-child(2) {
                background: #f1f5f9;
            }
            [data-theme="light"] tr.judge-row:hover td:first-child,
            [data-theme="light"] tr.judge-row:hover td:nth-child(2) {
                background: #f8fafc;
            }
            [data-theme="light"] tr.judge-row.expanded td:first-child,
            [data-theme="light"] tr.judge-row.expanded td:nth-child(2) {
                background: #f1f5f9;
            }
            [data-theme="light"] thead th:nth-child(2),
            [data-theme="light"] tr.judge-row td:nth-child(2) {
                box-shadow: 3px 0 8px -2px rgba(15, 23, 42, 0.15);
            }
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
            gap: var(--space-1);
            font-weight: 700;
            color: var(--text-primary);
        }

        .expand-chevron {
            color: var(--text-muted);
            transition: transform 0.2s ease;
            flex-shrink: 0;
        }

        tr.judge-row.expanded .expand-chevron {
            transform: rotate(90deg);
            color: var(--accent-crimson);
        }

        .mono-num {
            font-family: var(--font-mono);
            font-weight: 600;
            font-variant-numeric: tabular-nums;
            font-feature-settings: "tnum" 1;
        }

        /* In-Cell Benchmark Deviation Badge */
        .rate-cell-group {
            display: inline-flex;
            align-items: center;
            gap: var(--space-1);
        }

        .rate-badge {
            font-family: var(--font-mono);
            font-size: var(--font-size-caption);
            font-weight: 700;
            padding: 2px 6px;
            border-radius: var(--radius);
            font-variant-numeric: tabular-nums;
            font-feature-settings: "tnum" 1;
            white-space: nowrap;
        }

        .rate-badge.over {
            background: var(--accent-crimson-bg);
            color: var(--accent-crimson);
        }

        .rate-badge.under {
            background: var(--accent-green-bg);
            color: var(--accent-green);
        }

        .rate-badge.draw {
            background: var(--bg-surface-elevated);
            color: var(--text-muted);
            border: 1px solid var(--border-subtle);
        }

        /* Interactive Dossier Drawer */
        tr.dossier-drawer-row {
            display: none;
            background: var(--bg-surface-elevated);
        }

        tr.dossier-drawer-row.visible {
            display: table-row;
        }

        tr.dossier-drawer-row td {
            position: static !important;
            width: 100% !important;
            min-width: 0 !important;
            max-width: none !important;
            box-shadow: none !important;
            border-right: none !important;
            background: var(--bg-surface-elevated) !important;
            padding: 0 !important;
            white-space: normal !important;
        }

        .dossier-card {
            padding: var(--space-3);
            display: grid;
            grid-template-columns: minmax(300px, 360px) minmax(0, 1fr);
            gap: var(--space-3);
            border-top: 1px solid var(--border-subtle);
            border-bottom: 2px solid var(--border-strong);
            border-left: 3px solid var(--accent-crimson);
            position: sticky;
            left: 0;
            width: 100%;
            max-width: 100%;
            box-sizing: border-box;
            background: var(--bg-surface-elevated);
            z-index: 6;
            white-space: normal !important;
        }

        @media (max-width: 1080px) {
            .dossier-card {
                grid-template-columns: 1fr;
                padding: var(--space-2);
                gap: var(--space-2);
            }
        }

        /* Dossier Left Column: Profile & Metrics */
        .dossier-profile {
            display: flex;
            flex-direction: column;
            gap: var(--space-2);
            border-right: 1px solid var(--border-subtle);
            padding-right: var(--space-3);
            min-width: 0;
            box-sizing: border-box;
        }

        @media (max-width: 1080px) {
            .dossier-profile {
                border-right: none;
                padding-right: 0;
                border-bottom: 1px solid var(--border-subtle);
                padding-bottom: var(--space-2);
            }
        }

        .dossier-profile-header {
            display: flex;
            flex-direction: column;
            gap: 6px;
        }

        .dossier-title-row {
            display: flex;
            align-items: center;
            gap: var(--space-1);
            flex-wrap: wrap;
        }

        .dossier-name {
            font-family: var(--font-display);
            font-size: var(--font-size-header);
            font-weight: 800;
            letter-spacing: -0.02em;
            color: var(--text-primary);
            margin: 0;
            line-height: 1.2;
        }

        .dossier-era-tag {
            display: inline-flex;
            align-items: center;
            gap: 6px;
            font-size: var(--font-size-caption);
            color: var(--text-secondary);
        }

        .dossier-era-tag strong {
            color: var(--text-primary);
            font-variant-numeric: tabular-nums;
        }

        /* Structured 2x2 Metric Tiles */
        .dossier-stats-grid {
            display: grid;
            grid-template-columns: repeat(2, minmax(0, 1fr));
            gap: var(--space-1);
        }

        .dossier-stat-tile {
            background: var(--bg-surface);
            border: 1px solid var(--border-subtle);
            border-radius: var(--radius);
            padding: 10px 12px;
            display: flex;
            flex-direction: column;
            justify-content: space-between;
            min-width: 0;
        }

        .stat-tile-label {
            font-size: 10px;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 0.05em;
            color: var(--text-muted);
            margin-bottom: 4px;
            white-space: normal;
            line-height: 1.25;
            word-break: break-word;
            overflow-wrap: break-word;
        }

        .stat-tile-value {
            font-family: var(--font-mono);
            font-size: 16px;
            font-weight: 800;
            color: var(--text-primary);
            font-variant-numeric: tabular-nums;
            line-height: 1.2;
            margin-bottom: 2px;
        }

        .stat-tile-sub {
            font-size: 11px;
            color: var(--text-secondary);
            line-height: 1.3;
            word-break: break-word;
            overflow-wrap: break-word;
        }

        /* Co-Judge Friction Highlight Box */
        .dossier-friction-box {
            background: var(--bg-surface);
            border: 1px solid var(--border-subtle);
            border-radius: var(--radius);
            padding: 12px;
            display: flex;
            flex-direction: column;
            gap: 4px;
            min-width: 0;
            box-sizing: border-box;
        }

        .friction-box-header {
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 8px;
            flex-wrap: wrap;
        }

        .friction-badge {
            font-size: 10px;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 0.05em;
            color: var(--accent-amber);
        }

        .friction-rate {
            font-family: var(--font-mono);
            font-size: 11px;
            font-weight: 700;
            color: var(--accent-crimson);
            background: var(--accent-crimson-bg);
            padding: 2px 6px;
            border-radius: var(--radius-pill);
            font-variant-numeric: tabular-nums;
            white-space: nowrap;
        }

        .friction-partner-name {
            font-family: var(--font-display);
            font-size: 14px;
            font-weight: 700;
            color: var(--text-primary);
            word-break: break-word;
            overflow-wrap: break-word;
        }

        .friction-subtext {
            font-size: 11px;
            color: var(--text-secondary);
            line-height: 1.4;
            word-break: break-word;
            overflow-wrap: break-word;
        }

        /* Dossier Right Column: Evidence Log */
        .dossier-evidence {
            display: flex;
            flex-direction: column;
            gap: var(--space-2);
            min-width: 0;
            box-sizing: border-box;
        }

        .dossier-evidence-header {
            display: flex;
            flex-direction: column;
            gap: 2px;
        }

        .dossier-evidence-header h5 {
            font-family: var(--font-display);
            font-size: var(--font-size-caption);
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 0.05em;
            color: var(--text-muted);
            margin: 0;
        }

        .evidence-caption {
            font-size: 11px;
            color: var(--text-secondary);
        }

        .dossier-cards-grid {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(230px, 1fr));
            gap: var(--space-2);
            min-width: 0;
        }

        @media (max-width: 580px) {
            .dossier-cards-grid {
                grid-template-columns: 1fr;
                gap: 8px;
            }
        }

        .dissent-card {
            background: var(--bg-surface);
            border: 1px solid var(--border-subtle);
            border-radius: var(--radius);
            padding: 12px 14px;
            display: flex;
            flex-direction: column;
            gap: 8px;
            transition: border-color 0.15s ease, background-color 0.15s ease;
            box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
            min-width: 0;
            overflow: hidden;
            box-sizing: border-box;
        }

        .dissent-card:hover {
            border-color: var(--border-strong);
            background: var(--bg-surface-hover);
        }

        .dissent-card-top {
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 8px;
        }

        .dissent-year-round {
            font-family: var(--font-mono);
            font-size: 11px;
            font-weight: 600;
            color: var(--text-muted);
            font-variant-numeric: tabular-nums;
        }

        .dissent-bout-name {
            font-family: var(--font-display);
            font-size: 13px;
            font-weight: 700;
            color: var(--text-primary);
            line-height: 1.3;
            word-break: break-word;
            overflow-wrap: break-word;
        }

        .dissent-scores-row {
            display: flex;
            flex-direction: column;
            gap: 6px;
            padding-top: 8px;
            border-top: 1px solid var(--border-subtle);
        }

        .dissent-judge-score {
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 8px;
        }

        .score-label {
            font-size: 11px;
            color: var(--text-muted);
            font-weight: 600;
        }

        .score-badge-crimson {
            font-family: var(--font-mono);
            font-size: 12px;
            font-weight: 800;
            color: var(--accent-crimson);
            background: var(--accent-crimson-bg);
            padding: 2px 8px;
            border-radius: var(--radius-pill);
            font-variant-numeric: tabular-nums;
            border: 1px solid var(--border-highlight);
        }

        .dissent-consensus-info {
            display: flex;
            flex-direction: column;
            gap: 2px;
            font-size: 11px;
            line-height: 1.4;
        }

        .consensus-label {
            color: var(--text-muted);
            font-weight: 600;
            font-size: 10px;
            text-transform: uppercase;
            letter-spacing: 0.04em;
        }

        .consensus-names {
            color: var(--text-secondary);
            word-break: break-word;
            overflow-wrap: break-word;
        }

        .dossier-expand-btn {
            background: var(--bg-surface-elevated);
            border: 1px solid var(--border-subtle);
            color: var(--text-secondary);
            font-size: 11px;
            font-weight: 700;
            padding: 4px 10px;
            border-radius: var(--radius-pill);
            cursor: pointer;
            transition: all 0.15s ease;
            white-space: nowrap;
            display: inline-flex;
            align-items: center;
            justify-content: center;
            letter-spacing: 0.02em;
        }

        .dossier-expand-btn:hover {
            border-color: var(--accent-crimson);
            color: var(--text-primary);
            background: var(--bg-surface-hover);
        }

        .dossier-expand-btn.active {
            background: var(--accent-crimson-bg);
            color: var(--accent-crimson);
            border-color: var(--border-highlight);
        }

        /* Visualizations Section */
        .chart-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(min(100%, 340px), 1fr));
            gap: var(--space-3);
            margin-top: var(--space-3);
        }

        @media (max-width: 600px) {
            .chart-grid {
                grid-template-columns: 1fr;
                gap: var(--space-2);
            }
        }

        .chart-card {
            background: var(--bg-surface);
            border: 1px solid var(--border-subtle);
            border-radius: var(--radius);
            padding: var(--space-3);
            box-shadow: var(--shadow-card);
        }

        @media (max-width: 600px) {
            .chart-card {
                padding: 14px 12px;
            }
        }

        .chart-card h4 {
            font-family: var(--font-display);
            font-size: clamp(15px, 3.5vw, var(--font-size-header));
            font-weight: 700;
            color: var(--text-primary);
            margin-bottom: var(--space-half);
        }

        .chart-card p {
            font-size: var(--font-size-caption);
            color: var(--text-secondary);
            margin-bottom: var(--space-2);
        }

        .chart-card.fight-chart {
            display: none;
        }

        .callout-card {
            margin-top: var(--space-2);
            margin-bottom: var(--space-2);
            padding: var(--space-2);
            background: var(--bg-surface-elevated);
            border-left: 3px solid var(--accent-blue);
            border-radius: var(--radius);
            font-size: var(--font-size-body);
            line-height: 1.5;
        }

        #theme-icon-sun {
            display: none;
        }

        .chart-img-wrap {
            width: 100%;
            border-radius: var(--radius);
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
            border-radius: var(--radius);
            padding: var(--space-3);
            margin-top: var(--space-2);
        }

        @media (max-width: 600px) {
            .anatomy-bar-container {
                padding: 14px 12px;
            }
        }

        .anatomy-bar {
            height: 28px;
            display: flex;
            border-radius: var(--radius);
            overflow: hidden;
            margin: var(--space-2) 0;
        }

        .seg-10-9 { background: #38bdf8; width: 95.76%; }
        .seg-10-8 { background: var(--accent-amber); width: 3.73%; }
        .seg-draw { background: var(--accent-green); width: 0.48%; }
        .seg-10-7 { background: var(--accent-crimson); width: 0.03%; min-width: 4px; }

        .anatomy-legend {
            display: flex;
            gap: var(--space-3);
            flex-wrap: wrap;
            font-size: var(--font-size-caption);
        }

        @media (max-width: 600px) {
            .anatomy-legend {
                display: grid;
                grid-template-columns: 1fr 1fr;
                gap: 8px;
            }
            .anatomy-item {
                background: var(--bg-surface-elevated);
                padding: 5px 8px;
                border-radius: var(--radius);
                border: 1px solid var(--border-subtle);
                font-size: 11px;
            }
        }

        .anatomy-item {
            display: flex;
            align-items: center;
            gap: var(--space-1);
        }

        .dot-10-9 { background: #38bdf8; }
        .dot-10-8 { background: var(--accent-amber); }
        .dot-draw { background: var(--accent-green); }
        .dot-10-7 { background: var(--accent-crimson); }

        /* Footer */
        .site-footer {
            margin-top: var(--space-4);
            padding-top: var(--space-3);
            border-top: 1px solid var(--border-subtle);
            display: flex;
            justify-content: space-between;
            align-items: center;
            font-size: var(--font-size-caption);
            color: var(--text-muted);
            flex-wrap: wrap;
            gap: var(--space-2);
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
                <p>UFC Judging & Round-by-Round Scoring Analytics (1995–2026)</p>
            </div>
        </div>
        <div class="nav-controls">
            <div class="mode-toggle-group">
                <button class="mode-btn active" id="btn-mode-rounds"><span class="label-full">Round Scoring Disagreements</span><span class="label-short" aria-hidden="true">Round Scoring</span></button>
                <button class="mode-btn" id="btn-mode-fights"><span class="label-full">Fight Decision Splits</span><span class="label-short" aria-hidden="true">Fight Splits</span></button>
                <button class="mode-btn" id="btn-mode-fighters"><span class="label-full">Fighter Controversy Index</span><span class="label-short" aria-hidden="true">Fighter Index</span></button>
            </div>
            <button class="theme-btn" id="theme-toggle" title="Toggle Light / Dark mode" aria-label="Toggle theme">
                <svg id="theme-icon-sun" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="5"></circle><line x1="12" y1="1" x2="12" y2="3"></line><line x1="12" y1="21" x2="12" y2="23"></line><line x1="4.22" y1="4.22" x2="5.64" y2="5.64"></line><line x1="18.36" y1="18.36" x2="19.78" y2="19.78"></line><line x1="1" y1="12" x2="3" y2="12"></line><line x1="21" y1="12" x2="23" y2="12"></line><line x1="4.22" y1="19.78" x2="5.64" y2="18.36"></line><line x1="18.36" y1="5.64" x2="19.78" y2="4.22"></line></svg>
                <svg id="theme-icon-moon" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"></path></svg>
            </button>
        </div>
    </header>

    <!-- Chapter 1: The Core Question & Macro Benchmark -->
    <section class="hero-lead-card">
        <div class="chapter-badge">Chapter 1 · The Core Discovery</div>
        <h2 class="hero-headline" id="hero-question">When two cage-side judges agree on a round, which third judge breaks away most often?</h2>
        <p class="hero-subhead" id="hero-narrative">
            Across 32,876 individual rounds evaluated by 3-judge panels (including completed rounds from fights ending inside the distance), exactly <strong>2,376 rounds (7.23%)</strong> produced a lone dissenting judge.
            Among high-volume UFC mainstays (250+ rounds), <strong>Cardo Urso</strong> ranks #1 with a <strong>9.01%</strong> round dissent rate, followed by <strong>Rick Winter</strong> (8.75%) and <strong>David Lethaby</strong> (8.62%).
        </p>

        <!-- Focused 4 KPI Cards (Unique, non-redundant metrics) -->
        <div class="kpi-grid">
            <div class="kpi-card">
                <div class="kpi-label">Historical UFC Benchmark</div>
                <div class="kpi-value-row">
                    <span class="kpi-value" id="kpi-benchmark-val">7.23%</span>
                </div>
                <div class="kpi-context" id="kpi-benchmark-sub">Average dissent rate across all 32,876 rounds (1 in every 13.8 rounds)</div>
            </div>

            <div class="kpi-card">
                <div class="kpi-label">#1 Veteran Mainstay (250+ Rds)</div>
                <div class="kpi-value-row">
                    <span class="kpi-value" id="kpi-leader-val">9.01%</span>
                    <span class="kpi-delta high" id="kpi-leader-delta">+1.78% vs avg</span>
                </div>
                <div class="kpi-context" id="kpi-leader-sub"><strong>Cardo Urso</strong> · 29 dissents in 322 rounds (1 in every 11.1 rounds)</div>
            </div>

            <div class="kpi-card">
                <div class="kpi-label">Most Consensual Mainstay</div>
                <div class="kpi-value-row">
                    <span class="kpi-value" id="kpi-agreeable-val">6.87%</span>
                    <span class="kpi-delta consensual" id="kpi-agreeable-delta">-0.36% vs avg</span>
                </div>
                <div class="kpi-context" id="kpi-agreeable-sub"><strong>Ben Cartlidge</strong> · 58 dissents in 844 rounds (highest agreement rate)</div>
            </div>

            <div class="kpi-card">
                <div class="kpi-label">Highest Absolute Dissents</div>
                <div class="kpi-value-row">
                    <span class="kpi-value" id="kpi-volume-val">223</span>
                </div>
                <div class="kpi-context" id="kpi-volume-sub"><strong>Sal D'Amato</strong> · 6.24% rate over 3,573 scored rounds (historic volume)</div>
            </div>
        </div>

        <!-- High-density Benchmark Deviation Bar Chart (Zero wasted space) -->
        <div class="gauge-section" id="benchmark-gauge-section">
            <div class="gauge-header">
                <div>
                    <div class="gauge-title" id="gauge-heading">Veteran Mainstays vs 7.23% Historical UFC Average</div>
                    <div class="gauge-subtitle" id="gauge-subheading">
                        Top 10 judges with 250+ rounds scored · All Eras
                    </div>
                </div>
                <div class="gauge-controls-cluster">
                    <!-- View Toggle: Top Dissenters vs Most Consensual -->
                    <div class="segmented-group" id="gauge-view-toggle">
                        <button class="seg-btn active" id="btn-gauge-dissenters" data-view="dissenters">
                            <span class="status-dot crimson"></span> <span class="label-full">Top Dissenters (Disagreers)</span><span class="label-short" aria-hidden="true">Dissenters</span>
                        </button>
                        <button class="seg-btn" id="btn-gauge-agreers" data-view="agreers">
                            <span class="status-dot active"></span> <span class="label-full">Most Consensual (Agreers)</span><span class="label-short" aria-hidden="true">Consensual</span>
                        </button>
                    </div>
                    <!-- Roster Status Toggle: All Eras vs Currently Active -->
                    <div class="segmented-group" id="gauge-roster-toggle">
                        <button class="seg-btn active" id="btn-gauge-all" data-roster="all">All Eras</button>
                        <button class="seg-btn" id="btn-gauge-active" data-roster="active"><span class="status-dot active"></span> Active Only</button>
                    </div>
                </div>
            </div>
            <div class="gauge-legend" id="gauge-legend-container">
                <span><span class="legend-dot crimson"></span> Higher Dissent Rate (Above Benchmark)</span>
                <span><span class="legend-dot green"></span> Lower Dissent Rate (More Consensual)</span>
                <span><span class="legend-dot benchmark"></span> 7.23% UFC Average</span>
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
            <div class="toolbar-left-cluster">
                <div class="filter-pills" id="filter-pills-container">
                    <!-- Filter buttons injected dynamically -->
                </div>
                <div class="segmented-group" id="table-roster-segmented" title="Filter by judge activity status">
                    <button class="seg-btn active" id="btn-roster-all" data-roster="all"><span class="label-full">All Eras (1995–2026)</span><span class="label-short" aria-hidden="true">All Eras</span></button>
                    <button class="seg-btn" id="btn-roster-active" data-roster="active"><span class="status-dot active"></span> <span class="label-full">Currently Active</span><span class="label-short" aria-hidden="true">Active</span></button>
                    <button class="seg-btn" id="btn-roster-historical" data-roster="historical"><span class="status-dot historical"></span> <span class="label-full">Historical (&lt; 2024)</span><span class="label-short" aria-hidden="true">Historical</span></button>
                </div>
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
            <div class="table-scroll-hint">
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="15 18 9 12 15 6"></polyline></svg>
                <span>Swipe table horizontally to see all metrics</span>
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="9 18 15 12 9 6"></polyline></svg>
            </div>
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
    <section class="content-section" id="pairs-section">
        <div class="section-header-block">
            <div class="chapter-badge">Chapter 3 · Panel Friction</div>
            <h3 class="section-title">Co-Judge Head-to-Head Clash Matrix</h3>
            <p class="section-desc">How often do pairs of judges seated on the exact same bout disagree on who won individual rounds? Analyzed across co-judges with at least 15 rounds together.</p>
        </div>

        <div class="table-card">
            <div class="table-scroll-hint">
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="15 18 9 12 15 6"></polyline></svg>
                <span>Swipe table horizontally to see all metrics</span>
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="9 18 15 12 9 6"></polyline></svg>
            </div>
            <div class="table-responsive">
                <table>
                    <thead>
                        <tr>
                            <th class="col-text">Judge Pair</th>
                            <th class="col-num">Rounds Together</th>
                            <th class="col-num">Conflicting Round Scores</th>
                            <th class="col-num">Disagreement Rate (%)</th>
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
            <p class="section-desc">How often does a round score deviate from the standard 10-9? Out of 32,876 total scored rounds (32,588 decision rounds + 288 rounds from 48 stoppage bouts where scorecards exist):</p>
        </div>

        <div class="anatomy-bar-container">
            <div class="anatomy-bar">
                <div class="seg-10-9" title="10-9 (95.76%)"></div>
                <div class="seg-10-8" title="10-8 (3.73%)"></div>
                <div class="seg-draw" title="10-10 Draw (0.48%)"></div>
                <div class="seg-10-7" title="10-7 (0.03%)"></div>
            </div>
            <div class="anatomy-legend">
                <div class="anatomy-item"><span class="legend-dot dot-10-9"></span> <strong>10-9 Rounds</strong>: 31,482 (95.76%)</div>
                <div class="anatomy-item"><span class="legend-dot dot-10-8"></span> <strong>10-8 Dominant Rounds</strong>: 1,227 (3.73%)</div>
                <div class="anatomy-item"><span class="legend-dot dot-draw"></span> <strong>10-10 Even Rounds</strong>: 157 (0.48%)</div>
                <div class="anatomy-item"><span class="legend-dot dot-10-7"></span> <strong>10-7 Blowout Rounds</strong>: 10 (0.03%)</div>
            </div>
        </div>

        <div class="callout-card">
            <strong>Scoring Methodology & Comprehensive Scope:</strong> When evaluating how judges score rounds, this analysis includes <em>every fight where official scorecards exist</em>, not just bouts that reached a final decision. If a fight concluded via KO, TKO, or submission in Round 4 (e.g. Miocic vs. Cormier 2 or Du Plessis vs. Adesanya), the official scores for Rounds 1, 2, and 3 are preserved and analyzed. Similarly, for 5-round title bouts ending in Round 5 (such as Usman vs. Covington 1 or Adesanya vs. Pereira 1), all completed prior rounds (1 through 4) are incorporated.
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
            <div class="chart-card fight-chart">
                <h4>Decision Split Rates (Min 50 Fights)</h4>
                <p>Full 15-minute fight decision disagreement rate across judges.</p>
                <div class="chart-img-wrap"><img src="__IMG_MIN50__" alt="Fight Decision Dissent Rate Min 50"></div>
            </div>
            <div class="chart-card fight-chart">
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
            Empirical research into 32,876 UFC rounds across 4,010 decisions and 48 stoppage bouts (1995–2026). Data sourced from MMADecisions.com.
        </div>
    </footer>
</div>

<script>
    const ROUND_JUDGES = __ROUND_JUDGES_JSON__;
    const FIGHT_JUDGES = __FIGHT_JUDGES_JSON__;
    const FIGHTERS = __FIGHTERS_JSON__;
    const FIGHTER_KPIS = __FIGHTER_KPIS_JSON__;
    const ROUND_PAIRS = __ROUND_PAIRS_JSON__;
    const FIGHT_PAIRS = __FIGHT_PAIRS_JSON__;
    const SUMMARY = __SUMMARY_JSON__;
    const ROUND_SUMMARY = __ROUND_SUMMARY_JSON__;

    const UFC_BASELINE_PCT = (typeof ROUND_SUMMARY !== 'undefined' && ROUND_SUMMARY.round_dissent_pct) ? ROUND_SUMMARY.round_dissent_pct : 7.23;
    const UFC_SPLIT_BASELINE_PCT = 20.05;

    let currentMode = 'rounds'; // 'rounds', 'fights', or 'fighters'
    let currentFilterMin = 250;
    let currentRosterFilter = 'all'; // 'all', 'active', or 'historical'
    let currentGaugeView = 'dissenters'; // 'dissenters' or 'agreers'
    let searchQuery = '';
    let sortColumn = 'rate';
    let sortAsc = false;
    let expandedJudge = null;

    // DOM References
    const btnModeRounds = document.getElementById('btn-mode-rounds');
    const btnModeFights = document.getElementById('btn-mode-fights');
    const btnModeFighters = document.getElementById('btn-mode-fighters');
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

    // Helper: Determine if judge is currently active (judged UFC fights in 2024–2026)
    function isJudgeActive(j) {
        const lastYear = Number(j.last_year);
        return !isNaN(lastYear) && lastYear >= 2024;
    }

    // Helper: Determine if fighter is currently active (fought in UFC in 2024–2026)
    function isFighterActive(f) {
        const lastYear = Number(f.last_year);
        return !isNaN(lastYear) && lastYear >= 2024;
    }

    // Dynamic Chapter 1 Hero & KPI updater
    function updateChapter1HeroAndKpis() {
        if (currentMode === 'rounds') {
            document.getElementById('hero-question').textContent = "When two cage-side judges agree on a round, which third judge breaks away most often?";

            if (currentRosterFilter === 'active') {
                document.getElementById('hero-narrative').innerHTML = "Across 32,876 individual rounds evaluated by 3-judge panels (including completed rounds from stoppage bouts), exactly <strong>2,376 rounds (7.23%)</strong> produced a lone dissenting judge. Among currently active UFC mainstays (250+ rounds, 2024–2026), <strong>Rick Winter</strong> holds the #1 disagreement rate at <strong>8.75%</strong>, followed by <strong>David Lethaby</strong> (8.62%) and <strong>Dave Tirelli</strong> (8.54%). Meanwhile, <strong>Clemens Werner</strong> is the most consensual active judge at <strong>4.99%</strong> dissent (95.01% colleague agreement rate).";

                document.getElementById('kpi-benchmark-val').textContent = "7.23%";
                document.getElementById('kpi-benchmark-sub').textContent = "Average dissent rate across all 32,876 rounds (1 in every 13.8 rounds)";

                document.getElementById('kpi-leader-val').textContent = "8.75%";
                document.getElementById('kpi-leader-delta').textContent = "+1.52% vs avg";
                document.getElementById('kpi-leader-sub').innerHTML = "<strong>Rick Winter</strong> · 30 dissents in 343 rounds (#1 active dissenter)";

                document.getElementById('kpi-agreeable-val').textContent = "4.99%";
                document.getElementById('kpi-agreeable-delta').textContent = "-2.24% vs avg";
                document.getElementById('kpi-agreeable-sub').innerHTML = "<strong>Clemens Werner</strong> · 95.01% agreement in 481 rounds (most consensual active)";

                document.getElementById('kpi-volume-val').textContent = "223";
                document.getElementById('kpi-volume-sub').innerHTML = "<strong>Sal D'Amato</strong> · 6.24% rate over 3,573 scored rounds (active through 2026)";
            } else if (currentRosterFilter === 'historical') {
                document.getElementById('hero-narrative').innerHTML = "Among historical UFC mainstays who have stepped away from the cage (&lt; 2024), <strong>Cardo Urso</strong> (last judged 2019) leads all-time round dissents at <strong>9.01%</strong>, followed by <strong>Glenn Trowbridge</strong> (last judged 2020) at <strong>8.37%</strong> and <strong>Marcos Rosales</strong> (last judged 2021) at <strong>7.97%</strong>.";

                document.getElementById('kpi-benchmark-val').textContent = "7.23%";
                document.getElementById('kpi-benchmark-sub').textContent = "Average dissent rate across all 32,876 rounds";

                document.getElementById('kpi-leader-val').textContent = "9.01%";
                document.getElementById('kpi-leader-delta').textContent = "+1.78% vs avg";
                document.getElementById('kpi-leader-sub').innerHTML = "<strong>Cardo Urso</strong> · 29 dissents in 322 rounds (last judged 2019)";

                document.getElementById('kpi-agreeable-val').textContent = "5.36%";
                document.getElementById('kpi-agreeable-delta').textContent = "-1.87% vs avg";
                document.getElementById('kpi-agreeable-sub').innerHTML = "<strong>Jeff Mullen</strong> · 94.64% agreement in 280 rounds (last judged 2017)";

                document.getElementById('kpi-volume-val').textContent = "41";
                document.getElementById('kpi-volume-sub').innerHTML = "<strong>Glenn Trowbridge</strong> · 490 rounds (historical mainstay)";
            } else {
                document.getElementById('hero-narrative').innerHTML = "Across 32,876 individual rounds evaluated by 3-judge panels (including completed rounds from stoppage bouts), exactly <strong>2,376 rounds (7.23%)</strong> produced a lone dissenting judge. Among high-volume UFC mainstays (250+ rounds), <strong>Cardo Urso</strong> ranks #1 with a <strong>9.01%</strong> round dissent rate, followed by <strong>Rick Winter</strong> (8.75%) and <strong>David Lethaby</strong> (8.62%).";

                document.getElementById('kpi-benchmark-val').textContent = "7.23%";
                document.getElementById('kpi-benchmark-sub').textContent = "Average dissent rate across all 32,876 rounds (1 in every 13.8 rounds)";

                document.getElementById('kpi-leader-val').textContent = "9.01%";
                document.getElementById('kpi-leader-delta').textContent = "+1.78% vs avg";
                document.getElementById('kpi-leader-sub').innerHTML = "<strong>Cardo Urso</strong> · 29 dissents in 322 rounds (1 in every 11.1 rounds)";

                document.getElementById('kpi-agreeable-val').textContent = "4.99%";
                document.getElementById('kpi-agreeable-delta').textContent = "-2.24% vs avg";
                document.getElementById('kpi-agreeable-sub').innerHTML = "<strong>Clemens Werner</strong> · 95.01% agreement in 481 rounds (most consensual)";

                document.getElementById('kpi-volume-val').textContent = "223";
                document.getElementById('kpi-volume-sub').innerHTML = "<strong>Sal D'Amato</strong> · 6.24% rate over 3,573 scored rounds (historic volume)";
            }
        } else if (currentMode === 'fights') {
            document.getElementById('hero-question').textContent = "Which UFC judge dissents most often on the final fight decision outcome?";

            if (currentRosterFilter === 'active') {
                document.getElementById('hero-narrative').innerHTML = "When evaluating the final 15-minute fight decision across active UFC judges (50+ bouts, 2024–2026), <strong>Adalaide Byrd</strong> ranks #1 in split dissent rate at <strong>9.29%</strong> among veterans, while <strong>Ben Cartlidge</strong> holds the highest colleague consensus at <strong>4.85%</strong> dissent.";

                document.getElementById('kpi-benchmark-val').textContent = "20.0%";
                document.getElementById('kpi-benchmark-sub').textContent = "Split decision rate across 4,010 UFC fights (804 split decisions)";

                document.getElementById('kpi-leader-val').textContent = "9.29%";
                document.getElementById('kpi-leader-delta').textContent = "+4.4% vs avg";
                document.getElementById('kpi-leader-sub').innerHTML = "<strong>Adalaide Byrd</strong> · 26 split dissents in 280 fights (active 2026)";

                document.getElementById('kpi-agreeable-val').textContent = "4.85%";
                document.getElementById('kpi-agreeable-delta').textContent = "-4.5% vs avg";
                document.getElementById('kpi-agreeable-sub').innerHTML = "<strong>Ben Cartlidge</strong> · 13 dissents in 268 fights (most consensual active)";

                document.getElementById('kpi-volume-val').textContent = "75";
                document.getElementById('kpi-volume-sub').innerHTML = "<strong>Sal D'Amato</strong> · 1,151 fights judged (most active in UFC history)";
            } else if (currentRosterFilter === 'historical') {
                document.getElementById('hero-narrative').innerHTML = "Among historical judges no longer active in the UFC (&lt; 2024), <strong>Barry Foley</strong> holds the #1 fight decision disagreement rate at <strong>22.64%</strong> (12 dissents in 53 fights).";

                document.getElementById('kpi-benchmark-val').textContent = "20.0%";
                document.getElementById('kpi-benchmark-sub').textContent = "Split decision rate across 4,010 UFC fights";

                document.getElementById('kpi-leader-val').textContent = "22.64%";
                document.getElementById('kpi-leader-delta').textContent = "+13.3% vs avg";
                document.getElementById('kpi-leader-sub').innerHTML = "<strong>Barry Foley</strong> · 12 dissents in 53 fights (last judged 2013)";

                document.getElementById('kpi-agreeable-val').textContent = "5.04%";
                document.getElementById('kpi-agreeable-delta').textContent = "-4.3% vs avg";
                document.getElementById('kpi-agreeable-sub').innerHTML = "<strong>Jeff Mullen</strong> · 6 dissents in 119 fights (last judged 2017)";

                document.getElementById('kpi-volume-val').textContent = "36";
                document.getElementById('kpi-volume-sub').innerHTML = "<strong>Glenn Trowbridge</strong> · 150 fights judged (last judged 2020)";
            } else {
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
            }
        } else {
            // Fighter Controversy & Disagreement Index Mode
            document.getElementById('hero-question').textContent = "Which UFC fighters are subject to the most judging disagreements and controversial split decisions?";

            if (currentRosterFilter === 'active') {
                document.getElementById('hero-narrative').innerHTML = "Among currently active UFC fighters (2024–2026), <strong>Sean Strickland</strong> and <strong>Andre Fili</strong> have been involved in <strong>7 split decisions</strong> each, winning 5 of them (5W-2L record, +3 net luck). <strong>Sean Woodson</strong> holds a <strong>57.14% split decision rate</strong> (4 of 7 decisions, 3W-0L), while <strong>Angela Hill</strong> has suffered the most split decision losses among active fighters with <strong>4 split losses</strong> (1W-4L, net -3). <strong>Alexander Hernandez</strong> leads active fighters in contested rounds with <strong>40.74%</strong> of his scored rounds dissented.";

                document.getElementById('kpi-benchmark-val').textContent = "20.05%";
                document.getElementById('kpi-benchmark-sub').textContent = "Overall UFC Split Decision Rate (804 of 4,010 decisions)";

                document.getElementById('kpi-leader-val').textContent = "57.14%";
                document.getElementById('kpi-leader-delta').textContent = "+37.1% vs avg";
                document.getElementById('kpi-leader-sub').innerHTML = "<strong>Sean Woodson</strong> · 4 splits in 7 decisions (3W-0L, undefeated in splits)";

                document.getElementById('kpi-agreeable-val').textContent = "1W - 4L";
                document.getElementById('kpi-agreeable-delta').textContent = "-3 Net Luck";
                document.getElementById('kpi-agreeable-sub').innerHTML = "<strong>Angela Hill</strong> · 4 split losses in 25 decisions (#1 active split losses)";

                document.getElementById('kpi-volume-val').textContent = "5W - 2L";
                document.getElementById('kpi-volume-sub').innerHTML = "<strong>Sean Strickland</strong> · 5 split wins in 17 decisions (tied with Andre Fili)";
            } else if (currentRosterFilter === 'historical') {
                document.getElementById('hero-narrative').innerHTML = "Among historical UFC fighters (&lt; 2024), <strong>Zubaira Tukhugov</strong> recorded an astounding <strong>83.33% split decision rate</strong> (5 of 6 decisions ended in splits). <strong>Jorge Masvidal</strong> and <strong>Andrea Lee</strong> share the all-time UFC record for the most unlucky split decision record at <strong>0W-4L (net -4 luck)</strong>. <strong>Paul Felder</strong> holds the all-time record for contested rounds: <strong>48.39%</strong> of his scored rounds (15 of 31) had a judge dissent, and 6 of his 9 decisions were splits (66.67%).";

                document.getElementById('kpi-benchmark-val').textContent = "20.05%";
                document.getElementById('kpi-benchmark-sub').textContent = "Overall UFC Split Decision Rate across all eras";

                document.getElementById('kpi-leader-val').textContent = "83.33%";
                document.getElementById('kpi-leader-delta').textContent = "+63.3% vs avg";
                document.getElementById('kpi-leader-sub').innerHTML = "<strong>Zubaira Tukhugov</strong> · 5 splits in 6 bouts (#1 all-time split rate)";

                document.getElementById('kpi-agreeable-val').textContent = "0W - 4L";
                document.getElementById('kpi-agreeable-delta').textContent = "-4 Net Luck";
                document.getElementById('kpi-agreeable-sub').innerHTML = "<strong>Jorge Masvidal</strong> · 4 split losses, 0 wins (tied with Andrea Lee)";

                document.getElementById('kpi-volume-val').textContent = "48.39%";
                document.getElementById('kpi-volume-sub').innerHTML = "<strong>Paul Felder</strong> · 15 of 31 rounds contested (6 of 9 fights splits)";
            } else {
                document.getElementById('hero-narrative').innerHTML = "Across 4,010 UFC bouts ending in a decision, exactly <strong>804 bouts (20.05%)</strong> resulted in a split decision. <strong>Clay Guida</strong> holds the all-time record for career split decisions with <strong>8 splits</strong> (4W-4L). <strong>Zubaira Tukhugov</strong> holds the highest career split rate at <strong>83.33%</strong> (5 of 6). <strong>Jorge Masvidal</strong> and <strong>Andrea Lee</strong> are the most unlucky fighters in UFC history with <strong>4 split losses and 0 split wins (0W-4L, net -4)</strong>, while <strong>Neil Magny</strong> and <strong>Benson Henderson</strong> are undefeated in splits at <strong>4W-0L (+4)</strong>, and <strong>Sean Strickland</strong> has the most split wins at <strong>5W-2L (+3)</strong>.";

                document.getElementById('kpi-benchmark-val').textContent = "20.05%";
                document.getElementById('kpi-benchmark-sub').textContent = "804 split decisions across 4,010 UFC bouts (1 in every 5 decisions)";

                document.getElementById('kpi-leader-val').textContent = "83.33%";
                document.getElementById('kpi-leader-delta').textContent = "+63.3% vs avg";
                document.getElementById('kpi-leader-sub').innerHTML = "<strong>Zubaira Tukhugov</strong> · 5 split decisions in 6 bouts (1W-3L-1D)";

                document.getElementById('kpi-agreeable-val').textContent = "0W - 4L";
                document.getElementById('kpi-agreeable-delta').textContent = "-4 Net Luck";
                document.getElementById('kpi-agreeable-sub').innerHTML = "<strong>Jorge Masvidal</strong> · 4 split losses, 0 wins (tied with Andrea Lee)";

                document.getElementById('kpi-volume-val').textContent = "8 Splits";
                document.getElementById('kpi-volume-sub').innerHTML = "<strong>Clay Guida</strong> · 8 split decisions in 18 bouts (4W-4L record)";
            }
        }
    }

    // Mode Switcher (Rounds vs Fights vs Fighters)
    function setMode(mode) {
        currentMode = mode;
        expandedJudge = null;
        if (mode === 'rounds') {
            btnModeRounds.classList.add('active');
            btnModeFights.classList.remove('active');
            btnModeFighters.classList.remove('active');
            currentFilterMin = 250;
            sortColumn = 'rate';
            sortAsc = false;

            document.getElementById('benchmark-gauge-section').style.display = 'block';
            document.getElementById('pairs-section').style.display = 'block';
            document.getElementById('anatomy-section').style.display = 'block';
            document.getElementById('table-section-title').textContent = "The Hall of Dissent: Judge Rankings";
            document.getElementById('search-input').placeholder = "Search judge name...";
            const btnD = document.getElementById('btn-gauge-dissenters');
            const btnA = document.getElementById('btn-gauge-agreers');
            if (btnD) btnD.innerHTML = `<span class="status-dot crimson"></span> <span class="label-full">Top Dissenters (Disagreers)</span><span class="label-short" aria-hidden="true">Dissenters</span>`;
            if (btnA) btnA.innerHTML = `<span class="status-dot active"></span> <span class="label-full">Most Consensual (Agreers)</span><span class="label-short" aria-hidden="true">Consensual</span>`;
            document.querySelectorAll('.round-chart').forEach(c => c.style.display = 'block');
            document.querySelectorAll('.fight-chart').forEach(c => c.style.display = 'none');
        } else if (mode === 'fights') {
            btnModeRounds.classList.remove('active');
            btnModeFights.classList.add('active');
            btnModeFighters.classList.remove('active');
            currentFilterMin = 100;
            sortColumn = 'rate';
            sortAsc = false;

            document.getElementById('benchmark-gauge-section').style.display = 'none';
            document.getElementById('pairs-section').style.display = 'block';
            document.getElementById('anatomy-section').style.display = 'none';
            document.getElementById('table-section-title').textContent = "Fight Decision Dissent: Judge Rankings";
            document.getElementById('search-input').placeholder = "Search judge name...";
            document.querySelectorAll('.round-chart').forEach(c => c.style.display = 'none');
            document.querySelectorAll('.fight-chart').forEach(c => c.style.display = 'block');
        } else {
            btnModeRounds.classList.remove('active');
            btnModeFights.classList.remove('active');
            btnModeFighters.classList.add('active');
            currentFilterMin = 5;
            sortColumn = 'split_pct';
            sortAsc = false;

            document.getElementById('benchmark-gauge-section').style.display = 'block';
            document.getElementById('pairs-section').style.display = 'none';
            document.getElementById('anatomy-section').style.display = 'none';
            document.getElementById('table-section-title').textContent = "The Fighter Controversy Index: Most Contested Fighters";
            document.getElementById('search-input').placeholder = "Search fighter name...";
            const btnD = document.getElementById('btn-gauge-dissenters');
            const btnA = document.getElementById('btn-gauge-agreers');
            if (btnD) btnD.innerHTML = `<span class="status-dot crimson"></span> <span class="label-full">Highest Split % (Close Bouts)</span><span class="label-short" aria-hidden="true">Highest Split %</span>`;
            if (btnA) btnA.innerHTML = `<span class="status-dot active"></span> <span class="label-full">Luck Index (Unlucky vs Fortunate)</span><span class="label-short" aria-hidden="true">Luck Index</span>`;
            document.querySelectorAll('.round-chart').forEach(c => c.style.display = 'none');
            document.querySelectorAll('.fight-chart').forEach(c => c.style.display = 'none');
        }

        updateChapter1HeroAndKpis();
        renderFilterPills();
        renderTableHeaders();
        renderTable();
        renderDeviationBars();
        renderPairsTable();
    }

    // Roster Filter Switcher (All vs Active vs Historical)
    function setRosterFilter(filter) {
        currentRosterFilter = filter;

        // Sync Gauge roster toggle buttons
        const btnGaugeAll = document.getElementById('btn-gauge-all');
        const btnGaugeActive = document.getElementById('btn-gauge-active');
        if (btnGaugeAll) btnGaugeAll.classList.toggle('active', filter === 'all');
        if (btnGaugeActive) btnGaugeActive.classList.toggle('active', filter === 'active');

        // Sync Table roster toggle buttons
        document.querySelectorAll('#table-roster-segmented .seg-btn').forEach(btn => {
            btn.classList.toggle('active', btn.dataset.roster === filter);
        });

        updateChapter1HeroAndKpis();
        renderDeviationBars();
        renderTable();
    }

    // Gauge View Switcher (Dissenters vs Agreers)
    function setGaugeView(view) {
        currentGaugeView = view;
        const btnGaugeDissenters = document.getElementById('btn-gauge-dissenters');
        const btnGaugeAgreers = document.getElementById('btn-gauge-agreers');
        if (btnGaugeDissenters) btnGaugeDissenters.classList.toggle('active', view === 'dissenters');
        if (btnGaugeAgreers) btnGaugeAgreers.classList.toggle('active', view === 'agreers');
        renderDeviationBars();
    }

    // Benchmark Deviation Bars
    function renderDeviationBars() {
        if (currentMode === 'fights') return;

        const gaugeHeading = document.getElementById('gauge-heading');
        const gaugeSubheading = document.getElementById('gauge-subheading');
        const gaugeLegend = document.getElementById('gauge-legend-container');

        const rosterLabel = currentRosterFilter === 'active' ? 'Currently Active (2024–2026)' :
                           (currentRosterFilter === 'historical' ? 'Historical Only (&lt; 2024)' : 'All Eras (1995–2026)');

        if (currentMode === 'fighters') {
            let pool = FIGHTERS.filter(f => (f.total_fights || 0) >= 5);
            if (currentRosterFilter === 'active') {
                pool = pool.filter(f => isFighterActive(f));
            } else if (currentRosterFilter === 'historical') {
                pool = pool.filter(f => !isFighterActive(f));
            }

            if (currentGaugeView === 'dissenters') {
                pool.sort((a, b) => (b.split_pct || 0) - (a.split_pct || 0));
                const topFighters = pool.slice(0, 10);

                if (gaugeHeading) gaugeHeading.textContent = "Fighter Split Decision Rates vs 20.05% UFC Benchmark";
                if (gaugeSubheading) gaugeSubheading.innerHTML = `Top 10 fighters with highest split decision rates · ${rosterLabel} (Min 5 decisions)`;
                if (gaugeLegend) {
                    gaugeLegend.innerHTML = `
                        <span><span class="legend-dot crimson"></span> Higher Split Rate (Above 20.05% Benchmark)</span>
                        <span><span class="legend-dot green"></span> Lower Split Rate (More Decisive Decisions)</span>
                        <span><span class="legend-dot benchmark"></span> 20.05% UFC Average</span>
                    `;
                }

                deviationBars.innerHTML = topFighters.map(f => {
                    const pct = f.split_pct || 0;
                    const diff = pct - UFC_SPLIT_BASELINE_PCT;
                    const isOver = diff >= 0;
                    const diffStr = (isOver ? '+' : '') + diff.toFixed(1) + '%';
                    const barColor = isOver ? 'var(--accent-crimson)' : 'var(--accent-green)';
                    const barWidth = Math.min(100, Math.max(10, (pct / 85) * 100));
                    const active = isFighterActive(f);
                    const statusBadge = active
                        ? `<span class="roster-badge active"><span class="status-dot active"></span> Active</span>`
                        : `<span class="roster-badge historical">${f.last_year || 'Historical'}</span>`;

                    return `
                        <div class="bar-row">
                            <div class="bar-judge-col">
                                <span class="bar-judge-name" title="${escapeHtml(f.fighter_name)}">${escapeHtml(f.fighter_name)}</span>
                                ${statusBadge}
                            </div>
                            <div class="bar-track">
                                <div class="bar-benchmark-line" style="left: ${(UFC_SPLIT_BASELINE_PCT / 85) * 100}%;" title="20.05% Baseline Split Rate"></div>
                                <div class="bar-fill" style="width: ${barWidth}%; background: ${barColor};"></div>
                            </div>
                            <div class="bar-val-col">
                                <span class="bar-val" style="color: ${barColor};">${pct.toFixed(1)}%</span>
                                <span class="bar-delta">(${diffStr})</span>
                            </div>
                        </div>
                    `;
                }).join('');
            } else {
                // Luck Differential View
                const unluckyPool = [...pool].sort((a, b) => a.net_split_diff - b.net_split_diff).slice(0, 5);
                const fortunatePool = [...pool].sort((a, b) => b.net_split_diff - a.net_split_diff).slice(0, 5);
                const luckDisplay = [...unluckyPool, ...fortunatePool];

                if (gaugeHeading) gaugeHeading.textContent = "The UFC Luck Differential: Most Unlucky vs Most Fortunate";
                if (gaugeSubheading) gaugeSubheading.innerHTML = `Fighters with most extreme split decision records (Wins vs Losses) · ${rosterLabel}`;
                if (gaugeLegend) {
                    gaugeLegend.innerHTML = `
                        <span><span class="legend-dot crimson"></span> Unlucky (Negative Split Record)</span>
                        <span><span class="legend-dot green"></span> Fortunate (Positive Split Record)</span>
                        <span><span class="legend-dot benchmark"></span> 0 Net Differential (Even 50-50)</span>
                    `;
                }

                deviationBars.innerHTML = luckDisplay.map(f => {
                    const diff = f.net_split_diff || 0;
                    const isFortunate = diff > 0;
                    const isUnlucky = diff < 0;
                    const barColor = isUnlucky ? 'var(--accent-crimson)' : (isFortunate ? '#10b981' : 'var(--text-muted)');
                    const diffSign = diff > 0 ? '+' : '';
                    const recStr = `${f.split_wins}W - ${f.split_losses}L`;
                    const barWidth = Math.max(12, (Math.abs(diff) / 4) * 80);
                    const active = isFighterActive(f);
                    const statusBadge = active
                        ? `<span class="roster-badge active"><span class="status-dot active"></span> Active</span>`
                        : `<span class="roster-badge historical">${f.last_year || 'Historical'}</span>`;

                    return `
                        <div class="bar-row">
                            <div class="bar-judge-col">
                                <span class="bar-judge-name" title="${escapeHtml(f.fighter_name)}">${escapeHtml(f.fighter_name)}</span>
                                ${statusBadge}
                            </div>
                            <div class="bar-track">
                                <div class="bar-fill" style="width: ${barWidth}%; background: ${barColor};"></div>
                            </div>
                            <div class="bar-val-col">
                                <span class="bar-val" style="color: ${barColor};">${diffSign}${diff} Net</span>
                                <span class="bar-delta">(${recStr})</span>
                            </div>
                        </div>
                    `;
                }).join('');
            }
            return;
        }

        let pool = ROUND_JUDGES.filter(j => (j.total_rounds || 0) >= 250);
        if (currentRosterFilter === 'active') {
            pool = pool.filter(j => isJudgeActive(j));
        } else if (currentRosterFilter === 'historical') {
            pool = pool.filter(j => !isJudgeActive(j));
        }

        if (currentGaugeView === 'dissenters') {
            pool.sort((a, b) => (b.round_dissent_pct || 0) - (a.round_dissent_pct || 0));
            const topJudges = pool.slice(0, 10);

            if (gaugeHeading) gaugeHeading.textContent = `Veteran Mainstays vs ${UFC_BASELINE_PCT.toFixed(2)}% Historical UFC Average`;
            if (gaugeSubheading) gaugeSubheading.innerHTML = `Top 10 judges with highest round dissent rates · ${rosterLabel} (250+ rounds scored)`;
            if (gaugeLegend) {
                gaugeLegend.innerHTML = `
                    <span><span class="legend-dot crimson"></span> Higher Dissent Rate (Above Benchmark)</span>
                    <span><span class="legend-dot green"></span> Lower Dissent Rate (More Consensual)</span>
                    <span><span class="legend-dot benchmark"></span> ${UFC_BASELINE_PCT.toFixed(2)}% UFC Average</span>
                `;
            }

            deviationBars.innerHTML = topJudges.map(j => {
                const pct = j.round_dissent_pct || 0;
                const diff = pct - UFC_BASELINE_PCT;
                const isOver = diff >= 0;
                const diffStr = (isOver ? '+' : '') + diff.toFixed(2) + '%';
                const barColor = isOver ? 'var(--accent-crimson)' : 'var(--accent-green)';
                const barWidth = Math.min(100, Math.max(8, (pct / 12) * 100));
                const active = isJudgeActive(j);
                const statusBadge = active
                    ? `<span class="roster-badge active"><span class="status-dot active"></span> Active</span>`
                    : `<span class="roster-badge historical">${j.last_year || 'Historical'}</span>`;

                return `
                    <div class="bar-row">
                        <div class="bar-judge-col">
                            <span class="bar-judge-name" title="${escapeHtml(j.judge_name)}">${escapeHtml(j.judge_name)}</span>
                            ${statusBadge}
                        </div>
                        <div class="bar-track">
                            <div class="bar-benchmark-line" style="left: ${(UFC_BASELINE_PCT / 12) * 100}%;" title="${UFC_BASELINE_PCT.toFixed(2)}% Baseline"></div>
                            <div class="bar-fill" style="width: ${barWidth}%; background: ${barColor};"></div>
                        </div>
                        <div class="bar-val-col">
                            <span class="bar-val" style="color: ${barColor};">${pct.toFixed(2)}%</span>
                            <span class="bar-delta">(${diffStr})</span>
                        </div>
                    </div>
                `;
            }).join('');
        } else {
            // Most Consensual (Agreers): sort lowest dissent rate first
            pool.sort((a, b) => (a.round_dissent_pct || 0) - (b.round_dissent_pct || 0));
            const topJudges = pool.slice(0, 10);
            const baselineAgree = +(100 - UFC_BASELINE_PCT).toFixed(2);

            if (gaugeHeading) gaugeHeading.textContent = "Most Consensual Judges (Highest Colleague Agreement Rates)";
            if (gaugeSubheading) gaugeSubheading.innerHTML = `Top 10 judges with highest colleague agreement · ${rosterLabel} (250+ rounds scored)`;
            if (gaugeLegend) {
                gaugeLegend.innerHTML = `
                    <span><span class="legend-dot green"></span> Colleague Agreement Rate (%)</span>
                    <span><span class="legend-dot benchmark"></span> ${baselineAgree}% UFC Baseline Agreement (100% - ${UFC_BASELINE_PCT.toFixed(2)}%)</span>
                `;
            }

            const minScale = 88;
            const maxScale = 96;
            const baselinePos = ((baselineAgree - minScale) / (maxScale - minScale)) * 100;

            deviationBars.innerHTML = topJudges.map(j => {
                const dissentPct = j.round_dissent_pct || 0;
                const agreePct = +(100 - dissentPct).toFixed(2);
                const dissentDiff = dissentPct - UFC_BASELINE_PCT;
                const diffStr = (dissentDiff >= 0 ? '+' : '') + dissentDiff.toFixed(2) + '% diss';
                const barWidth = Math.min(100, Math.max(10, ((agreePct - minScale) / (maxScale - minScale)) * 100));
                const active = isJudgeActive(j);
                const statusBadge = active
                    ? `<span class="roster-badge active"><span class="status-dot active"></span> Active</span>`
                    : `<span class="roster-badge historical">${j.last_year || 'Historical'}</span>`;

                return `
                    <div class="bar-row">
                        <div class="bar-judge-col">
                            <span class="bar-judge-name" title="${escapeHtml(j.judge_name)}">${escapeHtml(j.judge_name)}</span>
                            ${statusBadge}
                        </div>
                        <div class="bar-track">
                            <div class="bar-benchmark-line" style="left: ${baselinePos}%;" title="92.59% Baseline Colleague Agreement"></div>
                            <div class="bar-fill" style="width: ${barWidth}%; background: linear-gradient(90deg, #059669, #10b981);"></div>
                        </div>
                        <div class="bar-val-col">
                            <span class="bar-val" style="color: var(--accent-green);">${agreePct.toFixed(2)}%</span>
                            <span class="bar-delta">(${diffStr})</span>
                        </div>
                    </div>
                `;
            }).join('');
        }
    }

    // Filter Buttons
    function renderFilterPills() {
        filterPillsContainer.innerHTML = '';
        const filters = currentMode === 'rounds' ? [
            { label: 'All-Time Mainstays (250+ Rds)', min: 250 },
            { label: 'Regular Veterans (100+ Rds)', min: 100 },
            { label: 'Emerging / Mid-Volume (50+ Rds)', min: 50 },
            { label: 'All Judges (1+ Rds)', min: 1 }
        ] : (currentMode === 'fights' ? [
            { label: 'All-Time Mainstays (250+ Fights)', min: 250 },
            { label: 'Veterans (100+ Fights)', min: 100 },
            { label: 'Regulars (50+ Fights)', min: 50 },
            { label: 'All Judges', min: 1 }
        ] : [
            { label: 'Veterans (10+ Decs)', min: 10 },
            { label: 'Regulars (5+ Decs)', min: 5 },
            { label: 'Contested (3+ Splits)', min: 'splits_3' },
            { label: 'Most Unlucky (Net ≤ -1)', min: 'unlucky' },
            { label: 'Most Fortunate (Net ≥ +1)', min: 'fortunate' },
            { label: 'All Fighters', min: 1 }
        ]);

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
                    <th data-sort="rank" class="col-center" style="width:50px;">#</th>
                    <th data-sort="name" class="col-text">Judge Name & Status</th>
                    <th data-sort="rounds" class="col-num">Rounds Judged</th>
                    <th data-sort="dissents" class="col-num">Lone Dissents</th>
                    <th data-sort="rate" class="col-num">Dissent Rate (%)</th>
                    <th data-sort="ten_eight" class="col-num">10-8 Rounds (%)</th>
                    <th data-sort="partner" class="col-text">Top Friction Co-Judge</th>
                    <th class="col-center" style="width:90px;">Profile</th>
                </tr>
            `;
        } else if (currentMode === 'fights') {
            tableHead.innerHTML = `
                <tr>
                    <th data-sort="rank" class="col-center" style="width:50px;">#</th>
                    <th data-sort="name" class="col-text">Judge Name & Status</th>
                    <th data-sort="fights" class="col-num">Fights Judged</th>
                    <th data-sort="dissents" class="col-num">Split Dissents</th>
                    <th data-sort="rate" class="col-num">Dissent Rate (%)</th>
                    <th data-sort="unanimous" class="col-num">Unanimous %</th>
                    <th data-sort="era" class="col-center">Active Era</th>
                    <th class="col-center" style="width:90px;">Profile</th>
                </tr>
            `;
        } else {
            tableHead.innerHTML = `
                <tr>
                    <th data-sort="rank" class="col-center" style="width:50px;">#</th>
                    <th data-sort="name" class="col-text">Fighter Name & Status</th>
                    <th data-sort="fights" class="col-num">Decision Bouts</th>
                    <th data-sort="splits" class="col-num">Split Decisions</th>
                    <th data-sort="split_pct" class="col-num">Split Rate (%)</th>
                    <th data-sort="record" class="col-center">Split Record (W-L-D)</th>
                    <th data-sort="luck" class="col-center">Luck Index</th>
                    <th data-sort="contested" class="col-num">Contested Rounds (%)</th>
                    <th class="col-center" style="width:90px;">Profile</th>
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
        if (currentMode === 'fighters') {
            let filtered = FIGHTERS.filter(f => {
                if (typeof currentFilterMin === 'number') {
                    if ((f.total_fights || 0) < currentFilterMin) return false;
                } else if (currentFilterMin === 'splits_3') {
                    if ((f.split_fights || 0) < 3) return false;
                } else if (currentFilterMin === 'unlucky') {
                    if ((f.net_split_diff || 0) > -1) return false;
                } else if (currentFilterMin === 'fortunate') {
                    if ((f.net_split_diff || 0) < 1) return false;
                }
                if (currentRosterFilter === 'active' && !isFighterActive(f)) return false;
                if (currentRosterFilter === 'historical' && isFighterActive(f)) return false;
                if (searchQuery) {
                    return f.fighter_name.toLowerCase().includes(searchQuery.toLowerCase());
                }
                return true;
            });

            // Sorting
            filtered.sort((a, b) => {
                let valA, valB;
                if (sortColumn === 'name') { valA = a.fighter_name; valB = b.fighter_name; }
                else if (sortColumn === 'fights') { valA = a.total_fights; valB = b.total_fights; }
                else if (sortColumn === 'splits') { valA = a.split_fights; valB = b.split_fights; }
                else if (sortColumn === 'split_pct') { valA = a.split_pct; valB = b.split_pct; }
                else if (sortColumn === 'record') { valA = a.split_wins; valB = b.split_wins; }
                else if (sortColumn === 'luck') { valA = a.net_split_diff; valB = b.net_split_diff; }
                else if (sortColumn === 'contested') { valA = a.contested_round_pct; valB = b.contested_round_pct; }
                else { valA = a.split_pct; valB = b.split_pct; }

                if (valA < valB) return sortAsc ? -1 : 1;
                if (valA > valB) return sortAsc ? 1 : -1;
                return (b.total_fights || 0) - (a.total_fights || 0);
            });

            if (filtered.length === 0) {
                tableBody.innerHTML = `<tr><td colspan="9" style="text-align:center; padding: 32px; color: var(--text-muted);">No fighters found matching search or filter criteria.</td></tr>`;
                return;
            }

            let html = '';
            filtered.forEach((f, idx) => {
                const isExpanded = expandedJudge === f.fighter_name;
                const active = isFighterActive(f);
                const rosterBadge = active
                    ? `<span class="roster-badge active" title="Active in UFC (2024–2026)"><span class="status-dot active"></span> Active</span>`
                    : `<span class="roster-badge historical" title="Historical (last fought ${f.last_year || 'earlier'})">${f.first_year || ''}–${f.last_year || 'Past'}</span>`;

                const pct = f.split_pct || 0;
                const diff = pct - UFC_SPLIT_BASELINE_PCT;
                const badgeClass = diff >= 0 ? 'over' : 'under';
                const badgeSign = diff >= 0 ? '+' : '';

                const net = f.net_split_diff || 0;
                let luckStyle = '';
                if (net < 0) {
                    luckStyle = 'background:var(--accent-crimson-bg); color:var(--accent-crimson);';
                } else if (net > 0) {
                    luckStyle = 'background:var(--accent-green-bg); color:var(--accent-green);';
                } else {
                    luckStyle = 'background:var(--bg-surface-elevated); color:var(--text-muted); border:1px solid var(--border-subtle);';
                }
                const luckSign = net > 0 ? '+' : '';
                const recStr = `${f.split_wins}W - ${f.split_losses}L${f.split_draws ? ' - ' + f.split_draws + 'D' : ''}`;

                html += `
                    <tr class="judge-row ${isExpanded ? 'expanded' : ''}" data-judge="${escapeHtml(f.fighter_name)}">
                        <td class="col-center mono-num" style="color:var(--text-muted);">${idx + 1}</td>
                        <td class="col-text">
                            <div class="judge-cell">
                                <svg class="expand-chevron" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><polyline points="9 18 15 12 9 6"></polyline></svg>
                                <span class="judge-name-text">${escapeHtml(f.fighter_name)}</span>
                                ${rosterBadge}
                            </div>
                        </td>
                        <td class="col-num mono-num">${(f.total_fights || 0).toLocaleString()}</td>
                        <td class="col-num mono-num">${(f.split_fights || 0).toLocaleString()}</td>
                        <td class="col-num">
                            <div class="rate-cell-group" style="justify-content: flex-end;">
                                <span class="mono-num" style="font-weight:700;">${pct.toFixed(1)}%</span>
                                <span class="rate-badge ${badgeClass}">${badgeSign}${diff.toFixed(1)}%</span>
                            </div>
                        </td>
                        <td class="col-center mono-num">${recStr}</td>
                        <td class="col-center">
                            <span class="rate-badge" style="${luckStyle}">
                                ${luckSign}${net} (${f.luck_badge})
                            </span>
                        </td>
                        <td class="col-num mono-num">${f.contested_rounds || 0} / ${f.total_rounds || 0} (${(f.contested_round_pct || 0).toFixed(1)}%)</td>
                        <td class="col-center">
                            <button class="dossier-expand-btn ${isExpanded ? 'active' : ''}">${isExpanded ? 'Close' : 'Dossier'}</button>
                        </td>
                    </tr>
                `;

                // Fighter Dossier Drawer Row
                if (isExpanded) {
                    const sampleFights = f.sample_close_fights || [];
                    const fightsHtml = sampleFights.length > 0 ? sampleFights.map(fight => {
                        const resStr = (fight.result || '').toLowerCase();
                        const isWin = resStr.startsWith('w');
                        const isLoss = resStr.startsWith('l');
                        const resBadgeClass = isWin ? 'under' : (isLoss ? 'over' : 'draw');
                        const resLabel = isWin ? 'WIN' : (isLoss ? 'LOSS' : 'DRAW');
                        return `
                            <div class="dissent-card">
                                <div class="dissent-card-top">
                                    <span class="dissent-year-round">${fight.year || ''}</span>
                                    <span class="rate-badge ${resBadgeClass}">${resLabel}</span>
                                </div>
                                <div class="dissent-bout-name">vs ${escapeHtml(fight.opponent || 'Opponent')}</div>
                                <div class="dissent-scores-row">
                                    <div class="dissent-judge-score">
                                        <span class="score-label">Decision:</span>
                                        <span class="rate-badge draw">${escapeHtml(fight.type || 'Split')} Decision</span>
                                    </div>
                                    <div class="dissent-consensus-info">
                                        <span class="consensus-label">Event:</span>
                                        <span class="consensus-names">${escapeHtml(fight.event || 'UFC Bout')}</span>
                                    </div>
                                </div>
                            </div>
                        `;
                    }).join('') : '<div style="color:var(--text-muted); font-size:var(--font-size-caption); padding: var(--space-2) 0;">No close split decision samples on file.</div>';

                    const eraYears = (f.last_year && f.first_year) ? `${(f.last_year - f.first_year + 1)} seasons` : 'Career';

                    html += `
                        <tr class="dossier-drawer-row visible">
                            <td colspan="9" style="padding:0;">
                                <div class="dossier-card">
                                    <div class="dossier-profile">
                                        <div class="dossier-profile-header">
                                            <div class="dossier-title-row">
                                                <h4 class="dossier-name">${escapeHtml(f.fighter_name)}</h4>
                                                ${rosterBadge}
                                            </div>
                                            <div class="dossier-era-tag">
                                                <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"></circle><polyline points="12 6 12 12 16 14"></polyline></svg>
                                                <span>UFC Career Span: <strong>${f.first_year || ''} – ${f.last_year || ''}</strong> (${eraYears})</span>
                                            </div>
                                        </div>
                                        <div class="dossier-stats-grid">
                                            <div class="dossier-stat-tile">
                                                <span class="stat-tile-label">Split Decision Rate</span>
                                                <div class="stat-tile-value" style="color: ${diff >= 0 ? 'var(--accent-crimson)' : 'var(--accent-green)'};">${pct.toFixed(1)}%</div>
                                                <span class="stat-tile-sub">${f.split_fights} of ${f.total_fights} decisions (UFC avg 20.05%)</span>
                                            </div>
                                            <div class="dossier-stat-tile">
                                                <span class="stat-tile-label">Career Split Record</span>
                                                <div class="stat-tile-value">${recStr}</div>
                                                <span class="stat-tile-sub">Net Luck: ${luckSign}${net}</span>
                                            </div>
                                            <div class="dossier-stat-tile">
                                                <span class="stat-tile-label">Contested Rounds</span>
                                                <div class="stat-tile-value">${(f.contested_round_pct || 0).toFixed(1)}%</div>
                                                <span class="stat-tile-sub">${f.contested_rounds || 0} of ${f.total_rounds || 0} rounds</span>
                                            </div>
                                            <div class="dossier-stat-tile">
                                                <span class="stat-tile-label">Decision Breakdown</span>
                                                <div class="stat-tile-value">${f.unanimous_fights || 0} UD</div>
                                                <span class="stat-tile-sub">${f.split_fights || 0} SD · ${f.majority_fights || 0} MD</span>
                                            </div>
                                        </div>
                                        <div class="dossier-friction-box">
                                            <div class="friction-box-header">
                                                <span class="friction-badge">Career Split Luck Index</span>
                                                <span class="rate-badge" style="${luckStyle}">${luckSign}${net} (${f.luck_badge})</span>
                                            </div>
                                            <div class="friction-partner-name">${f.split_wins} Split Wins · ${f.split_losses} Split Losses</div>
                                            <div class="friction-subtext">${net > 0 ? 'Fighter has benefited from split decision variance (+luck)' : (net < 0 ? 'Fighter has suffered negative variance in split verdicts (-luck)' : 'Even split decision distribution over career')}</div>
                                        </div>
                                    </div>
                                    <div class="dossier-evidence">
                                        <div class="dossier-evidence-header">
                                            <h5>Notable Split Decision Bouts</h5>
                                            <span class="evidence-caption">Key fights decided by divided or razor-thin judge scorecards</span>
                                        </div>
                                        <div class="dossier-cards-grid">
                                            ${fightsHtml}
                                        </div>
                                    </div>
                                </div>
                            </td>
                        </tr>
                    `;
                }
            });

            tableBody.innerHTML = html;

            tableBody.querySelectorAll('tr.judge-row').forEach(row => {
                row.addEventListener('click', () => {
                    const jName = row.dataset.judge;
                    expandedJudge = (expandedJudge === jName) ? null : jName;
                    renderTable();
                });
            });
            return;
        }

        const rawList = currentMode === 'rounds' ? ROUND_JUDGES : FIGHT_JUDGES;

        let filtered = rawList.filter(j => {
            const count = currentMode === 'rounds' ? (j.total_rounds || 0) : (j.total_fights || 0);
            if (count < currentFilterMin) return false;
            if (currentRosterFilter === 'active' && !isJudgeActive(j)) return false;
            if (currentRosterFilter === 'historical' && isJudgeActive(j)) return false;
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
            const active = isJudgeActive(j);
            const rosterBadge = active
                ? `<span class="roster-badge active" title="Active in UFC (2024–2026)"><span class="status-dot active"></span> Active</span>`
                : `<span class="roster-badge historical" title="Historical (last judged ${j.last_year || 'earlier'})">Historical (${j.last_year || 'Past'})</span>`;

            if (currentMode === 'rounds') {
                const pct = j.round_dissent_pct || 0;
                const diff = pct - UFC_BASELINE_PCT;
                const badgeClass = diff >= 0 ? 'over' : 'under';
                const badgeSign = diff >= 0 ? '+' : '';
                const tenEightStr = `${(j.ten_eight_rounds || 0).toLocaleString()} (${(j.ten_eight_pct || 0).toFixed(1)}%)`;
                const clashStr = j.top_clash_partner ? `${escapeHtml(j.top_clash_partner)} (${(j.top_clash_pct || 0).toFixed(1)}%)` : '—';

                html += `
                    <tr class="judge-row ${isExpanded ? 'expanded' : ''}" data-judge="${escapeHtml(j.judge_name)}">
                        <td class="col-center mono-num" style="color:var(--text-muted);">${idx + 1}</td>
                        <td class="col-text">
                            <div class="judge-cell">
                                <svg class="expand-chevron" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><polyline points="9 18 15 12 9 6"></polyline></svg>
                                <span class="judge-name-text">${escapeHtml(j.judge_name)}</span>
                                ${rosterBadge}
                            </div>
                        </td>
                        <td class="col-num mono-num">${(j.total_rounds || 0).toLocaleString()}</td>
                        <td class="col-num mono-num">${(j.round_dissents || 0).toLocaleString()}</td>
                        <td class="col-num">
                            <div class="rate-cell-group" style="justify-content: flex-end;">
                                <span class="mono-num" style="font-weight:700;">${pct.toFixed(2)}%</span>
                                <span class="rate-badge ${badgeClass}">${badgeSign}${diff.toFixed(2)}%</span>
                            </div>
                        </td>
                        <td class="col-num mono-num">${tenEightStr}</td>
                        <td class="col-text">${clashStr}</td>
                        <td class="col-center">
                            <button class="dossier-expand-btn ${isExpanded ? 'active' : ''}">${isExpanded ? 'Close' : 'Dossier'}</button>
                        </td>
                    </tr>
                `;

                // Dossier Drawer Row
                if (isExpanded) {
                    const sampleDissents = j.sample_dissents || [];
                    const dissentsHtml = sampleDissents.length > 0 ? sampleDissents.map(d => {
                        const finishBadge = d.is_finish
                            ? `<span class="finish-badge" style="background:rgba(239,68,68,0.2); color:#fca5a5; font-size:10px; padding:1px 6px; border-radius:var(--radius-pill); font-weight:700;" title="Bout finished in Round ${d.finish_round || ''} via ${d.finish_method || 'Finish'}">${d.finish_method || 'Finish'} (R${d.finish_round || '?'})</span>`
                            : '';
                        return `
                        <div class="dissent-card">
                            <div class="dissent-card-top">
                                <span class="dissent-year-round">${d.year || ''} · Round ${d.round || ''}</span>
                                ${finishBadge}
                            </div>
                            <div class="dissent-bout-name">${escapeHtml(d.fight || '')}</div>
                            <div class="dissent-scores-row">
                                <div class="dissent-judge-score">
                                    <span class="score-label">Judge Score:</span>
                                    <span class="score-badge-crimson">${d.score}</span>
                                </div>
                                <div class="dissent-consensus-info">
                                    <span class="consensus-label">Dissented Against:</span>
                                    <span class="consensus-names">${escapeHtml(d.c1)}, ${escapeHtml(d.c2)}</span>
                                </div>
                            </div>
                        </div>
                    `;}).join('') : '<div style="color:var(--text-muted); font-size:var(--font-size-caption); padding: var(--space-2) 0;">No round dissent samples on file for this judge.</div>';

                    const freq = j.round_dissents > 0 ? (j.total_rounds / j.round_dissents).toFixed(1) : '—';
                    const agreePct = (100 - pct).toFixed(2);
                    const finishRoundsCount = (j.finish_rounds || 0).toLocaleString();
                    const eraYears = (j.last_year && j.first_year) ? `${(j.last_year - j.first_year + 1)} seasons` : 'Career';

                    html += `
                        <tr class="dossier-drawer-row visible">
                            <td colspan="8" style="padding:0;">
                                <div class="dossier-card">
                                    <div class="dossier-profile">
                                        <div class="dossier-profile-header">
                                            <div class="dossier-title-row">
                                                <h4 class="dossier-name">${escapeHtml(j.judge_name)}</h4>
                                                ${rosterBadge}
                                            </div>
                                            <div class="dossier-era-tag">
                                                <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"></circle><polyline points="12 6 12 12 16 14"></polyline></svg>
                                                <span>Active UFC Era: <strong>${j.first_year || 1995} – ${j.last_year || 2026}</strong> (${eraYears})</span>
                                            </div>
                                        </div>
                                        <div class="dossier-stats-grid">
                                            <div class="dossier-stat-tile">
                                                <span class="stat-tile-label">Dissent Rate</span>
                                                <div class="stat-tile-value" style="color: ${diff >= 0 ? 'var(--accent-crimson)' : 'var(--accent-green)'};">${pct.toFixed(2)}%</div>
                                                <span class="stat-tile-sub">1 every ${freq} rounds (${badgeSign}${diff.toFixed(2)}% vs avg)</span>
                                            </div>
                                            <div class="dossier-stat-tile">
                                                <span class="stat-tile-label">Consensus Rate</span>
                                                <div class="stat-tile-value">${agreePct}%</div>
                                                <span class="stat-tile-sub">Agrees with colleagues</span>
                                            </div>
                                            <div class="dossier-stat-tile">
                                                <span class="stat-tile-label">Dominant 10–8s</span>
                                                <div class="stat-tile-value">${(j.ten_eight_rounds || 0).toLocaleString()}</div>
                                                <span class="stat-tile-sub">${(j.ten_eight_pct || 0).toFixed(1)}% of scored rounds</span>
                                            </div>
                                            <div class="dossier-stat-tile">
                                                <span class="stat-tile-label">Completed Stoppage Rounds</span>
                                                <div class="stat-tile-value">${finishRoundsCount}</div>
                                                <span class="stat-tile-sub">Rounds prior to finish</span>
                                            </div>
                                        </div>
                                        <div class="dossier-friction-box">
                                            <div class="friction-box-header">
                                                <span class="friction-badge">Top Colleague Friction</span>
                                                <span class="friction-rate">${(j.top_clash_pct || 0).toFixed(1)}% Disagreement</span>
                                            </div>
                                            <div class="friction-partner-name">${escapeHtml(j.top_clash_partner || 'None recorded')}</div>
                                            <div class="friction-subtext">Disagreed on ${Math.round(((j.top_clash_pct || 0) / 100) * (j.top_clash_rounds || 0))} of ${j.top_clash_rounds || 0} shared rounds seated together</div>
                                        </div>
                                    </div>
                                    <div class="dossier-evidence">
                                        <div class="dossier-evidence-header">
                                            <h5>Notable Lone Round Dissents</h5>
                                            <span class="evidence-caption">Scorecards where ${escapeHtml(j.judge_name)} broke away from colleague consensus</span>
                                        </div>
                                        <div class="dossier-cards-grid">
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
                    <tr class="judge-row ${isExpanded ? 'expanded' : ''}" data-judge="${escapeHtml(j.judge_name)}">
                        <td class="col-center mono-num" style="color:var(--text-muted);">${idx + 1}</td>
                        <td class="col-text">
                            <div class="judge-cell">
                                <svg class="expand-chevron" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><polyline points="9 18 15 12 9 6"></polyline></svg>
                                <span class="judge-name-text">${escapeHtml(j.judge_name)}</span>
                                ${rosterBadge}
                            </div>
                        </td>
                        <td class="col-num mono-num">${(j.total_fights || 0).toLocaleString()}</td>
                        <td class="col-num mono-num">${(j.dissents || 0).toLocaleString()}</td>
                        <td class="col-num mono-num" style="font-weight:700;">${pct.toFixed(2)}%</td>
                        <td class="col-num mono-num">${j.unanimous_pct || 0}%</td>
                        <td class="col-center">${era}</td>
                        <td class="col-center">
                            <button class="dossier-expand-btn ${isExpanded ? 'active' : ''}">${isExpanded ? 'Close' : 'Dossier'}</button>
                        </td>
                    </tr>
                `;

                if (isExpanded) {
                    const eraYears = (j.last_year && j.first_year) ? `${(j.last_year - j.first_year + 1)} seasons` : 'Career';
                    html += `
                        <tr class="dossier-drawer-row visible">
                            <td colspan="8" style="padding:0;">
                                <div class="dossier-card">
                                    <div class="dossier-profile">
                                        <div class="dossier-profile-header">
                                            <div class="dossier-title-row">
                                                <h4 class="dossier-name">${escapeHtml(j.judge_name)}</h4>
                                                ${rosterBadge}
                                            </div>
                                            <div class="dossier-era-tag">
                                                <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"></circle><polyline points="12 6 12 12 16 14"></polyline></svg>
                                                <span>Active UFC Era: <strong>${j.first_year || 1995} – ${j.last_year || 2026}</strong> (${eraYears})</span>
                                            </div>
                                        </div>
                                        <div class="dossier-stats-grid">
                                            <div class="dossier-stat-tile">
                                                <span class="stat-tile-label">Split Dissents</span>
                                                <div class="stat-tile-value" style="color:var(--accent-crimson);">${(j.dissents || 0).toLocaleString()}</div>
                                                <span class="stat-tile-sub">${pct.toFixed(2)}% of judged bouts</span>
                                            </div>
                                            <div class="dossier-stat-tile">
                                                <span class="stat-tile-label">Unanimous Bouts</span>
                                                <div class="stat-tile-value">${(j.unanimous_pct || 0).toFixed(1)}%</div>
                                                <span class="stat-tile-sub">${(j.unanimous_fights || 0).toLocaleString()} consensual decisions</span>
                                            </div>
                                            <div class="dossier-stat-tile">
                                                <span class="stat-tile-label">Total Fights</span>
                                                <div class="stat-tile-value">${(j.total_fights || 0).toLocaleString()}</div>
                                                <span class="stat-tile-sub">Full bouts evaluated</span>
                                            </div>
                                            <div class="dossier-stat-tile">
                                                <span class="stat-tile-label">Scorecard Variance</span>
                                                <div class="stat-tile-value">${(j.score_dissents || 0).toLocaleString()}</div>
                                                <span class="stat-tile-sub">${(j.score_dissent_pct || 0).toFixed(1)}% round dissent rate</span>
                                            </div>
                                        </div>
                                        <div class="dossier-friction-box">
                                            <div class="friction-box-header">
                                                <span class="friction-badge">Career Decision Overview</span>
                                                <span class="friction-rate">${(j.unanimous_pct || 0).toFixed(1)}% Consensual</span>
                                            </div>
                                            <div class="friction-partner-name">${(j.total_fights || 0).toLocaleString()} UFC Decisions Judged</div>
                                            <div class="friction-subtext">Judged from ${j.first_year || ''} to ${j.last_year || ''}. Dissenting minority in ${(j.dissents || 0).toLocaleString()} split verdicts.</div>
                                        </div>
                                    </div>
                                    <div class="dossier-evidence">
                                        <div class="dossier-evidence-header">
                                            <h5>Fight-Level Verdict Distribution</h5>
                                            <span class="evidence-caption">Career breakdown of unanimous vs split decisions</span>
                                        </div>
                                        <div class="dossier-cards-grid">
                                            <div class="dissent-card">
                                                <div class="dissent-card-top">
                                                    <span class="dissent-year-round">Consensual</span>
                                                    <span class="rate-badge under">Unanimous</span>
                                                </div>
                                                <div class="dissent-bout-name">${(j.unanimous_fights || 0).toLocaleString()} Unanimous Decisions</div>
                                                <div class="dissent-scores-row">
                                                    <div class="dissent-judge-score">
                                                        <span class="score-label">Consensus Rate:</span>
                                                        <span class="score-badge-crimson" style="background:var(--accent-green-bg); color:var(--accent-green); border-color:rgba(16,185,129,0.3);">${j.unanimous_pct || 0}%</span>
                                                    </div>
                                                </div>
                                            </div>
                                            <div class="dissent-card">
                                                <div class="dissent-card-top">
                                                    <span class="dissent-year-round">Split Verdicts</span>
                                                    <span class="rate-badge over">Dissent</span>
                                                </div>
                                                <div class="dissent-bout-name">${(j.dissents || 0).toLocaleString()} Lone Dissents</div>
                                                <div class="dissent-scores-row">
                                                    <div class="dissent-judge-score">
                                                        <span class="score-label">Dissent Rate:</span>
                                                        <span class="score-badge-crimson">${pct.toFixed(2)}%</span>
                                                    </div>
                                                </div>
                                            </div>
                                        </div>
                                    </div>
                                </div>
                            </td>
                        </tr>
                    `;
                }
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
                    <td class="col-text" style="font-weight:700; color:var(--text-primary);">${pairName}</td>
                    <td class="col-num mono-num">${volume.toLocaleString()}</td>
                    <td class="col-num mono-num">${diff.toLocaleString()}</td>
                    <td class="col-num">
                        <span class="rate-badge ${badgeClass}">${rate.toFixed(1)}%</span>
                    </td>
                </tr>
            `;
        }).join('');
    }

    // Export to CSV Function
    btnExportCsv.addEventListener('click', () => {
        let csv = '';
        if (currentMode === 'rounds') {
            csv = "Judge Name,Roster Status,Last Year,Total Rounds,Round Dissents,Dissent Rate Pct,Colleague Agreement Pct,Ten Eight Rounds,Consensus Rounds,Top Clash Partner\\n";
            ROUND_JUDGES.forEach(j => {
                const status = isJudgeActive(j) ? 'Active' : 'Historical';
                const agreePct = (100 - (j.round_dissent_pct || 0)).toFixed(2);
                csv += `"${j.judge_name}","${status}",${j.last_year || ''},${j.total_rounds},${j.round_dissents},${j.round_dissent_pct},${agreePct},${j.ten_eight_rounds},${j.consensus_rounds},"${j.top_clash_partner || ''}"\\n`;
            });
        } else if (currentMode === 'fights') {
            csv = "Judge Name,Roster Status,First Year,Last Year,Total Fights,Dissents,Dissent Rate Pct,Unanimous Pct\\n";
            FIGHT_JUDGES.forEach(j => {
                const status = isJudgeActive(j) ? 'Active' : 'Historical';
                csv += `"${j.judge_name}","${status}",${j.first_year},${j.last_year},${j.total_fights},${j.dissents},${j.dissent_pct},${j.unanimous_pct}\\n`;
            });
        } else {
            csv = "Fighter Name,Roster Status,First Year,Last Year,Decision Bouts,Split Decisions,Split Rate Pct,Split Wins,Split Losses,Split Draws,Net Luck Index,Luck Category,Total Rounds,Contested Rounds,Contested Round Pct\\n";
            FIGHTERS.forEach(f => {
                const status = isFighterActive(f) ? 'Active' : 'Historical';
                csv += `"${f.fighter_name}","${status}",${f.first_year || ''},${f.last_year || ''},${f.total_fights},${f.split_fights},${f.split_pct},${f.split_wins},${f.split_losses},${f.split_draws},${f.net_split_diff},"${f.luck_badge}",${f.total_rounds},${f.contested_rounds},${f.contested_round_pct}\\n`;
            });
        }

        const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        const filename = currentMode === 'fighters' ? 'ufc_fighter_controversy_index.csv' : `ufc_judging_${currentMode}_analysis.csv`;
        a.download = filename;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
    });

    // Event Listeners
    btnModeRounds.addEventListener('click', () => setMode('rounds'));
    btnModeFights.addEventListener('click', () => setMode('fights'));
    btnModeFighters.addEventListener('click', () => setMode('fighters'));
    searchInput.addEventListener('input', (e) => {
        searchQuery = e.target.value.trim();
        renderTable();
    });

    // Gauge View Controls (Dissenters vs Agreers)
    const btnGaugeDissenters = document.getElementById('btn-gauge-dissenters');
    const btnGaugeAgreers = document.getElementById('btn-gauge-agreers');
    if (btnGaugeDissenters) {
        btnGaugeDissenters.addEventListener('click', () => setGaugeView('dissenters'));
    }
    if (btnGaugeAgreers) {
        btnGaugeAgreers.addEventListener('click', () => setGaugeView('agreers'));
    }

    // Gauge Roster Controls (All vs Active)
    const btnGaugeAll = document.getElementById('btn-gauge-all');
    const btnGaugeActive = document.getElementById('btn-gauge-active');
    if (btnGaugeAll) {
        btnGaugeAll.addEventListener('click', () => setRosterFilter('all'));
    }
    if (btnGaugeActive) {
        btnGaugeActive.addEventListener('click', () => setRosterFilter('active'));
    }

    // Table Roster Controls (All vs Active vs Historical)
    document.querySelectorAll('#table-roster-segmented .seg-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            const roster = btn.dataset.roster || 'all';
            setRosterFilter(roster);
        });
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
        judging_data: dict[str, Any] = json.load(f)

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

    # Safe JSON stringification preventing </script> injection and line separator breakout
    safe_round_judges_json = safe_json_embed(judging_data.get("round_judges", []))
    safe_fight_judges_json = safe_json_embed(judging_data.get("judges", []))
    safe_fighters_json = safe_json_embed(judging_data.get("fighters", []))
    safe_fighter_kpis_json = safe_json_embed(judging_data.get("summary", {}).get("fighters", {}))
    safe_round_pairs_json = safe_json_embed(judging_data.get("round_pairs", []))
    safe_fight_pairs_json = safe_json_embed(judging_data.get("pairs", []))
    safe_summary_json = safe_json_embed(judging_data.get("summary", {}))
    safe_round_summary_json = safe_json_embed(judging_data.get("summary", {}).get("rounds", {}))

    html_content = DASHBOARD_TEMPLATE
    replacements = {
        "__ROUND_JUDGES_JSON__": safe_round_judges_json,
        "__FIGHT_JUDGES_JSON__": safe_fight_judges_json,
        "__FIGHTERS_JSON__": safe_fighters_json,
        "__FIGHTER_KPIS_JSON__": safe_fighter_kpis_json,
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
    logger.info("Compiled standalone UFC judging dashboard to %s", OUTPUT_HTML_PATH)
    return OUTPUT_HTML_PATH


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    build_dashboard_html()
