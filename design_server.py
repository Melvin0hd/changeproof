"""Thin static presentation adapter around the unchanged F1 application."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import webbrowser

ROOT = Path(__file__).resolve().parent
ENGINE = ROOT if (ROOT / "changeproof_app").exists() else ROOT / "release_repository"
sys.path.insert(0, str(ENGINE / "changeproof_app"))
from app import Handler, Product, Server

AUDIT_HASH = "6dfc0d4f6c1ebd0c6d5ba9b97f7fcd54e2e6431a2e1ca6583382d849a19901cc"

def verified_record():
    raw = (ENGINE / "examples/genuine_ui_review.json").read_bytes()
    if hashlib.sha256(raw).hexdigest() != AUDIT_HASH:
        raise ValueError("recorded_evidence_hash_mismatch")
    # The original verifier replays the captured response through the frozen
    # schema, literal support, applicability guard and decision adapter offline.
    keep = {'PATH','SYSTEMROOT','WINDIR','SYSTEMDRIVE','TEMP','TMP','COMSPEC','PATHEXT','PROGRAMFILES','PROGRAMFILES(X86)','LOCALAPPDATA'}
    safe_env = {k:v for k,v in os.environ.items() if k.upper() in keep}
    result = subprocess.run([sys.executable, "-B", str(ENGINE / "VERIFY_RECORDED_EVIDENCE.py")],
                            capture_output=True, text=True, timeout=20, env=safe_env)
    if result.returncode:
        raise ValueError("recorded_evidence_revalidation_failed")
    verification = json.loads(result.stdout)
    return {"record": json.loads(raw), "revalidation": verification, "sha256": AUDIT_HASH,
            "presentation_kind": "RECORDED_PROVIDER_EVIDENCE", "new_provider_calls": 0}

class DesignHandler(Handler):
    def send(self, status, payload, mime='application/json'):
        if self.path == '/spatial/index.html' and status == 200:
            self.send_response(status)
            headers = {'Content-Type': mime, 'Content-Length': str(len(payload)),
                       'Cache-Control': 'no-store', 'X-Content-Type-Options': 'nosniff',
                       'Referrer-Policy': 'no-referrer',
                       'Content-Security-Policy': "default-src 'self'; script-src 'self'; style-src 'self'; connect-src 'none'; frame-ancestors 'self'"}
            for key, value in headers.items(): self.send_header(key, value)
            self.end_headers()
            self.wfile.write(payload)
            return
        return super().send(status, payload, mime)

    def do_GET(self):
        if not self.local():
            return self.send(403, {"error": "invalid_host"})
        if self.path == "/api/recorded":
            try:
                return self.send(200, verified_record())
            except (ValueError, subprocess.TimeoutExpired):
                return self.send(422, {"error": "recorded_evidence_verification_failed"})
        routes = {"/": ("START_HERE.html", "text/html; charset=utf-8")}
        for name in ["DESIGN_COMPARISON.md", "JUDGE_DEMO_GUIDE.md", "PUBLIC_RELEASE_READINESS.md", "VIDEO_PRODUCTION.md"]:
            routes["/" + name] = (name, "text/plain; charset=utf-8")
        for design in ["design_a_decision_flow", "design_b_evidence_lens"]:
            routes["/" + design + "/"] = (design + "/index.html", "text/html; charset=utf-8")
            routes["/" + design + "/index.html"] = routes["/" + design + "/"]
        for name, mime in [("app.js", "text/javascript; charset=utf-8"), ("model.js", "text/javascript; charset=utf-8"), ("style.css", "text/css; charset=utf-8"), ("start.css", "text/css; charset=utf-8"), ("lucide.min.js", "text/javascript"), ("LUCIDE_LICENSE", "text/plain; charset=utf-8")]:
            routes["/shared/" + name] = ("shared/" + name, mime)
        for name in ['presentation.js', 'bridge.js', 'bridge.css']:
            routes['/shared/' + name] = ('shared/' + name, 'text/css' if name.endswith('.css') else 'text/javascript')
        for name in ['index.html', 'app.js', 'core.js', 'style.css']:
            mime = 'text/html; charset=utf-8' if name.endswith('.html') else 'text/css' if name.endswith('.css') else 'text/javascript'
            routes['/spatial/' + name] = ('spatial/' + name, mime)
        if self.path in routes:
            name, mime = routes[self.path]
            return self.send(200, (ROOT / name).read_bytes(), mime)
        return super().do_GET()

def make_server(port=8901, product=None):
    server = Server(("127.0.0.1", port), product or Product(False))
    server.RequestHandlerClass = DesignHandler
    return server

def main():
    if sys.version_info < (3, 12):
        raise SystemExit("Python 3.12 or newer is required.")
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=8901)
    parser.add_argument("--design", choices=["a", "b"], default="a")
    parser.add_argument("--enable-live", action="store_true")
    parser.add_argument("--open-browser", action="store_true")
    args = parser.parse_args()
    verified_record()
    server = make_server(args.port, Product(args.enable_live))
    path = "design_a_decision_flow" if args.design == "a" else "design_b_evidence_lens"
    url = f"http://127.0.0.1:{server.server_port}/{path}/"
    print(url + " | " + ("live enabled; explicit confirmation still required" if args.enable_live else "offline; provider execution disabled"), flush=True)
    if args.open_browser:
        webbrowser.open(url)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.product.credentials.clear()
        server.server_close()

if __name__ == "__main__":
    main()
