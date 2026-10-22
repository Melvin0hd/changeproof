"""Isolated browser rehearsal: injected synthetic transports, never real providers."""
import os
from pathlib import Path
import sys
import threading
import time

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from app import Server
from test_c1 import AdversarialTransport, C1Tests


class BrowserTransport(AdversarialTransport):
    def open(self, request, timeout):
        if self.case == 'tavily_timeout':
            time.sleep(3)  # Synthetic delay to inspect the real loading/disabled UI.
        return super().open(request, timeout)


def main():
    for name in ('NEBIUS_API_KEY', 'TAVILY_API_KEY'):
        os.environ.pop(name, None)
    servers, threads = [], []
    try:
        for port, case, rate in [(8871, 'valid', .002), (8872, 'valid', .0005),
                                 (8873, 'missing_date', .002), (8874, 'tavily_timeout', .002),
                                 (8875, 'nebius_credits', .002)]:
            transport = BrowserTransport(case, rate)
            instance = C1Tests().instance(transport)
            if port == 8871: instance.credentials.clear()
            server = Server(('127.0.0.1', port), instance)
            servers.append(server)
            thread = threading.Thread(target=server.serve_forever, daemon=True)
            thread.start(); threads.append(thread)
            print(f'OFFLINE MOCK ONLY: http://127.0.0.1:{port}/ case={case}', flush=True)
        while any(t.is_alive() for t in threads): time.sleep(.2)
    except KeyboardInterrupt:
        pass
    finally:
        for server in servers:
            server.shutdown(); server.server_close()
            print({'port': server.server_port, 'mock_attempts': server.product.calls,
                   'real_provider_calls': 0}, flush=True)


if __name__ == '__main__': main()
