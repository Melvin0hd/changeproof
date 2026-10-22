"""Single Windows launch path; reuse a healthy app instead of duplicating it."""
import argparse
import json
from pathlib import Path
import socket
import subprocess
import sys
import time
import urllib.error
import urllib.request
import webbrowser

ROOT = Path(__file__).resolve().parent
STARTED_PROCESSES = []


def health(port):
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
    try:
        with opener.open(f'http://127.0.0.1:{port}/api/health', timeout=1) as response:
            data = json.loads(response.read(4096))
        return data.get('application') == 'changeproof' and data.get('interface_version') == 2 and data.get('ready') is True
    except (OSError, ValueError): return False


def ensure_started(port=8765, timeout=10):
    if health(port): return {'started': False, 'port': port}
    with socket.socket() as sock:
        if sock.connect_ex(('127.0.0.1', port)) == 0:
            raise RuntimeError(f'Port {port} is occupied by an older app or another service. Stop that instance or launch with --port 8766.')
    child = subprocess.Popen([sys.executable, '-B', str(ROOT / 'app.py'), '--enable-live', '--port', str(port)],
        cwd=ROOT, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if health(port):
            child.stdout.close(); child.stderr.close()
            STARTED_PROCESSES.append(child)
            return {'started': True, 'port': port, 'pid': child.pid, 'process': child}
        if child.poll() is not None:
            raise RuntimeError('ChangeProof server exited during startup. Verify Python 3.12+, readable source files and an unused port.')
        time.sleep(.15)
    child.terminate(); child.wait(timeout=5)
    raise RuntimeError('ChangeProof health check timed out. Check local firewall permissions; no provider calls occurred.')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--port', type=int, default=8765)
    parser.add_argument('--no-browser', action='store_true')
    args = parser.parse_args()
    try:
        if sys.version_info < (3, 12): raise RuntimeError('Python 3.12 or newer is required.')
        result = ensure_started(args.port)
        url = f'http://127.0.0.1:{args.port}'
        if not args.no_browser: webbrowser.open(url)
        print(('Started' if result['started'] else 'Reused existing') + ' ChangeProof: ' + url)
        print('Use Shut down in the app to stop it. Live requests require the in-app confirmation.')
    except RuntimeError as error:
        print('STARTUP BLOCKED: ' + str(error))
        raise SystemExit(1)


if __name__ == '__main__': main()
