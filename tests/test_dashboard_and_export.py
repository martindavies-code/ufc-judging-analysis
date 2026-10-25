"""Unit and integration tests for dashboard construction, XSS protection, and export pipeline."""

import json
from pathlib import Path

import pytest

from src.build_dashboard import build_dashboard_html, encode_image_base64
from src.export_web_data import export_web_data


class TestExportWebData:
    def test_missing_database_raises(self, tmp_path: Path) -> None:
        fake_db = tmp_path / "missing.db"
        with pytest.raises(FileNotFoundError):
            export_web_data(fake_db)

    def test_export_pipeline_execution(self, tmp_path: Path) -> None:
        # Run export on real database if exists
        real_db = Path("data/ufc_judging.db")
        if real_db.exists():
            json_path = export_web_data(real_db)
            assert json_path.exists()
            with open(json_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            assert "summary" in data
            assert "judges" in data
            assert "pairs" in data
            assert "recent_dissents" in data
            assert data["summary"]["total_fights"] > 0

            assert "fighters" in data
            assert "fighters" in data["summary"]
            assert len(data["fighters"]) > 0
            # Verify fighter schema
            sample_fighter = data["fighters"][0]
            assert "fighter_name" in sample_fighter
            assert "total_fights" in sample_fighter
            assert "split_fights" in sample_fighter
            assert "split_pct" in sample_fighter
            assert "net_split_diff" in sample_fighter
            assert "luck_badge" in sample_fighter
            assert "contested_round_pct" in sample_fighter
            assert "sample_close_fights" in sample_fighter

            # Verify stoppage round metrics in summary and recent_round_dissents
            assert "rounds" in data["summary"]
            rounds_summary = data["summary"]["rounds"]
            assert rounds_summary["total_rounds"] == 32876
            assert rounds_summary["finish_rounds"] == 288
            assert rounds_summary["finish_fights_count"] == 48
            assert rounds_summary["decision_rounds"] == 32588
            assert "recent_round_dissents" in data
            stoppage_dissents = [d for d in data["recent_round_dissents"] if d.get("is_finish")]
            assert len(stoppage_dissents) > 0
            assert any("Usman" in d.get("fight", "") for d in stoppage_dissents)


class TestBuildDashboard:
    def test_encode_image_base64_nonexistent(self) -> None:
        assert encode_image_base64("non_existent_img_12345.png") == ""

    def test_dashboard_compilation_and_xss_safety(self) -> None:
        dashboard_path = build_dashboard_html()
        assert dashboard_path.exists()

        with open(dashboard_path, "r", encoding="utf-8") as f:
            html_text = f.read()

        assert "<!DOCTYPE html>" in html_text
        assert "UFC Judging" in html_text
        assert "Round-by-Round" in html_text
        assert "ROUND_JUDGES" in html_text
        assert "FIGHTERS" in html_text
        assert "FIGHTER_KPIS" in html_text
        # Ensure raw unescaped script injection is not present
        assert "<script>alert" not in html_text
        # Ensure script breakout tag </script> is escaped inside JSON data
        assert "</script>" in html_text  # only legitimate closing tags
        # Verify agreers toggle and roster active/historical controls
        assert 'id="btn-gauge-dissenters"' in html_text
        assert 'id="btn-gauge-agreers"' in html_text
        assert 'id="gauge-roster-toggle"' in html_text
        assert 'id="table-roster-segmented"' in html_text
        assert 'data-roster="active"' in html_text
        assert 'data-roster="historical"' in html_text
        assert "Most Consensual (Agreers)" in html_text
        assert "Currently Active" in html_text
        # Verify Fighter Controversy controls
        assert 'id="btn-mode-fighters"' in html_text
        assert "Fighter Controversy Index" in html_text
        assert "ufc_fighter_controversy_index.csv" in html_text
        # Verify stoppage rounds metadata and comprehensive scope notice
        assert "32,876" in html_text
        assert "Comprehensive Scope" in html_text
        assert "finish-badge" in html_text
        assert "Completed Stoppage Rounds" in html_text

    def test_dashboard_javascript_syntax(self) -> None:
        import shutil
        import subprocess

        dashboard_path = build_dashboard_html()
        assert dashboard_path.exists()

        node_bin = shutil.which("node")
        if node_bin:
            res = subprocess.run(
                [
                    node_bin,
                    "-e",
                    "const fs = require('fs'); const html = fs.readFileSync('index.html', 'utf8'); const m = html.match(/<script>([\\s\\S]*?)<\\/script>/); if (m) { new Function(m[1]); }",
                ],
                capture_output=True,
                text=True,
                cwd=str(dashboard_path.parent),
            )
            assert res.returncode == 0, f"JavaScript syntax error in index.html: {res.stderr}"

    def test_export_data_year_typing(self) -> None:
        real_db = Path("data/ufc_judging.db")
        if real_db.exists():
            json_path = export_web_data(real_db)
            with open(json_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            # Ensure first_year and last_year are ints for judges
            for j in data["judges"][:10]:
                assert isinstance(j["first_year"], int)
                assert isinstance(j["last_year"], int)
            for rj in data["round_judges"][:10]:
                assert isinstance(rj["first_year"], int)
                assert isinstance(rj["last_year"], int)
            for f in data["fighters"][:10]:
                if f["first_year"] is not None:
                    assert isinstance(f["first_year"], int)
                if f["last_year"] is not None:
                    assert isinstance(f["last_year"], int)


class TestFighterAnalysis:
    def test_calculate_fighter_metrics_logic(self) -> None:
        import pandas as pd

        from src.fighter_analysis import calculate_fighter_metrics

        names_map = {
            "1": ("Fighter A", "Fighter B"),
            "2": ("Fighter C", "Fighter A"),
            "3": ("Fighter A", "Fighter D"),
        }

        df_fights = pd.DataFrame(
            [
                {
                    "decision_id": "1",
                    "event_year": 2023,
                    "fighter_1": "Fighter A",
                    "fighter_2": "Fighter B",
                    "outcome": "def",
                    "decision_type": "Split Decision",
                    "fight": "Fighter A def. Fighter B",
                },
                {
                    "decision_id": "2",
                    "event_year": 2024,
                    "fighter_1": "Fighter C",
                    "fighter_2": "Fighter A",
                    "outcome": "def",
                    "decision_type": "Split Decision",
                    "fight": "Fighter C def. Fighter A",
                },
                {
                    "decision_id": "3",
                    "event_year": 2024,
                    "fighter_1": "Fighter A",
                    "fighter_2": "Fighter D",
                    "outcome": "def",
                    "decision_type": "Unanimous Decision",
                    "fight": "Fighter A def. Fighter D",
                },
            ]
        )

        df_rounds = pd.DataFrame(
            [
                {"decision_id": "1", "round_num": 1, "round_dissented": 1},
                {"decision_id": "1", "round_num": 2, "round_dissented": 0},
                {"decision_id": "1", "round_num": 3, "round_dissented": 0},
                {"decision_id": "2", "round_num": 1, "round_dissented": 1},
                {"decision_id": "2", "round_num": 2, "round_dissented": 1},
                {"decision_id": "2", "round_num": 3, "round_dissented": 0},
                {"decision_id": "3", "round_num": 1, "round_dissented": 0},
                {"decision_id": "3", "round_num": 2, "round_dissented": 0},
                {"decision_id": "3", "round_num": 3, "round_dissented": 0},
            ]
        )

        fighters_list, _kpis = calculate_fighter_metrics(df_fights, df_rounds, names_map=names_map)
        f_a = next(f for f in fighters_list if f["fighter_name"] == "Fighter A")
        assert f_a["total_fights"] == 3
        assert f_a["split_fights"] == 2
        assert round(f_a["split_pct"], 2) == 66.67
        assert f_a["split_wins"] == 1
        assert f_a["split_losses"] == 1
        assert f_a["net_split_diff"] == 0
        assert f_a["luck_badge"] == "Even"
        assert f_a["total_rounds"] == 9
        assert f_a["contested_rounds"] == 3
        assert round(f_a["contested_round_pct"], 2) == 33.33
        assert f_a["first_year"] == 2023
        assert f_a["last_year"] == 2024
        assert len(f_a["sample_close_fights"]) == 3
        assert f_a["sample_close_fights"][0]["type"] == "Split Decision"
        assert f_a["sample_close_fights"][1]["type"] == "Split Decision"

    def test_export_web_data_empty_database(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        import sqlite3

        empty_db = tmp_path / "empty_test.db"
        conn = sqlite3.connect(empty_db)
        try:
            conn.execute("""
                CREATE TABLE fights (
                    decision_id TEXT, event_id TEXT, event_year TEXT, decision_type TEXT
                )
            """)
            conn.execute("""
                CREATE TABLE judge_appearances (
                    judge_name TEXT, fight TEXT, event_year TEXT, decision_type TEXT,
                    disagreed_with_both INT, disagreed_on_score INT
                )
            """)
            conn.commit()
        finally:
            conn.close()

        out_dir = tmp_path / "out1"
        out_dir.mkdir(parents=True, exist_ok=True)
        target_json = out_dir / "data.json"
        monkeypatch.setattr("src.export_web_data.OUTPUT_JSON_PATH", target_json)
        monkeypatch.setattr("src.export_web_data.OUTPUT_DIR", out_dir)
        out_json = export_web_data(empty_db)
        assert out_json.exists()
        with open(out_json, "r", encoding="utf-8") as f:
            data = json.load(f)
        assert data["summary"]["total_fights"] == 0
        assert data["judges"] == []
        assert data["recent_dissents"] == []

    def test_export_web_data_with_non_digit_years(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        import sqlite3

        db = tmp_path / "years_test.db"
        conn = sqlite3.connect(db)
        try:
            conn.execute("""
                CREATE TABLE fights (
                    decision_id TEXT, event_id TEXT, event_year TEXT, decision_type TEXT,
                    has_dissenter INT, event_date TEXT, fighter_1 TEXT, fighter_2 TEXT, outcome TEXT
                )
            """)
            conn.execute("""
                CREATE TABLE judge_appearances (
                    judge_name TEXT, fight TEXT, event_year TEXT, decision_type TEXT,
                    disagreed_with_both INT, disagreed_on_score INT
                )
            """)
            conn.execute("""
                CREATE TABLE round_scores (
                    decision_id TEXT, round_num INT, judge_name TEXT, event_year TEXT,
                    round_pick TEXT, colleagues_agreed INT, round_dissented INT, is_ten_eight INT,
                    fight TEXT, score_f1 INT, score_f2 INT, colleague_1 TEXT, colleague_2 TEXT,
                    is_finish INT, finish_round INT, finish_method TEXT
                )
            """)
            conn.execute(
                "INSERT INTO fights VALUES ('1', '10', 'UnknownYear', 'Split Decision', 1, '2024-01-01', 'Fighter 1', 'Fighter 2', 'def')"
            )
            conn.execute(
                "INSERT INTO judge_appearances VALUES ('Judge X', 'Fight 1', 'UnknownYear', 'Split Decision', 1, 0)"
            )
            conn.execute(
                "INSERT INTO round_scores VALUES ('1', 1, 'Judge X', 'NonDigit', 'fighter_1', 1, 1, 0, 'Fight 1', 10, 9, 'Judge Y', 'Judge Z', 0, NULL, NULL)"
            )
            conn.commit()
        finally:
            conn.close()

        out_dir = tmp_path / "out2"
        out_dir.mkdir(parents=True, exist_ok=True)
        target_json = out_dir / "data.json"
        monkeypatch.setattr("src.export_web_data.OUTPUT_JSON_PATH", target_json)
        monkeypatch.setattr("src.export_web_data.OUTPUT_DIR", out_dir)
        out_json = export_web_data(db)
        assert out_json.exists()
        with open(out_json, "r", encoding="utf-8") as f:
            data = json.load(f)
        assert data["summary"]["total_fights"] == 1

    def test_build_dashboard_missing_data_raises(self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
        from src import build_dashboard

        monkeypatch.setattr(build_dashboard, "WEB_DATA_PATH", tmp_path / "non_existent.json")
        with pytest.raises(FileNotFoundError):
            build_dashboard.build_dashboard_html()
