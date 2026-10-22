import hashlib
import json
from pathlib import Path
import subprocess
import sys
import threading
import unittest
import urllib.error
import urllib.request
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from design_server import AUDIT_HASH, ENGINE, Product, make_server, verified_record
from decision_config import DEFAULT

class DesignContractTests(unittest.TestCase):
    def test_actual_record_is_unchanged(self):
        data = verified_record()
        self.assertEqual(data['sha256'], AUDIT_HASH)
        self.assertEqual(data['record'], json.loads((ENGINE/'examples/genuine_ui_review.json').read_text()))
        self.assertEqual(data['new_provider_calls'], 0)

    def test_recorded_pipeline_revalidates_without_inference(self):
        data = verified_record()
        self.assertEqual(data['revalidation']['status'], 'PASS')
        self.assertEqual(data['revalidation']['decision'], 'ESCALATE')
        self.assertEqual(data['record']['outcome']['trace']['calculations'], {})

    def test_three_real_outcomes_from_existing_engine(self):
        with patch.dict('os.environ', {}, clear=True):
            p = Product(False)
            for scenario, expected in [('keep','KEEP'), ('reopen','REOPEN'), ('escalate','ESCALATE')]:
                r = p.review({'mode':'demo','scenario':scenario})
                self.assertEqual(r['outcome']['decision'], expected)
            self.assertEqual(p.calls, {'tavily':0,'nebius':0})

    def test_edited_budget_changes_real_outcome(self):
        p = Product(False)
        p.configure(dict(DEFAULT, budget_threshold_usd=250))
        result = p.review({'mode':'demo','scenario':'reopen'})
        self.assertEqual(result['outcome']['decision'],'KEEP')
        self.assertEqual(result['outcome']['trace']['calculations']['monthly_cost']['threshold'],250)

    def test_model_illustration_cannot_modify_audit(self):
        node = __import__('shutil').which('node')
        if not node:
            self.skipTest('Node is optional for this JavaScript test')
        program = "const fs=require('fs'),assert=require('assert/strict'),m=require('./shared/model.js');const r=JSON.parse(fs.readFileSync(process.argv[1],'utf8'));const before=JSON.stringify(r);const v=m.view(r,'recorded');assert.equal(v.status,'ESCALATE');assert.equal(v.rate,.006);assert.equal(v.illustration,600);assert.equal(v.acceptedCalculation,null);assert.equal(JSON.stringify(r),before);assert.equal(v.claim.extraction_confidence,'medium');assert.equal(v.sources.length,3);assert.equal(v.label,'RECORDED PROVIDER EVIDENCE');"
        result = subprocess.run([node,'-e',program,str(ENGINE/'examples/genuine_ui_review.json')],cwd=ROOT,capture_output=True,text=True)
        self.assertEqual(result.returncode,0,result.stderr)

    def test_renderer_rejects_unknown_or_missing_classification(self):
        node = __import__('shutil').which('node')
        if not node:
            self.skipTest('Node is optional for this JavaScript test')
        program="const assert=require('assert/strict'),m=require('./shared/model.js');for(const r of [{},{outcome:{decision:'WINNER'}},{outcome:{decision:'KEEP'}}])assert.throws(()=>m.view(r,'recorded'));"
        result = subprocess.run([node,'-e',program],cwd=ROOT,capture_output=True,text=True)
        self.assertEqual(result.returncode,0,result.stderr)

    def test_both_views_reuse_identical_contract_and_logic(self):
        for d in ['design_a_decision_flow','design_b_evidence_lens']:
            text=(ROOT/d/'index.html').read_text()
            self.assertIn('../shared/app.js',text)
            self.assertIn('../shared/model.js',text)
        text=(ROOT/'shared/app.js').read_text()
        self.assertIn("'/api/review'",text)
        self.assertIn("'/api/live-review'",text)
        self.assertNotIn('localStorage',text)
        self.assertIn("for(const id of ['review','mode','edit','reduce-motion'])$(id).disabled=true",text)
        self.assertNotIn('setInterval',text)

class HTTPTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server=make_server(0,Product(False))
        cls.thread=threading.Thread(target=cls.server.serve_forever,daemon=True);cls.thread.start()
        cls.url=f'http://127.0.0.1:{cls.server.server_port}'
        cls.opener=urllib.request.build_opener(urllib.request.ProxyHandler({}))
        with cls.opener.open(cls.url+'/api/config') as r:cls.config=json.load(r)
    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown();cls.server.server_close();cls.thread.join()
    def post(self,path,body,csrf=True,origin=None):
        headers={'Content-Type':'application/json'}
        if csrf:headers['X-ChangeProof-CSRF']=self.config['csrf']
        if origin:headers['Origin']=origin
        return self.opener.open(urllib.request.Request(self.url+path,data=json.dumps(body).encode(),headers=headers))
    def test_both_prototypes_and_assets_are_local(self):
        for path in ['/design_a_decision_flow/','/design_b_evidence_lens/','/shared/style.css','/shared/model.js','/shared/lucide.min.js','/JUDGE_DEMO_GUIDE.md']:
            with self.opener.open(self.url+path) as r:
                self.assertEqual(r.status,200)
                self.assertIn("default-src 'self'",r.headers['Content-Security-Policy'])
    def test_recorded_endpoint_is_labeled_not_new_review(self):
        previous = len(self.server.product.reports)
        with self.opener.open(self.url+'/api/recorded') as r:data=json.load(r)
        self.assertEqual(data['presentation_kind'],'RECORDED_PROVIDER_EVIDENCE')
        self.assertEqual(data['new_provider_calls'],0)
        self.assertEqual(len(self.server.product.reports),previous)
    def test_all_review_outcomes_and_export_contract(self):
        for case,status in [('keep','KEEP'),('reopen','REOPEN'),('escalate','ESCALATE')]:
            with self.post('/api/review',{'mode':'demo','scenario':case}) as r:data=json.load(r)
            self.assertEqual(data['outcome']['decision'],status)
            self.assertEqual(data['mode'],'OFFLINE_DEMO')
            self.assertFalse(data['automatic_vendor_action'])
    def test_no_keys_or_live_execution_by_default(self):
        with self.assertRaises(urllib.error.HTTPError) as e:
            self.post('/api/live-review',{'confirmation':'CONFIRM_BOUNDED_LIVE_REVIEW','credits_confirmed':True})
        self.assertEqual(e.exception.code,400)
        self.assertEqual(self.server.product.calls,{'tavily':0,'nebius':0})
    def test_csrf_required(self):
        with self.assertRaises(urllib.error.HTTPError) as e:self.post('/api/review',{'mode':'demo','scenario':'keep'},csrf=False)
        self.assertEqual(e.exception.code,403)
    def test_cross_origin_rejected(self):
        with self.assertRaises(urllib.error.HTTPError) as e:self.post('/api/review',{'mode':'demo','scenario':'keep'},origin='https://outside.invalid')
        self.assertEqual(e.exception.code,403)
    def test_private_paths_and_traversal_not_served(self):
        for path in ['/release_repository/examples/genuine_ui_review.json','/.git/config','/shared/../design_server.py','/design_server.py']:
            with self.assertRaises(urllib.error.HTTPError) as e:self.opener.open(self.url+path)
            self.assertEqual(e.exception.code,404)

if __name__=='__main__':unittest.main()
