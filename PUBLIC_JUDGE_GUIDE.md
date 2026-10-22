# Test ChangeProof in five minutes

**Demo URL: `<PUBLIC_DEMO_URL_PENDING_OWNER_APPROVAL>`**

The prepared destination is https://melvin0hd.github.io/changeproof/ . It is not
yet published or verified. Until authorized publication, use the static test-build
ZIP or the full local application. Both require no credentials for review.

## Interactive static demo

Serve the extracted static package with any ordinary HTTP(S) static server.
With Python: `python -m http.server 8952 --bind 127.0.0.1`, then open
http://127.0.0.1:8952/ . The hosted version will need only a browser, not Python.

1. Select **Recorded provider evidence** and review the hypothetical decision.
2. Open the result: ESCALATE is intentional, not an unfinished inference.
3. Choose **Explore evidence**. Check the same review ID in the second view.
4. Select source 2 or 3 to inspect those references. Choose **Evidence focus**:
   the claim correctly traces back to source 1, rather than claiming support
   from whichever reference happened to be selected.
5. Read the exact highlighted Linux 2-core x64 row. Select the claim to return
   to its source. Use **Decision impact** to inspect the reason and qualifications.
6. Return with **Decision Flow** or Escape. The original review remains available.
7. Export the audit in either view and compare it with the original JSON linked
   from [the evidence index](PUBLIC_EVIDENCE_INDEX.md).
8. Select synthetic examples to see KEEP, REOPEN, incomplete evidence, conflicting
   rates and a clearly labeled mocked technical failure. These are saved controls,
   not fresh provider calls. The static baseline is deliberately not editable.

Keyboard: ordinary Tab/Enter access, named controls, visible focus, Escape return.
Use Reduce motion or the system preference; the workflow does not require motion.
Small screens use vertical scrolling. Formal assistive-technology certification
and exhaustive cross-browser coverage are not claimed.

## Complete operational application

Python 3.12+; no pip dependencies. Run:

```sh
python -B design_server.py --port 8950 --design a --open-browser
```

The local synthetic examples execute the real engine. Editing the budget to
USD 250 makes the USD 0.002/minute example KEEP instead of REOPEN. The UI labels
do not choose the outcome. Recorded review preserves the original audit.

Fresh live usage is separate and optional: `--enable-live` retains the existing
masked process-local credential dialog and explicit credit confirmation. No
unrestricted or publicly funded endpoint is shipped in the static site. Judges
must not enter credentials into the hosted recorded demo.

## Offline validation

```sh
python -B tools/validate_release.py --output local-validation
```

Node 24 is required for the complete development test suite, but not to run the
application. Validation copies the manifest-listed source into a new temporary
directory, removes credentials from child environments, blocks external Python
connections, retains logs and fails if correctness checks fail. It reuses actual
recorded responses, not a fake agent or new inference.
