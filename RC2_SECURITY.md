# RC2 scoped release checks and boundaries

No provider keys are needed or inherited by the offline validation process.
No Tavily, Nebius or Duo calls are authorized or made during this assembly.
Original engine, decision adapter, schema, benchmark/genuine evidence hashes and
MIT license are checked against RC1. Frozen RC1 files, packages and video remain
unchanged outside this independent candidate.

The only live-server addition is a fixed allowlist of presentation assets.
Existing Host, Origin, CSRF, body-size, no-store and loopback safeguards remain.
Only Spatial HTML permits framing by the SAME origin; other app routes continue
to reject framing. Spatial disallows network connections. Parent and child both
verify message origin and source window. This is an isolation boundary for UI
coupling, not a sandbox against malicious same-origin source code.

Audit/source content uses text nodes, not HTML interpretation. Links allow only
HTTP(S); the main renderer rejects embedded credentials. No source relationship
is inferred from rank. Exact source ID, URL, publisher and span must match one
reference, otherwise the UI suppresses linked arithmetic without rewriting the
original verdict. Unknown verdicts/invalid audit structures fail closed.

The release scanner checks known credential formats, private filesystem paths,
personal contact strings, excluded runtime/secret folders and nested archive
content. A clean scoped scan is not a penetration test or guarantee against all
possible secret formats. Review release diffs and licensing before publication.

RC1 legacy prototypes are retained for reproducibility but are not the RC2 judge
entry point. Publish only the curated static `judge_demo/` artifact for Pages.
Do not expose the local Python server to a public network.
