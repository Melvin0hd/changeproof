# Scoped publication and security review

This is a bounded release audit, not a claim of exhaustive security certification.

## Preserved boundaries

The existing F1 Host/Origin checks, CSRF requirement, request-size limit, fixed static route allowlist, loopback binding, process-memory secrets, redaction and one-attempt budgets remain unchanged. A thin GET-only adapter serves allowlisted UI assets and the hash-checked historical audit. No arbitrary local paths, private repositories or browser state are exposed. The offline revalidation subprocess receives an environment allowlist, not provider credentials.

The default launcher does not enable live execution. Preparation and browser QA use no real provider transport. Explicit failure tests install the existing MockProviders opener and fake fixture keys in isolated QA processes; their output is labelled MOCKED TRANSPORT. They are not genuine provider results.

No credentials, .env, local-secrets directory, runtime artifacts, identity documents, benchmark gold or Observer modules belong to the public allowlist. A recursive known-secret/private-path scan and clean extraction tests are required by the release builder. Audit downloads preserve the sanitized original record; illustrative presentation arithmetic is never written into its accepted calculations.

Frontend rendering uses textContent for external evidence and source URLs, restricts clickable links to HTTP(S), and does not use localStorage. Invalid model output remains rejected by F1. A traceable literal is not represented as verified truth; provenance_checked=false is retained in the original audit.

## Rights and attribution

The original MIT notice is unchanged. Lucide is bundled with its ISC license. No model weights, provider services, third-party logos, stock media, music or reference artwork are sublicensed as MIT. The two supplied reference images are excluded from distribution. New geometry is original software-generated document/path/lens presentation, not copied reference artwork. GitHub documentation snippets and genuine provider output retain source attribution and their original rights.

No human team member list is invented. The owner must confirm eligibility, contributor attribution and evidence/voice publication rights before public release. The optional video reuses the existing locally synthesized Microsoft Zira narration; no human voice clone or endorsement is implied. Human listening remains necessary.

## Remaining limitations

No arbitrary-website agent, automated supplier action, web hosting isolation, live billing verification or independent truth certification is provided. Schema/lexical grounding and the conservative applicability guard are not semantic proof. Historical tariff excerpts may be stale and are not re-fetched in this mission. One publisher appearing three times does not create independent corroboration.
