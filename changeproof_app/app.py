"""Local-only application using the existing independent ChangeProof engine."""
import argparse
from collections import deque
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import os
from pathlib import Path
import secrets
import sys
import threading
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT.parent / 'changeproof_evidence_intake_v1'))
from provider_client import NebiusClient, MODEL
from extractors.nebius_nemotron_contract import NebiusNemotronExtractor
from recovery_pipeline import run_evidence, evidence_from_retrieval
from retrieval.tavily_runtime import TavilyRetriever
from schemas import StructuredClaim
from fixtures import baseline
from provider_client import credential, redact
import decision_config
from pricing_guard import guarded_claims
from pricing_selection import select_pricing_evidence, model_evidence
import hashlib

VERSION = 'C1-final-extraction-1'

SCENARIOS = {
    'keep': ('Lower-than-threshold fee', 'Build usage costs $0.0005 per minute.', .0005, '$0.0005 per minute'),
    'reopen': ('Budget threshold crossed', 'Build usage costs $0.002 per minute.', .002, '$0.002 per minute'),
    'escalate': ('Contract applicability unresolved', 'A build usage fee may apply; rate and contract scope are not specified.', None, 'fee may apply')}


class FixtureExtractor:
    def __init__(self, scenario): self.scenario = scenario
    def extract_claims(self, evidence, context):
        _, _, value, span = self.scenario
        uncertain = value is None
        return [StructuredClaim('demo_rate', evidence['source_id'], evidence['source_url'], None,
            evidence['publisher'], 'scope' if uncertain else 'pricing_rate',
            'fee_scope' if uncertain else 'fee_rate', 'unknown' if uncertain else value,
            'none' if uncertain else 'usd_per_minute', None, ('C01',), span,
            ('missing_rate', 'missing_scope') if uncertain else (), uncertain, 'low' if uncertain else 'high')]


