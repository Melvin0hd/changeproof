# Presentation boundary / no new decision architecture

```text
Decision Flow or Evidence Lens
           |
existing local JSON API and CSRF boundary
           |
unchanged F1 Product
  Tavily -> deterministic excerpt selection -> Nemotron
           -> strict schema and literal grounding
           -> applicability guard -> KEEP / REOPEN / ESCALATE
```

`design_server.py` inherits the original HTTP handler, changes no POST action and adds only fixed UI GET routes plus `/api/recorded`. A hash-pinned audit is run through the original offline verifier before that recorded endpoint returns it. It is never inserted into Product history as a new live review.

`shared/model.js` reads the real F1 audit contract and creates a view. It cannot select a decision by scenario name. Its gross multiplication is presentation-only; the raw record is unchanged and exported as originally recorded. Unknown decisions/incomplete contracts are rejected. `shared/app.js` uses the existing review, decision, credentials and live-review endpoints. Live presentation shows one actual waiting state because F1 does not stream provider stages. Offline playback begins only after a result exists.

Synthetic controls execute the original engine with FixtureExtractor. The genuine audit uses captured actual provider output. Failure QA uses the original mocked opener. Newly configured live mode is a fourth, separately labelled execution path, disabled by default and not exercised here.

The original F1 modules remain byte-identical. No Observer Core dependency, dashboard, agent framework, new provider SDK, persistence system or automated action has been added.
