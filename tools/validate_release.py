"""Offline CI/local validation; failed tests remain failed, logs are always retained."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import time

ROOT=Path(__file__).resolve().parents[1]

def validate(output):
    output=Path(output).resolve();output.mkdir(parents=True,exist_ok=True)
    summary={'status':'FAIL','new_provider_calls':0,'credential_environment':'allowlisted_without_keys','checks':[]}
    try:
        if sys.version_info < (3,12):raise ValueError('python_3_12_required')
        node=shutil.which('node')
        if not node:raise ValueError('node_required_for_complete_tests')
        manifest=json.loads((ROOT/'RELEASE_MANIFEST.json').read_text(encoding='utf-8'))
        with tempfile.TemporaryDirectory(prefix='changeproof-offline-') as tmp:
            tmp=Path(tmp);work=tmp/'source';guard=tmp/'network_guard';guard.mkdir()
            shutil.copyfile(ROOT/'tools/offline_guard.py',guard/'sitecustomize.py')
            for name,digest in manifest['files'].items():
                p=ROOT/name
                if p.is_symlink() or not p.resolve().is_relative_to(ROOT):raise ValueError('untrusted_source_path')
                if hashlib.sha256(p.read_bytes()).hexdigest()!=digest:raise ValueError('source_hash_mismatch:'+name)
                q=work/name;q.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(p,q)
            shutil.copyfile(ROOT/'RELEASE_MANIFEST.json',work/'RELEASE_MANIFEST.json')
            allowed={'PATH','SYSTEMROOT','WINDIR','SYSTEMDRIVE','TEMP','TMP','COMSPEC','PATHEXT','PROGRAMFILES','PROGRAMFILES(X86)','LOCALAPPDATA','LANG','LC_ALL'}
            env={k:v for k,v in os.environ.items() if k.upper() in allowed}
            env.update(PYTHONDONTWRITEBYTECODE='1',PYTHONPATH=str(guard),PYTHONIOENCODING='utf-8')
            checks=[('genuine_record',[sys.executable,'-B','VERIFY_RECORDED_EVIDENCE.py'],None),
                    ('engine',[sys.executable,'-B','-m','unittest','discover','-s','changeproof_app/tests','-v'],'Ran 39 tests'),
                    ('interface',[sys.executable,'-B','-m','unittest','discover','-s','tests','-v'],'Ran 18 tests'),
                    ('release',[sys.executable,'-B','-m','unittest','discover','-s','release_tests','-v'],'Ran 4 tests'),
                    ('javascript',[node,'--test','tests/test_view.cjs','tests/test_rc2.cjs'],'tests 16'),
                    ('publication',[sys.executable,'-B','-m','unittest','discover','-s','publication_tests','-v'],'Ran 6 tests'),
                    ('static_package',[sys.executable,'-B','tools/package_static.py','--output',str(tmp/'site')],None)]
            failed=False
            for label,command,expected in checks:
                start=time.monotonic()
                p=subprocess.run(command,cwd=work,env=env,capture_output=True,text=True,encoding='utf-8',errors='replace',timeout=180)
                log=p.stdout+p.stderr;(output/(label+'.log')).write_text(log,encoding='utf-8')
                passed=p.returncode==0 and (expected is None or expected in log) and 'skipped=' not in log
                summary['checks'].append({'name':label,'returncode':p.returncode,'passed':passed,'seconds':round(time.monotonic()-start,3)})
                failed|=not passed
            summary.update(status='FAIL' if failed else 'PASS',python_tests_passed=67 if not failed else None,node_tests_passed=16 if not failed else None,original_http_mock_variants=8,files_verified=len(manifest['files']))
    except Exception as error:
        summary['error']=str(error)
    (output/'summary.json').write_text(json.dumps(summary,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(summary,indent=2))
    return 0 if summary['status']=='PASS' else 1

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--output',required=True)
    raise SystemExit(validate(p.parse_args().output))
