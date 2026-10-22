import hashlib
import json
from pathlib import Path
import threading
import unittest
import urllib.request
from unittest.mock import patch

R=Path(__file__).resolve().parents[1]
from design_server import make_server, Product

class RC2Tests(unittest.TestCase):
 def test_frozen_engine_and_benchmark_bytes(self):
  manifest=json.loads((R/'SOURCE_MANIFEST.json').read_text(encoding='utf-8'))
  for path,digest in manifest['frozen_source_and_evidence'].items():
   self.assertEqual(hashlib.sha256((R/path).read_bytes()).hexdigest(),digest,path)
 def test_no_duplicate_calls_for_readonly_assets(self):
  product=Product(False);s=make_server(0,product);t=threading.Thread(target=s.serve_forever,daemon=True);t.start()
  try:
   url=f'http://127.0.0.1:{s.server_port}';op=urllib.request.build_opener(urllib.request.ProxyHandler({}))
   for _ in range(3):
    for path in ['/spatial/index.html','/shared/bridge.js','/shared/presentation.js','/spatial/app.js','/spatial/core.js','/spatial/style.css']:
     with op.open(url+path) as r:
      self.assertEqual(r.status,200)
      if path.endswith('index.html'):self.assertIn("connect-src 'none'; frame-ancestors 'self'",r.headers['Content-Security-Policy'])
   self.assertEqual(product.calls,{'tavily':0,'nebius':0});self.assertEqual(len(product.reports),0)
   with op.open(url+'/design_a_decision_flow/') as r:self.assertIn("frame-ancestors 'none'",r.headers['Content-Security-Policy'])
  finally:s.shutdown();s.server_close();t.join()
 def test_static_snapshot_audit_is_exact(self):
  text=(R/'judge_demo/fixtures.js').read_text(encoding='utf-8');d=json.loads(text.split(' = ',1)[1].strip().rstrip(';'))
  self.assertEqual(d['recorded']['record'],json.loads((R/'examples/genuine_ui_review.json').read_text(encoding='utf-8')))
  self.assertFalse(d['config']['live_enabled'])
 def test_same_fixture_name_does_not_hardcode_classification(self):
  p=Product(False);p.configure(dict(p.decision,budget_threshold_usd=250))
  self.assertEqual(p.review({'mode':'demo','scenario':'reopen'})['outcome']['decision'],'KEEP')
