import io
import json
import os
from pathlib import Path
import sys
import threading
import unittest
import urllib.error
import urllib.request
from unittest.mock import patch
sys.path.insert(0, str(Path(__file__).parents[1]))
from app import Product, Server, MODEL


class Response(io.BytesIO):
    status = 200
    def __enter__(self): return self
    def __exit__(self, *args): self.close()


class Transport:
    def __init__(self): self.calls = []
    def open(self, request, timeout):
        self.calls.append(request.full_url)
        if 'tavily' in request.full_url:
            result = {'results': [{'url': 'https://example.invalid/pricing', 'title': 'Synthetic', 'content': '$0.002 per minute'}]}
        else:
            prompt = json.loads(json.loads(request.data)['messages'][0]['content'])
            e = prompt['evidence']
            c = {'claim_id': 'rate', 'source_id': e['source_id'], 'source_url': e['source_url'],
                'publisher': e['publisher'], 'source_date': None, 'claim_type': 'pricing_rate',
                'normalized_proposition': 'fee_rate', 'normalized_value': .002, 'unit': 'usd_per_minute',
                'effective_date': None, 'criterion_candidates': ['C01'], 'evidence_span': '$0.002 per minute',
                'ambiguity_flags': [], 'review_required': False, 'extraction_confidence': 'high'}
            result = {'model': MODEL, 'choices': [{'finish_reason': 'stop', 'message': {'content': json.dumps({'claims': [c]})}}],
                      'usage': {'prompt_tokens': 10, 'completion_tokens': 10}}
        return Response(json.dumps(result).encode())


class ProductTests(unittest.TestCase):
    def test_three_demo_outcomes_real_adapter(self):
        p = Product()
        with patch('urllib.request.build_opener', side_effect=AssertionError('provider forbidden')):
            for name, expected, cost in [('keep', 'KEEP', 50), ('reopen', 'REOPEN', 200), ('escalate', 'ESCALATE', None)]:
                r = p.review({'mode': 'demo', 'scenario': name})
                self.assertEqual(r['outcome']['decision'], expected)
                self.assertEqual(r['mode'], 'OFFLINE_DEMO')
                self.assertFalse(r['automatic_vendor_action'])
                if cost: self.assertEqual(r['outcome']['trace']['calculations']['monthly_cost']['result'], cost)
                else: self.assertTrue(r['outcome']['validation_errors'])
        self.assertEqual(p.calls, {'nebius': 0, 'tavily': 0})

    def test_disabled_and_missing_credentials(self):
        with self.assertRaisesRegex(ValueError, 'live_execution_not_authorized'):
            Product().reserve('nebius', 'CONFIRM_ONE_NEBIUS_REVIEW', 'CONFIRM_ONE_NEBIUS_REVIEW')
        with patch.dict(os.environ, {}, clear=True), self.assertRaisesRegex(ValueError, 'provider_credential_not_configured'):
            Product(True).reserve('nebius', 'ok', 'ok')

    def test_mock_research_to_unverified_escalation(self):
        t = Transport()
        p = Product(True, t)
        with patch.dict(os.environ, {'TAVILY_API_KEY': 'offline_fake', 'NEBIUS_API_KEY': 'offline_fake'}):
            research = p.research({'query': 'price', 'confirmation': 'CONFIRM_ONE_TAVILY_SEARCH'})
            source = research['sources'][0]
            self.assertEqual(source['query'], 'price')
            self.assertTrue(source['retrieved_at'])
            r = p.review({'mode': 'nebius', 'source_id': source['source_id'], 'confirmation': 'CONFIRM_ONE_NEBIUS_REVIEW'})
            self.assertEqual(r['outcome']['decision'], 'ESCALATE')
            self.assertIn('retrieved_excerpt_requires_source_review', r['outcome']['validation_errors'])
            with self.assertRaisesRegex(ValueError, 'session_provider_budget_consumed'):
                p.research({'query': 'price', 'confirmation': 'CONFIRM_ONE_TAVILY_SEARCH'})
        self.assertEqual(len(t.calls), 2)

    def test_mock_reviewed_source_to_reopen(self):
        p = Product(True, Transport())
        with patch.dict(os.environ, {'TAVILY_API_KEY': 'offline_fake', 'NEBIUS_API_KEY': 'offline_fake'}):
            source = p.research({'query': 'price', 'confirmation': 'CONFIRM_ONE_TAVILY_SEARCH'})['sources'][0]
            r = p.review({'mode': 'nebius', 'source_id': source['source_id'], 'source_reviewed': True,
                          'confirmation': 'CONFIRM_ONE_NEBIUS_REVIEW'})
            self.assertEqual(r['outcome']['decision'], 'REOPEN')
            self.assertFalse(r['outcome']['semantic_entailment_proven'])

    def test_no_silent_retry(self):
        class Broken:
            def open(self, *args, **kw): raise TimeoutError('not logged')
        p = Product(True, Broken())
        data = {'mode': 'nebius', 'text': '$0.002 per minute', 'url': 'https://example.invalid',
                'publisher': 'Synthetic', 'confirmation': 'CONFIRM_ONE_NEBIUS_REVIEW'}
        with patch.dict(os.environ, {'NEBIUS_API_KEY': 'offline_fake'}):
            self.assertEqual(p.review(data)['outcome']['decision'], 'ESCALATE')
            with self.assertRaisesRegex(ValueError, 'session_provider_budget_consumed'): p.review(data)

    def test_invalid_source_never_spends(self):
        p = Product(True, Transport())
        with self.assertRaises(ValueError): p.review({'mode': 'nebius', 'text': 'x', 'url': 'file:///private', 'publisher': 'x'})
        self.assertEqual(p.calls['nebius'], 0)

    def test_history_bounded_and_no_credentials(self):
        p = Product()
        with patch.dict(os.environ, {'NEBIUS_API_KEY': 'offline_fake'}):
            for _ in range(30): p.review({'mode': 'demo', 'scenario': 'keep'})
            self.assertNotIn('offline_fake', json.dumps(p.config()))
            self.assertNotIn('offline_fake', json.dumps(list(p.reports)))
        self.assertEqual(len(p.reports), 25)


