"""Real captured inputs; model outputs here are explicitly synthetic, not live success."""
import copy
import hashlib
import json
import os
import sys
from pathlib import Path
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from app import Product, MODEL
from test_workflow import Response
from pricing_selection import select_pricing_evidence, model_evidence
from extractors.nebius_nemotron_contract import extraction_prompt

CAPTURE = Path(__file__).parent / 'fixtures' / 'actual_live_input.json'


def capture():
    return json.loads(CAPTURE.read_text(encoding='utf-8'))


class CapturedTransport:
    def __init__(self, variant='real_excerpt', rate=None):
        self.fixture = capture()
        self.variant, self.rate, self.requests = variant, rate, []
        self.prompts = []

    def open(self, request, timeout):
        self.requests.append(request.full_url)
        if 'tavily' in request.full_url:
            result = copy.deepcopy(self.fixture['tavily_response'])
            for row in result['results']:
                text = row['content']
                if self.variant == 'wrong_runner': text = text.replace('`actions_linux`', '`actions_linux_arm`')
                if self.variant == 'missing_heading': text = text.replace('Operating system', 'Unknown column')
                if self.variant == 'wrong_units': text = text.replace('Per-minute rate (USD)', 'Per-hour rate (USD)')
                if self.variant == 'no_match': text = text.replace('Linux 2-core (x64)', 'Linux 4-core (x64)')
                if self.variant == 'unrelated': text = 'Unrelated source with no machine price.'
                if self.variant == 'qualifier': text += '\nNot applicable to public repositories. Discounts require a contract.'
                if self.variant in {'complete_keep', 'complete_reopen'}:
                    # Deliberately synthetic positive control, NOT authentic retrieved evidence.
                    text = ('Effective 2026-10-17. Applies to billable private-repository minutes '
                            'after included minutes are exhausted; no discounts assumed.\n'
                            '| Operating system | Billing SKU | Per-minute rate (USD) |\n --- \n'
                            f'| Linux 2-core (x64) | `actions_linux` | ${self.rate} |')
                row['content'] = text
            if self.variant == 'contradiction':
                result['results'][1]['content'] = result['results'][1]['content'].replace('`actions_linux` | $0.006', '`actions_linux` | $0.007')
            if self.variant == 'mixed_wrong_header':
                for row in result['results']:
                    row['content'] = ('| Operating system | Billing SKU | Per-minute rate (USD) |\n --- \n'
                                      '| Linux 1-core (x64) | `actions_linux_slim` | $0.002 |\n'
                                      '| Operating system | Billing SKU | Per-hour rate (USD) |\n --- \n'
                                      '| Linux 2-core (x64) | `actions_linux` | $0.006 |')
        else:
            body = json.loads(request.data)
            prompt = json.loads(body['messages'][0]['content'])
            self.prompts.append(prompt)
            assert body['max_tokens'] == 768
            assert prompt['output_contract']['properties']['claims']['maxItems'] == 1
            props = prompt['output_contract']['properties']['claims']['items']['properties']
            assert props['unit']['enum'] == ['usd_per_minute']
            assert props['claim_type']['enum'] == ['pricing_rate']
            assert props['criterion_candidates']['maxItems'] == 1
            e = prompt['evidence']
            scope = e['pricing_selection']
            assert len(e['raw_text']) < len(self.fixture['evidence']['raw_text'])
            c = {'claim_id':'target_rate','source_id':e['source_id'],'source_url':e['source_url'],
                 'source_date':e['publication_date'],'publisher':e['publisher'],'claim_type':'pricing_rate',
                 'normalized_proposition':'fee_rate','normalized_value':scope['rate'],
                 'unit':'usd_per_minute','effective_date':None,'criterion_candidates':['C01'],
                 'evidence_span':scope['row']['text'],'ambiguity_flags':[],
                 'review_required':False,'extraction_confidence':'high'}
            if self.variant in {'complete_keep', 'complete_reopen'}: c['effective_date'] = '2026-10-17'
            if self.variant == 'wrong_span': c['evidence_span'] = '| Linux 2-core | `linux_2_core_arm` | $0.005 |'
            if self.variant == 'bare_value': c['evidence_span'] = '$0.006'
            if self.variant == 'wrong_value': c['normalized_value'] = .005
            claims = [c]
            if self.variant == 'multiple_claims': claims.append(dict(c, claim_id='second'))
            choice = {'finish_reason':'stop','message':{'content':json.dumps({'claims':claims})}}
            result = {'model':MODEL,'choices':[choice], 'usage':{'prompt_tokens':100,'completion_tokens':200,'total_tokens':300}}
            if self.variant == 'prior_truncated':
                prior = self.fixture['nebius_response']
                result.update(usage=prior['usage'])
                choice['finish_reason'] = prior['finish_reason']
                choice['message']['content'] = prior['content']
        return Response(json.dumps(result).encode())


