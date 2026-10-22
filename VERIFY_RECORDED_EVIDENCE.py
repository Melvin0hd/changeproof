"""Verify captured genuine evidence through unchanged F1 code, never provider HTTP."""
import hashlib
import json
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT/'changeproof_app'))
from app import NebiusNemotronExtractor,run_evidence,decision_config
from pricing_selection import model_evidence
from pricing_guard import guarded_claims
from recovery_pipeline import inspect_claim
audit=json.loads((ROOT/'examples/genuine_ui_review.json').read_text())
provider=audit['provider']['nebius'];evidence=audit['evidence'];selection=audit['extraction_scope']
assert provider['http_status']==audit['provider']['tavily']['http_status']==200
assert provider['model']=='nvidia/Nemotron-3_5-Lightning'
assert provider['finish_reason']=='stop' and provider['reasoning_tokens']==0
assert audit['session_attempts']=={'tavily':1,'nebius':1}
assert hashlib.sha256(evidence['raw_text'].encode()).hexdigest()==selection['source_sha256']
class CapturedClient:
    def complete(self,*args,**kwargs):return provider
extractor=NebiusNemotronExtractor(CapturedClient());extractor.max_claims=1
claims=extractor.extract_claims(model_evidence(evidence,selection),audit['original_decision'])
assert len(claims)==1 and inspect_claim(claims[0],evidence)==[]
assert claims[0].normalized_value==.006
assert claims[0].evidence_span==selection['row']['text']
checked=guarded_claims(claims,evidence,audit['original_decision'],audit['sources'],selection)
class CapturedClaims:
    def extract_claims(self,*args):return checked
outcome=run_evidence(evidence,CapturedClaims(),decision_config.state_for(audit['original_decision']))
outcome=decision_config.annotate(outcome,audit['original_decision'])
outcome['validation_errors']=sorted(set(outcome['validation_errors'])|{f for c in outcome['claims'] if c['raw_claim']['review_required'] for f in c['raw_claim']['ambiguity_flags']})
assert outcome['decision']==audit['outcome']['decision']=='ESCALATE'
assert outcome['trace']['calculations']==audit['outcome']['trace']['calculations']=={}
assert set(outcome['validation_errors'])==set(audit['outcome']['validation_errors'])
assert audit['automatic_vendor_action'] is False and audit['source_truth_verified'] is False
assert audit['outcome']['claims'][0]['provenance_checked'] is False
print(json.dumps({'status':'PASS','kind':'offline_revalidation_of_authentic_record_not_new_inference','review_id':audit['review_id'],'decision':outcome['decision'],'schema_literal_support':'PASS','full_applicability':'UNRESOLVED','aggregate_provenance_checked':False,'usage':provider['usage'],'new_provider_calls':0},indent=2))
