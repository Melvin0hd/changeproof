# RC2 versus RC1

| Aspect | RC1 | RC2 |
|---|---|---|
| Default interface | Decision Flow D1 | Same Decision Flow D1 |
| Spatial | Separate recorded-only demo | Read-only second view of current review |
| Audit identity | Independent demo selection | Same review ID, baseline, sources and audit |
| Decision engine / provider runtime | Frozen | Identical frozen bytes |
| Provenance link | URL fallback in experimental view | Unique source ID+URL+publisher+span, or unavailable |
| Judge access | Local app plus optional static Spatial | Connected static no-key demo plus full local app |
| Recalculation | Local Python engine | Local Python engine; static build explicitly uses saved outputs |
| Motion | Separate prototype playback | Same object identities across spatial stages; no extra request |

The demonstrable benefit is a reversible chain from verdict to claim to exact
source, with the same audit export on both sides. No measured productivity,
accuracy or comprehension advantage is claimed. RC2 adds iframe/message-contract
complexity and narrow-screen scrolling; tests and visual evidence cover the
implemented behaviors, not every browser or assistive technology. RC1 remains a
safe fallback and is not replaced in place.
