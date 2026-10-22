import hashlib,json,unittest
from pathlib import Path
R=Path(__file__).resolve().parents[1]
class ReleaseTests(unittest.TestCase):
 def test_original_engine_and_audit_unchanged(self):
  m=json.loads((R/'SOURCE_MANIFEST.json').read_text())
  for p,h in m['frozen_source_and_evidence'].items():self.assertEqual(hashlib.sha256((R/p).read_bytes()).hexdigest(),h,p)
 def test_static_demo_original_audit(self):
  text=(R/'optional/spatial/recorded-data.js').read_text();record=json.loads(text.split(' = ',1)[1].rstrip(';\n'))['record'];self.assertEqual(record,json.loads((R/'examples/genuine_ui_review.json').read_text()));self.assertEqual(record['outcome']['decision'],'ESCALATE');self.assertEqual(record['outcome']['trace']['calculations'],{})
 def test_static_demo_has_no_network_or_backend_dependency(self):
  text=(R/'optional/spatial/app.js').read_text();self.assertNotIn('fetch(',text);self.assertNotIn('XMLHttpRequest',text);self.assertIn("if(body)throw Error",text);html=(R/'optional/spatial/index.html').read_text();self.assertNotIn('value="keep"',html);self.assertNotIn('http://127.0.0.1',html)
 def test_default_launcher_does_not_enable_live(self):
  text=(R/'START_CHANGEPROOF.cmd').read_text();self.assertIn('--design a',text);self.assertNotIn('--enable-live',text)
if __name__=='__main__':unittest.main()
