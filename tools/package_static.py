"""Create the static Pages artifact from pinned files, without regenerating evidence."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil

ROOT=Path(__file__).resolve().parents[1]

def package(output):
    output=Path(output).resolve()
    if output.exists():
        raise ValueError('output_must_not_exist')
    if output == ROOT or ROOT.is_relative_to(output):
        raise ValueError('unsafe_output_path')
    manifest=json.loads((ROOT/'RELEASE_MANIFEST.json').read_text(encoding='utf-8'))
    names=[n for n in manifest['files'] if n.startswith('judge_demo/')]
    if not names:
        raise ValueError('static_artifact_missing')
    for n in names+['LICENSE','THIRD_PARTY_NOTICES.md']:
        p=ROOT/n
        if p.is_symlink() or not p.resolve().is_relative_to(ROOT):
            raise ValueError('untrusted_artifact_path')
        if hashlib.sha256(p.read_bytes()).hexdigest()!=manifest['files'][n]:
            raise ValueError('static_artifact_hash_mismatch')
    for n in names:
        target=output/Path(n).relative_to('judge_demo')
        target.parent.mkdir(parents=True,exist_ok=True)
        shutil.copyfile(ROOT/n,target)
    for n in ['LICENSE','THIRD_PARTY_NOTICES.md']:
        shutil.copyfile(ROOT/n,output/n)
    print(json.dumps({'static_files':len(names)+2,'new_provider_calls':0,'live_backend_included':False}))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--output',required=True)
    package(p.parse_args().output)
