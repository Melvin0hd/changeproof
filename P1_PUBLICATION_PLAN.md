# Approved-candidate publication plan (NOT executed)

Target source: https://github.com/Melvin0hd/changeproof

Target demo: https://melvin0hd.github.io/changeproof/

The GitHub connector authenticated as **Melvin0hd** on 22 October 2026. An
authenticated repository lookup returned **404**. This means not found or not
accessible, NOT guaranteed name availability. The check neither reserves the
name nor proves create permission. No repository, push, hosting, workflow, video
upload or submission was performed. GitHub CLI was not found on this process PATH
or the checked standard locations; connector authentication is not CLI auth.

## Executable boundary

`PUBLISH_AFTER_APPROVAL.ps1` is inert by default. Its Plan mode was tested locally.
It does not install tools, ask for pasted credentials or read key files.
After separate approval, the operator must have official GitHub CLI authenticated
as Melvin0hd using existing Windows secure authentication. Do not switch accounts
or credentials silently. Before every write the script verifies the exact approved
commit, source hashes and account. Recheck publication rights and current destination.

### Source publication, separately authorized

```powershell
.\PUBLISH_AFTER_APPROVAL.ps1 -Stage Source -Execute `
  -Approval AUTHORIZE_CHANGEPROOF_PUBLIC_SOURCE `
  -ApprovedCommit <EXACT_APPROVED_P1_COMMIT> `
  -ApprovedManifestSha256 <EXACT_APPROVED_P1_MANIFEST_SHA256>
```

The first write creates only the named PUBLIC repository, without automatic
initialization/private history. Any existing target causes a stop. The clean
standalone HEAD is pushed normally to main, never forced. The script uses the
verified CLI account for Git authentication, not a pasted token, and checks the
created project's visibility and write access. Default branch is set to main.
An error after creation may leave an empty/partial public repository; it is not
automatically deleted or retried. Report that partial state explicitly.

### Static hosting, separately authorized

```powershell
.\PUBLISH_AFTER_APPROVAL.ps1 -Stage Hosting -Execute `
  -Approval AUTHORIZE_CHANGEPROOF_PAGES `
  -ApprovedCommit <EXACT_APPROVED_P1_COMMIT> `
  -ApprovedManifestSha256 <EXACT_APPROVED_P1_MANIFEST_SHA256>
```

This verifies the exact public main, enables only workflow-based Pages if absent,
then dispatches ONE manual Pages workflow. It calls offline validation, packages
only the pinned `judge_demo/` assets plus licenses, and deploys only after tests
pass. No push/schedule/PR/automatic provider trigger exists. Failed jobs retain
logs and stop deployment; no rerun or retry is authorized by this document.
The separate `validate.yml` can be manually dispatched for validation-only work,
but do not launch it in addition unless explicitly requested.

The workflow files use JSON syntax, a valid YAML representation, allowing the
actual config object to be parsed with Python's standard library. Official action
tags were resolved to pinned SHAs. Standard Ubuntu public runners only; no larger
runners, paid service setup, caches, secrets or provider keys. Actual GitHub
execution, permission policies, artifact upload and Pages availability remain
unverified until a separately authorized real run.

## Anonymous verification after successful deployment

Run `python -B tools/check_public_access.py --commit <APPROVED_SHA> --output public-checks.json`.
It makes only unauthenticated GETs to the exact GitHub/raw/Pages destinations.
It checks pinned source bytes, license, genuine audit, static UI assets and rejection
of operational API routes. This is NOT a substitute for real anonymous browser
checks: repeat source/claim/ESCALATE/return/export on desktop and 390px, confirm
recorded labels, inspect actual CI status/commit and published Pages URL.
GitHub Actions artifacts may require login to download; the self-contained
genuine audit and evidence index are committed publicly so judges need no such artifact.

Do not claim public access from local preview or present offline validation as
new provider activity. Keep judging access working through the required period.

## Separate final approvals

The owner still approves contributors/rights/eligibility and the full 169-second
film after a complete watch/listen. YouTube upload and Devpost submission are
separate from both source and hosting authorization. Placeholders in
`SUBMISSION_DRAFT.md` must be replaced only with genuinely working URLs.

The intended public GitHub account/destination must not change without permission.
Estimated post-approval source/hosting/anonymous verification: 30-60 minutes,
excluding authentication/service delays. No fresh provider test is part of P1.
