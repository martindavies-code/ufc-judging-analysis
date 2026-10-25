"""Unit tests for fighter controversy and split-decision analysis."""

import json
from pathlib import Path

import pandas as pd

from src.fighter_analysis import calculate_fighter_metrics, get_decision_fighter_names


class TestGetDecisionFighterNames:
    def test_cache_hit(self, tmp_path: Path):
        """Should load from existing valid cache JSON without reading HTML files."""
        cache_file = tmp_path / "cache.json"
        decisions_dir = tmp_path / "decisions"
        decisions_dir.mkdir()

        cache_data = {"101": ["Max Holloway", "Alexander Volkanovski"]}
        cache_file.write_text(json.dumps(cache_data), encoding="utf-8")

        res = get_decision_fighter_names(decisions_dir, cache_file, force_refresh=False)
        assert res == {"101": ("Max Holloway", "Alexander Volkanovski")}

    def test_corrupted_cache_fallback(self, tmp_path: Path):
        """Corrupt cache file should trigger rebuild from HTML files."""
        cache_file = tmp_path / "corrupt_cache.json"
        cache_file.write_text("{bad json...", encoding="utf-8")

        decisions_dir = tmp_path / "decisions"
        decisions_dir.mkdir()
        html_file = decisions_dir / "202.html"
        html_file.write_text("<title>Jon Jones def. Daniel Cormier :: UFC 182</title>", encoding="utf-8")

        res = get_decision_fighter_names(decisions_dir, cache_file, force_refresh=False)
        assert "202" in res
        assert res["202"] == ("Jon Jones", "Daniel Cormier")

    def test_missing_decisions_dir(self, tmp_path: Path):
        """If decisions directory does not exist, return existing cache or empty dict."""
        cache_file = tmp_path / "cache.json"
        non_existent_dir = tmp_path / "non_existent"

        res = get_decision_fighter_names(non_existent_dir, cache_file)
        assert res == {}

    def test_parses_various_title_separators(self, tmp_path: Path):
        """Test parsing 'drew with', 'vs.', 'vs', and '&nbsp;' in titles."""
        cache_file = tmp_path / "cache.json"
        decisions_dir = tmp_path / "decisions"
        decisions_dir.mkdir()

        (decisions_dir / "301.html").write_text(
            "<title>Tyron Woodley drew with Stephen Thompson :: UFC 205</title>", encoding="utf-8"
        )
        (decisions_dir / "302.html").write_text(
            "<title>Israel Adesanya vs. Robert Whittaker :: UFC 271</title>", encoding="utf-8"
        )
        (decisions_dir / "303.html").write_text(
            "<title>Conor&nbsp;McGregor vs Nate&nbsp;Diaz</title>", encoding="utf-8"
        )
        (decisions_dir / "not_html.txt").write_text("ignore me", encoding="utf-8")

        res = get_decision_fighter_names(decisions_dir, cache_file, force_refresh=True)
        assert res.get("301") == ("Tyron Woodley", "Stephen Thompson")
        assert res.get("302") == ("Israel Adesanya", "Robert Whittaker")
        assert res.get("303") == ("Conor McGregor", "Nate Diaz")
        assert "not_html" not in res


