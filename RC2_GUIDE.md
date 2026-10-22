# ChangeProof RC2: one review, two ways to understand it

A Melvenx project, originating in Observer Lab. Independent MIT-licensed
application; no private Observer module is included or required.

## Start in under ten minutes

Install Python 3.12 or newer. No Python runtime packages or paid accounts are
needed for offline review. All browser assets, including Lucide (ISC), are local.

Windows: double-click `START_CHANGEPROOF.cmd`. Open the printed loopback URL
(default `http://127.0.0.1:8940/design_a_decision_flow/`).

Other systems, or explicit startup:

```sh
python3 -B design_server.py --port 8940 --design a --open-browser
```

1. Open the recorded evidence review. Its baseline is hypothetical; the saved
   Tavily/Nemotron responses are genuine, from 19 October 2026.
2. Inspect ESCALATE: a grounded USD 0.006/minute claim does not establish the
   included allowance, effective date or contract applicability. USD 600 is
   illustrative arithmetic, NOT an accepted bill or accepted engine calculation.
3. Choose **Explore evidence**. The same review ID and audit enter Spatial.
4. Navigate source, grounded claim and decision in either direction. No provider
   is contacted. Return using Decision Flow or Escape; the review remains intact.
5. Export the original audit from either view. Compare the files with
   `examples/genuine_ui_review.json`; the data is unchanged.
6. Choose synthetic offline examples to exercise KEEP, REOPEN and ESCALATE.
   In the full local app, changing the budget recomputes with the original engine.

## No-key static judge build

`judge_demo/` is a self-contained static site. Start `START_JUDGE_DEMO.cmd` on
Windows, or run `python3 -m http.server 8941 --bind 127.0.0.1` in this folder and
visit `/judge_demo/`. It needs no API, database, build service or credentials.
The hosted browser experience needs only an ordinary browser.

The static build plays saved genuine evidence and saved offline engine results;
it does NOT execute a fresh Python calculation in the browser. Fixed baseline
editing is disabled. It also includes saved mocked empty, conflicting and
technical-failure cases. These are not authentic provider failures.

`python3 -B rc2_build_demo.py` regenerates synthetic snapshots with the unchanged
engine, without external calls. IDs/times of newly generated fixtures vary.
The recorded genuine audit is preserved byte-for-byte in `examples/`.

## Complete local live path (not run during RC2 assembly)

```sh
python3 -B design_server.py --port 8940 --design a --enable-live --open-browser
```

The existing masked local dialog accepts credentials into process memory only.
Both must validate before retrieval. A separate explicit credits/overage
confirmation is mandatory. The existing one-search/one-inference budget, no
retry, grounding, schema and applicability checks are unchanged. Do not use the
live mode merely to browse evidence. Switching views cannot start a review.
Provider substeps are not streamed; the UI states this instead of inventing progress.

Spatial uses a separate same-origin document solely to isolate its existing CSS
and animation controller. It does not duplicate the application or backend.

## Reproduce validation

```sh
python3 -B VERIFY_RECORDED_EVIDENCE.py
python3 -B -m unittest discover -s changeproof_app/tests -v
python3 -B -m unittest discover -s tests -v
python3 -B -m unittest discover -s release_tests -v
node --test tests/test_view.cjs tests/test_rc2.cjs
```

Node is needed only for JavaScript tests (and existing HTTP mock tests), not to
run the application. Use a clean temporary extraction and an empty credential
environment for offline verification.

## One canonical, read-only contract

`shared/presentation.js` wraps the existing `ChangeProofView` projection. It
clones and freezes the original audit, preserves its verdict and returns a
source relationship only when source ID, URL, publisher and exact span match
exactly one source. Missing or ambiguous links remain unavailable, never source 0.

Decision Flow sends this audit by a same-origin, parent/window-checked versioned
presentation message to the optional view. Spatial has no API transport. It
never selects a case, submits credentials, computes a new verdict or calls a
provider. Returning keeps the original Decision Flow DOM and review state.
Playback is explanatory motion of already available data, not provider latency.

## Evidence and limits

- Genuine original audit: `examples/genuine_ui_review.json`; revalidation:
  `VERIFY_RECORDED_EVIDENCE.py`.
- Three GitHub documentation references are one publisher, not three independent
  confirmations. Original `provenance_checked=false` remains unchanged.
- Static snapshots: `judge_demo/fixtures.js`; synthetic/mock provenance remains
  explicit. They do not prove a fresh live integration.
- Source/engine hashes: `SOURCE_MANIFEST.json`; RC2 package pins:
  `RELEASE_MANIFEST.json`. RC1 archives/video remain external and unchanged.
- Legacy design and publication documents are retained as historical context;
  this guide and `RC2_HOSTING_PLAN.md` govern RC2.
- Tested Chromium browser behavior is not a formal screen-reader/WCAG audit.
  Narrow screens use vertical scrolling for full evidence. No claim of cross-browser
  certification, security certification or independent usability study.

Do not publish or activate live providers without the owner's separate approval.
