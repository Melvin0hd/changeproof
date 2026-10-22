"""Post-approval anonymous GET checks. Never creates, submits or calls a provider."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import urllib.error
import urllib.request

ROOT=Path(__file__).resolve().parents[1]

def check(commit):
    if not re.fullmatch('[0-9a-f]{40}',commit):raise ValueError('exact_commit_required')
    raw=f'https://raw.githubusercontent.com/Melvin0hd/changeproof/{commit}/'
    site='https://melvin0hd.github.io/changeproof/'
    targets=[('repository','https://github.com/Melvin0hd/changeproof',200,None),
             ('readme',raw+'README.md',200,ROOT/'README.md'),
             ('license',raw+'LICENSE',200,ROOT/'LICENSE'),
             ('genuine_audit',raw+'examples/genuine_ui_review.json',200,ROOT/'examples/genuine_ui_review.json'),
             ('evidence_index',raw+'PUBLIC_EVIDENCE_INDEX.md',200,ROOT/'PUBLIC_EVIDENCE_INDEX.md'),
             ('pages_entry',site,200,ROOT/'judge_demo/index.html'),
             ('decision_flow',site+'design_a_decision_flow/index.html',200,ROOT/'judge_demo/design_a_decision_flow/index.html'),
             ('spatial',site+'spatial/index.html',200,ROOT/'judge_demo/spatial/index.html'),
             ('recorded_data',site+'fixtures.js',200,ROOT/'judge_demo/fixtures.js'),
             ('live_endpoint_absent',site+'api/live-review',404,None)]
    opener=urllib.request.build_opener(urllib.request.ProxyHandler({}));results=[]
    for label,url,expected,path in targets:
        try:
            with opener.open(urllib.request.Request(url,headers={'User-Agent':'ChangeProof-public-release-check'}),timeout=20) as r:
                status=r.status;body=r.read(2_000_001)
        except urllib.error.HTTPError as error:
            status=error.code;body=b''
        except Exception as error:
            results.append({'check':label,'passed':False,'error_type':type(error).__name__});continue
        passed=status==expected and (path is None or hashlib.sha256(body).hexdigest()==hashlib.sha256(path.read_bytes()).hexdigest())
        results.append({'check':label,'url':url,'http_status':status,'expected':expected,'passed':passed})
    return {'status':'PASS' if all(x['passed'] for x in results) else 'FAIL','kind':'anonymous_public_GETs_not_provider_execution','commit':commit,'checks':results}

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--commit',required=True);p.add_argument('--output',required=True);a=p.parse_args()
    result=check(a.commit);Path(a.output).write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8');print(json.dumps(result,indent=2))
    raise SystemExit(0 if result['status']=='PASS' else 1)
