"""Unit tests for score parsing, judge name normalization, consensus evaluation, and event HTML extraction."""

import json
import sqlite3
from pathlib import Path

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
    def test_standard_scores(self) -> None:
        assert parse_score("48 - 47") == (48, 47)
        assert parse_score("29-28") == (29, 28)
        assert parse_score("30:27") == (30, 27)
        assert parse_score(" 50 – 45 ") == (50, 45)

    def test_scores_with_annotations(self) -> None:
        # Point deduction notes
        assert parse_score("28-28 (1 pt deducted)") == (28, 28)
        assert parse_score("47 - 48 (round 2 10-8)") == (47, 48)

    def test_invalid_and_empty_inputs(self) -> None:
        assert parse_score("") == (None, None)
        assert parse_score(None) == (None, None)
        assert parse_score("Unanimous Decision") == (None, None)
        assert parse_score("48") == (None, None)

    def test_boundary_and_absurd_scores_rejected(self) -> None:
        # Scores below 10 or above 50 must be rejected
        assert parse_score("9 - 8") == (None, None)
        assert parse_score("100 - 90") == (None, None)
        assert parse_score("-29 - 28") == (None, None)


class TestCleanJudgeName:
    def test_slug_with_id_and_hyphenated_name(self) -> None:
        assert clean_judge_name("BELL", "judge/357/Michael-Bell") == "Michael Bell"
        assert clean_judge_name("D'AMATO", "judge/1/Sal-D'Amato") == "Sal D'Amato"

    def test_url_encoded_characters(self) -> None:
        assert clean_judge_name("COLON", "judge/86/Eric-Col%C3%B3n") == "Eric Colón"

    def test_raw_display_fallback(self) -> None:
        assert clean_judge_name("Chris Lee", None) == "Chris Lee"
        assert clean_judge_name("  derek   cleary  ", "") == "Derek Cleary"

    def test_empty_fallback(self) -> None:
        assert clean_judge_name(None, None) == "Unknown Judge"
        assert clean_judge_name("", "") == "Unknown Judge"


