"""Validate operator-declared decisions and adapt them to the frozen pricing rule."""
from dataclasses import replace
import math
from urllib.parse import urlsplit
from fixtures import baseline
from models import Threshold

DEFAULT = {'vendor': 'Northstar Build (fictional)', 'original_decision': 'Continue using the build provider',
    'assumptions': 'No platform fee; 100000 minutes per month. Contract applicability remains open.',
    'budget_threshold_usd': 100, 'monthly_minutes': 100000, 'units': 'minutes', 'rate': 0,
    'research_question': 'What is the current platform usage price per minute for this build service?',
    'official_domain': 'example.invalid', 'baseline_kind': 'operator_declared_not_independently_verified'}


def validate(data):
    if not isinstance(data, dict): raise ValueError('invalid_decision')
    result = {}
    for name, limit in [('vendor', 200), ('original_decision', 300), ('assumptions', 2000), ('research_question', 500)]:
        value = data.get(name)
        if not isinstance(value, str) or not value.strip() or len(value) > limit: raise ValueError('invalid_decision:' + name)
        result[name] = value.strip()
    for name in ('budget_threshold_usd', 'monthly_minutes', 'rate'):
        value = data.get(name)
        if type(value) not in (int, float) or not math.isfinite(value) or value < 0 or value > 1e9:
            raise ValueError('invalid_decision:' + name)
        if name != 'rate' and value == 0: raise ValueError('invalid_decision:' + name)
        if name == 'monthly_minutes' and int(value) != value: raise ValueError('invalid_decision:' + name)
        result[name] = value
    if data.get('units') != 'minutes': raise ValueError('unsupported_usage_units')
    result['units'] = 'minutes'
    domain = data.get('official_domain')
    if not isinstance(domain, str) or len(domain) > 253: raise ValueError('invalid_decision:official_domain')
    domain = domain.strip().lower()
    parsed = urlsplit('https://' + domain)
    if parsed.hostname != domain or '.' not in domain or parsed.path or parsed.port or parsed.username or any(c.isspace() for c in domain):
        raise ValueError('invalid_decision:official_domain')
    if not all(c.isascii() and (c.isalnum() or c in '.-') for c in domain): raise ValueError('invalid_decision:official_domain')
    result['official_domain'] = domain
    result['baseline_kind'] = 'operator_declared_not_independently_verified'
    return result


def state_for(decision):
    state = baseline(minutes=decision['monthly_minutes'])
    criteria = tuple(replace(c, current_value=decision['rate'] * decision['monthly_minutes'],
                             threshold=Threshold('gt', decision['budget_threshold_usd'])) if c.criterion_id == 'C01' else c
                     for c in state.criteria)
    evidence = tuple(replace(c, value=decision['rate']) if c.proposition == 'fee_rate' else c for c in state.evidence)
    return replace(state, criteria=criteria, evidence=evidence)


def annotate(report, decision):
    calc = report['trace']['calculations'].get('monthly_cost')
    if calc:
        # Frozen adapter computes against the supplied threshold but its trace
        # label is fixed at 100. Correct the label, never the measured decision.
        if calc['threshold'] != decision['budget_threshold_usd']:
            report['trace_annotation'] = 'Threshold label corrected to the supplied C01 policy; engine result unchanged.'
        calc['threshold'] = decision['budget_threshold_usd']
    report['policy_basis'] = 'Total monthly USD price for minute-based usage; not incremental cost or a vendor ranking.'
    return report
