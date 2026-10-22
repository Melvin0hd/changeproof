from dataclasses import dataclass, asdict
from typing import Any

@dataclass(frozen=True)
class Threshold: operator: str; value: float
@dataclass(frozen=True)
class Criterion:
    criterion_id: str; current_value: Any; threshold: Threshold|None=None
@dataclass(frozen=True)
class EvidenceClaim:
    claim_id: str; proposition: str; value: Any; criteria: tuple[str,...]=(); incomplete: bool=False
@dataclass(frozen=True)
class DecisionState:
    status: str; criteria: tuple[Criterion,...]; evidence: tuple[EvidenceClaim,...]; facts: dict; gaps: tuple[str,...]; version: int=1
@dataclass(frozen=True)
class DecisionTransition:
    previous_status: str; final_status: str; qualifier: str|None; claim_deltas: tuple[dict,...]; affected_criteria: tuple[str,...]; unchanged_criteria: tuple[str,...]; calculations: dict; contradictions: tuple[str,...]; reason_codes: tuple[str,...]; next_state: DecisionState; manual_intervention_required: bool
    def to_dict(self): return asdict(self)
