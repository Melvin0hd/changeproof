from schemas import ALLOWED_CRITERIA
def validate_mapping(claim):
 cs=claim.criterion_candidates
 if claim.claim_type=='irrelevant' or (not cs and claim.normalized_proposition in {'secondary_repeat','stale_policy_excerpt'}): return {'status':'ignored','criteria':()}
 if claim.review_required or claim.ambiguity_flags:return {'status':'review_required','criteria':()}
 if not cs or set(cs)-ALLOWED_CRITERIA:return {'status':'review_required','criteria':()}
 return {'status':'valid','criteria':cs}
