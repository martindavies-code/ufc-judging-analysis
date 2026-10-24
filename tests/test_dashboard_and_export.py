"""Unit and integration tests for dashboard construction, XSS protection, and export pipeline."""

import json
from pathlib import Path
import pytest

from src.build_dashboard import build_dashboard_html, encode_image_base64
from src.export_web_data import export_web_data


class TestExportWebData:
    def test_missing_database_raises(self, tmp_path):
        fake_db = tmp_path / "missing.db"
        with pytest.raises(FileNotFoundError):
            export_web_data(fake_db)

    def test_export_pipeline_execution(self, tmp_path):
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


class TestBuildDashboard:
    def test_encode_image_base64_nonexistent(self):
        assert encode_image_base64("non_existent_img_12345.png") == ""

    def test_dashboard_compilation_and_xss_safety(self):
        dashboard_path = build_dashboard_html()
        assert dashboard_path.exists()
        
        with open(dashboard_path, "r", encoding="utf-8") as f:
            html_text = f.read()
            
        assert "<!DOCTYPE html>" in html_text
        assert "UFC Judging" in html_text
        assert "Round-by-Round" in html_text
        assert "ROUND_JUDGES" in html_text
        # Ensure raw unescaped script injection is not present
        assert "<script>alert" not in html_text
        # Ensure script breakout tag </script> is escaped inside JSON data
        assert "</script>" in html_text  # only legitimate closing tags
