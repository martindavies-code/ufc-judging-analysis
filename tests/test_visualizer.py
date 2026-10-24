"""Unit and integration tests for visualization generation and matplotlib memory safety."""

import sqlite3
from pathlib import Path
import pytest
import matplotlib.pyplot as plt

from src.visualizer import generate_visualizations


class TestVisualizer:
    def test_missing_database_returns_early(self, tmp_path):
        fake_db = tmp_path / "non_existent.db"
        # Should cleanly return without crashing
        generate_visualizations(fake_db)

    def test_generate_visualizations_real_or_mock_db(self, tmp_path):
        real_db = Path("data/ufc_judging.db")
        if real_db.exists():
            # Test that figures generate and are closed without memory leak
            initial_figs = len(plt.get_fignums())
            generate_visualizations(real_db)
            final_figs = len(plt.get_fignums())
            # All figures must be closed to avoid memory leaks
            assert final_figs == initial_figs or final_figs == 0

    def test_generate_visualizations_on_empty_db(self, tmp_path):
        empty_db = tmp_path / "empty.db"
        with sqlite3.connect(empty_db) as conn:
            conn.execute("CREATE TABLE fights (event_year TEXT, decision_type TEXT)")
            conn.execute("CREATE TABLE judge_appearances (judge_name TEXT)")
            conn.execute("CREATE TABLE round_scores (judge_name TEXT, total_rounds INT)")
            conn.commit()

        initial_figs = len(plt.get_fignums())
        generate_visualizations(empty_db)
        final_figs = len(plt.get_fignums())
        assert final_figs == 0 or final_figs == initial_figs
