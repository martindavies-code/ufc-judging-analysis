"""Unit tests for asynchronous decision scorecards downloader."""

from unittest.mock import MagicMock, patch

import pytest
import requests

from src.download_decisions import download_all_decisions, download_single_decision


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
                dec_id, success, reason = download_single_decision(
                    (1516, "https://mmadecisions.com/decision/1516/test")
                )
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
                dec_id, success, reason = download_single_decision(
                    (99999, "https://mmadecisions.com/decision/99999/missing")
                )
                assert dec_id == 99999
                assert success is False
                assert "404" in reason

    def test_download_all_decisions_empty_list(self, tmp_path):
        mock_csv = tmp_path / "empty_scorecards.csv"
        mock_csv.write_text("decision_id,decision_url\n", encoding="utf-8")
        with (
            patch("src.download_decisions.SCORECARDS_CSV", mock_csv),
            patch("src.download_decisions.DECISIONS_HTML_DIR", tmp_path),
        ):
            res = download_all_decisions(max_workers=2)
            assert res == (0, 0, 0)

    def test_download_all_decisions_missing_csv_raises(self, tmp_path):
        with (
            patch("src.download_decisions.SCORECARDS_CSV", tmp_path / "missing.csv"),
            pytest.raises(FileNotFoundError),
        ):
            download_all_decisions()

    def test_download_all_decisions_reverse_and_slice(self, tmp_path):
        mock_csv = tmp_path / "scorecards.csv"
        mock_csv.write_text(
            "decision_id,decision_url\n101,https://mmadecisions.com/decision/101/a\n102,https://mmadecisions.com/decision/102/b\n103,https://mmadecisions.com/decision/103/c\n",
            encoding="utf-8",
        )

        # Pre-cache 102
        (tmp_path / "102.html").write_text("X" * 1200, encoding="utf-8")

        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.text = "<html>" + ("Y" * 1100) + "</html>"

        mock_session = MagicMock()
        mock_session.get.return_value = mock_resp

        with (
            patch("src.download_decisions.SCORECARDS_CSV", mock_csv),
            patch("src.download_decisions.DECISIONS_HTML_DIR", tmp_path),
            patch("src.download_decisions.get_thread_session", return_value=mock_session),
        ):
            # Test reverse=True, start_idx=0, end_idx=2 (items 103, 102)
            success, cached, failed = download_all_decisions(max_workers=2, reverse=True, start_idx=0, end_idx=2)
            assert success == 1
            assert cached == 1
            assert failed == 0

    def test_download_single_decision_request_exception(self, tmp_path):
        with patch("src.download_decisions.DECISIONS_HTML_DIR", tmp_path):
            mock_session = MagicMock()
            mock_session.get.side_effect = requests.RequestException("Network timeout")

            with patch("src.download_decisions.get_thread_session", return_value=mock_session):
                dec_id, success, reason = download_single_decision((555, "https://mmadecisions.com/decision/555/err"))
                assert dec_id == 555
                assert success is False
                assert "Network timeout" in reason

    def test_main_cli_execution(self, monkeypatch):
        import runpy
        import sys

        monkeypatch.setattr(sys, "argv", ["download_decisions.py", "--reverse", "--workers=4", "--start=0", "--end=0"])
        # Running with start=0, end=0 executes CLI parser and downloads 0 items without network calls
        runpy.run_module("src.download_decisions", run_name="__main__")
