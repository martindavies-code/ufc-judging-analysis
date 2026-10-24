"""Unit tests for automated weekly update pipeline."""

import json
from pathlib import Path
from unittest.mock import MagicMock, patch
import pytest

from src.weekly_update import fetch_new_events, ingest_new_decisions_and_rounds, run_weekly_pipeline


class TestWeeklyUpdate:
    def test_run_weekly_pipeline_when_up_to_date(self):
        with patch("src.weekly_update.fetch_new_events", return_value=[]), \
             patch("src.weekly_update.ingest_new_decisions_and_rounds", return_value=(0, 0)):
            res = run_weekly_pipeline(force=False)
            assert res["status"] == "up_to_date"
            assert res["new_events"] == 0
            assert res["new_fights"] == 0
            assert res["new_rounds"] == 0

    def test_run_weekly_pipeline_when_changes_occur(self):
        dummy_event = [{"event_id": "99999", "title": "UFC 999", "url": "https://mmadecisions.com/event/99999/test"}]
        with patch("src.weekly_update.fetch_new_events", return_value=dummy_event), \
             patch("src.weekly_update.ingest_new_decisions_and_rounds", return_value=(1, 3)), \
             patch("src.weekly_update.run_deep_analysis") as mock_analysis, \
             patch("src.weekly_update.generate_visualizations") as mock_vis, \
             patch("src.weekly_update.export_web_data") as mock_export, \
             patch("src.weekly_update.build_dashboard_html") as mock_build:
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
            {"event_id": "101", "title": "UFC 101", "url": "https://mmadecisions.com/event/101/test"}
        ]

        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.text = "<html>Event 101 details</html>"

        mock_session = MagicMock()
        mock_session.get.return_value = mock_resp

        with patch("src.weekly_update.fetch_events_for_year", return_value=scraped_mock), \
             patch("src.weekly_update.get_thread_session", return_value=mock_session):
            new_events = fetch_new_events(target_years=[2024])
            assert len(new_events) == 1
            assert new_events[0]["event_id"] == "101"
            assert (tmp_path / "101.html").exists()

