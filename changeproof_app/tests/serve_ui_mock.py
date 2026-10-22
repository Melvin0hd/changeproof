"""QA-only server: every provider response is explicitly synthetic."""
import os
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).parents[1]))
from app import Product, Server
from test_workflow import MockProviders
os.environ.pop('NEBIUS_API_KEY',None)
os.environ.pop('TAVILY_API_KEY',None)
server=Server(('127.0.0.1',8767),Product(True,MockProviders()))
try: server.serve_forever()
finally: server.server_close()
