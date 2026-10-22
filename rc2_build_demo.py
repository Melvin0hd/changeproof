"""Materialize explicitly recorded offline results for a static judge build."""
import json
from pathlib import Path
import shutil
import sys
from unittest.mock import patch
import os

R = Path(__file__).resolve().parent
sys.path.insert(0, str(R))
from design_server import Product, verified_record
sys.path.insert(0, str(R/'changeproof_app/tests'))
from test_c1 import AdversarialTransport, REQUEST
from decision_config import DEFAULT

def build():
    target = R/'judge_demo'
    target.mkdir(exist_ok=True)
    for folder in ['shared','spatial','design_a_decision_flow']:
        shutil.copytree(R/folder, target/folder, dirs_exist_ok=True)
    with patch.dict(os.environ, {}, clear=True):
        product = Product(False)
        reports = {s:product.review({'mode':'demo','scenario':s}) for s in ['keep','reopen','escalate']}
        config = product.config()
        for case in ['empty','conflicting','tavily_timeout']:
            p=Product(True, AdversarialTransport(case))
            p.configure(dict(DEFAULT,vendor='QA vendor',official_domain='example.com'))
            p.set_credentials({'tavily':'offline_placeholder_t','nebius':'offline_placeholder_n'})
            reports[case]=p.live_review(REQUEST)
    data = {'config':dict(config,csrf='static-no-write-transport'), 'recorded':verified_record(), 'reports':reports}
    (target/'fixtures.js').write_text('window.ChangeProofFixtures = '+json.dumps(data,ensure_ascii=True)+';\n',encoding='utf-8')
    shutil.copy2(R/'static_transport.js',target/'static_transport.js')
    for path in [target/'design_a_decision_flow/index.html',target/'spatial/index.html']:
        text=path.read_text(encoding='utf-8')
        text=text.replace('<meta name="viewport"', '<meta http-equiv="Content-Security-Policy" content="default-src \'self\'; script-src \'self\'; style-src \'self\'; connect-src \'none\'; object-src \'none\'; base-uri \'none\'"><meta name="viewport"')
        if 'design_a_decision_flow' in str(path):
            text=text.replace('<script defer src="../shared/app.js">','<script defer src="../fixtures.js"></script><script defer src="../static_transport.js"></script><script defer src="../shared/app.js">')
        path.write_text(text,encoding='utf-8')
    (target/'index.html').write_text('<!doctype html><html lang="en"><meta charset="utf-8"><meta http-equiv="refresh" content="0;url=design_a_decision_flow/"><title>ChangeProof no-key demo</title><a href="design_a_decision_flow/">Open ChangeProof</a></html>',encoding='utf-8')
    (target/'.nojekyll').touch()
    print('Static judge demo built from actual recorded audit and offline engine outputs. Zero external calls.')
if __name__=='__main__':build()
