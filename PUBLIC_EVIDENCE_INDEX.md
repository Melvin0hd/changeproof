# ChangeProof: inspect the evidence, not a marketing claim

**A successful extraction is not automatically sufficient decision evidence.**

Start with [the original sanitized audit](examples/genuine_ui_review.json).
Its SHA256 is `6dfc0d4f6c1ebd0c6d5ba9b97f7fcd54e2e6431a2e1ca6583382d849a19901cc`.
Review `8e4d40ad9e2e30a0` was recorded on 19 October 2026. Opening it today does
not retrieve current prices, run a new model or certify tariff applicability.

## Direct audit map

| Claim about the demonstration | Inspect this JSON location | Observed value |
|---|---|---|
| Genuine Tavily retrieval completed | `provider.tavily.http_status`, `.response` | 200; original sanitized results retained |
| Retrieved references | `sources` | Three docs.github.com URLs, one publisher; repeated excerpt |
| Genuine NVIDIA inference through Nebius | `provider.nebius` | HTTP 200; `nvidia/Nemotron-3_5-Lightning` |
| Actual returned structured content | `provider.nebius.content`, `.result` | Raw content and parsed extraction retained |
| Completed output, not truncation | `provider.nebius.finish_reason` | `stop` |
| Measured usage | `provider.nebius.usage` | 1,816 input / 204 output / 2,020 total tokens; 0 reasoning tokens |
| Exactly one relevant claim | `outcome.claims[0].raw_claim` | USD 0.006/minute, `criterion_candidates=["C01"]` |
| Exact source relationship | Claim `source_id`, `source_url`, `publisher`, `evidence_span`; `sources[0]` | `retrieval_1`, docs.github.com, literal span |
| Hypothetical starting assumption | `original_decision` | 100,000 potentially billable minutes; USD 700 budget; assumed rate USD 0.005 |
| Final deterministic outcome | `outcome.decision`, `.trace` | ESCALATE; accepted `calculations={}` |
| Human action boundary | `automatic_vendor_action` | false |

The exact supporting span is preserved, not rewritten:

```text
| Linux 2-core (x64) | `actions_linux` | $0.006 |
```

[Original selected source URL](https://docs.github.com/en/billing/reference/actions-minute-multipliers#x64-powered-larger-runners).
The preserved excerpt contains several tables and omissions. The link alone
does not establish that the quoted row applies to the operator's account.

## Why ESCALATE is justified

Literal/numeric grounding and the extraction schema revalidate offline. However,
included minutes and contract applicability are unconfirmed, an effective date
is absent, and the excerpt has omissions. The guarded mapping requires review.
The original aggregate `provenance_checked=false` remains false: do not label
this an unqualified provenance or applicability PASS.

100,000 x USD 0.006 = USD 600 is illustrative gross arithmetic only. It is NOT
an accepted engine calculation or verified monthly bill. Falling below the
hypothetical USD 700 budget does not resolve those conditions.

Run `python -B VERIFY_RECORDED_EVIDENCE.py` to independently feed the saved
response through the original extractor, grounding guard and decision adapter.
It makes zero new provider calls. It is not evidence of a fresh inference.

## Roles in the real, opt-in workflow

- [Tavily retriever](changeproof_evidence_intake_v1/retrieval/tavily_runtime.py):
  one Basic search, up to three attributed source excerpts. Without retrieval,
  this live path has no newly acquired source text to examine.
- [Nebius client](changeproof_evidence_intake_v1/provider_client.py): sends the
  authorized bounded request to Nebius Token Factory's inference endpoint.
  Nebius is the actual serving platform, not a decorative vendor label.
- [Nemotron extractor](changeproof_evidence_intake_v1/extractors/nebius_nemotron_contract.py):
  converts the selected excerpt into one strict structured claim. It does not
  choose the final decision. The genuine returned model ID is recorded above.
- [Application](changeproof_app/app.py), [pricing selection](changeproof_app/pricing_selection.py)
  and [applicability guard](changeproof_app/pricing_guard.py): constrain evidence,
  verify literal/numeric support and apply the unchanged deterministic adapter.

These integrations are essential to this implemented live acquisition/extraction
path, not a claim that no alternative retrieval service or model could work.
No speed/cost superiority, source truth certification or production adoption is claimed.

## Three explicitly different experiences

1. **Recorded genuine provider evidence:** the immutable 19 October audit above.
2. **Synthetic offline controls:** saved or locally computed fictional KEEP,
   REOPEN and ESCALATE results. Mocked failures are labeled QA, not provider history.
3. **Fresh live execution:** available only in the full local application with
   separate authorization, both credentials and one-call budgets. Not on Pages.

The two interfaces consume one read-only current-review contract. Explore/Return,
source selection, playback and export never run a provider. The static judge
build intentionally plays pinned saved results; arbitrary baseline recomputation
requires the separately included local Python application.

## Public reproducibility

- [Judge instructions](PUBLIC_JUDGE_GUIDE.md)
- [Complete local app and contract](RC2_GUIDE.md)
- [Release validation command](tools/validate_release.py)
- [MIT license](LICENSE) and [third-party/evidence rights](THIRD_PARTY_NOTICES.md)
- [Publication plan and limits](P1_PUBLICATION_PLAN.md)

The original audit is self-contained evidence from the project's own records,
not an externally notarized provider receipt. No new paid call is needed to inspect it.