class HTTPTests(unittest.TestCase):
    def setUp(self):
        self.server = Server(('127.0.0.1', 0), Product())
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.url = f'http://127.0.0.1:{self.server.server_port}'
        self.transport = urllib.request.build_opener(urllib.request.ProxyHandler({}))
    def tearDown(self):
        self.server.shutdown(); self.server.server_close(); self.thread.join()
    def request(self, path, data=None, **headers):
        req = urllib.request.Request(self.url + path, data=None if data is None else json.dumps(data).encode(),
                                     headers=headers)
        return self.transport.open(req, timeout=5)
    def test_real_http_workflow(self):
        with self.request('/api/config') as r: config = json.load(r)
        with self.request('/api/review', {'mode': 'demo', 'scenario': 'reopen'},
                          **{'Content-Type': 'application/json', 'X-ChangeProof-CSRF': config['csrf']}) as r:
            self.assertEqual(json.load(r)['outcome']['decision'], 'REOPEN')
        with self.request('/api/history') as r: self.assertEqual(len(json.load(r)), 1)
    def test_missing_csrf_blocked(self):
        with self.assertRaises(urllib.error.HTTPError) as e: self.request('/api/review', {'mode': 'demo'})
        self.assertEqual(e.exception.code, 403)
    def test_cross_origin_blocked(self):
        with self.request('/api/config') as r: token = json.load(r)['csrf']
        with self.assertRaises(urllib.error.HTTPError) as e:
            self.request('/api/review', {}, **{'Content-Type': 'application/json', 'X-ChangeProof-CSRF': token, 'Origin': 'https://evil.invalid'})
        self.assertEqual(e.exception.code, 403)
    def test_static_allowlist_and_security_headers(self):
        with self.request('/') as r:
            self.assertIn('ChangeProof', r.read().decode())
            self.assertIn("frame-ancestors 'none'", r.headers['Content-Security-Policy'])
        with self.assertRaises(urllib.error.HTTPError): self.request('/../provider_client.py')


if __name__ == '__main__': unittest.main()
