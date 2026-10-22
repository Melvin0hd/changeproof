"""Actual JS handlers, mocked DOM and providers, real local HTTP. No browser claim."""
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import threading
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from app import Server
from test_final_extraction import CapturedTransport, product

NODE = shutil.which('node')
TEST_ENV = {k: os.environ[k] for k in ('PATH','SYSTEMROOT','WINDIR','SYSTEMDRIVE','TEMP','TMP','COMSPEC') if k in os.environ}


class FinalUITests(unittest.TestCase):
    @unittest.skipUnless(NODE, 'Optional Node.js UI-logic test runtime unavailable')
    def test_actual_javascript_to_http_to_pipeline_and_audit(self):
        for variant, expected, rate in [('real_excerpt','ESCALATE',None),('complete_keep','KEEP',.006),
                                      ('complete_reopen','REOPEN',.008),('prior_truncated','ESCALATE',None),
                                      ('missing_heading','ESCALATE',None),('wrong_runner','ESCALATE',None),
                                      ('qualifier','ESCALATE',None),('contradiction','ESCALATE',None)]:
            with self.subTest(variant=variant),patch.dict(os.environ,TEST_ENV,clear=True):
                transport=CapturedTransport(variant,rate)
                server=Server(('127.0.0.1',0),product(transport))
                thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
                try:
                    result=subprocess.run([NODE,str(Path(__file__).with_name('final_ui.cjs')),
                        f'http://127.0.0.1:{server.server_port}',expected],capture_output=True,text=True,timeout=20)
                    self.assertEqual(result.returncode,0,result.stdout+result.stderr)
                    report=json.loads(result.stdout)
                    self.assertEqual(report['ui_logic'],'PASS')
                    self.assertEqual(report['dom'],'test_double_not_browser')
                    self.assertEqual(len(server.product.reports),1)
                    self.assertEqual(len(transport.requests),1 if variant in {'missing_heading','wrong_runner','contradiction'} else 2)
                finally:
                    server.shutdown();server.server_close();thread.join()


if __name__=='__main__':unittest.main()
