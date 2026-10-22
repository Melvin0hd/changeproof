"""Conservative application intake gates, not a replacement for semantic review."""
from datetime import date, datetime, timezone
from dataclasses import replace
import re
from pricing_selection import validate_selected_claim


PRICE = r'(?:USD\s*\$?|US\s*\$|\$)\s*(\d+(?:\.\d+)?)\s*(?:per\s+minute|/\s*min(?:ute)?\b)'


def guarded_claims(claims, evidence, decision, sources=(), selection=None):
    rates = {c.normalized_value for c in claims
             if c.normalized_proposition == 'fee_rate'
             and type(c.normalized_value) in (int, float)}
    checked = []
    for claim in claims:
        issues = []
        span = claim.evidence_span
        if claim.extraction_confidence not in {'high', 'medium', 'low'}:
            issues.append('unsupported_confidence')
        if claim.claim_type != 'pricing_rate' or claim.normalized_proposition != 'fee_rate':
            issues.append('minute_pricing_scope_unresolved')
        else:
            if selection is not None:
                issues.extend(validate_selected_claim(claim, evidence, selection))
                # Units and runner identity are bound structurally to the exact
                # selected row/header, not inferred from an isolated dollar value.
                dates = [v for v in (claim.source_date, claim.effective_date) if v]
                if not dates:
                    issues.append('publication_or_effective_date_missing')
                for value in dates:
                    try:
                        if value not in evidence['raw_text'] or date.fromisoformat(value) > datetime.now(timezone.utc).date():
                            issues.append('date_not_grounded_or_not_yet_effective')
                    except (ValueError, TypeError):
                        issues.append('date_not_grounded_or_not_yet_effective')
                if issues:
                    claim = replace(claim, review_required=True,
                                    ambiguity_flags=tuple(sorted(set(claim.ambiguity_flags) | set(issues))))
                checked.append(claim)
                continue
            literal_rates = set(map(float, re.findall(PRICE, span, re.I)))
            if type(claim.normalized_value) not in (int, float) or claim.normalized_value not in literal_rates:
                issues.append('price_value_not_bound_to_minute_unit')
            if not re.search(r'(?:\bper\s+minute\b|/\s*min(?:ute)?\b)', span, re.I):
                issues.append('unconfirmed_per_minute_unit')
            if not re.search(r'\bUSD\b|\bUS\s*\$', span, re.I):
                issues.append('unconfirmed_usd_currency')
            # The declared vendor includes the service/tariff being compared.
            # Conservative lexical support is necessary, never proof of entailment.
            tokens = re.findall(r'[a-z0-9]+', decision['vendor'].lower())
            observed = set(re.findall(r'[a-z0-9]+', span.lower()))
            if not tokens or not set(tokens).issubset(observed):
                issues.append('vendor_service_applicability_unresolved')
            dates = [v for v in (claim.source_date, claim.effective_date) if v]
            if not dates:
                issues.append('publication_or_effective_date_missing')
            for value in dates:
                try:
                    parsed = date.fromisoformat(value)
                    if value not in span or parsed > datetime.now(timezone.utc).date():
                        issues.append('date_not_grounded_or_not_yet_effective')
                except (ValueError, TypeError):
                    issues.append('date_not_grounded_or_not_yet_effective')
            if len(rates) > 1:
                issues.append('conflicting_price_claims')
            # Multiple explicit minute rates in the chosen excerpt are not silently
            # resolved by taking whichever claim the model selected first.
            quoted = re.findall(PRICE, evidence['raw_text'], re.I)
            if len(set(map(float, quoted))) > 1:
                issues.append('multiple_source_rates_require_review')
            related_rates = {float(value) for source in sources
                             for value in re.findall(PRICE, source['raw_text'], re.I)}
            if len(related_rates) > 1:
                issues.append('retrieved_sources_have_competing_rates')
        if issues:
            claim = replace(claim, review_required=True,
                            ambiguity_flags=tuple(sorted(set(claim.ambiguity_flags) | set(issues))))
        checked.append(claim)
    return checked
