"""Unit tests for asynchronous decision scorecards downloader."""

from pathlib import Path
from unittest.mock import MagicMock, patch
import pytest
import requests

from src.download_decisions import download_single_decision, download_all_decisions


class TestDownloadDecisions:
    def test_download_cached_file(self, tmp_path):
        with patch("src.download_decisions.DECISIONS_HTML_DIR", tmp_path):
            test_file = tmp_path / "1516.html"
            test_file.write_text("A" * 900, encoding="utf-8")

            dec_id, success, reason = download_single_decision((1516, "https://mmadecisions.com/decision/1516/test"))
            assert dec_id == 1516
            assert success is True
            assert reason == "cached"

    def test_download_ssrf_attempt_fails(self, tmp_path):
        with patch("src.download_decisions.DECISIONS_HTML_DIR", tmp_path):
            dec_id, success, reason = download_single_decision((1516, "http://169.254.169.254/latest/meta-data"))
            assert dec_id == 1516
            assert success is False
            assert "SSRF" in reason or "Prohibited" in reason or "Untrusted" in reason

    def test_download_successful_request(self, tmp_path):
        with patch("src.download_decisions.DECISIONS_HTML_DIR", tmp_path):
            mock_resp = MagicMock()
            mock_resp.status_code = 200
            mock_resp.text = "<html>Valid scorecard content... " + ("X" * 900) + "</html>"

            mock_session = MagicMock()
            mock_session.get.return_value = mock_resp

            with patch("src.download_decisions.get_thread_session", return_value=mock_session):
                dec_id, success, reason = download_single_decision((1516, "https://mmadecisions.com/decision/1516/test"))
                assert dec_id == 1516
                assert success is True
                assert reason == "downloaded"
                saved_file = tmp_path / "1516.html"
                assert saved_file.exists()

    def test_download_404_response(self, tmp_path):
        with patch("src.download_decisions.DECISIONS_HTML_DIR", tmp_path):
            mock_resp = MagicMock()
            mock_resp.status_code = 404

            mock_session = MagicMock()
            mock_session.get.return_value = mock_resp

            with patch("src.download_decisions.get_thread_session", return_value=mock_session):
                dec_id, success, reason = download_single_decision((99999, "https://mmadecisions.com/decision/99999/missing"))
                assert dec_id == 99999
                assert success is False
                assert "404" in reason

    def test_download_all_decisions_empty_list(self, tmp_path):
        mock_csv = tmp_path / "empty_scorecards.csv"
        mock_csv.write_text("decision_id,decision_url\n", encoding="utf-8")
        with patch("src.download_decisions.SCORECARDS_CSV", mock_csv), \
             patch("src.download_decisions.DECISIONS_HTML_DIR", tmp_path):
            res = download_all_decisions(max_workers=2)
            assert res == (0, 0, 0)
