"""Synthetic transports only; the actual local HTTP application is exercised."""
import json
import os
import unittest
import urllib.error
from unittest.mock import patch

import test_app as http_fixture
from test_workflow import MockProviders, Response
from app import Product
from decision_config import DEFAULT


REQUEST = {'confirmation': 'CONFIRM_BOUNDED_LIVE_REVIEW', 'credits_confirmed': True}


def product(transport):
    instance = Product(True, transport)
    instance.configure(dict(DEFAULT, vendor='QA vendor', official_domain='example.com'))
    return instance


class PreflightTests(unittest.TestCase):
    def test_each_missing_credential_blocks_before_either_request(self):
        for missing in ('TAVILY_API_KEY', 'NEBIUS_API_KEY'):
            with self.subTest(missing=missing), patch.dict(os.environ, {}, clear=True):
                os.environ['NEBIUS_API_KEY' if missing == 'TAVILY_API_KEY' else 'TAVILY_API_KEY'] = 'offline_fake'
                transport = MockProviders()
                instance = product(transport)
                with self.assertRaisesRegex(ValueError, 'provider_credential_not_configured'):
                    instance.live_review(REQUEST)
                self.assertEqual(transport.calls, [])
                self.assertEqual(instance.calls, {'tavily': 0, 'nebius': 0})
                self.assertFalse(instance.active)

    def test_each_invalid_credential_blocks_before_search(self):
        for provider in ('TAVILY_API_KEY', 'NEBIUS_API_KEY'):
            for value in (' ', '\t', 'bad\nkey', 'bad\rkey', 'bad key', 'bad\x00key', 'bad\u200bkey'):
                with self.subTest(provider=provider, value_kind=repr(value)), patch('app.os.environ',
                        {'TAVILY_API_KEY': 'offline_t', 'NEBIUS_API_KEY': 'offline_n', provider: value}):
                    transport = MockProviders()
                    instance = product(transport)
                    with self.assertRaises(ValueError): instance.live_review(REQUEST)
                    self.assertEqual(transport.calls, [])
                    self.assertEqual(instance.calls, {'tavily': 0, 'nebius': 0})
                    self.assertFalse(instance.active)
                    self.assertFalse(instance.config()['providers'][
                        'tavily_configured' if provider == 'TAVILY_API_KEY' else 'nebius_configured'])

    def test_environment_changes_cannot_replace_validated_session_keys(self):
        class ChangingTransport(MockProviders):
            def open(self, request, timeout):
                expected = 'offline_t' if 'tavily' in request.full_url else 'offline_n'
                if request.get_header('Authorization') != 'Bearer ' + expected:
                    raise AssertionError('wrong synthetic session credential')
                response = super().open(request, timeout)
                os.environ['NEBIUS_API_KEY'] = 'bad\nreplacement'
                os.environ.pop('TAVILY_API_KEY', None)
                return response
        with patch.dict(os.environ, {'TAVILY_API_KEY': 'offline_t', 'NEBIUS_API_KEY': 'offline_n'}, clear=True):
            transport = ChangingTransport()
            instance = product(transport)
            result = instance.live_review(REQUEST)
            self.assertEqual(result['outcome']['decision'], 'REOPEN')
            self.assertEqual(len(transport.calls), 2)
            self.assertNotIn('offline_n', json.dumps(result))
            self.assertNotIn('offline_t', json.dumps(result))

    def test_invalid_manual_single_provider_does_not_reserve_attempt(self):
        with patch.dict(os.environ, {'NEBIUS_API_KEY': 'bad\nkey'}, clear=True):
            instance = product(MockProviders())
            with self.assertRaises(ValueError): instance.reserve('nebius', 'ok', 'ok')
            self.assertEqual(instance.calls['nebius'], 0)

    def test_validated_preflight_is_not_claimed_provider_authentication(self):
        with patch.dict(os.environ, {'TAVILY_API_KEY': 'offline_t', 'NEBIUS_API_KEY': 'offline_n'}, clear=True):
            transport = MockProviders('nebius')
            instance = product(transport)
            self.assertTrue(all(instance.config()['providers'].values()))
            result = instance.live_review(REQUEST)
            self.assertEqual(result['outcome']['decision'], 'ESCALATE')
            self.assertEqual(len(transport.calls), 2)
            with self.assertRaises(ValueError): instance.live_review(REQUEST)
            self.assertEqual(len(transport.calls), 2)


