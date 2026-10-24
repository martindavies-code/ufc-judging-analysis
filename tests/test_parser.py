"""Unit tests for score parsing, judge name normalization, consensus evaluation, and event HTML extraction."""

import sqlite3
import pytest

from src.models import JudgeScorecard
from src.parser import (
    clean_judge_name,
    determine_panel_consensus,
    init_database_schema,
    parse_event_html,
    parse_score,
)


class TestParseScore:
    def test_standard_scores(self):
        assert parse_score("48 - 47") == (48, 47)
        assert parse_score("29-28") == (29, 28)
        assert parse_score("30:27") == (30, 27)
        assert parse_score(" 50 – 45 ") == (50, 45)

    def test_scores_with_annotations(self):
        # Point deduction notes
        assert parse_score("28-28 (1 pt deducted)") == (28, 28)
        assert parse_score("47 - 48 (round 2 10-8)") == (47, 48)

    def test_invalid_and_empty_inputs(self):
        assert parse_score("") == (None, None)
        assert parse_score(None) == (None, None)
        assert parse_score("Unanimous Decision") == (None, None)
        assert parse_score("48") == (None, None)

    def test_boundary_and_absurd_scores_rejected(self):
        # Scores below 10 or above 50 must be rejected
        assert parse_score("9 - 8") == (None, None)
        assert parse_score("100 - 90") == (None, None)
        assert parse_score("-29 - 28") == (None, None)


class TestCleanJudgeName:
    def test_slug_with_id_and_hyphenated_name(self):
        assert clean_judge_name("BELL", "judge/357/Michael-Bell") == "Michael Bell"
        assert clean_judge_name("D'AMATO", "judge/1/Sal-D'Amato") == "Sal D'Amato"

    def test_url_encoded_characters(self):
        assert clean_judge_name("COLON", "judge/86/Eric-Col%C3%B3n") == "Eric Colón"

    def test_raw_display_fallback(self):
        assert clean_judge_name("Chris Lee", None) == "Chris Lee"
        assert clean_judge_name("  derek   cleary  ", "") == "Derek Cleary"

    def test_empty_fallback(self):
        assert clean_judge_name(None, None) == "Unknown Judge"
        assert clean_judge_name("", "") == "Unknown Judge"


class TestDeterminePanelConsensus:
    def test_unanimous_decision(self):
        judges = [
            JudgeScorecard(judge_id="1", judge_name="Bell", judge_short="BELL", score_text="30-27", score_f1=30, score_f2=27, pick="fighter_1", has_selected_class=False),
            JudgeScorecard(judge_id="2", judge_name="Lee", judge_short="LEE", score_text="30-27", score_f1=30, score_f2=27, pick="fighter_1", has_selected_class=False),
            JudgeScorecard(judge_id="3", judge_name="Cleary", judge_short="CLEARY", score_text="29-28", score_f1=29, score_f2=28, pick="fighter_1", has_selected_class=False),
        ]
        consensus = determine_panel_consensus(judges)
        assert consensus.majority_pick == "fighter_1"
        assert not consensus.has_dissenter
        assert consensus.dissenter_idx is None
        assert not consensus.is_three_way_split

    def test_split_decision_with_dissenter(self):
        judges = [
            JudgeScorecard(judge_id="1", judge_name="Bell", judge_short="BELL", score_text="29-28", score_f1=29, score_f2=28, pick="fighter_1", has_selected_class=False),
            JudgeScorecard(judge_id="2", judge_name="Lee", judge_short="LEE", score_text="28-29", score_f1=28, score_f2=29, pick="fighter_2", has_selected_class=True),
            JudgeScorecard(judge_id="3", judge_name="Cleary", judge_short="CLEARY", score_text="29-28", score_f1=29, score_f2=28, pick="fighter_1", has_selected_class=False),
        ]
        consensus = determine_panel_consensus(judges)
        assert consensus.majority_pick == "fighter_1"
        assert consensus.has_dissenter
        assert consensus.dissenter_idx == 1
        assert consensus.dissenter_name == "Lee"
        assert not consensus.is_three_way_split

    def test_majority_draw_with_dissenter(self):
        judges = [
            JudgeScorecard(judge_id="1", judge_name="Bell", judge_short="BELL", score_text="28-28", score_f1=28, score_f2=28, pick="draw", has_selected_class=False),
            JudgeScorecard(judge_id="2", judge_name="Lee", judge_short="LEE", score_text="28-28", score_f1=28, score_f2=28, pick="draw", has_selected_class=False),
            JudgeScorecard(judge_id="3", judge_name="Cleary", judge_short="CLEARY", score_text="29-28", score_f1=29, score_f2=28, pick="fighter_1", has_selected_class=True),
        ]
        consensus = determine_panel_consensus(judges)
        assert consensus.majority_pick == "draw"
        assert consensus.has_dissenter
        assert consensus.dissenter_idx == 2
        assert consensus.dissenter_name == "Cleary"

    def test_three_way_split_draw(self):
        judges = [
            JudgeScorecard(judge_id="1", judge_name="Bell", judge_short="BELL", score_text="29-28", score_f1=29, score_f2=28, pick="fighter_1", has_selected_class=False),
            JudgeScorecard(judge_id="2", judge_name="Lee", judge_short="LEE", score_text="28-29", score_f1=28, score_f2=29, pick="fighter_2", has_selected_class=False),
            JudgeScorecard(judge_id="3", judge_name="Cleary", judge_short="CLEARY", score_text="28-28", score_f1=28, score_f2=28, pick="draw", has_selected_class=False),
        ]
        consensus = determine_panel_consensus(judges)
        assert consensus.majority_pick is None
        assert not consensus.has_dissenter
        assert consensus.is_three_way_split

    def test_invalid_panel_size_raises(self):
        with pytest.raises(ValueError, match="exactly 3 judges"):
            determine_panel_consensus([])
        with pytest.raises(ValueError, match="exactly 3 judges"):
            determine_panel_consensus([
                JudgeScorecard(judge_id="1", judge_name="A", judge_short="A", score_text="30-27", score_f1=30, score_f2=27, pick="fighter_1", has_selected_class=False)
            ])


