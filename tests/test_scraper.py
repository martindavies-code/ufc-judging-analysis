"""Unit tests for scraper resiliency, atomic writes, and path traversal validation."""

from pathlib import Path
from unittest.mock import MagicMock, patch
import pytest

from src.scraper import (
    atomic_write_text,
    download_single_event,
    fetch_events_for_year,
    get_available_years,
)


class TestAtomicWriteText:
    def test_successful_atomic_write(self, tmp_path):
        target = tmp_path / "test_file.txt"
        atomic_write_text(target, "Hello UFC World")
        assert target.exists()
        assert target.read_text(encoding="utf-8") == "Hello UFC World"

    def test_overwrite_atomic_write(self, tmp_path):
        target = tmp_path / "overwrite.txt"
        target.write_text("Old content")
        atomic_write_text(target, "New content")
        assert target.read_text(encoding="utf-8") == "New content"


class TestDownloadSingleEvent:
    def test_cached_event_skip(self, tmp_path, monkeypatch):
        # Point EVENTS_HTML_DIR to tmp_path
        monkeypatch.setattr("src.scraper.EVENTS_HTML_DIR", tmp_path)
        cached_file = tmp_path / "1516.html"
        cached_file.write_text("A" * 1500) # > 1000 bytes

        eid, ok, status = download_single_event({'event_id': '1516', 'url': 'http://example.com'})
        assert eid == "1516"
        assert ok is True
        assert status == "cached"

    def test_path_traversal_event_id_raises(self, tmp_path, monkeypatch):
        monkeypatch.setattr("src.scraper.EVENTS_HTML_DIR", tmp_path)
        with pytest.raises(ValueError, match="numeric digits"):
            download_single_event({'event_id': '../../etc/passwd', 'url': 'http://example.com'})


class TestFetchEventsForYear:
    @patch("src.scraper.get_thread_session")
    def test_fetch_events_filtering(self, mock_get_session):
        mock_session = MagicMock()
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = """
        <html>
            <a href="event/1516/UFC-310-Pantoja-vs-Asakura">UFC 310: Pantoja vs. Asakura</a>
            <a href="event/1515/Bellator-Champions-Series">Bellator Champions Series</a>
        </html>
        """
        mock_session.get.return_value = mock_response
        mock_get_session.return_value = mock_session

        events = fetch_events_for_year("2024")
        assert len(events) == 1
        assert events[0]['event_id'] == "1516"
        assert "UFC 310" in events[0]['title']

    @patch("src.scraper.get_thread_session")
    def test_fetch_events_http_error(self, mock_get_session):
        mock_session = MagicMock()
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_session.get.return_value = mock_response
        mock_get_session.return_value = mock_session

        events = fetch_events_for_year("2024")
        assert events == []


class TestDownloadAllEvents:
    def test_download_single_event_successful_fetch(self, tmp_path, monkeypatch):
        monkeypatch.setattr("src.scraper.EVENTS_HTML_DIR", tmp_path)
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.text = "<html>Valid event page... " + ("X" * 1200) + "</html>"

        mock_session = MagicMock()
        mock_session.get.return_value = mock_resp

        with patch("src.scraper.get_thread_session", return_value=mock_session):
            eid, ok, status = download_single_event({
                'event_id': '1516',
                'url': 'https://mmadecisions.com/event/1516/test'
            })
            assert eid == '1516'
            assert ok is True
            assert status == 'downloaded'
            assert (tmp_path / "1516.html").exists()

    def test_download_single_event_ssrf_protection(self, tmp_path, monkeypatch):
        monkeypatch.setattr("src.scraper.EVENTS_HTML_DIR", tmp_path)
        with pytest.raises(ValueError, match="Prohibited target host"):
            download_single_event({
                'event_id': '1516',
                'url': 'http://127.0.0.1/admin'
            })

