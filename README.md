# ChangeProof

## Public launch candidate P1 (not yet published)

**[Start here: judge guide](PUBLIC_JUDGE_GUIDE.md)** ·
**[Inspect genuine evidence](PUBLIC_EVIDENCE_INDEX.md)** ·
**[Submission draft](SUBMISSION_DRAFT.md)** ·
**[Publication boundary](P1_PUBLICATION_PLAN.md)**

Decision Flow → Explore evidence → exact source → return, using the SAME audit.
The no-key static demo plays labeled recorded/synthetic results. The full local
application separately retains the opt-in Tavily → Nebius/Nemotron → deterministic
validation path. No provider calls are needed for judging the prepared demo.

Run `python -B tools/validate_release.py --output local-validation` for the
complete offline suite (Python 3.12+, Node 24 for development tests). The prepared
GitHub workflows are manual-only and have NOT run on GitHub. They are release
validation, never fresh provider evidence. Source/hosting/video URLs remain pending
owner approval; do not treat proposed URLs or local test results as publication.

The following RC2/RC1 sections preserve historical context. The P1 documents above
govern this publication candidate.

## RC2: Decision Flow + Spatial Investigation

**Start with [RC2_GUIDE.md](RC2_GUIDE.md)** for the connected two-view experience,
the independent [no-key judge demo](judge_demo/), current launch commands,
tests and limitations. The same review opens with **Explore evidence** and returns
without another provider request. See [hosting plan](RC2_HOSTING_PLAN.md),
[RC1 comparison](RC2_COMPARISON.md) and [security boundaries](RC2_SECURITY.md).

The following retained RC1 material describes the original engine and evidence;
references to a separate Spatial demo are historical, not the RC2 entry point.

**New evidence challenges an assumption behind an earlier decision. Trace the source, validate the claim, and identify what still needs human review.**

A Melvenx project · Observer Lab. Standalone MIT software; no private Observer Core or private development history is included.

## Judge quick start: Decision Flow

Python 3.12+ and a browser. No pip packages, credentials or paid services are needed.

1. Extract the complete test-build ZIP.
2. Windows: double-click `START_CHANGEPROOF.cmd`. Otherwise: `python -B design_server.py --design a --port 8940`.
3. Open http://127.0.0.1:8940/design_a_decision_flow/ . Choose another free port if occupied; Ctrl+C stops the process.
4. Review **Recorded provider evidence**. Inspect sources, the exact span, unresolved qualifications and audit. Export preserves the original sanitized record.
5. Select **Synthetic offline example**: Lower fee → KEEP, Budget crossed → REOPEN, Missing conditions → ESCALATE. These execute the actual local engine with fictional data.

Decision Flow D1 is the main interface. Editing the synthetic budget from USD 100 to USD 250 makes the same USD 0.002/minute case KEEP instead of REOPEN. Animation and case labels do not select the outcome.

## What actually happens

**Original decision → Tavily retrieval → targeted source selection → Nemotron extraction → deterministic validation → KEEP / REOPEN / ESCALATE → human review and audit export.**

The operator supplies an earlier decision, assumption, usage and budget. Tavily retrieves public excerpts. Deterministic selection preserves the relevant row, headers, URL and qualifications. NVIDIA Nemotron on Nebius Token Factory extracts a bounded strict-schema claim. Existing code checks schema, source metadata, literal/numeric grounding, criterion mapping and applicability before the unchanged decision adapter runs.

- KEEP: accepted evidence does not cross the configured threshold; other supplier risks remain outside this check.
- REOPEN: accepted evidence crosses the relevant threshold; reconsider the earlier decision.
- ESCALATE: evidence is invalid, incomplete or insufficiently applicable, or a provider attempt failed. Inspect the reason before acting.

The model does not make the final decision. Literal support is not source-truth or contract verification. There is no automatic purchase or vendor change.

## Genuine, independently inspectable runtime evidence

[Evidence index](EVIDENCE.md) · [Original redacted audit](examples/genuine_ui_review.json) · [Verifier](VERIFY_RECORDED_EVIDENCE.py)

The October 19 audit records Tavily HTTP 200, three official GitHub documentation references from one publisher, and Nebius HTTP 200 from `nvidia/Nemotron-3_5-Lightning`. The completed response has `finish_reason=stop`, 1,816 input tokens, 204 output tokens and zero reasoning tokens. One USD 0.006/minute claim is supported by the Linux 2-core x64 / `actions_linux` row.

The baseline is hypothetical: 100,000 potentially billable minutes and USD 700 budget. USD 600 is illustrative gross arithmetic, not an accepted invoice; the original accepted calculations remain empty. Included minutes, contract applicability, effective date and excerpt omissions remain unresolved: **ESCALATE**. Three references from one publisher are not independent corroboration. Historical excerpts are not current pricing advice.

## Distinct modes

| Mode | Execution |
|---|---|
| Main recorded review | Local hash-check and offline revalidation of the genuine preserved response; no provider call |
| Main synthetic examples | Actual deterministic engine with fictional fixtures; no provider call |
| Separately authorized live use | Existing provider path with both-key preflight, explicit confirmation and one-attempt budgets |
| Optional Spatial V3 | Static recorded-data playback, without backend connection, evaluation or provider calls |

Open `optional/spatial/index.html` as the separate **optional recorded-evidence investigation demo**. Source sheets, a provenance lens and a grounded claim transform continuously and remain traceable in reverse. It is not the main application, not fresh inference and not registered on the application server. All data is bundled; no fetch, import or API transport is used. No backend dependency is added.

## Operational live path, disabled by default

Complete provider code is included unchanged. Future authorized use may run `python -B design_server.py --design a --port 8930 --enable-live`, configure both keys through the existing masked process-memory UI, and explicitly confirm included credits/no paid overage. Never put keys in files or audits. The path allows one Tavily Basic search / three results and one Nemotron inference / 768 output tokens per process, without retry or mock fallback. Both credentials are required before the first call. This package authorizes no provider request or billing change. The local single-user server must not be exposed to the internet.

## Reproduce checks

```text
python -B VERIFY_RECORDED_EVIDENCE.py
python -B -m unittest discover -s changeproof_app/tests -v
python -B -m unittest discover -s tests -v
python -B -m unittest discover -s release_tests -v
node --test tests/test_view.cjs
```

Node is optional for development tests, not an app dependency. `RELEASE_MANIFEST.json` is authoritative for this candidate. Earlier manifests are retained as input provenance. Historical F1 and Evidence Lens D1 assets remain for reproducibility; Decision Flow is the judge route.

MIT and Lucide ISC notices are retained. Third-party excerpts and provider/model services retain their rights. No model weights, reference artwork, music, credentials or private modules are bundled. See [release safety](RELEASE_SAFETY.md), [publication plan](PUBLICATION_PLAN.md) and [Devpost draft](DEVPOST_DRAFT.md).

Not published or submitted. Proposed destination: https://github.com/Melvin0hd/changeproof , subject to ownership/availability verification and approval. Public source, working test-build download and video URLs remain pending. No organizer acceptance of recorded proof as a substitute for a requested fresh-runtime test is claimed.
