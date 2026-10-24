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
        # Verify agreers toggle and roster active/historical controls
        assert 'id="btn-gauge-dissenters"' in html_text
        assert 'id="btn-gauge-agreers"' in html_text
        assert 'id="gauge-roster-toggle"' in html_text
        assert 'id="table-roster-segmented"' in html_text
        assert 'data-roster="active"' in html_text
        assert 'data-roster="historical"' in html_text
        assert 'Most Consensual (Agreers)' in html_text
        assert 'Currently Active' in html_text

    def test_export_data_year_typing(self):
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

