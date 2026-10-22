# Windows persistence remediation — round 1

Date: 2026-10-23. Status: **implementation and verification complete;
independent re-verdicts pending**.

## Authority, settled object and boundary

The operator authorized fixing Windows persistence, committing/pushing the
completed checkpoint, and running the review cycle. This is the first merged
remediation of that cycle, not a new capability or broader compatibility project.

Reviewed cache checkpoint:
`6d91a0cec59bb926e4ffb627847a6e1562b0dc9e`, with Lifecycle integration at
`e979f2412b809e2a8a60eefb942790cef1e715ff`.
The [Code report](WindowsPersistence-ReviewCode.md) returned NO-GO with P2-1;
the [State report](WindowsPersistence-ReviewState.md) returned GO with P3-1.
Reports are filed verbatim. There is no blind convergence: the findings concern
different roots. The combined gate is **NO-GO while Code P2-1 remains open**.

Deliver one cohesive patch in this package: Windows root admission, necessary
existing ABI bindings, focused Windows trust/concurrency regressions, and current
policy/evidence. Prefer enforcing the existing complete-ancestry invariant by
rejecting directory-backed drive anchors whose physical root cannot be proven.
Do not implement substituted-drive support, redesign traversal, change artifact
formats/public routing, weaken handle protections, or introduce dependencies.

Lifecycle is reference-only unless a narrowly necessary cache integration test
or its cache documentation must change; report necessity before using that
existing three-file overlay boundary. Its runtime/annotation fix is immutable.
YIDL, Astichi, Dataclass, Undoable, Pyrolyze, GEARU, GWZ configuration and other
platform projects remain reference-only. No archive-reference repairs. Preserve
other dirty work and the newly filed review outputs.

## Finding dispositions and closure tests

| Finding | Disposition | Required closure test |
| --- | --- | --- |
| Code P2-1: substituted drive hides physical ancestors | Fix the initial-anchor premise before private storage admission. Establish from a held handle that the anchor is an actual supported volume root, or conservatively reject it. A pathname-only resolve followed by unprotected reopening does not close the finding. Keep complete held-handle traversal for accepted roots. | On actual Windows, reproduce the reviewed hidden-ancestor case with a disposable drive mapping and unsafe ancestry. Before the fix, demonstrate the differing trust result; after it, require typed bypass before decoding for an authoritative override, automatic fallback to a separate trusted ordinary NTFS root, producer-at-most-once, and bounded mapping/artifact cleanup. Retain ordinary-drive cold/warm generation-forbidden proof and existing ancestry/junction tests. |
| State P3-1: publication test assumes both Windows writers must publish | Correct the test contract in the same patch. Keep safe sharing modes and existing POSIX expectations. A Windows sharing-conflict loser may return a typed bypass while both callers receive correct generated code and one complete artifact remains. | Deterministically hold the first writer after its successful rename but before closing its exclusive handle, let the second replacement fail, then release the first. Require the documented miss/bypass outcomes, bounded diagnostics, no abandoned temporary files, and a fresh generation-forbidden reader hit. Preserve POSIX assertions where applicable. |

P3-1 is nonblocking and is included as a bounded test correction alongside the
blocking fix; it is not a separate package or independent product requirement.
The implementer must not self-close either finding. A disputed finding requires
a written, evidence-based disposition rather than silent omission.

## Implementation and evidence sequence

1. Read the exact reports, current policy, amendment, instructions and original
   evidence. Record the allowed files/components before editing. Run the smallest
   actual-Windows counterexamples first in disposable isolated storage, without
   changing the original workspace environment or global host settings.
2. Add the failing regressions before the corresponding code/test correction.
   Record source revision, actual outcomes and why the failure reproduces the
   original report. Do not mislabel an unsupported setup or skipped probe as RED.
3. Make the localized guard/test changes as one cohesive patch. Update current
   policy/amendment to state supported-root restrictions. Retain the historical
   evidence manifest; add separately identified remediation evidence rather than
   rewriting old platform runs or the original review reports.
4. Run actual Windows focused fault/concurrency tests and canonical cold/warm
   persistence on both explicit engines with no fallback, then appropriate cache
   and POSIX regression checks. Preserve unsupported ReFS safe bypass and NTFS
   home fallback. No broad version/platform expansion is a prerequisite.
5. Return exact changed paths, RED/GREEN evidence, residual limitations and
   whether the diff changed a shared interface, architecture, mutation boundary,
   compatibility rule, platform assumption or previously reviewed call graph.
   Do not claim independent closure. No Git mutations by the implementer.
6. The lane owner settles one revised committed tuple using the already
   authorized GWZ operations. Re-review uses the original reviewers for a local
   invariant correction; materially changed review premises require replacement
   reviewers under the review-loop rule. Exactly two reviewers maximum per
   revision. Each verifies its original counterexample and files a closure table.

## Gate accounting and landing

The implementer returned one ten-file correction with separately identified
[remediation evidence](WindowsPersistence-RemEvidence-1.md) and
[manifest](WindowsPersistence-RemEvidence-1.json). Both original counterexamples
were reproduced on actual Windows before correction. The held-anchor root check
and deterministic publication-conflict tests pass afterward; reported Windows,
Lifecycle integration and POSIX preservation checks are recorded in that evidence.
These results do not self-close either finding. The shared interface, envelope,
routing and mutation boundary remain unchanged; the additional guard enforces
the existing complete-ancestry premise. The lane owner will settle the revised
tuple for focused re-verdicts by the original two reviewers.

Initial full review: one revision, two independent axes. Remediation rounds
started: one of at most two. Blocking findings open: one. Nonblocking findings
open: one. Reviewer-classified architectural roots: no new classification beyond
the filed root-premise defect is asserted by the lane owner.

The original commit/push authorization covers recording a corrected reviewable
checkpoint and its audit evidence through GWZ. Do not push or claim acceptance
of the correction before the focused re-verdicts. No tag, registry publication,
site deployment or release activation is authorized. A new architectural root
beyond the skill's cap stops the lane for an operator decision.
