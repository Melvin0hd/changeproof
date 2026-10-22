import io
import json
import os
from pathlib import Path
import socket
import sys
import time
import unittest
import urllib.request
from unittest.mock import patch
sys.path.insert(0, str(Path(__file__).parents[1]))
from app import Product, MODEL
from decision_config import DEFAULT, validate
from launch import ensure_started, health


class Response(io.BytesIO):
    status = 200
    def __enter__(self): return self
    def __exit__(self, *args): self.close()


class MockProviders:
    def __init__(self, failure=None, rate=.002): self.calls=[]; self.failure=failure; self.rate=rate
    def open(self, request, timeout):
        self.calls.append(request.full_url)
        if self.failure == 'tavily' and 'tavily' in request.full_url: raise TimeoutError('offline fixture')
        if self.failure == 'nebius' and 'nebius' in request.full_url: raise TimeoutError('offline fixture')
        if 'tavily' in request.full_url:
            body=json.loads(request.data)
            assert body['include_domains']==['example.com']
            result={'results': [] if self.failure=='empty' else [
                {'url':'https://example.com/pricing','title':'Synthetic QA vendor',
                 'content':f'QA vendor build usage costs USD ${self.rate} per minute. Effective 2026-10-17.'}]}
        else:
            e=json.loads(json.loads(request.data)['messages'][0]['content'])['evidence']
            claim={'claim_id':'rate','source_id':e['source_id'],'source_url':e['source_url'],
                'publisher':e['publisher'],'source_date':None,'claim_type':'pricing_rate',
                'normalized_proposition':'fee_rate','normalized_value':self.rate,'unit':'usd_per_minute',
                'effective_date':'2026-10-17','criterion_candidates':['C01'],'evidence_span':e['raw_text'],
                'ambiguity_flags':[],'review_required':False,'extraction_confidence':'high'}
            if self.failure=='grounding': claim['evidence_span']='invented'
            result={'model':MODEL,'choices':[{'finish_reason':'stop','message':{'content':json.dumps({'claims':[claim]})}}],
                    'usage':{'prompt_tokens':10,'completion_tokens':10,'total_tokens':20}}
        return Response(json.dumps(result).encode())


class WorkflowTests(unittest.TestCase):
    def product(self, transport):
        p=Product(True,transport)
        p.configure(dict(DEFAULT,vendor='QA vendor',official_domain='example.com'))
        p.set_credentials({'nebius':'offline_fake_n','tavily':'offline_fake_t'})
        return p
    def request(self): return {'confirmation':'CONFIRM_BOUNDED_LIVE_REVIEW','credits_confirmed':True}
    def test_config_validation(self):
        for name,value in [('vendor',''),('monthly_minutes',True),('monthly_minutes',.5),
                           ('budget_threshold_usd',float('nan')),('official_domain','evil.com/path'),('units','requests')]:
            with self.assertRaises(ValueError): validate(dict(DEFAULT,**{name:value}))
    def test_custom_budget_engine_and_trace(self):
        for threshold,status in [(100,'REOPEN'),(250,'KEEP')]:
            p=Product();p.configure(dict(DEFAULT,budget_threshold_usd=threshold))
            r=p.review({'mode':'demo','scenario':'reopen'})
            self.assertEqual(r['outcome']['decision'],status)
            self.assertEqual(r['outcome']['trace']['calculations']['monthly_cost']['threshold'],threshold)
    def test_full_bounded_chain_two_calls(self):
        with patch.dict(os.environ,{},clear=True):
            t=MockProviders();p=self.product(t);r=p.live_review(self.request())
            self.assertEqual(r['mode'],'MOCK_LIVE_WORKFLOW')
            self.assertEqual(r['outcome']['decision'],'REOPEN')
            self.assertEqual(r['outcome']['validation_errors'],[])
            self.assertEqual(len(t.calls),2)
            self.assertEqual(r['original_decision']['vendor'],'QA vendor')
            self.assertIn('retrieved_at',r['evidence'])
            self.assertNotIn('offline_fake',json.dumps(r))
            with self.assertRaises(ValueError): p.live_review(self.request())
            self.assertEqual(len(t.calls),2)
    def test_failure_stops_chain(self):
        with patch.dict(os.environ,{},clear=True):
            for failure,count in [('tavily',1),('empty',1),('nebius',2),('grounding',2)]:
                t=MockProviders(failure);r=self.product(t).live_review(self.request())
                self.assertEqual(r['outcome']['decision'],'ESCALATE')
                self.assertEqual(len(t.calls),count)
    def test_no_confirmation_no_calls(self):
        with patch.dict(os.environ,{},clear=True):
            t=MockProviders();p=self.product(t)
            for request in [{}, {'confirmation':'CONFIRM_BOUNDED_LIVE_REVIEW'}]:
                with self.assertRaises(ValueError): p.live_review(request)
            self.assertEqual(t.calls,[])
    def test_credentials_atomic_private_prefer_process(self):
        with patch.dict(os.environ,{},clear=True):
            p=Product(True)
            with self.assertRaises(ValueError): p.set_credentials({'nebius':'offline_fake','tavily':'bad\nkey'})
            self.assertEqual(p.credentials,{})
            p.set_credentials({'nebius':'offline_secret'})
            self.assertNotIn('offline_secret',json.dumps(p.config()))
            self.assertEqual(p.sanitize({'text':'offline_secret'}),{'text':'[REDACTED]'})
            with patch.dict(os.environ,{'NEBIUS_API_KEY':'process_fake'}): self.assertEqual(p.key('nebius'),'process_fake')
    def test_missing_keys_fail_before_search(self):
        with patch.dict(os.environ,{},clear=True):
            t=MockProviders();p=Product(True,t);p.configure(dict(DEFAULT,official_domain='example.com'))
            with self.assertRaisesRegex(ValueError,'provider_credential_not_configured'): p.live_review(self.request())
            self.assertEqual(t.calls,[])
    def test_in_progress_rejects_parallel_manual_actions(self):
        p=Product(True);p.active=True
        with self.assertRaisesRegex(ValueError,'review_in_progress'): p.review({'mode':'demo','scenario':'keep'})
        with self.assertRaisesRegex(ValueError,'review_in_progress'): p.research({'query':'x'})
    def test_occupied_port_is_actionable_no_spawn(self):
        with patch('launch.health',return_value=False), patch('launch.socket.socket') as socket_factory, patch('launch.subprocess.Popen') as child:
            socket_factory.return_value.__enter__.return_value.connect_ex.return_value=0
            with self.assertRaisesRegex(RuntimeError,'occupied'): ensure_started(8765)
            child.assert_not_called()
    def test_launcher_reuse_and_shutdown_actual(self):
        with socket.socket() as s: s.bind(('127.0.0.1',0));port=s.getsockname()[1]
        result=ensure_started(port)
        try:
            self.assertTrue(result['started']);self.assertTrue(health(port))
            self.assertFalse(ensure_started(port)['started'])
        finally:
            transport=urllib.request.build_opener(urllib.request.ProxyHandler({}))
            with transport.open(f'http://127.0.0.1:{port}/api/config') as r: config=json.load(r)
            req=urllib.request.Request(f'http://127.0.0.1:{port}/api/shutdown',data=b'{}',
                headers={'Content-Type':'application/json','X-ChangeProof-CSRF':config['csrf']})
            with transport.open(req) as r: self.assertTrue(json.load(r)['stopped'])
            for _ in range(20):
                if not health(port): break
                time.sleep(.1)
            self.assertFalse(health(port))
            result['process'].wait(timeout=5)


if __name__=='__main__': unittest.main()
