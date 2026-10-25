"""Unit tests for round-by-round parser and consensus determination."""

import pytest
from bs4 import BeautifulSoup
from src.round_parser import parse_round_cells, parse_decision_rounds


def test_parse_round_cells_valid():
    """Verify standard valid round score rows are correctly parsed."""
    soup = BeautifulSoup("<tr><td>1</td><td>10</td><td>9</td></tr>", "html.parser")
    cells = soup.find_all("td")
    parsed = parse_round_cells(cells)
    assert parsed == (1, 10, 9)

    # 10-8 round
    soup = BeautifulSoup("<tr><td>3</td><td>8</td><td>10</td></tr>", "html.parser")
    cells = soup.find_all("td")
    assert parse_round_cells(cells) == (3, 8, 10)


def test_parse_round_cells_invalid():
    """Verify malformed, out-of-range, or corrupted cells are rejected."""
    # Round 6 out of bounds
    soup = BeautifulSoup("<tr><td>6</td><td>10</td><td>9</td></tr>", "html.parser")
    assert parse_round_cells(soup.find_all("td")) is None

    # Score out of bounds (15)
    soup = BeautifulSoup("<tr><td>1</td><td>15</td><td>9</td></tr>", "html.parser")
    assert parse_round_cells(soup.find_all("td")) is None

    # Non-digit text
    soup = BeautifulSoup("<tr><td>TOTAL</td><td>29</td><td>28</td></tr>", "html.parser")
    assert parse_round_cells(soup.find_all("td")) is None

    # Fewer than 3 cells
    soup = BeautifulSoup("<tr><td>1</td><td>10</td></tr>", "html.parser")
    assert parse_round_cells(soup.find_all("td")) is None


def test_parse_decision_rounds_consensus_and_dissent():
    """Verify round consensus and dissent logic with synthetic HTML."""
    html_content = """
    <html><body>
    <table>
      <tr><td class="judge"><a href="judge/1/Judge-Alpha">Judge Alpha</a></td></tr>
      <tr class="decision"><td>1</td><td>10</td><td>9</td></tr>
      <tr class="decision"><td>2</td><td>10</td><td>9</td></tr>
    </table>
    <table>
      <tr><td class="judge"><a href="judge/2/Judge-Beta">Judge Beta</a></td></tr>
      <tr class="decision"><td>1</td><td>10</td><td>9</td></tr>
      <tr class="decision"><td>2</td><td>9</td><td>10</td></tr>
    </table>
    <table>
      <tr><td class="judge"><a href="judge/3/Judge-Gamma">Judge Gamma</a></td></tr>
      <tr class="decision"><td>1</td><td>9</td><td>10</td></tr>
      <tr class="decision"><td>2</td><td>10</td><td>9</td></tr>
    </table>
    </body></html>
    """
    metadata = {
        'event_id': '100',
        'event_year': '2024',
        'fight': 'Fighter A vs Fighter B',
        'fighter_1': 'Fighter A',
        'fighter_2': 'Fighter B'
    }
    rounds = parse_decision_rounds(html_content, "999", metadata)
    assert len(rounds) == 6  # 3 judges * 2 rounds

    # Round 1: Alpha=F1, Beta=F1, Gamma=F2
    # Gamma should be dissenter!
    r1_scores = {r.judge_name: r for r in rounds if r.round_num == 1}
    assert r1_scores['Judge Alpha'].round_pick == 'fighter_1'
    assert r1_scores['Judge Beta'].round_pick == 'fighter_1'
    assert r1_scores['Judge Gamma'].round_pick == 'fighter_2'

    assert r1_scores['Judge Gamma'].round_dissented is True
    assert r1_scores['Judge Gamma'].colleagues_agreed is True

    # Alpha's colleagues are Beta (F1) and Gamma (F2) -> they disagreed
    assert r1_scores['Judge Alpha'].colleagues_agreed is False
    assert r1_scores['Judge Alpha'].round_dissented is False

    # Round 2: Alpha=F1, Beta=F2, Gamma=F1
    # Beta should be dissenter!
    r2_scores = {r.judge_name: r for r in rounds if r.round_num == 2}
    assert r2_scores['Judge Beta'].round_dissented is True
    assert r2_scores['Judge Beta'].colleagues_agreed is True
    assert r2_scores['Judge Alpha'].round_dissented is False
    assert r2_scores['Judge Gamma'].round_dissented is False


def test_parse_decision_rounds_ten_eight():
    """Verify 10-8 scoring detection."""
    html_content = """
    <html><body>
    <table><tr><td class="judge">Judge One</td></tr><tr class="decision"><td>1</td><td>10</td><td>8</td></tr></table>
    <table><tr><td class="judge">Judge Two</td></tr><tr class="decision"><td>1</td><td>10</td><td>9</td></tr></table>
    <table><tr><td class="judge">Judge Three</td></tr><tr class="decision"><td>1</td><td>10</td><td>9</td></tr></table>
    </body></html>
    """
    rounds = parse_decision_rounds(html_content, "888", {})
    scores_by_judge = {r.judge_name: r for r in rounds}
    assert scores_by_judge['Judge One'].is_ten_eight is True
    assert scores_by_judge['Judge Two'].is_ten_eight is False
    assert scores_by_judge['Judge Three'].is_ten_eight is False


