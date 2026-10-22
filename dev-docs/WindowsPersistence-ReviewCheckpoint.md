# Windows persistence settled-checkpoint review

Date: 2026-10-23. Status: **NO-GO at the initial settled checkpoint; first
bounded correction verified by the implementer, independent re-verdicts pending**.

## Authority and authorized boundary

The operator requested closing the Windows persistence implementation gap,
then authorized committing/pushing the completed work as a reviewable checkpoint,
and subsequently directed running a review cycle on the Windows cache patch.
The original observed failure was a Lifecycle diagnostic expecting a persisted
home-route hit while the old non-POSIX trust guard correctly bypassed storage.
Code generation worked; safe Windows persistence was missing.

This review covers the Windows storage/trust amendment in this package and the
three cache-only Lifecycle integration changes below. The review deliverables
are generated canonical prompts, two verbatim independent reports, a merged
verdict and, if necessary, bounded remediation/re-verdict evidence. Only review
documents may be added by the lane owner during the read-only review.

YIDL, Astichi, Dataclass, Undoable, Pyrolyze, GEARU and GWZ are reference-only.
The concurrent Undoable annotation patch, YIDL documentation publication and
Glade/workspace integration are excluded. No archive/history references are
repaired. Discovery does not authorize broader implementation.

## Settled object

| Repository | Base | Reviewed checkpoint |
| --- | --- | --- |
| This package | `a4ae595e0f9835a86dadec3bedebd383ebf9ae2f` | `6d91a0cec59bb926e4ffb627847a6e1562b0dc9e` |
| `../yidl-lifecycle` | `77b0dd574404e314fecc46069a54f8fcedb9555d` | `e979f2412b809e2a8a60eefb942790cef1e715ff` |

The cache checkpoint changes fourteen paths, including the new Windows backend,
storage dispatch, tests, policy and evidence. The Lifecycle range changes only
`dev-docs/LifecycleCodeCache.md`, `tests/test_cache_location_failures.py` and
`tests/test_lifecycle_code_cache.py`. Its base already includes the separate
constructor-annotation correction; that correction is not this review's diff.

The controlling amendment is [WindowsPersistence.md](WindowsPersistence.md) at
the cache checkpoint. Governing context includes [CachePolicy](../docs/CachePolicy.md),
[location policy](CacheLocationPolicyPlan.md),
[location checkpoint](CacheLocationPolicyCheckpoint.md), repository instructions,
and the operator directives above. Historical review acceptance does not accept
the subsequent Windows change.

Reference source objects are Astichi
`ce47c629973d8e5a6340ceaa89b0bc3e8788d5fe` and YIDL
`ee5ded0854aa5b1fc0ddfa7213b765009b63bb95`; later YIDL documentation commits do
not change that runtime-source evidence boundary.

## Review process

Tier: **dual**, because executable persisted artifacts and a platform storage
trust contract change are involved. Exactly two fresh, peer-blind reviewers
inspect the same committed object. Code includes the public-surface mandate;
State covers trust, races, durability, recovery and maintenance. Both perform
requirement provenance, necessity and component-authorization checks. They
verify both reviewed HEADs at start and end. Other member/root HEADs may move.

Prompts were generated from the review-loop canonical reviewer template,
SHA-256 `3b10ae89cf101c6273d34668eaaeaebf7e030a4c132406e0b234a846665eca58`, with the appropriate axis section and exact tuple:

- [Code prompt](WindowsPersistence-PromptCode.md), SHA-256
  `6384ccf3a642635698bc927800f033d9c399cc24129ff227e63e66671185f01a`.
- [State prompt](WindowsPersistence-PromptState.md), SHA-256
  `a90b2992615bc2275f6485b79470323bac5d49d1288b3f4fc9ba5c42c93a1baa`.

Reviewers perform inspection only, with no source/report writes, Git changes,
tests, builds, installs, cache/ACL changes or remote-host mutations. Existing
real-platform evidence is evaluated as reported evidence rather than represented
as independently re-executed by the reviewers.

## Initial results and remediation

- [Code report](WindowsPersistence-ReviewCode.md): **NO-GO**, one P2 finding.
  A substituted drive anchor can omit physical ancestors from the trust walk.
- [State report](WindowsPersistence-ReviewState.md): **GO**, one nonblocking P3
  finding. A concurrency test demands two successful publications even though a
  safe Windows sharing conflict may produce a typed bypass for one writer.

Reports are filed verbatim. Both reviewers verified the same starting/ending
tuple. There was no blind convergence; the findings have distinct roots. The
merged verdict is **NO-GO** while Code P2-1 remains open.

[Remediation round 1](WindowsPersistence-RemPlan-1.md) maps both findings to one
cohesive patch and explicit original-counterexample checks. The implementer may
not self-close findings. P0/P1/P2 findings block acceptance; P3-only findings are
nonblocking. The two-remediation-round cap and architectural-root stop apply.

The [separate remediation evidence](WindowsPersistence-RemEvidence-1.md) records
actual-Windows reproduction before correction, typed root rejection before
decoding, safe publication-conflict results, and Windows/Lifecycle/POSIX checks.
The correction is a local enforcement of the existing actual-root/complete-
ancestry invariant and test contract, without changing shared interfaces,
artifact formats, routing or mutation boundaries. Both original reviewers will
verify their own counterexamples on one newly committed tuple. No finding is
closed by this implementation-status update.

This checkpoint grants no registry publication, deployment, performance claim,
new platform qualification or broader release acceptance.
