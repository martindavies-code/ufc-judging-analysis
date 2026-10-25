"""Unit tests for statistical analysis engine and pair clash calculations."""

import sqlite3
from pathlib import Path

import pandas as pd
import pytest

from src.analyzer import (
    calculate_judge_metrics,
    calculate_judge_round_metrics,
    calculate_pair_clashes,
    calculate_round_pair_clashes,
    run_deep_analysis,
)


class TestCalculateJudgeRoundMetrics:
    def test_round_metrics_calculation(self):
        df_rounds = pd.DataFrame(
            [
                {
                    "judge_name": "Ben Cartlidge",
                    "round_num": 1,
                    "colleagues_agreed": True,
                    "round_dissented": True,
                    "is_ten_eight": False,
                    "is_finish": True,
                },
                {
                    "judge_name": "Ben Cartlidge",
                    "round_num": 2,
                    "colleagues_agreed": True,
                    "round_dissented": False,
                    "is_ten_eight": False,
                    "is_finish": True,
                },
                {
                    "judge_name": "Ben Cartlidge",
                    "round_num": 3,
                    "colleagues_agreed": False,
                    "round_dissented": False,
                    "is_ten_eight": True,
                    "is_finish": False,
                },
                {
                    "judge_name": "Derek Cleary",
                    "round_num": 1,
                    "colleagues_agreed": True,
                    "round_dissented": False,
                    "is_ten_eight": False,
                    "is_finish": False,
                },
                {
                    "judge_name": "Derek Cleary",
                    "round_num": 2,
                    "colleagues_agreed": True,
                    "round_dissented": False,
                    "is_ten_eight": False,
                    "is_finish": False,
                },
            ]
        )

        metrics = calculate_judge_round_metrics(df_rounds)
        assert len(metrics) == 2

        ben = metrics[metrics["judge_name"] == "Ben Cartlidge"].iloc[0]
        assert ben["total_rounds"] == 3
        assert ben["consensus_rounds"] == 2
        assert ben["round_dissents"] == 1
        assert pytest.approx(ben["round_dissent_pct"], 0.01) == 33.33
        assert pytest.approx(ben["consensus_dissent_pct"], 0.01) == 50.0
        assert ben["ten_eight_rounds"] == 1
        assert ben["finish_rounds"] == 2
        assert ben["decision_rounds"] == 1

        derek = metrics[metrics["judge_name"] == "Derek Cleary"].iloc[0]
        assert derek["total_rounds"] == 2
        assert derek["round_dissents"] == 0
        assert derek["round_dissent_pct"] == 0.0
        assert derek["finish_rounds"] == 0
        assert derek["decision_rounds"] == 2

    def test_empty_rounds_dataframe(self):
        empty_df = pd.DataFrame(
            columns=["judge_name", "round_num", "colleagues_agreed", "round_dissented", "is_ten_eight"]
        )
        metrics = calculate_judge_round_metrics(empty_df)
        assert metrics.empty
        assert "round_dissent_pct" in metrics.columns


class TestCalculateRoundPairClashes:
    def test_round_pair_clashes(self):
        df_rounds = pd.DataFrame(
            [
                # Round 1 in fight 1: A and B agree (f1), C dissents (f2)
                {"decision_id": "101", "round_num": 1, "judge_name": "Judge A", "round_pick": "fighter_1"},
                {"decision_id": "101", "round_num": 1, "judge_name": "Judge B", "round_pick": "fighter_1"},
                {"decision_id": "101", "round_num": 1, "judge_name": "Judge C", "round_pick": "fighter_2"},
                # Round 2 in fight 1: A, B, and C all agree (f1)
                {"decision_id": "101", "round_num": 2, "judge_name": "Judge A", "round_pick": "fighter_1"},
                {"decision_id": "101", "round_num": 2, "judge_name": "Judge B", "round_pick": "fighter_1"},
                {"decision_id": "101", "round_num": 2, "judge_name": "Judge C", "round_pick": "fighter_1"},
            ]
        )

        pairs = calculate_round_pair_clashes(df_rounds, min_rounds=1)
        assert len(pairs) == 3

        # Judge A & Judge B: disagreed 0 times out of 2 rounds -> 0%
        ab = pairs[pairs["pair"] == "Judge A & Judge B"].iloc[0]
        assert ab["rounds_together"] == 2
        assert ab["round_winner_disagreements"] == 0
        assert ab["round_disagree_pct"] == 0.0

        # Judge A & Judge C: disagreed 1 time out of 2 rounds -> 50%
        ac = pairs[pairs["pair"] == "Judge A & Judge C"].iloc[0]
        assert ac["rounds_together"] == 2
        assert ac["round_winner_disagreements"] == 1
        assert ac["round_disagree_pct"] == 50.0

    def test_empty_round_pair_clashes(self):
        empty_df = pd.DataFrame(columns=["decision_id", "round_num", "judge_name", "round_pick"])
        pairs = calculate_round_pair_clashes(empty_df, min_rounds=1)
        assert pairs.empty


