"""Explicit QA transport; no network-capable provider opener is installed."""
import argparse
import os
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from design_server import ENGINE,Product,make_server
sys.path.insert(0,str(ENGINE/'changeproof_app/tests'))
from test_workflow import MockProviders
from decision_config import DEFAULT
for key in ('NEBIUS_API_KEY','TAVILY_API_KEY'):os.environ.pop(key,None)
p=argparse.ArgumentParser();p.add_argument('--port',type=int,default=8903);p.add_argument('--failure',choices=['tavily','nebius','grounding'],default='tavily');args=p.parse_args()
product=Product(True,MockProviders(args.failure));product.configure(dict(DEFAULT,vendor='Synthetic QA vendor',official_domain='example.com'))
product.set_credentials({'tavily':'offline_fake_t','nebius':'offline_fake_n'})
server=make_server(args.port,product)
print(f'QA MOCK ONLY: http://127.0.0.1:{args.port}',flush=True)
try:server.serve_forever()
finally:server.server_close()
