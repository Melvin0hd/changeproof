"""Add literal grounding checks without changing the frozen decision adapter."""
import math
import re
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parents[1] / 'changeproof_decision_adapter_v1'))
from decision_adapter import evaluate
from fixtures import baseline
from models import EvidenceClaim
from validators import validate_claim
from criterion_mapper import validate_mapping


def evidence_from_retrieval(item):
    return {'source_id': item.source_id, 'source_url': item.url,
            'publisher': item.publisher, 'publication_date': item.published_date,
            'raw_text': item.raw_text, 'query': item.query,
            'retrieved_at': item.retrieved_at, 'source_role': item.source_role}


def inspect_claim(claim, evidence):
    errors = validate_claim(claim, {evidence['source_id']})
    if evidence.get('source_role') == 'search_excerpt_unverified':
        errors.append('retrieved_excerpt_requires_source_review')
    for field, expected in [('source_url', evidence['source_url']),
                            ('publisher', evidence['publisher']),
                            ('source_date', evidence.get('publication_date'))]:
        if getattr(claim, field) != expected:
            errors.append('source_metadata_mismatch:' + field)
    if not claim.evidence_span or claim.evidence_span not in evidence['raw_text']:
        errors.append('ungrounded_span')
    if claim.unit == 'usd_per_minute':
        value = claim.normalized_value
        if type(value) not in (int, float) or not math.isfinite(value):
            errors.append('invalid_numeric_value')
        else:
            numbers = re.findall(r'(?<![\w.])\d+(?:\.\d+)?', claim.evidence_span)
            if value not in [float(n) for n in numbers]:
                errors.append('numeric_value_not_in_span')
    allowed = {'fee_rate': ('pricing_rate', 'usd_per_minute', {'C01'}),
               'fee_status': ('policy_status', 'status', {'C05', 'C06', 'C07'})}
    if claim.claim_type != 'irrelevant':
        contract = allowed.get(claim.normalized_proposition)
        if contract is None or (claim.claim_type, claim.unit) != contract[:2] or set(claim.criterion_candidates) != contract[2]:
            errors.append('unsupported_proposition_mapping')
        if claim.normalized_proposition == 'fee_status':
            if claim.normalized_value not in {'announced', 'postponed', 'not_effective'}:
                errors.append('unsupported_status')
            elif claim.normalized_value not in claim.evidence_span:
                errors.append('status_not_in_span')
    return sorted(set(errors))


def run_evidence(evidence, extractor, state=None):
    state = state or baseline()
    rows = []
    errors = []
    claims = []
    try:
        claims = extractor.extract_claims(evidence, {'criteria': 'frozen_pricing_C01_C05_C06_C07'})
        if not claims:
            errors.append('empty_extraction_requires_review')
        if len({c.claim_id for c in claims}) != len(claims):
            errors.append('duplicate_claim_ids')
        for claim in claims:
            issues = inspect_claim(claim, evidence)
            mapping = validate_mapping(claim)
            if mapping['status'] == 'review_required':
                issues.append('mapping_requires_review')
            errors.extend(issues)
            rows.append({'raw_claim': claim.to_dict(), 'validation_errors': sorted(set(issues)),
                         'provenance_checked': not issues, 'mapping': mapping})
    except Exception as error:
        errors.append('extraction_or_validation_failure:' + type(error).__name__)
    if errors:
        accepted = [EvidenceClaim('intake_failure', 'fee_scope', 'unresolved', ('C01',), True)]
    else:
        accepted = [EvidenceClaim(c.claim_id, c.normalized_proposition, c.normalized_value,
                                  validate_mapping(c)['criteria']) for c in claims
                    if validate_mapping(c)['status'] != 'ignored']
    transition = evaluate(state, accepted)
    return {'source_reference': evidence['source_url'], 'query': evidence.get('query'),
            'source_id': evidence['source_id'], 'claims': rows,
            'validation_errors': sorted(set(errors)), 'decision': transition.final_status,
            'trace': transition.to_dict(), 'semantic_entailment_proven': False,
            'human_review_required': True}
