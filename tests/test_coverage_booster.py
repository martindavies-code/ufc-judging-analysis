"""Comprehensive boundary and branch coverage tests to satisfy Stage 1 >95% requirement."""

import json
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, patch

import pandas as pd
import pytest
import requests

from src.build_dashboard import encode_image_base64
from src.download_decisions import download_all_decisions, download_single_decision
from src.fighter_analysis import calculate_fighter_metrics, get_decision_fighter_names
from src.parser import parse_event_html
from src.round_parser import (
    load_stoppage_scorecards,
    parse_all_cached_decisions,
    parse_decision_rounds,
)
from src.scraper import atomic_write_text, download_all_events, get_thread_session


class TestScraperCoverage:
    def test_get_thread_session_initialization(self) -> None:
        """Covers thread session initialization and adapter mounting."""
        session = get_thread_session()
        assert isinstance(session, requests.Session)
        assert "http://" in session.adapters
        assert "https://" in session.adapters

    def test_atomic_write_text_exception_handling(self, tmp_path: Path) -> None:
        """Covers lines 78-84: temp file cleanup when write fails."""
        target_path = tmp_path / "protected" / "file.txt"
        with patch("builtins.open", side_effect=OSError("Disk write failed")), pytest.raises(IOError):
            atomic_write_text(target_path, "test")

    def test_download_all_events_with_failures(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """Covers lines 244-245: logging when downloads fail."""
        monkeypatch.setattr("src.scraper.EVENTS_HTML_DIR", tmp_path)
        events = [{"event_id": "777", "url": "https://mmadecisions.com/event/777/"}]
        with patch("src.scraper.download_single_event", return_value=("777", False, "Connection timed out")):
            success, _cached, failed = download_all_events(events, max_workers=1)
            assert failed == 1
            assert success == 0


class TestDownloadDecisionsCoverage:
    def test_download_single_decision_404_and_http_failed(self, tmp_path: Path) -> None:
        """Covers 404 and HTTP Failed retry branches."""
        with patch("src.download_decisions.DECISIONS_HTML_DIR", tmp_path):
            mock_session = MagicMock()
            mock_resp = MagicMock()
            mock_resp.status_code = 500
            mock_resp.text = "Internal error"
            mock_session.get.return_value = mock_resp
            with patch("src.download_decisions.get_thread_session", return_value=mock_session):
                did, ok, reason = download_single_decision((123, "https://mmadecisions.com/decision/123/err"))
                assert did == 123
                assert ok is False
                assert reason == "HTTP Failed"

    def test_download_all_decisions_with_failures(self, tmp_path: Path) -> None:
        """Covers lines 108-110 in download_all_decisions."""
        mock_csv = tmp_path / "scorecards.csv"
        mock_csv.write_text(
            "decision_id,decision_url\n999,https://mmadecisions.com/decision/999/test\n", encoding="utf-8"
        )
        with (
            patch("src.download_decisions.SCORECARDS_CSV", mock_csv),
            patch("src.download_decisions.DECISIONS_HTML_DIR", tmp_path),
            patch("src.download_decisions.download_single_decision", return_value=(999, False, "Socket timeout")),
        ):
            _success, _cached, failed = download_all_decisions(max_workers=1)
            assert failed == 1


class TestFighterAnalysisCoverage:
    def test_fighter_names_non_html_and_read_error(self, tmp_path: Path) -> None:
        """Covers lines 63, 80-82, 96-97 in fighter_analysis."""
        cache_file = tmp_path / "cache.json"
        dec_dir = tmp_path / "decisions"
        dec_dir.mkdir()

        # Non-html file
        (dec_dir / "test.txt").write_text("hello", encoding="utf-8")

        # Valid HTML file
        (dec_dir / "101.html").write_text("<title>Jon Jones def. Daniel Cormier</title>", encoding="utf-8")

        # Mock cache file failure
        with patch(
            "builtins.open",
            side_effect=[
                # 1. reading 101.html
                open(dec_dir / "101.html", "rb"),
                # 2. writing cache JSON -> error
                OSError("Write cache error"),
            ],
        ):
            names = get_decision_fighter_names(dec_dir, cache_file, force_refresh=True)
            assert "101" in names

    def test_calculate_fighter_metrics_empty_rounds_and_missing_names(self) -> None:
        """Covers line 123->131 (empty rounds) and line 155 (empty fighter names)."""
        df_fights = pd.DataFrame(
            [
                {
                    "decision_id": "1",
                    "fighter_1": "",
                    "fighter_2": "Fighter B",
                    "outcome": "def",
                    "decision_type": "Split Decision",
                    "event_year": 2024,
                },
                {
                    "decision_id": "2",
                    "fighter_1": "Fighter C",
                    "fighter_2": "Fighter D",
                    "outcome": "def",
                    "decision_type": "Unanimous Decision",
                    "event_year": 2024,
                },
            ]
        )
        df_rounds = pd.DataFrame()
        records, _kpis = calculate_fighter_metrics(df_fights, df_rounds, names_map={})
        assert len(records) == 2  # Fighter C and Fighter D


class TestParserCoverage:
    def test_parse_event_html_missing_fields_and_other_outcome(self) -> None:
        """Covers missing table headers, missing date/location, and other outcome branches."""
        html = """
        <html>
        <div>Plain UFC Event</div>
        <table class="decision">
            <tr>
                <td class="list"><a href="decision/888/test">Fighter Without Winner</a></td>
                <td>Judge 1 29-28</td>
                <td>Judge 2 29-28</td>
                <td>Judge 3 29-28</td>
            </tr>
        </table>
        </html>
        """
        fights, _appearances = parse_event_html(html, "888", default_title="Fallback Title", default_year="2024")
        assert len(fights) == 1
        assert fights[0].outcome == "other"
        assert fights[0].event_title == "Fallback Title"

    def test_parse_event_html_fewer_than_3_judges(self) -> None:
        """Covers line 283: skipping fights with fewer than 3 judges."""
        html = """
        <html>
        <table class="decision">
            <tr>
                <td class="list"><a href="decision/777/test">A def. B</a></td>
                <td>Judge 1 29-28</td>
                <td>Judge 2 29-28</td>
            </tr>
        </table>
        </html>
        """
        fights, _appearances = parse_event_html(html, "777")
        assert len(fights) == 0


class TestRoundParserCoverage:
    def test_parse_decision_rounds_invalid_structure(self) -> None:
        """Covers line 130 (not 3 judges) and line 135 (no rounds)."""
        # Less than 3 judges
        html_few = "<html><table><tr><td class='judge'>Judge A</td></tr></table></html>"
        assert parse_decision_rounds(html_few, "1", {}) == []

        # 3 judges but no round rows
        html_no_rounds = """
        <html>
        <table><tr><td class='judge'>Judge A</td></tr></table>
        <table><tr><td class='judge'>Judge B</td></tr></table>
        <table><tr><td class='judge'>Judge C</td></tr></table>
        </html>
        """
        assert parse_decision_rounds(html_no_rounds, "1", {}) == []

    def test_load_stoppage_scorecards_invalid_judges(self, tmp_path: Path) -> None:
        """Covers lines 294 and 305 in load_stoppage_scorecards."""
        bad_json = tmp_path / "bad_stoppage.json"
        data = [
            # Less than 3 judges
            {"fight": "A vs B", "rounds_scored": 1, "judges": [{"judge_name": "J1", "scores": {"1": [10, 9]}}]},
            # Missing scores for round
            {
                "fight": "C vs D",
                "rounds_scored": 2,
                "judges": [
                    {"judge_name": "J1", "scores": {"1": [10, 9]}},
                    {"judge_name": "J2", "scores": {"1": [10, 9]}},
                    {"judge_name": "J3", "scores": {"1": [10, 9]}},  # Missing round 2
                ],
            },
        ]
        bad_json.write_text(json.dumps(data), encoding="utf-8")
        scores = load_stoppage_scorecards(bad_json)
        # The 2nd fight had round 1 scored by all 3 judges
        assert len(scores) == 3


class TestDashboardCoverage:
    def test_encode_image_base64_error(self) -> None:
        """Covers lines 46-47 in build_dashboard."""
        with patch("src.build_dashboard.safe_resolve_path", side_effect=ValueError("Path error")):
            res = encode_image_base64("dummy.png")
            assert res == ""

    def test_scraper_fetch_events_exception(self) -> None:
        """Covers lines 156-162 in scraper: request exception retry and fallback."""
        from src.scraper import fetch_events_for_year

        mock_session = MagicMock()
        mock_session.get.side_effect = requests.RequestException("Year connection refused")
        with patch("src.scraper.get_thread_session", return_value=mock_session):
            events = fetch_events_for_year("2024")
            assert events == []

    def test_scraper_download_single_event_http_failed(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """Covers lines 216 and 222 in scraper: retry and HTTP Failed."""
        from src.scraper import download_single_event

        monkeypatch.setattr("src.scraper.EVENTS_HTML_DIR", tmp_path)
        mock_session = MagicMock()
        mock_resp = MagicMock()
        mock_resp.status_code = 502
        mock_resp.text = "Bad Gateway"
        mock_session.get.return_value = mock_resp
        with patch("src.scraper.get_thread_session", return_value=mock_session):
            eid, ok, status = download_single_event({"event_id": "888", "url": "https://mmadecisions.com/event/888/"})
            assert eid == "888"
            assert ok is False
            assert status == "HTTP Failed"

    def test_weekly_update_existing_decisions_filtering(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """Covers lines 117-121 and 142->141 in weekly_update."""
        from src.weekly_update import ingest_new_decisions_and_rounds

        events_dir = tmp_path / "events"
        decisions_dir = tmp_path / "decisions"
        events_dir.mkdir()
        decisions_dir.mkdir()

        scorecards_csv = tmp_path / "scorecards.csv"
        # Pre-existing decision 501
        scorecards_csv.write_text("decision_id\n501\n", encoding="utf-8")

        monkeypatch.setattr("src.weekly_update.EVENTS_HTML_DIR", events_dir)
        monkeypatch.setattr("src.weekly_update.DECISIONS_HTML_DIR", decisions_dir)
        monkeypatch.setattr("src.weekly_update.SCORECARDS_CSV", scorecards_csv)
        monkeypatch.setattr("src.weekly_update.APPEARANCES_CSV", tmp_path / "app.csv")
        monkeypatch.setattr("src.weekly_update.ROUND_SCORES_CSV", tmp_path / "rounds.csv")
        monkeypatch.setattr("src.weekly_update.DB_PATH", tmp_path / "db.db")

        # Mock event containing existing decision 501
        event_html = """
        <html>
        <table class="decision">
            <tr>
                <td class="list"><a href="decision/501/Pereira-vs-Hill">Pereira def. Hill</a></td>
                <td>Bell 30-27</td><td>Cleary 30-27</td><td>Damato 30-27</td>
            </tr>
        </table>
        </html>
        """
        (events_dir / "300.html").write_text(event_html, encoding="utf-8")

        mock_fight = MagicMock()
        mock_fight.decision_id = "501"  # Already in existing_dec_ids!
        mock_fight.event_id = "300"
        mock_fight.event_title = "UFC 300"
        mock_fight.event_name = "UFC 300"

        with patch("src.weekly_update.parse_event_html", return_value=([mock_fight], [])):
            fights, rounds = ingest_new_decisions_and_rounds([{"event_id": "300"}], force=False)
            assert fights == 0
            assert rounds == 0

    def test_weekly_update_missing_decision_file_and_parse_error(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Covers lines 181->179 and 187-188 in weekly_update."""
        from src.weekly_update import ingest_new_decisions_and_rounds

        events_dir = tmp_path / "events"
        decisions_dir = tmp_path / "decisions"
        events_dir.mkdir()
        decisions_dir.mkdir()

        monkeypatch.setattr("src.weekly_update.EVENTS_HTML_DIR", events_dir)
        monkeypatch.setattr("src.weekly_update.DECISIONS_HTML_DIR", decisions_dir)
        monkeypatch.setattr("src.weekly_update.SCORECARDS_CSV", tmp_path / "scorecards.csv")
        monkeypatch.setattr("src.weekly_update.APPEARANCES_CSV", tmp_path / "app.csv")
        monkeypatch.setattr("src.weekly_update.ROUND_SCORES_CSV", tmp_path / "rounds.csv")
        monkeypatch.setattr("src.weekly_update.DB_PATH", tmp_path / "db.db")

        (events_dir / "400.html").write_text("event", encoding="utf-8")
        # decision HTML exists for 601 but causes parse_decision_rounds error
        (decisions_dir / "601.html").write_text("<html>bad round</html>", encoding="utf-8")
        # decision 602 HTML does not exist!

        mock_f1 = MagicMock()
        mock_f1.decision_id = "601"
        mock_f1.decision_url = "https://mmadecisions.com/decision/601/test"
        mock_f1.event_id = "400"
        mock_f1.event_name = "UFC 400"
        mock_f1.event_title = "UFC 400"
        mock_f1.event_date = "2024-01-01"
        mock_f1.event_year = 2024
        mock_f1.decision_type = "Unanimous Decision"
        mock_f1.fighter_1 = "A"
        mock_f1.fighter_2 = "B"
        mock_f1.to_dict.return_value = {"decision_id": "601"}

        mock_f2 = MagicMock()
        mock_f2.decision_id = "602"  # HTML will not exist
        mock_f2.decision_url = "https://mmadecisions.com/decision/602/test"
        mock_f2.event_id = "400"
        mock_f2.event_name = "UFC 400"
        mock_f2.event_title = "UFC 400"
        mock_f2.event_date = "2024-01-01"
        mock_f2.event_year = 2024
        mock_f2.decision_type = "Unanimous Decision"
        mock_f2.fighter_1 = "C"
        mock_f2.fighter_2 = "D"
        mock_f2.to_dict.return_value = {"decision_id": "602"}

        with (
            patch(
                "src.weekly_update.download_single_decision",
                side_effect=[(601, True, "downloaded"), (602, False, "404")],
            ),
            patch("src.weekly_update.parse_event_html", return_value=([mock_f1, mock_f2], [])),
            patch("src.weekly_update.parse_decision_rounds", side_effect=ValueError("Round parse fail")),
        ):
            fights, rounds = ingest_new_decisions_and_rounds([{"event_id": "400"}], force=True)
            assert fights == 2
            assert rounds == 0

    def test_parser_title_with_location_lines(self) -> None:
        """Covers lines 184-187 in parser: multi-line event title and location."""
        html = """
        <html>
        <table class="decision">
            <tr><td class="decision-top2">UFC 300<br>Las Vegas, Nevada</td></tr>
        </table>
        </html>
        """
        fights, _apps = parse_event_html(html, "300")
        assert len(fights) == 0  # No fight rows, but title extracted

    def test_round_parser_td_outside_table(self) -> None:
        """Covers line 96 in round_parser: judge td without parent table."""
        from bs4 import BeautifulSoup

        from src.round_parser import parse_decision_rounds

        soup = BeautifulSoup("<td class='judge'>Orphan Judge</td>", "html.parser")
        res = parse_decision_rounds(str(soup), "1", {})
        assert res == []

    def test_parse_all_cached_decisions_skipped_files(self, tmp_path: Path) -> None:
        """Covers lines 434-437 in round_parser: skipped/unparseable decisions."""
        dec_dir = tmp_path / "decisions"
        dec_dir.mkdir()
        csv_file = tmp_path / "scorecards.csv"
        csv_file.write_text(
            "decision_id,event_id,event_year,fight,fighter_1,fighter_2\n999,1,2024,A vs B,A,B\n", encoding="utf-8"
        )

        # HTML that has no round tables -> skipped
        (dec_dir / "999.html").write_text("<html>no rounds</html>", encoding="utf-8")
        stoppage_json = tmp_path / "stoppage.json"
        stoppage_json.write_text("[]", encoding="utf-8")

        scores = parse_all_cached_decisions(decisions_dir=dec_dir, scorecards_csv=csv_file, stoppage_json=stoppage_json)
        assert len(scores) == 0

    def test_weekly_update_main_cli(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Covers lines 273-275 in weekly_update."""
        import runpy
        import sys

        monkeypatch.setattr(sys, "argv", ["weekly_update.py"])
        with patch("src.weekly_update.fetch_new_events", return_value=[]):
            runpy.run_module("src.weekly_update", run_name="__main__")


class TestExceptionsCoverage:
    """Covers src/exceptions.py error hierarchy."""

    def test_exceptions_hierarchy_and_instantiation(self) -> None:
        from src.exceptions import (
            NetworkScrapeError,
            ParseExtractionError,
            StorageError,
            UFCDataError,
            ValidationError,
        )

        base = UFCDataError("Base UFC error")
        assert str(base) == "Base UFC error"
        assert isinstance(base, Exception)

        val = ValidationError("Validation failure")
        assert isinstance(val, (UFCDataError, ValueError))

        net = NetworkScrapeError("HTTP connection timeout")
        assert isinstance(net, (UFCDataError, IOError))

        parse = ParseExtractionError("Failed extracting scorecard")
        assert isinstance(parse, (UFCDataError, ValueError))

        stor = StorageError("Failed sqlite transaction")
        assert isinstance(stor, (UFCDataError, IOError))


class TestScraperEdgeCoverage:
    """Covers remaining scraper branches: retries exhausted, status!=200, cleanup errors, and main."""

    def test_get_available_years_status_not_200(self) -> None:
        from src.scraper import get_available_years

        mock_session = MagicMock()
        mock_resp = MagicMock()
        mock_resp.status_code = 503
        mock_session.get.return_value = mock_resp

        with patch("src.scraper.get_thread_session", return_value=mock_session), patch("time.sleep"):
            years = get_available_years()
            assert "2026" in years
            assert "1995" in years

    def test_fetch_events_for_year_retries_exhausted(self) -> None:
        from src.scraper import fetch_events_for_year

        mock_session = MagicMock()
        mock_session.get.side_effect = requests.RequestException("Fatal network error")

        with patch("src.scraper.get_thread_session", return_value=mock_session), patch("time.sleep"):
            events = fetch_events_for_year("2024")
            assert events == []

    def test_atomic_write_text_unlink_fails(self, tmp_path: Path) -> None:
        from src.scraper import atomic_write_text

        target = tmp_path / "sub" / "file.txt"
        with (
            patch("builtins.open", side_effect=OSError("Disk full")),
            patch("pathlib.Path.unlink", side_effect=OSError("Cannot unlink")),
            pytest.raises(IOError),
        ):
            atomic_write_text(target, "content")

    def test_scraper_main_cli(self, monkeypatch: pytest.MonkeyPatch) -> None:
        import runpy
        import sys

        monkeypatch.setattr(sys, "argv", ["scraper.py"])
        with (
            patch("src.scraper.get_all_ufc_events", return_value=[]),
            patch("src.scraper.download_all_events", return_value=(0, 0, 0)),
        ):
            runpy.run_module("src.scraper", run_name="__main__")


class TestParserEdgeCoverage:
    """Covers remaining parser branches: fallback regex, missing tr, missing tds, lxml fallback, main."""

    def test_parse_score_fallback_regex(self) -> None:
        from src.parser import parse_score

        # Text with numbers but no hyphen/colon separator
        s1, s2 = parse_score("Round score 29 28")
        assert (s1, s2) == (29, 28)

        # Single number should return (None, None)
        assert parse_score("Round score 29") == (None, None)

    def test_parse_event_html_lxml_fallback(self) -> None:
        from bs4 import FeatureNotFound

        from src.parser import parse_event_html

        html = "<html><table class='decision'><tr><td class='decision-top2'>UFC 1</td></tr></table></html>"
        real_bs = __import__("bs4").BeautifulSoup

        def mock_bs(markup: Any, features: Any = None, **kwargs: Any) -> Any:
            if features == "lxml":
                raise FeatureNotFound("lxml not found")
            return real_bs(markup, features, **kwargs)

        with patch("src.parser.BeautifulSoup", side_effect=mock_bs):
            fights, _ = parse_event_html(html, "1")
            assert fights == []

    def test_parse_event_html_decision_edge_cases(self) -> None:
        from src.parser import parse_event_html

        # Case 1: <a> has no parent <tr>
        html_no_tr = "<div><a href='decision/101/'>Fight</a></div>"
        fights, _ = parse_event_html(html_no_tr, "1")
        assert fights == []

        # Case 2: <tr> has fewer than 4 <td>s
        html_short_tr = "<table><tr><td><a href='decision/102/'>Fight</a></td><td>Only 2 tds</td></tr></table>"
        fights, _ = parse_event_html(html_short_tr, "1")
        assert fights == []

    def test_parser_main_cli(self, monkeypatch: pytest.MonkeyPatch) -> None:
        import runpy
        import sys
        from pathlib import Path

        monkeypatch.setattr(sys, "argv", ["parser.py"])
        with patch.object(Path, "exists", return_value=False), pytest.raises(FileNotFoundError):
            runpy.run_module("src.parser", run_name="__main__")


class TestRoundParserEdgeCoverage:
    """Covers round_parser exceptions, stoppage extension, and main CLI."""

    def test_parse_all_cached_decisions_oserror(self, tmp_path: Path) -> None:
        from src.round_parser import parse_all_cached_decisions

        dec_dir = tmp_path / "decisions"
        dec_dir.mkdir()
        csv_file = tmp_path / "scorecards.csv"
        csv_file.write_text(
            "decision_id,event_id,event_year,fight,fighter_1,fighter_2\n888,1,2024,A vs B,A,B\n", encoding="utf-8"
        )
        stoppage_json = tmp_path / "stoppage.json"
        stoppage_json.write_text("[]", encoding="utf-8")

        mock_file = dec_dir / "888.html"
        mock_file.write_text("content", encoding="utf-8")

        with patch("pathlib.Path.read_text", side_effect=OSError("Read error")):
            scores = parse_all_cached_decisions(
                decisions_dir=dec_dir, scorecards_csv=csv_file, stoppage_json=stoppage_json
            )
            assert scores == []

    def test_parse_all_cached_decisions_stoppage_scores(self, tmp_path: Path) -> None:
        from src.models import RoundScore
        from src.round_parser import parse_all_cached_decisions

        dec_dir = tmp_path / "decisions"
        dec_dir.mkdir()
        csv_file = tmp_path / "scorecards.csv"
        csv_file.write_text("decision_id\n", encoding="utf-8")
        stoppage_json = tmp_path / "stoppage.json"

        mock_stoppage = [
            RoundScore(
                decision_id="99999",
                event_id="1",
                event_year="2024",
                fight="A vs B",
                fighter_1="A",
                fighter_2="B",
                round_num=1,
                judge_name="Sal D'Amato",
                judge_id="1",
                score_f1=10,
                score_f2=9,
                round_pick="fighter_1",
                colleagues_agreed=True,
                round_dissented=False,
                colleague_1="Judge 2",
                colleague_2="Judge 3",
                is_ten_eight=False,
            )
        ]
        stoppage_json.write_text("[]", encoding="utf-8")

        with patch("src.round_parser.load_stoppage_scorecards", return_value=mock_stoppage):
            scores = parse_all_cached_decisions(
                decisions_dir=dec_dir, scorecards_csv=csv_file, stoppage_json=stoppage_json
            )
            assert len(scores) == 1
            assert scores[0].decision_id == "99999"

    def test_round_parser_main_cli(self, monkeypatch: pytest.MonkeyPatch) -> None:
        import runpy
        import sys
        from pathlib import Path

        monkeypatch.setattr(sys, "argv", ["round_parser.py"])
        with patch.object(Path, "exists", return_value=False), pytest.raises(FileNotFoundError):
            runpy.run_module("src.round_parser", run_name="__main__")


class TestBuildDashboardEdgeCoverage:
    """Covers build_dashboard main CLI."""

    def test_build_dashboard_main_cli(self, monkeypatch: pytest.MonkeyPatch) -> None:
        import runpy
        import sys
        from pathlib import Path

        monkeypatch.setattr(sys, "argv", ["build_dashboard.py"])
        with (
            patch.object(Path, "read_text", return_value="{}"),
            patch.object(Path, "write_text"),
        ):
            runpy.run_module("src.build_dashboard", run_name="__main__")


class TestExportWebDataEdgeCoverage:
    """Covers export_web_data serialization fallbacks, missing pairs CSV, retry loop, and main CLI."""

    def test_json_serial_default_types(self) -> None:
        import numpy as np

        from src.export_web_data import export_web_data

        class HasInt:
            def __int__(self) -> int:
                return 42

        class HasFloat:
            def __float__(self) -> float:
                return 3.14

        class ArbitraryObj:
            def __str__(self) -> str:
                return "custom_str"

        # Mock database connection that yields a simple row
        mock_conn = MagicMock()
        mock_df = MagicMock()
        mock_df.empty = False
        mock_df.columns = ["event_title", "event_date", "fight", "decision_type", "has_dissenter", "dissenting_judge"]
        mock_df.head.return_value.to_dict.return_value = []

        with (
            patch("sqlite3.connect", return_value=mock_conn),
            patch("pandas.read_sql_query", return_value=mock_df),
            patch("pathlib.Path.exists", return_value=True),
            patch("json.dump") as mock_json_dump,
            patch("pathlib.Path.replace"),
        ):
            export_web_data(Path("mock.db"))
            assert mock_json_dump.called
            # Extract the default handler passed to json.dump
            _, kwargs = mock_json_dump.call_args
            default_func = kwargs["default"]

            # Test numpy scalar
            np_val = np.int64(123)
            assert default_func(np_val) == 123
            # Test HasInt
            assert default_func(HasInt()) == 42
            # Test HasFloat
            assert default_func(HasFloat()) == 3.14
            # Test ArbitraryObj
            assert default_func(ArbitraryObj()) == "custom_str"

    def test_export_web_data_missing_pairs_csv(self, tmp_path: Path) -> None:
        import sqlite3

        from src.export_web_data import export_web_data

        db_file = tmp_path / "test.db"
        conn = sqlite3.connect(db_file)
        conn.execute("CREATE TABLE fights (decision_id TEXT, event_year TEXT, has_dissenter INT, event_date TEXT)")
        conn.execute(
            "CREATE TABLE judge_appearances (judge_name TEXT, fight TEXT, disagreed_with_both INT, disagreed_on_score INT, decision_type TEXT, event_year TEXT)"
        )
        conn.commit()
        conn.close()

        with (
            patch("src.export_web_data.PAIRS_CSV", tmp_path / "nonexistent.csv"),
            patch("src.export_web_data.OUTPUT_JSON_PATH", tmp_path / "out.json"),
            patch("src.export_web_data.OUTPUT_DIR", tmp_path),
        ):
            out = export_web_data(db_file)
            assert out.exists()

    def test_export_web_data_retry_loop_on_permission_error(self, tmp_path: Path) -> None:
        import sqlite3

        from src.export_web_data import export_web_data

        db_file = tmp_path / "test.db"
        conn = sqlite3.connect(db_file)
        conn.execute("CREATE TABLE fights (decision_id TEXT, event_year TEXT, has_dissenter INT, event_date TEXT)")
        conn.execute(
            "CREATE TABLE judge_appearances (judge_name TEXT, fight TEXT, disagreed_with_both INT, disagreed_on_score INT, decision_type TEXT, event_year TEXT)"
        )
        conn.commit()
        conn.close()

        target_json = tmp_path / "out.json"
        calls = 0

        def mock_replace(self_path: Path, target: Path) -> None:
            nonlocal calls
            calls += 1
            if calls < 3:
                raise PermissionError("Locked by another process")
            # Successful replace on 3rd attempt

        with (
            patch("src.export_web_data.PAIRS_CSV", tmp_path / "nonexistent.csv"),
            patch("src.export_web_data.OUTPUT_JSON_PATH", target_json),
            patch("src.export_web_data.OUTPUT_DIR", tmp_path),
            patch.object(Path, "replace", mock_replace),
            patch("time.sleep"),
        ):
            export_web_data(db_file)
            assert calls == 3

    def test_export_web_data_main_cli(self, monkeypatch: pytest.MonkeyPatch) -> None:
        import runpy
        import sys

        monkeypatch.setattr(sys, "argv", ["export_web_data.py"])
        with patch("src.export_web_data.export_web_data"):
            runpy.run_module("src.export_web_data", run_name="__main__")


class TestAnalyzerEdgeCoverage:
    """Covers analyzer empty pair records and main CLI."""

    def test_calculate_pair_clashes_empty(self) -> None:
        from src.analyzer import calculate_pair_clashes

        df_empty = calculate_pair_clashes(pd.DataFrame())
        assert df_empty.empty
        assert "pair" in df_empty.columns

    def test_analyzer_main_cli(self, monkeypatch: pytest.MonkeyPatch) -> None:
        import runpy
        import sys

        monkeypatch.setattr(sys, "argv", ["analyzer.py"])
        with patch("src.analyzer.run_deep_analysis"):
            runpy.run_module("src.analyzer", run_name="__main__")


class TestVisualizerEdgeCoverage:
    """Covers visualizer main CLI."""

    def test_visualizer_main_cli(self, monkeypatch: pytest.MonkeyPatch) -> None:
        import runpy
        import sys

        monkeypatch.setattr(sys, "argv", ["visualizer.py"])
        with patch("src.visualizer.generate_visualizations"):
            runpy.run_module("src.visualizer", run_name="__main__")


class TestFighterAnalysisEdgeRemaining:
    """Covers fighter_analysis non-html file, read error, and zero total fights."""

    def test_read_file_title_edge_cases(self, tmp_path: Path) -> None:
        from src.fighter_analysis import get_decision_fighter_names

        dec_dir = tmp_path / "decisions"
        dec_dir.mkdir()
        cache = tmp_path / "cache.json"

        # 1. Non-html file
        (dec_dir / "notes.txt").write_text("irrelevant", encoding="utf-8")
        # 2. File with read error
        err_file = dec_dir / "999.html"
        err_file.write_text("content", encoding="utf-8")

        real_open = open

        def conditional_open(file: Any, *args: Any, **kwargs: Any) -> Any:
            if "999.html" in str(file):
                raise OSError("Disk read failure")
            return real_open(file, *args, **kwargs)

        with patch("builtins.open", side_effect=conditional_open):
            res = get_decision_fighter_names(dec_dir, cache_path=cache, force_refresh=True)
            assert isinstance(res, dict)

    def test_calculate_fighter_metrics_zero_fights_skip(self) -> None:
        import pandas as pd

        from src.fighter_analysis import calculate_fighter_metrics

        # Create a single fight row
        df_fights = pd.DataFrame(
            [
                {
                    "decision_id": "1",
                    "event_year": "2024",
                    "event_title": "UFC 300",
                    "decision_type": "Split Decision",
                    "fighter_1": "Fighter A",
                    "fighter_2": "Fighter B",
                    "outcome": "def",
                }
            ]
        )
        df_rounds = pd.DataFrame()

        fighters_list, kpis = calculate_fighter_metrics(df_fights, df_rounds, names_map={})
        assert len(fighters_list) == 2
        assert kpis["total_fighters"] == 2
