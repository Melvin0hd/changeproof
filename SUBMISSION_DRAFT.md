# ChangeProof

**Draft only. Do not submit or replace placeholders until publication is approved.**

## Tagline
When new evidence challenges an old decision, trace the claim before changing course.

## Problem
An earlier supplier decision rests on assumptions: a price, a usage level and a
budget. A changed webpage can appear to invalidate it, yet its tariff may not
apply to that customer. An AI summary alone hides the difference between an
observed source, an extracted claim and an actionable conclusion.

## What we built
ChangeProof preserves the original assumption and reviews new source evidence
against it. Decision Flow gives a clear review; Explore evidence opens a
reversible Spatial Investigation of the SAME audit, not another AI request.
Reviewers can trace decision to claim to exact source, navigate back and export
the original audit before taking any action.

## How it works
In the authorized live path, Tavily Basic retrieves attributed excerpts.
Deterministic selection narrows them to the declared pricing criterion while
retaining headings and qualifiers. NVIDIA `nvidia/Nemotron-3_5-Lightning`, served
by Nebius Token Factory, extracts a strict structured claim. Schema, metadata,
literal/numeric grounding and applicability checks precede a deterministic
KEEP / REOPEN / ESCALATE adapter. The model does not choose the verdict.

The standalone implementation uses Python's standard library and vanilla
JavaScript/CSS/SVG, with vendored ISC Lucide icons. It is MIT-licensed software
originating with Melvenx / Observer Lab, without private Observer internals.

## A genuine result, including uncertainty
Our recorded GitHub Actions review returned Tavily HTTP 200 and Nemotron HTTP
200, with 1,816 input and 204 output tokens, zero reasoning tokens and a completed
response. The single grounded claim was USD 0.006/minute for Linux 2-core x64.
The baseline of 100,000 potentially billable minutes and USD 700 is hypothetical,
not a customer case study. USD 600 is illustrative gross arithmetic, not an
accepted bill. Included allowance, effective date, contract applicability and
excerpt omissions remain unresolved. The supported outcome is **ESCALATE**.

That is the point: technically valid AI output should not conceal a missing
qualification. The public evidence index preserves the original content, exact
span, provenance flags and empty accepted-calculation trace.

## Engineering challenges and specific platform feedback
Real earlier attempts exposed three different failure classes: endpoint/model
availability, reasoning consuming the output budget, and JSON that did not match
the extraction contract. We did not solve these by accepting arbitrary fields
or coercing types. Model discovery and the working endpoint fixed access; explicit
JSON instructions, thinking control and a single-criterion excerpt reduced
generation scope. The successful recorded response completed with zero reasoning
tokens. Strict validation still rejects truncation, ungrounded claims and unknown
applicability.

**Token Factory feedback:** a region/model compatibility view and concrete,
hosted-endpoint examples for structured extraction would have reduced integration
trial and error. HTTP success, finish reason and token breakdown should be easy
to inspect together. Our observed endpoint/model errors do not establish a
general service outage or comparative reliability ranking.

**Nemotron feedback:** the useful output here is one compact, exact-span claim.
Explicitly disabling thinking and narrowing the evidence helped in our observed
runs. Strict server-enforced schema support remains unproven in this integration;
the application validates the existing contract rather than assuming it.
These are observations from this project's own evidence, not benchmark superiority.

We used Token Factory inference, not Nebius AI Cloud deployment. Tavily performs
actual runtime retrieval in the live product, not merely an incidental citation.

## Honest limits
The static public demo uses recorded genuine evidence and saved synthetic/mock
controls; it does not perform fresh inference or arbitrary Python calculations.
The full local application provides the actual separately authorized provider
path. Three references from one publisher are not independent confirmations.
Literal grounding is not truth certification. No production users, procurement
automation, measured time savings or autonomous supplier actions are claimed.

## Submission fields
- Track: **Best Apps and Agents Track**.
- Optional bonus consideration: Best Use of Tavily, based on functional runtime
  evidence; award eligibility remains the organizer's decision.
- Built with: Python, JavaScript, CSS/SVG, Tavily, Nebius Token Factory,
  NVIDIA Nemotron, Lucide.
- Working demo: `<PUBLIC_DEMO_URL_PENDING_OWNER_APPROVAL>`
- Public source: `<PUBLIC_REPOSITORY_URL_PENDING_OWNER_APPROVAL>`
- YouTube: `<PUBLIC_YOUTUBE_URL_PENDING_OWNER_APPROVAL>`
- Intended source destination: https://github.com/Melvin0hd/changeproof
- Intended demo destination: https://melvin0hd.github.io/changeproof/

Owner must confirm contributors, rights, eligibility, team representative and
significant in-period work before submitting. Do not invent personal details,
development dates, testimonials, credit balances or publication URLs.
