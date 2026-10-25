"""Unit tests for data models."""

from src.models import FightRecord, JudgeAppearance, JudgeRoundStats, RoundScore


def test_fight_record_to_dict():
    record = FightRecord(
        event_id="456",
        event_title="UFC 300",
        event_date="2024-04-13",
        event_year="2024",
        event_location="Las Vegas, NV",
        decision_id="123",
        decision_url="http://mmadecisions.com/decision/123/test",
        fight="Pereira def. Hill",
        fighter_1="Alex Pereira",
        fighter_2="Jamahal Hill",
        outcome="def",
        decision_type="Unanimous Decision",
        majority_pick="fighter_1",
        has_dissenter=False,
        dissenter_judge_name=None,
        j1_name="Judge 1",
        j1_score="30-27",
        j1_pick="fighter_1",
        j1_dissented=False,
        j2_name="Judge 2",
        j2_score="30-27",
        j2_pick="fighter_1",
        j2_dissented=False,
        j3_name="Judge 3",
        j3_score="30-27",
        j3_pick="fighter_1",
        j3_dissented=False,
    )
    d = record.to_dict()
    assert isinstance(d, dict)
    assert d["decision_id"] == "123"
    assert d["fighter_1"] == "Alex Pereira"


def test_judge_appearance_to_dict():
    app = JudgeAppearance(
        judge_id="1",
        judge_name="Mike Bell",
        event_id="456",
        event_title="UFC 300",
        event_date="2024-04-13",
        event_year="2024",
        decision_id="123",
        fight="Pereira def. Hill",
        decision_type="Unanimous Decision",
        judge_score="30-27",
        judge_pick="fighter_1",
        colleagues_agreed=True,
        disagreed_with_both=False,
        colleagues_same_score=True,
        disagreed_on_score=False,
        has_selected_class=False,
        colleague_1="Judge 2",
        colleague_2="Judge 3",
    )
    d = app.to_dict()
    assert isinstance(d, dict)
    assert d["judge_name"] == "Mike Bell"
    assert d["colleagues_agreed"] is True


def test_round_score_to_dict():
    rs = RoundScore(
        decision_id="123",
        event_id="456",
        event_year="2024",
        fight="Pereira def. Hill",
        fighter_1="Alex Pereira",
        fighter_2="Jamahal Hill",
        round_num=1,
        judge_name="Mike Bell",
        judge_id="1",
        score_f1=10,
        score_f2=9,
        round_pick="fighter_1",
        colleagues_agreed=True,
        round_dissented=False,
        colleague_1="Judge 2",
        colleague_2="Judge 3",
        is_ten_eight=False,
        is_finish=False,
    )
    d = rs.to_dict()
    assert isinstance(d, dict)
    assert d["round_num"] == 1
    assert d["score_f1"] == 10


def test_judge_round_stats_to_dict():
    stats = JudgeRoundStats(
        judge_name="Mike Bell",
        total_rounds=100,
        consensus_rounds=95,
        round_dissents=5,
        round_dissent_pct=5.0,
        f1_round_picks=60,
        f2_round_picks=38,
        draw_round_picks=2,
        ten_eight_rounds=10,
        ten_eight_pct=10.0,
    )
    d = stats.to_dict()
    assert isinstance(d, dict)
    assert d["judge_name"] == "Mike Bell"
    assert d["total_rounds"] == 100
