from dataclasses import dataclass, asdict
from typing import Any

ALLOWED_CRITERIA={f'C{i:02d}' for i in range(1,8)}
ALLOWED_TYPES={'pricing_rate','policy_status','irrelevant','scope'}
ALLOWED_UNITS={'usd_per_minute','status','none'}
@dataclass(frozen=True)
class SearchEvidence:
 query:str; source_id:str; url:str; title:str; publisher:str; published_date:str|None; retrieved_at:str; raw_text:str; source_role:str; search_rank:int
@dataclass(frozen=True)
class StructuredClaim:
 claim_id:str; source_id:str; source_url:str; source_date:str|None; publisher:str; claim_type:str; normalized_proposition:str; normalized_value:Any; unit:str; effective_date:str|None; criterion_candidates:tuple[str,...]; evidence_span:str; ambiguity_flags:tuple[str,...]; review_required:bool; extraction_confidence:str
 def to_dict(self): return asdict(self)