def test_parse_decision_rounds_unanimous():
    """Verify when all 3 judges agree, round_dissented is False for all."""
    html_content = """
    <html><body>
    <table><tr><td class="judge">Judge One</td></tr><tr class="decision"><td>1</td><td>10</td><td>9</td></tr></table>
    <table><tr><td class="judge">Judge Two</td></tr><tr class="decision"><td>1</td><td>10</td><td>9</td></tr></table>
    <table><tr><td class="judge">Judge Three</td></tr><tr class="decision"><td>1</td><td>10</td><td>9</td></tr></table>
    </body></html>
    """
    rounds = parse_decision_rounds(html_content, "777", {})
    assert len(rounds) == 3
    for r in rounds:
        assert r.round_pick == 'fighter_1'
        assert r.colleagues_agreed is True
        assert r.round_dissented is False


def test_parse_decision_rounds_draw():
    """Verify 10-10 draw pick detection and dissent when two pick a fighter."""
    html_content = """
    <html><body>
    <table><tr><td class="judge">Judge One</td></tr><tr class="decision"><td>1</td><td>10</td><td>10</td></tr></table>
    <table><tr><td class="judge">Judge Two</td></tr><tr class="decision"><td>1</td><td>10</td><td>9</td></tr></table>
    <table><tr><td class="judge">Judge Three</td></tr><tr class="decision"><td>1</td><td>10</td><td>9</td></tr></table>
    </body></html>
    """
    rounds = parse_decision_rounds(html_content, "666", {})
    by_judge = {r.judge_name: r for r in rounds}
    assert by_judge['Judge One'].round_pick == 'draw'
    assert by_judge['Judge Two'].round_pick == 'fighter_1'
    assert by_judge['Judge Two'].round_dissented is False


def test_parse_decision_rounds_edge_cases():
    """Verify handling of empty HTML, missing judges, and 2-judge panels."""
    assert parse_decision_rounds("", "101") == []
    assert parse_decision_rounds("<html><body>No tables</body></html>", "102") == []

    # Only 2 judges (e.g. missing judge table)
    two_judges_html = """
    <html><body>
    <table><tr><td class="judge">Judge One</td></tr><tr class="decision"><td>1</td><td>10</td><td>9</td></tr></table>
    <table><tr><td class="judge">Judge Two</td></tr><tr class="decision"><td>1</td><td>10</td><td>9</td></tr></table>
    </body></html>
    """
    assert parse_decision_rounds(two_judges_html, "103") == []


def test_save_round_scores_to_csv_and_sqlite(tmp_path):
    """Verify save_round_scores creates CSV and SQLite tables with indices."""
    from src.round_parser import save_round_scores, parse_decision_rounds
    import sqlite3

    html_content = """
    <html><body>
    <table><tr><td class="judge">Judge Alpha</td></tr><tr class="decision"><td>1</td><td>10</td><td>9</td></tr></table>
    <table><tr><td class="judge">Judge Beta</td></tr><tr class="decision"><td>1</td><td>10</td><td>9</td></tr></table>
    <table><tr><td class="judge">Judge Gamma</td></tr><tr class="decision"><td>1</td><td>9</td><td>10</td></tr></table>
    </body></html>
    """
    scores = parse_decision_rounds(html_content, "555")
    test_csv = tmp_path / "rounds.csv"
    test_db = tmp_path / "test.db"

    save_round_scores(scores, csv_path=test_csv, db_path=test_db)

    assert test_csv.exists()
    assert test_db.exists()

    with sqlite3.connect(test_db) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM round_scores")
        count = cursor.fetchone()[0]
        assert count == 3

        # Verify index creation
        cursor.execute("SELECT name FROM sqlite_master WHERE type='index' AND name='idx_rs_judge'")
        assert cursor.fetchone() is not None

    # Test saving empty list
    save_round_scores([], csv_path=test_csv, db_path=test_db)


def test_load_stoppage_scorecards_success():
    """Verify official stoppage scorecards load correctly with all metadata."""
    from src.round_parser import load_stoppage_scorecards

    stoppage_scores = load_stoppage_scorecards()
    assert len(stoppage_scores) == 288  # 48 fights, 96 rounds, 288 judge scores

    # Verify all records have is_finish=True
    assert all(r.is_finish for r in stoppage_scores)

    # Verify finish_round and finish_method are populated
    for r in stoppage_scores:
        assert r.finish_round in [1, 2, 3, 4, 5]
        assert r.finish_method in ['KO', 'TKO', 'TKO (Doctor Stoppage)', 'KO/TKO', 'Submission', 'DQ']
        assert r.round_num <= r.finish_round  # Completed rounds are scored!

    # Verify Usman vs Covington 1 (UFC 245, stopped in R5) has R1-R4 scored
    usman_scores = [r for r in stoppage_scores if 'Usman' in r.fight and 'Covington' in r.fight]
    assert len(usman_scores) == 12  # 3 judges * 4 completed rounds
    rounds_present = {r.round_num for r in usman_scores}
    assert rounds_present == {1, 2, 3, 4}

    # Verify Miocic vs Cormier 2 (UFC 241, stopped in R4) has R1-R3 scored
    miocic_scores = [r for r in stoppage_scores if 'Miocic' in r.fight and 'Cormier' in r.fight]
    assert len(miocic_scores) == 9  # 3 judges * 3 completed rounds
    assert {r.round_num for r in miocic_scores} == {1, 2, 3}


def test_load_stoppage_scorecards_missing_and_corrupt(tmp_path):
    """Verify load_stoppage_scorecards handles missing and corrupt files safely."""
    from src.round_parser import load_stoppage_scorecards
    import json

    missing_path = tmp_path / "nonexistent.json"
    assert load_stoppage_scorecards(missing_path) == []

    corrupt_path = tmp_path / "corrupt.json"
    corrupt_path.write_text("{not valid json}", encoding="utf-8")
    assert load_stoppage_scorecards(corrupt_path) == []

    empty_path = tmp_path / "empty.json"
    empty_path.write_text("[]", encoding="utf-8")
    assert load_stoppage_scorecards(empty_path) == []


