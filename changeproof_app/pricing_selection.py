"""Select a single declared GitHub tariff without rewriting retrieved evidence."""
import hashlib
import re
from urllib.parse import urlsplit

TARGET = 'GitHub Actions Linux 2-core x64'
HEADER = re.compile(r'\|\s*Operating system\s*\|\s*Billing SKU\s*\|\s*Per-minute rate \(USD\)\s*\|', re.I)
ANY_HEADER = re.compile(r'\|\s*Operating system\s*\|\s*Billing SKU\s*\|[^|\r\n]*\|', re.I)
ROW = re.compile(r'\|\s*Linux 2-core \(x64\)\s*\|\s*`actions_linux`\s*\|\s*\$(\d+(?:\.\d+)?)\s*\|')
PRICE_ROW = re.compile(r'\|[^|\r\n]*\|\s*`[a-z0-9_]+`\s*\|\s*\$\d+(?:\.\d+)?\s*\|')
PATHS = {'/en/billing/reference/actions-runner-pricing', '/en/billing/reference/actions-minute-multipliers'}


def select_pricing_evidence(sources, decision):
    if not decision['vendor'].lower().startswith('github actions'):
        return None
    if decision['vendor'] != TARGET or decision['official_domain'] != 'docs.github.com':
        raise ValueError('unsupported_declared_runner')
    candidates = []
    for source in sources:
        url = urlsplit(source['source_url'])
        if url.scheme != 'https' or url.hostname != 'docs.github.com' or url.username or url.password or url.path not in PATHS:
            continue
        raw = source['raw_text']
        for row in ROW.finditer(raw):
            headers = [h for h in HEADER.finditer(raw, 0, row.start())]
            if not headers:
                raise ValueError('target_table_header_missing_or_wrong_unit')
            header = headers[-1]
            nearest = list(ANY_HEADER.finditer(raw, 0, row.start()))[-1]
            if nearest.start() != header.start():
                raise ValueError('target_table_header_missing_or_wrong_unit')
            between = raw[header.end():row.start()]
            if len(between) > 1000 or re.search(r'(?m)^\s*#', between):
                raise ValueError('target_table_context_not_comparable')
            candidates.append((source, header, row))
    if not candidates:
        raise ValueError('no_matching_runner_tariff')
    if len({float(row.group(1)) for _, _, row in candidates}) != 1:
        raise ValueError('conflicting_target_prices')
    source, header, row = candidates[0]
    raw = source['raw_text']
    # Drop only fully recognized machine-price rows and table headers. All other
    # characters, including qualifiers/ellipsis markers, remain offset-addressed.
    removed = sorted([(m.start(), m.end()) for m in PRICE_ROW.finditer(raw)] +
                     [(m.start(), m.end()) for m in HEADER.finditer(raw)])
    context, offset = [], 0
    for start, end in removed:
        if start > offset and raw[offset:start].strip():
            context.append({'start': offset, 'end': start, 'text': raw[offset:start]})
        offset = max(offset, end)
    if offset < len(raw) and raw[offset:].strip():
        context.append({'start': offset, 'end': len(raw), 'text': raw[offset:]})
    if sum(len(p['text']) for p in context) > 6000:
        raise ValueError('pricing_qualifiers_exceed_bounded_input')
    qualifiers = ''.join(p['text'] for p in context)
    uncertainty = []
    if '[...]' in raw:
        uncertainty.append('retrieved_excerpt_has_omissions')
    if not all(re.search(word, qualifiers, re.I) for word in (r'\bbillable\b', r'\bincluded\b', r'\bexhausted\b')):
        uncertainty.append('included_minutes_and_contract_unconfirmed')
    return {'source_id': source['source_id'], 'source_sha256': hashlib.sha256(raw.encode()).hexdigest(),
            'target': TARGET, 'billing_sku': 'actions_linux', 'unit': 'usd_per_minute',
            'rate': float(row.group(1)), 'header': {'start': header.start(), 'end': header.end(), 'text': header.group()},
            'row': {'start': row.start(), 'end': row.end(), 'text': row.group()},
            'context_fragments': context, 'uncertainties': uncertainty,
            'model_excerpt': raw[header.start():row.end()], 'candidate_rows_checked': len(candidates)}


def model_evidence(source, selection):
    if selection is None:
        return source
    raw = source['raw_text']
    if source['source_id'] != selection['source_id'] or hashlib.sha256(raw.encode()).hexdigest() != selection['source_sha256']:
        raise ValueError('selection_source_hash_mismatch')
    for part in [selection['header'], selection['row'], *selection['context_fragments']]:
        if raw[part['start']:part['end']] != part['text']:
            raise ValueError('selection_offset_mismatch')
    row = ROW.fullmatch(selection['row']['text'])
    if (row is None or float(row.group(1)) != selection['rate'] or
            HEADER.fullmatch(selection['header']['text']) is None or
            selection['model_excerpt'] != raw[selection['header']['start']:selection['row']['end']]):
        raise ValueError('selection_tariff_binding_mismatch')
    return dict(source, raw_text=selection['model_excerpt'], pricing_selection={
        k: v for k, v in selection.items() if k != 'model_excerpt'})


def validate_selected_claim(claim, source, selection):
    # Recheck provenance/offsets locally; model-produced fields cannot authorize a tariff.
    model_evidence(source, selection)
    errors = list(selection['uncertainties'])
    if selection['row']['text'] not in claim.evidence_span:
        errors.append('selected_runner_row_not_in_span')
    if type(claim.normalized_value) not in (int, float) or claim.normalized_value != selection['rate']:
        errors.append('selected_runner_price_mismatch')
    if claim.unit != selection['unit'] or claim.claim_type != 'pricing_rate' or claim.normalized_proposition != 'fee_rate' or claim.criterion_candidates != ('C01',):
        errors.append('selected_tariff_contract_mismatch')
    if claim.evidence_span not in source['raw_text']:
        errors.append('selected_span_not_literal')
    return errors