class TestDeterminePanelConsensus:
    def test_unanimous_decision(self) -> None:
        judges = [
            JudgeScorecard(
                judge_id="1",
                judge_name="Bell",
                judge_short="BELL",
                score_text="30-27",
                score_f1=30,
                score_f2=27,
                pick="fighter_1",
                has_selected_class=False,
            ),
            JudgeScorecard(
                judge_id="2",
                judge_name="Lee",
                judge_short="LEE",
                score_text="30-27",
                score_f1=30,
                score_f2=27,
                pick="fighter_1",
                has_selected_class=False,
            ),
            JudgeScorecard(
                judge_id="3",
                judge_name="Cleary",
                judge_short="CLEARY",
                score_text="29-28",
                score_f1=29,
                score_f2=28,
                pick="fighter_1",
                has_selected_class=False,
            ),
        ]
        consensus = determine_panel_consensus(judges)
        assert consensus.majority_pick == "fighter_1"
        assert not consensus.has_dissenter
        assert consensus.dissenter_idx is None
        assert not consensus.is_three_way_split

    def test_split_decision_with_dissenter(self) -> None:
        judges = [
            JudgeScorecard(
                judge_id="1",
                judge_name="Bell",
                judge_short="BELL",
                score_text="29-28",
                score_f1=29,
                score_f2=28,
                pick="fighter_1",
                has_selected_class=False,
            ),
            JudgeScorecard(
                judge_id="2",
                judge_name="Lee",
                judge_short="LEE",
                score_text="28-29",
                score_f1=28,
                score_f2=29,
                pick="fighter_2",
                has_selected_class=True,
            ),
            JudgeScorecard(
                judge_id="3",
                judge_name="Cleary",
                judge_short="CLEARY",
                score_text="29-28",
                score_f1=29,
                score_f2=28,
                pick="fighter_1",
                has_selected_class=False,
            ),
        ]
        consensus = determine_panel_consensus(judges)
        assert consensus.majority_pick == "fighter_1"
        assert consensus.has_dissenter
        assert consensus.dissenter_idx == 1
        assert consensus.dissenter_name == "Lee"
        assert not consensus.is_three_way_split

    def test_majority_draw_with_dissenter(self) -> None:
        judges = [
            JudgeScorecard(
                judge_id="1",
                judge_name="Bell",
                judge_short="BELL",
                score_text="28-28",
                score_f1=28,
                score_f2=28,
                pick="draw",
                has_selected_class=False,
            ),
            JudgeScorecard(
                judge_id="2",
                judge_name="Lee",
                judge_short="LEE",
                score_text="28-28",
                score_f1=28,
                score_f2=28,
                pick="draw",
                has_selected_class=False,
            ),
            JudgeScorecard(
                judge_id="3",
                judge_name="Cleary",
                judge_short="CLEARY",
                score_text="29-28",
                score_f1=29,
                score_f2=28,
                pick="fighter_1",
                has_selected_class=True,
            ),
        ]
        consensus = determine_panel_consensus(judges)
        assert consensus.majority_pick == "draw"
        assert consensus.has_dissenter
        assert consensus.dissenter_idx == 2
        assert consensus.dissenter_name == "Cleary"

    def test_three_way_split_draw(self) -> None:
        judges = [
            JudgeScorecard(
                judge_id="1",
                judge_name="Bell",
                judge_short="BELL",
                score_text="29-28",
                score_f1=29,
                score_f2=28,
                pick="fighter_1",
                has_selected_class=False,
            ),
            JudgeScorecard(
                judge_id="2",
                judge_name="Lee",
                judge_short="LEE",
                score_text="28-29",
                score_f1=28,
                score_f2=29,
                pick="fighter_2",
                has_selected_class=False,
            ),
            JudgeScorecard(
                judge_id="3",
                judge_name="Cleary",
                judge_short="CLEARY",
                score_text="28-28",
                score_f1=28,
                score_f2=28,
                pick="draw",
                has_selected_class=False,
            ),
        ]
        consensus = determine_panel_consensus(judges)
        assert consensus.majority_pick is None
        assert not consensus.has_dissenter
        assert consensus.is_three_way_split

    def test_invalid_panel_size_raises(self) -> None:
        with pytest.raises(ValueError, match="exactly 3 judges"):
            determine_panel_consensus([])
        with pytest.raises(ValueError, match="exactly 3 judges"):
            determine_panel_consensus(
                [
                    JudgeScorecard(
                        judge_id="1",
                        judge_name="A",
                        judge_short="A",
                        score_text="30-27",
                        score_f1=30,
                        score_f2=27,
                        pick="fighter_1",
                        has_selected_class=False,
                    )
                ]
            )


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

    def test_parse_event_html_valid(self) -> None:
        fights, appearances = parse_event_html(
            self.MOCK_EVENT_HTML, event_id="300", default_title="UFC 300", default_year="2024"
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
    def test_schema_creation_and_indexes(self) -> None:
        conn = sqlite3.connect(":memory:")
        try:
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
        finally:
            conn.close()

    def test_parse_event_html_drew_with_and_draw_scores(self) -> None:
        html = """
        <html>
        <div class="decision-top">UFC 205</div>
        <table class="decision">
            <tr>
                <td class="list"><a href="decision/999/Woodley-Thompson">Tyron Woodley drew with Stephen Thompson</a></td>
                <td>Judge Alpha<br><span>28 - 28</span></td>
                <td><a href="judge/5/Beta">Judge Beta</a><br><span>29 - 28</span></td>
                <td>Judge Gamma</td>
            </tr>
        </table>
        </html>
        """
        fights, appearances = parse_event_html(html, event_id="205", default_title="UFC 205", default_year="2016")
        assert len(fights) == 1
        assert fights[0].outcome == "draw"
        assert fights[0].fighter_1 == "Tyron Woodley"
        assert fights[0].fighter_2 == "Stephen Thompson"
        assert len(appearances) == 3

    def test_parse_all_events_full_flow(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        from src import parser

        json_events = tmp_path / "ufc_events.json"
        events_dir = tmp_path / "events_html"
        events_dir.mkdir()

        json_events.write_text(
            json.dumps(
                [
                    {"event_id": "100", "title": "UFC 100", "year": "2009"},
                    {"event_id": "101", "title": "UFC 101", "year": "2009"},
                ]
            ),
            encoding="utf-8",
        )

        event_html = """
        <html>
        <div class="decision-top">UFC 100</div>
        <table class="decision">
            <tr>
                <td class="list"><a href="decision/10/Lesnar-Mir">Brock Lesnar def. Frank Mir</a></td>
                <td><a href="judge/1/Bell">Mike Bell</a><span>29-28</span></td>
                <td><a href="judge/2/Cleary">Derek Cleary</a><span>29-28</span></td>
                <td><a href="judge/3/Damato">Sal D'Amato</a><span>29-28</span></td>
            </tr>
        </table>
        </html>
        """
        (events_dir / "100.html").write_text(event_html, encoding="utf-8")

        fights_csv = tmp_path / "fights.csv"
        judges_csv = tmp_path / "judges.csv"
        db_file = tmp_path / "ufc.db"

        monkeypatch.setattr(parser, "EVENTS_JSON_PATH", json_events)
        monkeypatch.setattr(parser, "EVENTS_HTML_DIR", events_dir)
        monkeypatch.setattr(parser, "CSV_OUTPUT_PATH", fights_csv)
        monkeypatch.setattr(parser, "JUDGE_CSV_OUTPUT_PATH", judges_csv)
        monkeypatch.setattr(parser, "DB_OUTPUT_PATH", db_file)

        df_f, df_j = parser.parse_all_events()
        assert len(df_f) == 1
        assert len(df_j) == 3
        assert fights_csv.exists()
        assert judges_csv.exists()
        assert db_file.exists()

    def test_parse_all_events_missing_json_raises(self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
        from src import parser

        monkeypatch.setattr(parser, "EVENTS_JSON_PATH", tmp_path / "non_existent.json")
        with pytest.raises(FileNotFoundError):
            parser.parse_all_events()