class TestParseEventHtml:
    MOCK_EVENT_HTML = """
    <html>
      <table>
        <tr>
          <td class="decision-top2">UFC 300: Pereira vs. Hill<br>T-Mobile Arena, Las Vegas</td>
        </tr>
        <tr>
          <td class="decision-bottom2">April 13, 2024</td>
        </tr>
      </table>
      <table>
        <tr>
          <td><b>Fight</b></td><td colspan="3"><b>Scores</b></td>
        </tr>
        <tr>
          <td>
            <a href="decision/12345/Fighter-A-vs-Fighter-B">Fighter A def. Fighter B</a>
            <br><i>Split</i>
          </td>
          <td>
            <a href="judge/1/Michael-Bell">BELL</a>
            <br><span>29 - 28</span>
          </td>
          <td class="selected">
            <a href="judge/2/Chris-Lee">LEE</a>
            <br><span>28 - 29</span>
          </td>
          <td>
            <a href="judge/3/Derek-Cleary">CLEARY</a>
            <br><span>29 - 28</span>
          </td>
        </tr>
      </table>
    </html>
    """

    def test_parse_event_html_valid(self):
        fights, appearances = parse_event_html(
            self.MOCK_EVENT_HTML,
            event_id="300",
            default_title="UFC 300",
            default_year="2024"
        )
        assert len(fights) == 1
        f = fights[0]
        assert f.event_id == "300"
        assert f.event_title == "UFC 300: Pereira vs. Hill"
        assert f.event_date == "April 13, 2024"
        assert f.fighter_1 == "Fighter A"
        assert f.fighter_2 == "Fighter B"
        assert f.decision_type == "Split"
        assert f.has_dissenter is True
        assert f.dissenter_judge_name == "Chris Lee"
        assert f.j2_dissented is True
        assert f.j1_dissented is False

        assert len(appearances) == 3
        app_lee = next(a for a in appearances if a.judge_name == "Chris Lee")
        assert app_lee.disagreed_with_both is True
        assert app_lee.has_selected_class is True

        app_bell = next(a for a in appearances if a.judge_name == "Michael Bell")
        assert app_bell.disagreed_with_both is False


class TestDatabaseSchema:
    def test_schema_creation_and_indexes(self):
        conn = sqlite3.connect(":memory:")
        init_database_schema(conn)
        cursor = conn.cursor()
        
        # Verify tables exist
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = [r[0] for r in cursor.fetchall()]
        assert "fights" in tables
        assert "judge_appearances" in tables

        # Verify indexes exist
        cursor.execute("SELECT name FROM sqlite_master WHERE type='index';")
        indexes = [r[0] for r in cursor.fetchall()]
        assert "idx_ja_judge_name" in indexes
        assert "idx_ja_event_year" in indexes
        conn.close()
