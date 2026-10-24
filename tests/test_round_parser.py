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
    assert by_judge['Judge One'].round_dissented is True  # Two colleagues agreed on fighter_1
    assert by_judge['Judge Two'].round_pick == 'fighter_1'
    assert by_judge['Judge Two'].round_dissented is False
