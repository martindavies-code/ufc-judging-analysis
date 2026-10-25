"""Unit tests for scraper resiliency, atomic writes, and path traversal validation."""

from unittest.mock import MagicMock, patch

import pytest
import requests

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
        cached_file.write_text("A" * 1500)  # > 1000 bytes

        eid, ok, status = download_single_event({"event_id": "1516", "url": "http://example.com"})
        assert eid == "1516"
        assert ok is True
        assert status == "cached"

    def test_path_traversal_event_id_raises(self, tmp_path, monkeypatch):
        monkeypatch.setattr("src.scraper.EVENTS_HTML_DIR", tmp_path)
        with pytest.raises(ValueError, match="numeric digits"):
            download_single_event({"event_id": "../../etc/passwd", "url": "http://example.com"})


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
        assert events[0]["event_id"] == "1516"
        assert "UFC 310" in events[0]["title"]

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
            eid, ok, status = download_single_event(
                {"event_id": "1516", "url": "https://mmadecisions.com/event/1516/test"}
            )
            assert eid == "1516"
            assert ok is True
            assert status == "downloaded"
            assert (tmp_path / "1516.html").exists()

    def test_download_single_event_ssrf_protection(self, tmp_path, monkeypatch):
        monkeypatch.setattr("src.scraper.EVENTS_HTML_DIR", tmp_path)
        with pytest.raises(ValueError, match="Prohibited target host"):
            download_single_event({"event_id": "1516", "url": "http://127.0.0.1/admin"})

    def test_download_single_event_request_exception(self, tmp_path, monkeypatch):
        monkeypatch.setattr("src.scraper.EVENTS_HTML_DIR", tmp_path)
        mock_session = MagicMock()
        mock_session.get.side_effect = requests.RequestException("Event fetch failed")
        with patch("src.scraper.get_thread_session", return_value=mock_session):
            eid, ok, status = download_single_event(
                {"event_id": "999", "url": "https://mmadecisions.com/event/999/fail"}
            )
            assert eid == "999"
            assert ok is False
            assert "Event fetch failed" in status

    def test_get_available_years_success(self):
        mock_session = MagicMock()
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.text = """
        <html>
            <a href="/decisions-by-event/2024/">2024</a>
            <a href="/decisions-by-event/2023/">2023</a>
        </html>
        """
        mock_session.get.return_value = mock_resp
        with patch("src.scraper.get_thread_session", return_value=mock_session):
            years = get_available_years()
            assert "2024" in years
            assert "2023" in years
            assert "2026" in years

    def test_get_available_years_fallback_on_exception(self):
        mock_session = MagicMock()
        mock_session.get.side_effect = requests.RequestException("Archive failure")
        with patch("src.scraper.get_thread_session", return_value=mock_session):
            years = get_available_years()
            assert len(years) > 20
            assert "2026" in years
            assert "1995" in years

    def test_get_all_ufc_events(self, tmp_path, monkeypatch):
        mock_json = tmp_path / "events.json"
        monkeypatch.setattr("src.scraper.EVENTS_JSON_PATH", mock_json)
        with (
            patch("src.scraper.get_available_years", return_value=["2024"]),
            patch(
                "src.scraper.fetch_events_for_year",
                return_value=[
                    {
                        "event_id": "101",
                        "title": "UFC 300",
                        "slug": "ufc-300",
                        "year": "2024",
                        "url": "https://mmadecisions.com/event/101/",
                    }
                ],
            ),
        ):
            from src.scraper import get_all_ufc_events

            events = get_all_ufc_events(max_workers=1)
            assert len(events) == 1
            assert events[0]["event_id"] == "101"
            assert mock_json.exists()

    def test_download_all_events(self, tmp_path, monkeypatch):
        monkeypatch.setattr("src.scraper.EVENTS_HTML_DIR", tmp_path)
        events = [
            {"event_id": "101", "url": "https://mmadecisions.com/event/101/"},
            {"event_id": "102", "url": "https://mmadecisions.com/event/102/"},
        ]
        # Pre-cache 101
        (tmp_path / "101.html").write_text("Z" * 1500, encoding="utf-8")

        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.text = "<html>" + ("K" * 1200) + "</html>"
        mock_session = MagicMock()
        mock_session.get.return_value = mock_resp

        with patch("src.scraper.get_thread_session", return_value=mock_session):
            from src.scraper import download_all_events

            success, cached, failed = download_all_events(events, max_workers=2)
            assert success == 1
            assert cached == 1
            assert failed == 0