class Product:
    def __init__(self, live=False, opener=None):
        self.live, self.opener = live, opener
        self.reports, self.retrieved = deque(maxlen=25), {}
        self.calls, self.lock = {'tavily': 0, 'nebius': 0}, threading.Lock()
        self.decision = dict(decision_config.DEFAULT)
        self.credentials = {}
        self.active = False

    def config(self):
        return {'version': VERSION, 'live_enabled': self.live, 'model': MODEL, 'calls': dict(self.calls),
            'providers': {'nebius_configured': self.credential_ready('nebius'),
                          'tavily_configured': self.credential_ready('tavily')},
            'scenarios': {key: {'title': s[0], 'text': s[1]} for key, s in SCENARIOS.items()},
            'decision': dict(self.decision), 'active': self.active}

    def key(self, provider):
        return os.environ.get('NEBIUS_API_KEY' if provider == 'nebius' else 'TAVILY_API_KEY') or self.credentials.get(provider)

    def credential_ready(self, provider):
        try:
            credential(self.key(provider))
            return True
        except ValueError:
            return False

    def sanitize(self, value):
        for provider in ('nebius', 'tavily'):
            if self.key(provider): value = redact(value, self.key(provider))
        return value

    def configure(self, data):
        decision = decision_config.validate(data)
        with self.lock:
            if self.active: raise ValueError('review_in_progress')
            self.decision = decision
        return self.config()

    def set_credentials(self, data):
        if self.active: raise ValueError('review_in_progress')
        pending = {}
        for provider in ('nebius', 'tavily'):
            if data.get(provider): pending[provider] = credential(data[provider])
        with self.lock:
            if self.active: raise ValueError('review_in_progress')
            self.credentials.update(pending)
        return {'providers': self.config()['providers'], 'storage': 'process_memory_only'}

    def reserve(self, provider, confirmation, expected, *, validated_key=None):
        if not self.live or confirmation != expected: raise ValueError('live_execution_not_authorized')
        key = self.key(provider) if validated_key is None else validated_key
        if not key: raise ValueError('provider_credential_not_configured')
        key = credential(key)
        with self.lock:
            if self.calls[provider]: raise ValueError('session_provider_budget_consumed')
            self.calls[provider] += 1
        return key

    def review(self, data):
        if self.active: raise ValueError('review_in_progress')
        mode = data.get('mode')
        provider = {'kind': 'fixture', 'provider_calls': 0}
        if mode == 'demo':
            s = SCENARIOS.get(data.get('scenario'))
            if s is None: raise ValueError('unknown_demo_scenario')
            evidence = {'source_id': 'synthetic_policy', 'source_url': 'https://example.invalid/northstar-policy',
                'publisher': 'Synthetic offline fixture', 'publication_date': None, 'raw_text': s[1],
                'source_role': 'synthetic_fixture'}
            extractor = FixtureExtractor(s)
        elif mode == 'nebius':
            source_id = data.get('source_id')
            if source_id:
                if source_id not in self.retrieved: raise ValueError('unknown_retrieved_source')
                evidence = dict(self.retrieved[source_id])
                if data.get('source_reviewed') is True:
                    evidence['source_role'] = 'operator_reviewed_excerpt'
                    evidence['operator_review_note'] = 'Reviewed by operator; not independently verified truth.'
            else:
                text, url, publisher = data.get('text'), data.get('url'), data.get('publisher')
                if not isinstance(text, str) or not text.strip() or len(text) > 12000: raise ValueError('invalid_evidence_text')
                if not isinstance(url, str) or len(url) > 2000: raise ValueError('invalid_evidence_url')
                parsed = urlsplit(url)
                if parsed.scheme not in {'https', 'http'} or not parsed.hostname or parsed.username or parsed.password:
                    raise ValueError('invalid_evidence_url')
                if not isinstance(publisher, str) or not publisher.strip() or len(publisher) > 200: raise ValueError('invalid_publisher')
                evidence = {'source_id': 'operator_source', 'source_url': url, 'publisher': publisher,
                    'publication_date': None, 'raw_text': text, 'source_role': 'operator_supplied_not_independently_verified'}
            key = self.reserve('nebius', data.get('confirmation'), 'CONFIRM_ONE_NEBIUS_REVIEW')
            extractor = NebiusNemotronExtractor(NebiusClient(key, opener=self.opener), authorized=True)
            extractor.max_output_tokens = 1024
        else: raise ValueError('invalid_review_mode')
        decision = dict(self.decision)
        outcome = decision_config.annotate(run_evidence(evidence, extractor, decision_config.state_for(decision)), decision)
        if mode == 'nebius': provider = extractor.last_result
        result = {'review_id': secrets.token_hex(8), 'reviewed_at': datetime.now(timezone.utc).isoformat(),
            'mode': 'OFFLINE_DEMO' if mode == 'demo' else 'LIVE_NEMOTRON',
            'evidence': evidence, 'outcome': outcome, 'provider': provider,
            'original_decision': self.config()['decision'], 'automatic_vendor_action': False}
        result = self.sanitize(result)
        self.reports.append(result)
        return result

    def live_review(self, data):
        if not self.live or data.get('confirmation') != 'CONFIRM_BOUNDED_LIVE_REVIEW':
            raise ValueError('live_execution_not_authorized')
        if data.get('credits_confirmed') is not True: raise ValueError('promotional_credit_confirmation_required')
        with self.lock:
            if self.active or any(self.calls.values()): raise ValueError('session_provider_budget_consumed')
            if not self.key('tavily') or not self.key('nebius'): raise ValueError('provider_credential_not_configured')
            # Validate and freeze both credentials before consuming either provider budget.
            keys = {provider: credential(self.key(provider)) for provider in ('tavily', 'nebius')}
            decision = decision_config.validate(self.decision)
            if decision['official_domain'].endswith('.invalid'): raise ValueError('real_vendor_domain_required')
            self.active = True
        providers = {'tavily': None, 'nebius': None}
        sources = []
        selection = None
        evidence = {'source_id': 'missing_source', 'source_url': None,
                    'publisher': 'No usable retrieved source', 'publication_date': None, 'raw_text': ''}
        try:
            key = self.reserve('tavily', 'CONFIRM_ONE_TAVILY_SEARCH', 'CONFIRM_ONE_TAVILY_SEARCH',
                               validated_key=keys['tavily'])
            retrieval = TavilyRetriever(key, self.opener).search(decision['research_question'], authorized=True,
                                                                include_domains=[decision['official_domain']])
            if retrieval['status'] != 'SUCCESS':
                providers['tavily'] = retrieval
                raise RuntimeError('tavily_request_failed')
            sources = [evidence_from_retrieval(item) for item in retrieval['evidence']]
            providers['tavily'] = {'status': 'SUCCESS', 'source_count': len(sources),
                'http_status': retrieval['http_status'], 'response': retrieval['provider_response'],
                'retry_performed': False}
            matching = [s for s in sources if (urlsplit(s['source_url']).hostname or '').lower() == decision['official_domain']
                        or (urlsplit(s['source_url']).hostname or '').lower().endswith('.' + decision['official_domain'])]
            if not matching: raise RuntimeError('no_source_on_declared_vendor_domain')
            evidence = dict(matching[0])
            evidence['source_role'] = 'declared_vendor_domain_matched_excerpt_not_independently_verified'
            evidence['selection_note'] = 'First ranked result matching the operator-declared official domain; other results retained.'
            selection = select_pricing_evidence(matching, decision)
            if selection is not None:
                evidence = dict(next(s for s in matching if s['source_id'] == selection['source_id']))
                evidence['source_role'] = 'declared_vendor_domain_matched_excerpt_not_independently_verified'
                evidence['selection_note'] = 'Exact declared runner SKU; headers and qualifiers preserved by source offsets.'
            key = self.reserve('nebius', 'CONFIRM_ONE_NEBIUS_REVIEW', 'CONFIRM_ONE_NEBIUS_REVIEW',
                               validated_key=keys['nebius'])
            inner = NebiusNemotronExtractor(NebiusClient(key, opener=self.opener), authorized=True)
            inner.max_output_tokens = 768
            inner.max_claims = 1
            class ContextExtractor:
                def extract_claims(self, source, context):
                    claims = inner.extract_claims(model_evidence(source, selection), dict(context, operator_decision=decision,
                        instruction='Extract only price for this vendor and stated service/usage. If currency, unit or applicability is uncertain, require review.'))
                    return guarded_claims(claims, source, decision, matching, selection)
            outcome = decision_config.annotate(run_evidence(evidence, ContextExtractor(), decision_config.state_for(decision)), decision)
            outcome['validation_errors'] = sorted(set(outcome['validation_errors']) | {
                flag for row in outcome['claims'] if row['raw_claim']['review_required']
                for flag in row['raw_claim']['ambiguity_flags']})
            providers['nebius'] = inner.last_result
            failure = None if inner.last_result and inner.last_result['status'] == 'SUCCESS' else 'nebius_extraction_failed'
        except Exception as error:
            reason = str(error) if str(error) in {'tavily_request_failed', 'no_source_on_declared_vendor_domain',
                'unsupported_declared_runner', 'target_table_header_missing_or_wrong_unit',
                'target_table_context_not_comparable', 'no_matching_runner_tariff',
                'conflicting_target_prices', 'pricing_qualifiers_exceed_bounded_input'} else 'live_review_interrupted'
            class EmptyExtractor:
                def extract_claims(self, evidence, context): return []
            outcome = run_evidence(evidence, EmptyExtractor(), decision_config.state_for(decision))
            outcome['validation_errors'].append(reason)
            failure = reason
        finally:
            self.active = False
        result = self.sanitize({'review_id': secrets.token_hex(8), 'reviewed_at': datetime.now(timezone.utc).isoformat(),
            'mode': 'MOCK_LIVE_WORKFLOW' if self.opener is not None else 'LIVE_TAVILY_NEMOTRON',
            'evidence': evidence, 'sources': sources, 'outcome': outcome,
            'provider': providers, 'original_decision': decision, 'automatic_vendor_action': False,
            'failure': failure, 'session_attempts': dict(self.calls), 'source_truth_verified': False,
            'application_version': VERSION,
            'extraction_scope': selection,
            'evidence_sha256': hashlib.sha256(evidence['raw_text'].encode('utf-8')).hexdigest(),
            'applicability_gate': 'conservative_lexical_checks_not_semantic_proof'})
        for key in keys.values(): result = redact(result, key)
        self.reports.append(result)
        return result

    def research(self, data):
        if self.active: raise ValueError('review_in_progress')
        query = data.get('query')
        if not isinstance(query, str) or not query.strip() or len(query) > 500: raise ValueError('invalid_query')
        key = self.reserve('tavily', data.get('confirmation'), 'CONFIRM_ONE_TAVILY_SEARCH')
        result = TavilyRetriever(key, self.opener).search(query, authorized=True)
        if result['status'] != 'SUCCESS': return {'mode': 'LIVE_TAVILY', 'provider': result, 'sources': []}
        sources = [evidence_from_retrieval(item) for item in result['evidence']]
        self.retrieved.update({item['source_id']: item for item in sources})
        return {'mode': 'LIVE_TAVILY', 'sources': sources, 'independent_verification': False}


