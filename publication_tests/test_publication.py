import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]

def load(name):
    spec=importlib.util.spec_from_file_location(name,ROOT/'tools'/(name+'.py'))
    m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m

class PublicationTests(unittest.TestCase):
    def test_authentic_evidence_is_not_recast_as_fresh_or_accepted_bill(self):
        r=json.loads((ROOT/'examples/genuine_ui_review.json').read_text(encoding='utf-8'))
        self.assertEqual(r['provider']['tavily']['http_status'],200)
        self.assertEqual(r['provider']['nebius']['http_status'],200)
        self.assertEqual(r['provider']['nebius']['model'],'nvidia/Nemotron-3_5-Lightning')
        c=r['outcome']['claims'][0]['raw_claim']
        self.assertEqual(c['normalized_value'],.006)
        self.assertIn(c['evidence_span'],r['evidence']['raw_text'])
        self.assertEqual(r['outcome']['decision'],'ESCALATE')
        self.assertEqual(r['outcome']['trace']['calculations'],{})
        self.assertFalse(r['outcome']['claims'][0]['provenance_checked'])
    def test_workflows_are_manual_public_only_and_pinned(self):
        for name in ['validate.yml','pages.yml']:
            # JSON is valid YAML; parse the actual workflow object without optional packages.
            d=json.loads((ROOT/'.github/workflows'/name).read_text(encoding='utf-8'))
            self.assertLessEqual(set(d['on']),{'workflow_dispatch','workflow_call'})
            self.assertIn('workflow_dispatch',d['on'])
            for job in d['jobs'].values():
                if 'runs-on' in job:self.assertEqual(job['runs-on'],'ubuntu-24.04')
                for step in job.get('steps',[]):
                    if 'uses' in step:self.assertRegex(step['uses'],r'^actions/[a-z-]+@[0-9a-f]{40}$')
            first=next(iter(d['jobs'].values()))
            self.assertIn("github.event.repository.private == false",first['if'])
            self.assertIn("Melvin0hd/changeproof",first['if'])
        pages=json.loads((ROOT/'.github/workflows/pages.yml').read_text())
        self.assertIn('APPROVE_CHANGEPROOF_PUBLIC_DEMO',pages['jobs']['guard']['steps'][0]['run'])
        self.assertEqual(pages['jobs']['build']['needs'],'verify')
        self.assertEqual(pages['jobs']['deploy']['needs'],'build')
    def test_static_artifact_contains_no_operational_backend(self):
        m=load('package_static')
        with tempfile.TemporaryDirectory() as tmp:
            out=Path(tmp)/'site';m.package(out)
            self.assertTrue((out/'index.html').exists());self.assertTrue((out/'LICENSE').exists())
            self.assertFalse(list(out.rglob('*.py')))
            self.assertFalse((out/'.git').exists())
            self.assertFalse((out/'changeproof_app').exists())
            self.assertIn("connect-src 'none'",(out/'design_a_decision_flow/index.html').read_text())
            with self.assertRaises(ValueError):m.package(out)
    def test_packaging_rejects_hash_tampering_before_output(self):
        m=load('package_static');data=json.loads((ROOT/'RELEASE_MANIFEST.json').read_text())
        data['files']['judge_demo/fixtures.js']='0'*64
        with tempfile.TemporaryDirectory() as tmp,patch.object(m.json,'loads',return_value=data):
            out=Path(tmp)/'site'
            with self.assertRaisesRegex(ValueError,'hash_mismatch'):m.package(out)
            self.assertFalse(out.exists())
    def test_external_network_guard_blocks_before_connection(self):
        import runpy,socket
        original_connect=socket.socket.connect;original_dns=socket.getaddrinfo
        try:
            module=runpy.run_path(str(ROOT/'tools/offline_guard.py'))
            with self.assertRaisesRegex(RuntimeError,'external_dns_denied'):socket.getaddrinfo('example.invalid',443)
            self.assertTrue(module['local']('127.0.0.1'));self.assertFalse(module['local']('203.0.113.1'))
        finally:
            socket.socket.connect=original_connect;socket.getaddrinfo=original_dns
    def test_failed_correctness_command_fails_validation_and_keeps_logs(self):
        m=load('validate_release')
        with tempfile.TemporaryDirectory() as tmp,patch.object(m.subprocess,'run',return_value=subprocess.CompletedProcess([],1,'intentional test failure','')):
            self.assertEqual(m.validate(tmp),1)
            r=json.loads((Path(tmp)/'summary.json').read_text())
            self.assertEqual(r['status'],'FAIL');self.assertIsNone(r['python_tests_passed'])
            self.assertTrue((Path(tmp)/'engine.log').exists())
