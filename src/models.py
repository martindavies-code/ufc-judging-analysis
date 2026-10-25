"""Strongly-typed data structures for UFC judging domain entities."""

from dataclasses import asdict, dataclass
from typing import Any


@dataclass(frozen=True)
class JudgeScorecard:
    """Represents an individual judge's scorecard for a single fight."""

    judge_id: str | None
    judge_name: str
    judge_short: str
    score_text: str
    score_f1: int | None
    score_f2: int | None
    pick: str  # 'fighter_1', 'fighter_2', 'draw', or 'unknown'
    has_selected_class: bool


@dataclass(frozen=True)
class PanelConsensus:
    """Encapsulates the consensus outcome of a 3-judge panel."""

    majority_pick: str | None  # 'fighter_1', 'fighter_2', 'draw', or None if 3-way split
    has_dissenter: bool
    dissenter_idx: int | None  # 0, 1, 2 or None
    dissenter_name: str | None
    is_three_way_split: bool


@dataclass(frozen=True)
class FightRecord:
    """Represents a fight decision parsed from an event card."""

    event_id: str
    event_title: str
    event_date: str
    event_year: str
    event_location: str
    decision_id: str
    decision_url: str
    fight: str
    fighter_1: str
    fighter_2: str
    outcome: str
    decision_type: str
    majority_pick: str | None
    has_dissenter: bool
    dissenter_judge_name: str | None
    j1_name: str
    j1_score: str
    j1_pick: str
    j1_dissented: bool
    j2_name: str
    j2_score: str
    j2_pick: str
    j2_dissented: bool
    j3_name: str
    j3_score: str
    j3_pick: str
    j3_dissented: bool

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class JudgeAppearance:
    """Represents one judge's scoring appearance in a specific fight."""

    judge_id: str | None
    judge_name: str
    event_id: str
    event_title: str
    event_date: str
    event_year: str
    decision_id: str
    fight: str
    decision_type: str
    judge_score: str
    judge_pick: str
    colleagues_agreed: bool
    disagreed_with_both: bool
    colleagues_same_score: bool
    disagreed_on_score: bool
    has_selected_class: bool
    colleague_1: str
    colleague_2: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class RoundScore:
    """Represents a single round score from one judge."""

    decision_id: str
    event_id: str
    event_year: str
    fight: str
    fighter_1: str
    fighter_2: str
    round_num: int
    judge_name: str
    judge_id: str | None
    score_f1: int
    score_f2: int
    round_pick: str  # 'fighter_1', 'fighter_2', 'draw'
    colleagues_agreed: bool  # did the other two judges agree on who won the round?
    round_dissented: bool  # did this judge dissent from the other 2 who agreed?
    colleague_1: str
    colleague_2: str
    is_ten_eight: bool  # |score_f1 - score_f2| >= 2
    is_finish: bool = False  # Did the fight end before the scheduled distance?
    finish_round: int | None = None  # Round in which stoppage occurred (e.g. 4 for 4th round finish)
    finish_method: str | None = None  # Method of finish (KO/TKO, Submission, DQ)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class JudgeRoundStats:
    """Aggregate round-level statistics for a judge."""

    judge_name: str
    total_rounds: int
    consensus_rounds: int
    round_dissents: int
    round_dissent_pct: float
    f1_round_picks: int
    f2_round_picks: int
    draw_round_picks: int
    ten_eight_rounds: int
    ten_eight_pct: float

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