class TestCalculateFighterMetrics:
    def test_empty_dataframe(self):
        records, kpis = calculate_fighter_metrics(pd.DataFrame(), pd.DataFrame())
        assert records == []
        assert kpis == {}

    def test_fighter_metrics_luck_badges_and_contested(self):
        """Verify calculation of split wins, losses, contested rounds, and luck badges."""
        df_fights = pd.DataFrame(
            [
                # Fighter A wins 2 split decisions vs Fighter B and C -> Net +2 -> Fortunate
                {
                    "decision_id": "1",
                    "fighter_1": "Fighter A",
                    "fighter_2": "Fighter B",
                    "outcome": "def",
                    "decision_type": "Split Decision",
                    "event_year": 2021,
                    "fight": "A def B",
                },
                {
                    "decision_id": "2",
                    "fighter_1": "Fighter A",
                    "fighter_2": "Fighter C",
                    "outcome": "def",
                    "decision_type": "Split Decision",
                    "event_year": 2022,
                    "fight": "A def C",
                },
                # Fighter B loses 2 split decisions (vs A and vs D) -> Net -2 -> Unlucky
                {
                    "decision_id": "3",
                    "fighter_1": "Fighter D",
                    "fighter_2": "Fighter B",
                    "outcome": "def",
                    "decision_type": "Split Decision",
                    "event_year": 2023,
                    "fight": "D def B",
                },
                # Fighter E has 1 split win and 1 split loss -> Net 0 -> Even
                {
                    "decision_id": "4",
                    "fighter_1": "Fighter E",
                    "fighter_2": "Fighter F",
                    "outcome": "def",
                    "decision_type": "Split Decision",
                    "event_year": 2020,
                    "fight": "E def F",
                },
                {
                    "decision_id": "5",
                    "fighter_1": "Fighter G",
                    "fighter_2": "Fighter E",
                    "outcome": "def",
                    "decision_type": "Split Decision",
                    "event_year": 2021,
                    "fight": "G def E",
                },
                # Fighter H has only unanimous fights -> Neutral
                {
                    "decision_id": "6",
                    "fighter_1": "Fighter H",
                    "fighter_2": "Fighter I",
                    "outcome": "def",
                    "decision_type": "Unanimous Decision",
                    "event_year": 2024,
                    "fight": "H def I",
                },
                # A split draw
                {
                    "decision_id": "7",
                    "fighter_1": "Fighter J",
                    "fighter_2": "Fighter K",
                    "outcome": "draw",
                    "decision_type": "Split Draw",
                    "event_year": 2022,
                    "fight": "J drew K",
                },
                # A majority decision
                {
                    "decision_id": "8",
                    "fighter_1": "Fighter L",
                    "fighter_2": "Fighter M",
                    "outcome": "def",
                    "decision_type": "Majority Decision",
                    "event_year": 2023,
                    "fight": "L def M",
                },
            ]
        )

        df_rounds = pd.DataFrame(
            [
                # Fight 1: Round 1 had dissented judge (contested)
                {"decision_id": "1", "round_num": 1, "round_dissented": 1},
                {"decision_id": "1", "round_num": 1, "round_dissented": 0},
                {"decision_id": "1", "round_num": 1, "round_dissented": 0},
                # Fight 1: Round 2 unanimous
                {"decision_id": "1", "round_num": 2, "round_dissented": 0},
                {"decision_id": "1", "round_num": 2, "round_dissented": 0},
                {"decision_id": "1", "round_num": 2, "round_dissented": 0},
            ]
        )

        records, kpis = calculate_fighter_metrics(df_fights, df_rounds)
        rec_map = {r["fighter_name"]: r for r in records}

        # Fighter A check
        assert rec_map["Fighter A"]["split_wins"] == 2
        assert rec_map["Fighter A"]["split_losses"] == 0
        assert rec_map["Fighter A"]["luck_badge"] == "Fortunate"
        assert rec_map["Fighter A"]["contested_rounds"] == 1

        # Fighter B check
        assert rec_map["Fighter B"]["split_losses"] == 2
        assert rec_map["Fighter B"]["luck_badge"] == "Unlucky"

        # Fighter E check
        assert rec_map["Fighter E"]["split_wins"] == 1
        assert rec_map["Fighter E"]["split_losses"] == 1
        assert rec_map["Fighter E"]["luck_badge"] == "Even"

        # Fighter H check
        assert rec_map["Fighter H"]["split_fights"] == 0
        assert rec_map["Fighter H"]["luck_badge"] == "Neutral"

        # Fighter J & K (Split draw)
        assert rec_map["Fighter J"]["split_draws"] == 1
        assert rec_map["Fighter K"]["split_draws"] == 1

        # Fighter L (Majority)
        assert rec_map["Fighter L"]["majority_fights"] == 1
        assert rec_map["Fighter L"]["disagreed_fights"] == 1

        # Check KPIs structure
        assert "total_fighters" in kpis
        assert "overall_split_decision_rate" in kpis