class TestCalculateJudgeMetrics:
    def test_standard_metrics_calculation(self):
        df_judges = pd.DataFrame(
            [
                {
                    "judge_name": "Barry Foley",
                    "fight": "Fight 1",
                    "colleagues_agreed": 1,
                    "disagreed_with_both": 1,
                    "disagreed_on_score": 1,
                },
                {
                    "judge_name": "Barry Foley",
                    "fight": "Fight 2",
                    "colleagues_agreed": 1,
                    "disagreed_with_both": 0,
                    "disagreed_on_score": 0,
                },
                {
                    "judge_name": "Barry Foley",
                    "fight": "Fight 3",
                    "colleagues_agreed": 1,
                    "disagreed_with_both": 0,
                    "disagreed_on_score": 1,
                },
                {
                    "judge_name": "Barry Foley",
                    "fight": "Fight 4",
                    "colleagues_agreed": 1,
                    "disagreed_with_both": 1,
                    "disagreed_on_score": 1,
                },
                {
                    "judge_name": "Adalaide Byrd",
                    "fight": "Fight 1",
                    "colleagues_agreed": 1,
                    "disagreed_with_both": 0,
                    "disagreed_on_score": 0,
                },
            ]
        )

        metrics = calculate_judge_metrics(df_judges)
        assert len(metrics) == 2

        foley = metrics[metrics["judge_name"] == "Barry Foley"].iloc[0]
        assert foley["total_fights"] == 4
        assert foley["outcome_dissents"] == 2
        assert foley["outcome_dissent_pct"] == 50.0
        assert foley["score_dissent_pct"] == 75.0

        byrd = metrics[metrics["judge_name"] == "Adalaide Byrd"].iloc[0]
        assert byrd["total_fights"] == 1
        assert byrd["outcome_dissents"] == 0
        assert byrd["outcome_dissent_pct"] == 0.0

    def test_empty_dataframe_handling(self):
        empty_df = pd.DataFrame(
            columns=["judge_name", "fight", "colleagues_agreed", "disagreed_with_both", "disagreed_on_score"]
        )
        metrics = calculate_judge_metrics(empty_df)
        assert metrics.empty
        assert "outcome_dissent_pct" in metrics.columns


class TestCalculatePairClashes:
    def test_pairwise_clash_calculation(self):
        df_fights = pd.DataFrame(
            [
                {
                    "j1_name": "Sal D'Amato",
                    "j2_name": "Chris Lee",
                    "j3_name": "Derek Cleary",
                    "j1_pick": "fighter_1",
                    "j2_pick": "fighter_1",
                    "j3_pick": "fighter_2",
                    "j1_score": "29-28",
                    "j2_score": "29-28",
                    "j3_score": "28-29",
                },
                {
                    "j1_name": "Sal D'Amato",
                    "j2_name": "Chris Lee",
                    "j3_name": "Derek Cleary",
                    "j1_pick": "fighter_1",
                    "j2_pick": "fighter_2",
                    "j3_pick": "fighter_1",
                    "j1_score": "30-27",
                    "j2_score": "28-29",
                    "j3_score": "29-28",
                },
            ]
        )

        # Test with min_fights=1 to include both pairs
        pairs = calculate_pair_clashes(df_fights, min_fights=1)
        assert not pairs.empty

        # D'Amato & Cleary: Fight 1: picked f1 vs f2 (disagreed), Fight 2: picked f1 vs f1 (agreed) -> 1/2 = 50%
        damato_cleary = pairs[pairs["pair"].str.contains("Derek Cleary & Sal D'Amato")].iloc[0]
        assert damato_cleary["fights_together"] == 2
        assert damato_cleary["pick_disagreements"] == 1
        assert damato_cleary["disagree_pct"] == 50.0

    def test_empty_fights_dataframe(self):
        empty_df = pd.DataFrame(
            columns=[
                "j1_name",
                "j2_name",
                "j3_name",
                "j1_pick",
                "j2_pick",
                "j3_pick",
                "j1_score",
                "j2_score",
                "j3_score",
            ]
        )
        pairs = calculate_pair_clashes(empty_df, min_fights=1)
        assert pairs.empty


