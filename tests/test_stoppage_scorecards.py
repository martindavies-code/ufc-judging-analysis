"""Unit tests for curated stoppage scorecards generation."""

import json
from pathlib import Path

from src.create_stoppage_scorecards import (
    STOPPAGE_FIGHTS,
    write_stoppage_scorecards_json,
)


def test_stoppage_fights_structure():
    """Verify all curated stoppage fights have valid schema and scores."""
    assert len(STOPPAGE_FIGHTS) > 0
    for fight in STOPPAGE_FIGHTS:
        assert "fight_id" in fight
        assert "fighter_1" in fight
        assert "fighter_2" in fight
        assert "finish_round" in fight
        assert "rounds_scored" in fight
        assert len(fight["judges"]) == 3
        for judge in fight["judges"]:
            assert "judge_name" in judge
            assert "scores" in judge
            for r_num, (s1, s2) in judge["scores"].items():
                assert int(r_num) <= fight["rounds_scored"]
                assert 7 <= s1 <= 10
                assert 7 <= s2 <= 10


def test_write_stoppage_scorecards_json(tmp_path: Path):
    """Test serializing stoppage scorecards to a target JSON file."""
    output_file = tmp_path / "data" / "stoppage_test.json"
    write_stoppage_scorecards_json(output_file)

    assert output_file.exists()
    with open(output_file, "r", encoding="utf-8") as f:
        loaded = json.load(f)
    assert len(loaded) == len(STOPPAGE_FIGHTS)
    assert loaded[0]["fight_id"] == STOPPAGE_FIGHTS[0]["fight_id"]


def test_stoppage_scorecards_main():
    import runpy

    # Executes lines 1063-1064 in create_stoppage_scorecards
    runpy.run_module("src.create_stoppage_scorecards", run_name="__main__")