class Server(ThreadingHTTPServer):
    daemon_threads = True
    def __init__(self, address, product):
        super().__init__(address, Handler)
        self.product, self.csrf = product, secrets.token_urlsafe(32)


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *args): pass
    def send(self, status, payload, mime='application/json'):
        if mime == 'application/json': payload = self.server.product.sanitize(payload)
        raw = json.dumps(payload, allow_nan=False).encode() if mime == 'application/json' else payload
        self.send_response(status)
        for key, value in {'Content-Type': mime, 'Content-Length': str(len(raw)), 'Cache-Control': 'no-store',
            'X-Content-Type-Options': 'nosniff', 'Referrer-Policy': 'no-referrer',
            'Content-Security-Policy': "default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self'; connect-src 'self'; frame-ancestors 'none'"}.items(): self.send_header(key, value)
        self.end_headers()
        self.wfile.write(raw)
    def local(self):
        return self.headers.get('Host') in {f'127.0.0.1:{self.server.server_port}', f'localhost:{self.server.server_port}'}
    def do_GET(self):
        if not self.local(): return self.send(403, {'error': 'invalid_host'})
        if self.path == '/api/health': return self.send(200, {'application': 'changeproof', 'interface_version': 2, 'ready': True})
        if self.path == '/api/config': return self.send(200, dict(self.server.product.config(), csrf=self.server.csrf))
        if self.path == '/api/history': return self.send(200, list(self.server.product.reports))
        routes = {'/': ('index.html', 'text/html; charset=utf-8'), '/app.js': ('app.js', 'text/javascript'),
                  '/style.css': ('style.css', 'text/css'), '/decision-flow.svg': ('decision-flow.svg', 'image/svg+xml')}
        if self.path not in routes: return self.send(404, {'error': 'not_found'})
        name, mime = routes[self.path]
        self.send(200, (ROOT / 'web' / name).read_bytes(), mime)
    def do_POST(self):
        try:
            size = int(self.headers.get('Content-Length', '0'))
            if not 0 < size <= 65536: raise ValueError('request_size_invalid')
            self.connection.settimeout(5)
            raw = self.rfile.read(size)
            if len(raw) != size: raise ValueError('incomplete_request')
        except (ValueError, TimeoutError):
            return self.send(400, {'error': 'request_size_invalid'})
        if not self.local() or self.headers.get('X-ChangeProof-CSRF') != self.server.csrf:
            return self.send(403, {'error': 'local_session_required'})
        origin = self.headers.get('Origin')
        if origin and origin not in {f'http://127.0.0.1:{self.server.server_port}', f'http://localhost:{self.server.server_port}'}:
            return self.send(403, {'error': 'cross_origin_rejected'})
        if self.headers.get('Content-Type') != 'application/json': return self.send(415, {'error': 'json_required'})
        if self.path not in {'/api/review', '/api/research', '/api/decision', '/api/credentials', '/api/live-review', '/api/shutdown'}:
            return self.send(404, {'error': 'not_found'})
        try:
            data = json.loads(raw)
            if not isinstance(data, dict): raise ValueError('object_required')
            if self.path == '/api/shutdown':
                if self.server.product.active: raise ValueError('review_in_progress')
                self.send(200, {'stopped': True})
                self.server.product.credentials.clear()
                threading.Thread(target=self.server.shutdown, daemon=True).start()
                return
            action = {'/api/review': self.server.product.review, '/api/research': self.server.product.research,
                      '/api/decision': self.server.product.configure, '/api/credentials': self.server.product.set_credentials,
                      '/api/live-review': self.server.product.live_review}[self.path]
            self.send(200, action(data))
        except ValueError as error:
            allowed = {'live_execution_not_authorized', 'provider_credential_not_configured', 'session_provider_budget_consumed',
                'unknown_demo_scenario', 'invalid_review_mode', 'unknown_retrieved_source', 'invalid_evidence_text',
                'invalid_evidence_url', 'invalid_publisher', 'invalid_query', 'request_size_invalid', 'object_required',
                'review_in_progress', 'promotional_credit_confirmation_required', 'real_vendor_domain_required',
                'missing_credential', 'credential_contains_linebreak', 'credential_contains_invalid_character', 'unsupported_usage_units'}
            allowed.update('invalid_decision:' + field for field in decision_config.DEFAULT)
            self.send(400, {'error': str(error) if str(error) in allowed else 'invalid_request'})
        except Exception: self.send(500, {'error': 'review_failed_no_retry'})


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--port', type=int, default=8765)
    parser.add_argument('--enable-live', action='store_true')
    args = parser.parse_args()
    server = Server(('127.0.0.1', args.port), Product(args.enable_live))
    print(f'ChangeProof: http://127.0.0.1:{server.server_port} (live={args.enable_live})', flush=True)
    try: server.serve_forever()
    except KeyboardInterrupt: pass
    finally: server.server_close()


if __name__ == '__main__': main()