class TestRunDeepAnalysis:
    def test_missing_database_raises_filenotfound(self, tmp_path):
        fake_db = tmp_path / "non_existent.db"
        with pytest.raises(FileNotFoundError):
            run_deep_analysis(fake_db)

    def test_run_deep_analysis_real_or_mock(self, tmp_path):
        real_db = Path("data/ufc_judging.db")
        if real_db.exists():
            res = run_deep_analysis(real_db)
            assert "round_judge_stats" in res
            assert "fight_judge_stats" in res
            assert "fight_pair_stats" in res
            assert len(res["round_judge_stats"]) > 0

    def test_run_deep_analysis_synthetic_db(self, tmp_path):
        synth_db = tmp_path / "synth.db"
        conn = sqlite3.connect(synth_db)
        try:
            conn.execute("""
                CREATE TABLE fights (
                    decision_id TEXT, event_id TEXT, event_year TEXT, decision_type TEXT,
                    j1_name TEXT, j2_name TEXT, j3_name TEXT,
                    j1_pick TEXT, j2_pick TEXT, j3_pick TEXT,
                    j1_score TEXT, j2_score TEXT, j3_score TEXT
                )
            """)
            conn.execute("""
                CREATE TABLE judge_appearances (
                    judge_name TEXT, fight TEXT, colleagues_agreed INT, disagreed_with_both INT, disagreed_on_score INT
                )
            """)
            conn.execute("""
                CREATE TABLE round_scores (
                    decision_id TEXT, round_num INT, judge_name TEXT, round_pick TEXT,
                    colleagues_agreed INT, round_dissented INT, is_ten_eight INT
                )
            """)
            conn.commit()
        finally:
            conn.close()

        res = run_deep_analysis(synth_db)
        assert isinstance(res, dict)
        assert res["round_judge_stats"].empty

    def test_run_deep_analysis_without_round_scores_table(self, tmp_path):
        synth_db = tmp_path / "no_rounds.db"
        conn = sqlite3.connect(synth_db)
        try:
            conn.execute("""
                CREATE TABLE fights (
                    decision_id TEXT, event_id TEXT, event_year TEXT, decision_type TEXT,
                    j1_name TEXT, j2_name TEXT, j3_name TEXT,
                    j1_pick TEXT, j2_pick TEXT, j3_pick TEXT,
                    j1_score TEXT, j2_score TEXT, j3_score TEXT
                )
            """)
            conn.execute("""
                CREATE TABLE judge_appearances (
                    judge_name TEXT, fight TEXT, colleagues_agreed INT, disagreed_with_both INT, disagreed_on_score INT
                )
            """)
            conn.commit()
        finally:
            conn.close()

        res = run_deep_analysis(synth_db)
        assert isinstance(res, dict)
        assert res["round_judge_stats"].empty

    def test_judge_round_metrics_without_is_finish_column(self):
        df_rounds = pd.DataFrame(
            [
                {
                    "judge_name": "Judge A",
                    "round_num": 1,
                    "colleagues_agreed": True,
                    "round_dissented": False,
                    "is_ten_eight": False,
                }
            ]
        )
        stats = calculate_judge_round_metrics(df_rounds)
        assert stats.iloc[0]["finish_rounds"] == 0
        assert stats.iloc[0]["decision_rounds"] == 1

    def test_round_pair_clashes_empty_merged(self):
        # Two records with different round numbers, so merge produces no pairs
        df_rounds = pd.DataFrame(
            [
                {"decision_id": "1", "round_num": 1, "judge_name": "Judge A", "round_pick": "fighter_1"},
                {"decision_id": "1", "round_num": 2, "judge_name": "Judge B", "round_pick": "fighter_2"},
            ]
        )
        res = calculate_round_pair_clashes(df_rounds)
        assert res.empty
        assert "round_disagree_pct" in res.columns
