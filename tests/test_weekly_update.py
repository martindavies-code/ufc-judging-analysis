"""Unit tests for automated weekly update pipeline."""

import json
from unittest.mock import MagicMock, patch

import requests

from src.weekly_update import (
    fetch_new_events,
    ingest_new_decisions_and_rounds,
    run_weekly_pipeline,
)


class TestWeeklyUpdate:
    def test_run_weekly_pipeline_when_up_to_date(self):
        with (
            patch("src.weekly_update.fetch_new_events", return_value=[]),
            patch("src.weekly_update.ingest_new_decisions_and_rounds", return_value=(0, 0)),
        ):
            res = run_weekly_pipeline(force=False)
            assert res["status"] == "up_to_date"
            assert res["new_events"] == 0
            assert res["new_fights"] == 0
            assert res["new_rounds"] == 0

    def test_run_weekly_pipeline_when_changes_occur(self):
        dummy_event = [{"event_id": "99999", "title": "UFC 999", "url": "https://mmadecisions.com/event/99999/test"}]
        with (
            patch("src.weekly_update.fetch_new_events", return_value=dummy_event),
            patch("src.weekly_update.ingest_new_decisions_and_rounds", return_value=(1, 3)),
            patch("src.weekly_update.run_deep_analysis") as mock_analysis,
            patch("src.weekly_update.generate_visualizations") as mock_vis,
            patch("src.weekly_update.export_web_data") as mock_export,
            patch("src.weekly_update.build_dashboard_html") as mock_build,
        ):
            res = run_weekly_pipeline(force=False)
            assert res["status"] == "updated"
            assert res["new_events"] == 1
            assert res["new_fights"] == 1
            assert res["new_rounds"] == 3
            mock_analysis.assert_called_once()
            mock_vis.assert_called_once()
            mock_export.assert_called_once()
            mock_build.assert_called_once()

    def test_ingest_no_events_no_force(self):
        fights, rounds = ingest_new_decisions_and_rounds([], force=False)
        assert fights == 0
        assert rounds == 0

    def test_fetch_new_events_discovery(self, tmp_path, monkeypatch):
        fake_events_json = tmp_path / "ufc_events.json"
        fake_events_json.write_text(json.dumps([{"event_id": "100", "title": "UFC 100"}]), encoding="utf-8")
        (tmp_path / "100.html").write_text("X" * 600, encoding="utf-8")
        monkeypatch.setattr("src.weekly_update.EVENTS_JSON_PATH", fake_events_json)
        monkeypatch.setattr("src.weekly_update.EVENTS_HTML_DIR", tmp_path)

        scraped_mock = [
            {"event_id": "100", "title": "UFC 100", "url": "https://mmadecisions.com/event/100/test"},
            {"event_id": "101", "title": "UFC 101", "url": "https://mmadecisions.com/event/101/test"},
        ]

        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.text = "<html>Event 101 details</html>"

        mock_session = MagicMock()
        mock_session.get.return_value = mock_resp

        with (
            patch("src.weekly_update.fetch_events_for_year", return_value=scraped_mock),
            patch("src.weekly_update.get_thread_session", return_value=mock_session),
        ):
            new_events = fetch_new_events(target_years=[2024])
            assert len(new_events) == 1
            assert new_events[0]["event_id"] == "101"
            assert (tmp_path / "101.html").exists()

    def test_ingest_new_decisions_and_rounds_full_flow(self, tmp_path, monkeypatch):
        events_dir = tmp_path / "events"
        decisions_dir = tmp_path / "decisions"
        events_dir.mkdir()
        decisions_dir.mkdir()

        db_path = tmp_path / "test.db"

        monkeypatch.setattr("src.weekly_update.EVENTS_HTML_DIR", events_dir)
        monkeypatch.setattr("src.weekly_update.DECISIONS_HTML_DIR", decisions_dir)
        monkeypatch.setattr("src.weekly_update.DB_PATH", db_path)
        monkeypatch.setattr("src.weekly_update.SCORECARDS_CSV", tmp_path / "scorecards.csv")
        monkeypatch.setattr("src.weekly_update.APPEARANCES_CSV", tmp_path / "appearances.csv")
        monkeypatch.setattr("src.weekly_update.ROUND_SCORES_CSV", tmp_path / "round_scores.csv")

        # Create a mock event HTML
        event_html = """
        <html>
        <div class="decision-top">UFC 300</div>
        <table class="decision">
            <tr>
                <td class="list"><a href="decision/501/Pereira-vs-Hill">Pereira def. Hill</a></td>
                <td class="bottom-cell"><a href="judge/1/Mike-Bell">Mike Bell</a> <span>30-27</span></td>
                <td class="bottom-cell"><a href="judge/2/Derek-Cleary">Derek Cleary</a> <span>30-27</span></td>
                <td class="bottom-cell"><a href="judge/3/Sal-Damato">Sal D'Amato</a> <span>30-27</span></td>
            </tr>
        </table>
        </html>
        """
        (events_dir / "300.html").write_text(event_html, encoding="utf-8")

        # Create a mock decision HTML with rounds
        dec_html = """
        <html>
        <table>
            <tr><td class="judge"><a href="judge/1/">Mike Bell</a></td></tr>
            <tr class="decision"><td>1</td><td>10</td><td>9</td></tr>
            <tr class="decision"><td>2</td><td>10</td><td>9</td></tr>
            <tr class="decision"><td>3</td><td>10</td><td>9</td></tr>
        </table>
        <table>
            <tr><td class="judge"><a href="judge/2/">Derek Cleary</a></td></tr>
            <tr class="decision"><td>1</td><td>10</td><td>9</td></tr>
            <tr class="decision"><td>2</td><td>10</td><td>9</td></tr>
            <tr class="decision"><td>3</td><td>10</td><td>9</td></tr>
        </table>
        <table>
            <tr><td class="judge"><a href="judge/3/">Sal D'Amato</a></td></tr>
            <tr class="decision"><td>1</td><td>10</td><td>9</td></tr>
            <tr class="decision"><td>2</td><td>10</td><td>9</td></tr>
            <tr class="decision"><td>3</td><td>10</td><td>9</td></tr>
        </table>
        </html>
        """
        (decisions_dir / "501.html").write_text(dec_html, encoding="utf-8")

        mock_fight = MagicMock()
        mock_fight.decision_id = "501"
        mock_fight.decision_url = "https://mmadecisions.com/decision/501/test"
        mock_fight.event_id = "300"
        mock_fight.event_name = "UFC 300"
        mock_fight.event_title = "UFC 300"
        mock_fight.event_date = "2024-04-13"
        mock_fight.event_year = 2024
        mock_fight.decision_type = "Unanimous Decision"
        mock_fight.fighter_1 = "Pereira"
        mock_fight.fighter_2 = "Hill"
        mock_fight.to_dict.return_value = {"decision_id": "501", "event_id": "300"}

        mock_app = MagicMock()
        mock_app.to_dict.return_value = {"judge_name": "Mike Bell", "fight": "Pereira def Hill"}

        with (
            patch("src.weekly_update.download_single_decision", return_value=(501, True, "downloaded")),
            patch("src.weekly_update.parse_event_html", return_value=([mock_fight], [mock_app])),
        ):
            new_events = [{"event_id": "300", "title": "UFC 300", "url": "https://mmadecisions.com/event/300/"}]
            fights, rounds = ingest_new_decisions_and_rounds(new_events, force=True)
            assert fights == 1
            assert rounds == 9
            assert (tmp_path / "scorecards.csv").exists()
            assert (tmp_path / "appearances.csv").exists()
            assert (tmp_path / "round_scores.csv").exists()

    def test_fetch_new_events_default_years_and_errors(self, tmp_path, monkeypatch):
        fake_events_json = tmp_path / "corrupt_events.json"
        fake_events_json.write_text("{corrupt...", encoding="utf-8")
        monkeypatch.setattr("src.weekly_update.EVENTS_JSON_PATH", fake_events_json)
        monkeypatch.setattr("src.weekly_update.EVENTS_HTML_DIR", tmp_path)

        mock_session = MagicMock()
        mock_session.get.side_effect = requests.RequestException("Download fail")

        with (
            patch(
                "src.weekly_update.fetch_events_for_year",
                return_value=[
                    {"event_id": "888", "title": "UFC 888", "url": "https://mmadecisions.com/event/888/test"}
                ],
            ),
            patch("src.weekly_update.get_thread_session", return_value=mock_session),
        ):
            new_events = fetch_new_events(target_years=None)
            assert len(new_events) == 2

    def test_ingest_with_existing_scorecards_csv_and_parse_error(self, tmp_path, monkeypatch):
        scorecards_csv = tmp_path / "existing_scorecards.csv"
        scorecards_csv.write_text("decision_id\n501\n", encoding="utf-8")
        monkeypatch.setattr("src.weekly_update.SCORECARDS_CSV", scorecards_csv)
        monkeypatch.setattr("src.weekly_update.EVENTS_HTML_DIR", tmp_path)
        monkeypatch.setattr("src.weekly_update.DECISIONS_HTML_DIR", tmp_path)

        # File that causes an error in parsing
        bad_event = tmp_path / "999.html"
        bad_event.write_text("bad event", encoding="utf-8")

        with patch("src.weekly_update.parse_event_html", side_effect=ValueError("Parsing error")):
            fights, rounds = ingest_new_decisions_and_rounds([{"event_id": "999"}], force=False)
            assert fights == 0
            assert rounds == 0
