from datetime import date
from schemas import ALLOWED_CRITERIA,ALLOWED_TYPES,ALLOWED_UNITS,StructuredClaim
def _date(v):
 if v is None:return
 date.fromisoformat(v)
def validate_claim(c,allowed_sources):
 errors=[]
 for f in c.__dataclass_fields__:
  if getattr(c,f,None) is None and f not in {'source_date','effective_date'}: errors.append('missing:'+f)
 if c.source_id not in allowed_sources: errors.append('invented_source_id')
 if c.claim_type not in ALLOWED_TYPES: errors.append('unsupported_claim_type')
 if c.unit not in ALLOWED_UNITS: errors.append('unsupported_unit')
 if len(c.criterion_candidates)!=len(set(c.criterion_candidates)): errors.append('duplicate_criterion_ids')
 if set(c.criterion_candidates)-ALLOWED_CRITERIA: errors.append('unknown_criterion')
 try:_date(c.source_date);_date(c.effective_date)
 except ValueError:errors.append('malformed_date')
 if c.unit=='usd_per_minute' and (not isinstance(c.normalized_value,(int,float)) or c.normalized_value<0): errors.append('impossible_value')
 return errors
