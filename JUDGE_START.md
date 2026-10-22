# ChangeProof / frozen F1 judge build

Python 3.12 or newer. No pip installation, API keys or internet required for the demo.

Windows: double-click START_JUDGE.cmd, then open http://127.0.0.1:8783.
Other systems: `python -B changeproof_app/app.py --port 8783`.
This command omits --enable-live: provider execution stays disabled, even if local keys exist.
Use a free port if occupied; do not shut down another application.

Choose each synthetic scenario, Review evidence, inspect all three result tabs and Download JSON.
KEEP / REOPEN / ESCALATE are synthetic controls, not fresh vendor research.
The separately labelled judge_guide pages display the unchanged genuine October 19 audit,
not a screenshot of that original run or a new inference. Open judge_guide/index.html directly.

Run `python -B -m unittest discover -s changeproof_app/tests -v`.
Optional Node.js executes the existing JavaScript/local-HTTP integration check; it is not an app dependency.
Run `python -B VERIFY_RECORDED_EVIDENCE.py` to revalidate the preserved actual response offline.

No audit is imported into the application as a new provider run. No automatic fallback,
shared owner credentials or public live endpoint. Stop with Ctrl+C or the in-app Shut down control.
The original F1 README, license, code and evidence are unchanged. SOURCE_MANIFEST.json pins every file.