class UIHTTPPreflightTests(unittest.TestCase):
    setUp = http_fixture.HTTPTests.setUp
    tearDown = http_fixture.HTTPTests.tearDown
    request = http_fixture.HTTPTests.request

    def post(self, path, payload):
        with self.request('/api/config') as response: config = json.load(response)
        return self.request(path, payload, **{'Content-Type': 'application/json',
                            'X-ChangeProof-CSRF': config['csrf']})

    def test_real_ui_endpoint_blocks_invalid_nebius_before_mock_search(self):
        with patch.dict(os.environ, {'TAVILY_API_KEY': 'offline_t', 'NEBIUS_API_KEY': 'bad\nkey'}, clear=True):
            transport = MockProviders()
            self.server.product = product(transport)
            with self.assertRaises(urllib.error.HTTPError) as caught: self.post('/api/live-review', REQUEST)
            with caught.exception as response:
                self.assertEqual(response.code, 400)
                self.assertEqual(json.load(response), {'error': 'credential_contains_linebreak'})
            self.assertEqual(transport.calls, [])
            with self.request('/api/history') as response: self.assertEqual(json.load(response), [])

    def test_masked_form_to_full_mock_review_to_audit_and_no_redispatch(self):
        with patch.dict(os.environ, {}, clear=True):
            transport = MockProviders()
            self.server.product = product(transport)
            with self.post('/api/credentials', {'tavily': 'offline_t', 'nebius': 'offline_n'}) as response:
                self.assertEqual(json.load(response)['storage'], 'process_memory_only')
            with self.post('/api/live-review', REQUEST) as response: result = json.load(response)
            self.assertEqual(result['mode'], 'MOCK_LIVE_WORKFLOW')
            self.assertEqual(result['outcome']['decision'], 'REOPEN')
            self.assertEqual(result['outcome']['validation_errors'], [])
            self.assertIn('$0.002 per minute', result['outcome']['claims'][0]['raw_claim']['evidence_span'])
            self.assertEqual(result['session_attempts'], {'tavily': 1, 'nebius': 1})
            with self.request('/api/history') as response: history = json.load(response)
            self.assertEqual(history, [result])
            self.assertNotIn('offline_', json.dumps(history))
            with self.assertRaises(urllib.error.HTTPError): self.post('/api/live-review', REQUEST)
            self.assertEqual(len(transport.calls), 2)

    def test_schema_content_finish_and_grounding_fail_closed_through_ui(self):
        class InvalidResponse(MockProviders):
            def open(self, request, timeout):
                response = super().open(request, timeout)
                if 'tavily' in request.full_url: return response
                result = json.loads(response.read())
                response.close()
                choice = result['choices'][0]
                if self.failure == 'missing_content': choice['message']['content'] = ''
                elif self.failure == 'reasoning_only': choice['message'] = {'content': '', 'reasoning_content': 'synthetic reasoning'}
                elif self.failure == 'invalid_json': choice['message']['content'] = '{'
                elif self.failure == 'incomplete': choice['finish_reason'] = 'length'
                elif self.failure == 'extra_property':
                    content = json.loads(choice['message']['content'])
                    content['meta'] = 'forbidden synthetic field'
                    choice['message']['content'] = json.dumps(content)
                return Response(json.dumps(result).encode())
        with patch.dict(os.environ, {'TAVILY_API_KEY': 'offline_t', 'NEBIUS_API_KEY': 'offline_n'}, clear=True):
            for failure in ('tavily', 'empty', 'nebius', 'grounding', 'missing_content',
                            'reasoning_only', 'invalid_json', 'incomplete', 'extra_property'):
                with self.subTest(failure=failure):
                    transport = InvalidResponse(failure)
                    self.server.product = product(transport)
                    with self.post('/api/live-review', REQUEST) as response: result = json.load(response)
                    self.assertEqual(result['outcome']['decision'], 'ESCALATE')
                    self.assertEqual(len(transport.calls), 1 if failure in ('tavily', 'empty') else 2)
                    self.assertFalse(self.server.product.active)
                    with self.assertRaises(urllib.error.HTTPError): self.post('/api/live-review', REQUEST)
                    self.assertNotIn('offline_', json.dumps(result))


if __name__ == '__main__': unittest.main()
