"""C1 adversarial checks use synthetic provider responses; zero external requests."""
import copy
import io
import json
import os
import unittest
import urllib.error
from unittest.mock import patch

from app import Product
from decision_config import DEFAULT
from test_workflow import MockProviders, Response

REQUEST = {'confirmation': 'CONFIRM_BOUNDED_LIVE_REVIEW', 'credits_confirmed': True}


class AdversarialTransport(MockProviders):
    def __init__(self, case='valid', rate=.002):
        super().__init__(rate=rate)
        self.case = case

    def open(self, request, timeout):
        response = super().open(request, timeout)
        result = json.loads(response.read())
        response.close()
        if 'tavily' in request.full_url:
            if self.case == 'unauthorized_domain': result['results'][0]['url'] = 'https://example.com.attacker.invalid/pricing'
            if self.case == 'empty': result['results'] = []
            if self.case == 'wrong_unit': result['results'][0]['content'] = 'QA vendor build usage costs USD $0.002 per hour. Effective 2026-10-17.'
            if self.case == 'wrong_currency': result['results'][0]['content'] = 'QA vendor build usage costs CAD $0.002 per minute. Effective 2026-10-17.'
            if self.case == 'wrong_service': result['results'][0]['content'] = 'Other vendor storage costs USD $0.002 per minute. Effective 2026-10-17.'
            if self.case == 'missing_date': result['results'][0]['content'] = 'QA vendor build usage costs USD $0.002 per minute.'
            if self.case == 'conflicting': result['results'][0]['content'] += ' QA vendor build usage costs USD $0.003 per minute. Effective 2026-10-17.'
            if self.case == 'other_source_conflict':
                result['results'].append({'url': 'https://example.com/other-pricing', 'title': 'Synthetic other source',
                    'content': 'QA vendor build usage costs USD $0.003 per minute. Effective 2026-10-17.'})
        else:
            content = json.loads(result['choices'][0]['message']['content'])
            claim = content['claims'][0]
            if self.case == 'missing_date': claim['effective_date'] = None
            if self.case == 'invented_date': claim['effective_date'] = '2026-10-16'
            if self.case == 'future_date': claim['effective_date'] = '2099-01-01'
            if self.case == 'unsupported_confidence': claim['extraction_confidence'] = 'certain'
            if self.case == 'missing_span': claim['evidence_span'] = ''
            if self.case == 'hallucinated_value': claim['normalized_value'] = .009
            if self.case == 'number_elsewhere': claim['normalized_value'] = 2026
            if self.case == 'unsupported_applicability': claim['review_required'] = True; claim['ambiguity_flags'] = ['contract_scope_unknown']
            if self.case == 'hallucinated_span': claim['evidence_span'] += ' invented text'
            if self.case == 'contradictory_claims':
                other = copy.deepcopy(claim); other.update(claim_id='other', normalized_value=.003)
                content['claims'].append(other)
            result['choices'][0]['message']['content'] = json.dumps(content)
        if self.case in {'tavily_credits', 'nebius_credits', 'tavily_timeout', 'nebius_timeout'}:
            target = 'tavily' if self.case.startswith('tavily') else 'nebius'
            if target in request.full_url:
                if self.case.endswith('timeout'): raise TimeoutError('synthetic timeout')
                raise urllib.error.HTTPError(request.full_url, 402, 'synthetic no credits', {},
                                             io.BytesIO(b'{"error":"insufficient_credits"}'))
        return Response(json.dumps(result).encode())