def product(transport):
    p = Product(True, transport)
    p.configure(capture()['baseline'])
    p.set_credentials({'tavily':'synthetic_t', 'nebius':'synthetic_n'})
    return p


REQUEST = {'confirmation':'CONFIRM_BOUNDED_LIVE_REVIEW','credits_confirmed':True}


class FinalExtractionTests(unittest.TestCase):
    def test_real_capture_provenance_unchanged(self):
        f = capture()
        self.assertEqual(f['fixture_kind'], 'authentic_sanitized_live_capture_not_gold')
        self.assertEqual(f['nebius_response']['finish_reason'], 'length')
        self.assertEqual(hashlib.sha256(f['evidence']['raw_text'].encode()).hexdigest(),
                         '5cbc7ce0730356f323f46e00847e855295f55193c8d879416957f55b6be1e5e2')

    def test_select_actual_tariff_and_preserve_every_context_fragment(self):
        f = capture(); s = select_pricing_evidence(f['sources'], f['baseline'])
        self.assertEqual(s['billing_sku'], 'actions_linux')
        self.assertEqual(s['rate'], .006)
        self.assertEqual(s['candidate_rows_checked'], 3)
        raw = f['evidence']['raw_text']
        for part in [s['row'], s['header'], *s['context_fragments']]:
            self.assertEqual(part['text'], raw[part['start']:part['end']])
        narrowed = model_evidence(f['evidence'], s)
        self.assertIn(s['row']['text'], narrowed['raw_text'])
        self.assertIn(s['header']['text'], narrowed['raw_text'])
        self.assertLess(len(narrowed['raw_text']), len(raw))
        self.assertIn('included_minutes_and_contract_unconfirmed', s['uncertainties'])
        self.assertIn('retrieved_excerpt_has_omissions', s['uncertainties'])

    def test_tampered_selection_refused(self):
        f=capture();s=select_pricing_evidence(f['sources'],f['baseline'])
        for variant in ('hash', 'offset'):
            wrong=copy.deepcopy(s)
            if variant=='hash': wrong['source_sha256']='0'*64
            else: wrong['row']['start']+=1
            with self.assertRaises(ValueError):model_evidence(f['evidence'],wrong)

    def test_real_inputs_and_failed_provider_response_through_whole_product(self):
        cases = ('real_excerpt','wrong_runner','missing_heading','wrong_units','no_match',
                 'unrelated','qualifier','contradiction','mixed_wrong_header','wrong_span',
                 'bare_value','wrong_value','multiple_claims','prior_truncated')
        for case in cases:
            with self.subTest(case=case),patch.dict(os.environ,{},clear=True):
                t=CapturedTransport(case);p=product(t);r=p.live_review(REQUEST)
                self.assertEqual(r['outcome']['decision'],'ESCALATE')
                self.assertTrue(r['outcome']['validation_errors'])
                self.assertEqual(r['outcome']['trace']['calculations'],{})
                self.assertEqual(len(t.requests),1 if case in {'wrong_runner','missing_heading','wrong_units','no_match','unrelated','contradiction','mixed_wrong_header'} else 2)
                with self.assertRaises(ValueError):p.live_review(REQUEST)
                if case=='real_excerpt':
                    self.assertEqual(len(r['outcome']['claims']),1)
                    self.assertEqual(r['outcome']['claims'][0]['raw_claim']['normalized_value'],.006)
                    self.assertIn('publication_or_effective_date_missing',r['outcome']['validation_errors'])
                if case=='qualifier':
                    self.assertTrue(any('Not applicable to public repositories.' in x['text']
                                        for x in r['extraction_scope']['context_fragments']))
                if case=='prior_truncated':self.assertEqual(r['provider']['nebius']['finish_reason'],'length')

    def test_synthetic_complete_inputs_allow_both_arithmetic_outcomes(self):
        for variant,rate,status,cost in [('complete_keep',.006,'KEEP',600),('complete_reopen',.008,'REOPEN',800)]:
            with self.subTest(variant=variant),patch.dict(os.environ,{},clear=True):
                t=CapturedTransport(variant,rate);r=product(t).live_review(REQUEST)
                self.assertEqual(r['mode'],'MOCK_LIVE_WORKFLOW')
                self.assertEqual(r['outcome']['decision'],status)
                self.assertEqual(r['outcome']['validation_errors'],[])
                self.assertEqual(r['outcome']['trace']['calculations']['monthly_cost']['result'],cost)
                self.assertEqual(r['outcome']['trace']['calculations']['monthly_cost']['threshold'],700)


if __name__=='__main__':unittest.main()
