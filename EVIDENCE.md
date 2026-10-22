# Genuine ChangeProof UI review

Audit: `examples/genuine_ui_review.json`; review ID `8e4d40ad9e2e30a0`,
2026-10-19T12:23:40.375618+02:00. Application C1-final-extraction-1.
This is captured existing application history, not a replay presented as live.

- Tavily Basic: HTTP 200; three docs.github.com references with repeated text.
- Nebius Token Factory: HTTP 200, `nvidia/Nemotron-3_5-Lightning`, finish_reason stop.
- 1816 prompt / 204 completion / 2020 total tokens; zero reasoning tokens.
- One schema-valid raw claim; normalized USD 0.006 per minute, criterion C01.
- Exact source span: `| Linux 2-core (x64) | `actions_linux` | $0.006 |`.
- [Original selected source](https://docs.github.com/en/billing/reference/actions-minute-multipliers#x64-powered-larger-runners).
- Deterministic outcome ESCALATE; automatic vendor action false.

Publication/effective date is absent, excerpt has omissions, included minutes and
contract applicability are unconfirmed. Literal support is not full applicability
approval. The aggregate `provenance_checked` flag is false because the guarded
mapping requires review; do not relabel it an unqualified provenance PASS.

There is no accepted numeric calculation in this live outcome. Conditional
100000 x 0.006 = USD 600 is arithmetic only, not an approved actual bill. The
original assumed USD 500 and USD 700 threshold belong to a hypothetical baseline.
Do not imply the source author confirmed those customer circumstances.

Native Chrome screenshot verification was blocked by browser URL detection; no
image of this run is fabricated. Existing synthetic UI screenshots are not this
live review. The JSON chain and application-rendering tests are separate evidence.
Technical Tavily runtime use is demonstrated; bonus eligibility is an organizer
decision, not a claim that the project won or met every submission requirement.