class C1Tests(unittest.TestCase):
    def instance(self, transport):
        instance = Product(True, transport)
        instance.configure(dict(DEFAULT, vendor='QA vendor', official_domain='example.com'))
        instance.set_credentials({'nebius': 'offline_n', 'tavily': 'offline_t'})
        return instance

    def test_reproduce_prior_acceptance_holes_at_intake(self):
        # These responses previously had numeric grounding yet no material-scope gate.
        for case, flag in [('wrong_unit', 'unconfirmed_per_minute_unit'),
                           ('wrong_currency', 'unconfirmed_usd_currency'),
                           ('wrong_service', 'vendor_service_applicability_unresolved'),
                           ('missing_date', 'publication_or_effective_date_missing'),
                           ('invented_date', 'date_not_grounded_or_not_yet_effective'),
                           ('unsupported_confidence', 'unsupported_confidence'),
                           ('conflicting', 'multiple_source_rates_require_review')]:
            with self.subTest(case=case), patch.dict(os.environ, {}, clear=True):
                result = self.instance(AdversarialTransport(case)).live_review(REQUEST)
                self.assertEqual(result['outcome']['decision'], 'ESCALATE')
                self.assertIn(flag, result['outcome']['claims'][0]['raw_claim']['ambiguity_flags'])
                self.assertEqual(result['outcome']['trace']['calculations'], {})

    def test_all_adversarial_cases_stop_without_redispatch(self):
        cases = ('wrong_unit', 'wrong_currency', 'wrong_service', 'missing_date', 'invented_date',
                 'future_date', 'unsupported_confidence', 'missing_span', 'hallucinated_value',
                 'unsupported_applicability', 'hallucinated_span', 'contradictory_claims', 'conflicting',
                 'other_source_conflict', 'number_elsewhere',
                 'unauthorized_domain', 'empty', 'tavily_timeout', 'nebius_timeout',
                 'tavily_credits', 'nebius_credits')
        for case in cases:
            with self.subTest(case=case), patch.dict(os.environ, {}, clear=True):
                transport = AdversarialTransport(case)
                instance = self.instance(transport)
                result = instance.live_review(REQUEST)
                self.assertEqual(result['outcome']['decision'], 'ESCALATE')
                self.assertTrue(result['outcome']['validation_errors'])
                expected = 1 if case in {'unauthorized_domain', 'empty', 'tavily_timeout', 'tavily_credits'} else 2
                self.assertEqual(len(transport.calls), expected)
                self.assertFalse(instance.active)
                self.assertEqual(list(instance.reports), [result])
                self.assertNotIn('offline_n', json.dumps(result))
                self.assertNotIn('offline_t', json.dumps(result))
                with self.assertRaises(ValueError): instance.live_review(REQUEST)
                self.assertEqual(len(transport.calls), expected)
                if case.endswith('credits'):
                    self.assertEqual(result['provider'][case.split('_')[0]]['http_status'], 402)

    def test_both_complete_supported_outcomes_have_auditable_calculations(self):
        for rate, expected in [(.0005, 'KEEP'), (.002, 'REOPEN')]:
            with self.subTest(expected=expected), patch.dict(os.environ, {}, clear=True):
                transport = AdversarialTransport(rate=rate)
                instance = self.instance(transport)
                result = instance.live_review(REQUEST)
                self.assertEqual(result['outcome']['decision'], expected)
                self.assertEqual(result['outcome']['validation_errors'], [])
                self.assertEqual(result['outcome']['trace']['calculations']['monthly_cost']['result'], 100000 * rate)
                self.assertEqual(result['provider']['tavily']['http_status'], 200)
                self.assertIn('results', result['provider']['tavily']['response'])
                self.assertEqual(len(result['evidence_sha256']), 64)
                self.assertFalse(result['source_truth_verified'])
                self.assertFalse(result['outcome']['semantic_entailment_proven'])
                self.assertEqual(len(transport.calls), 2)

    def test_every_environment_credential_is_only_checked_not_exported(self):
        with patch.dict(os.environ, {}, clear=True):
            transport = AdversarialTransport()
            instance = self.instance(transport)
            self.assertTrue(all(instance.config()['providers'].values()))
            self.assertNotIn('offline_n', json.dumps(instance.config()))
            with self.assertRaises(ValueError): instance.live_review(dict(REQUEST, credits_confirmed=False))
            self.assertEqual(transport.calls, [])


if __name__ == '__main__': unittest.main()
