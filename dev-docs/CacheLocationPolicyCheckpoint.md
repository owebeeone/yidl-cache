# Automatic Cache Location Checkpoint

## Windows Follow-up — 2026-10-23

The operator subsequently authorized closing the Windows persistence
implementation gap. The [bounded amendment](WindowsPersistence.md) records the
new NTFS trust/handle implementation and actual Windows verification, separately
from the original accepted specification and review tuple below. The Windows
amendment is now **accepted at cache
`aaa55ffba0f1cf63089da313fdf4e8316501a505` and Lifecycle
`e979f2412b809e2a8a60eefb942790cef1e715ff` after independent Code/State GO**;
the [settled review checkpoint](WindowsPersistence-ReviewCheckpoint.md) records
the initial findings, bounded correction, exact closure evidence and limits.
The historical reviews below do not accept the later Windows amendment. ReFS
storage remains unsupported, with verified automatic NTFS home fallback for
ReFS source files. No registry publication or broader release acceptance is claimed.

## Authority And Scope

The operator directed implementation and default-on Lifecycle caching, continuing
unless a serious problem is found, and subsequently authorized committing this
checkpoint in the isolated lane. Push, merge, and publication remain unauthorized.
Work is isolated from the active Pyrolyze LCM lane.

The R2 specification is accepted for design readiness after
[Consistency](CacheLocationPolicy-ReviewConsistency-2.md) and
[Safety](CacheLocationPolicy-ReviewSafety-2.md) independently reported GO.
Its exact SHA-256 is
`1cf2f73ab60de0fd0cae2a9fec8d306c33ead9fc5ecc4ba969f9c287bd2fcafc`.
The reviewed document's bytes remain unchanged; this checkpoint records progress
without relabeling specification approval as implementation approval.

Earlier namespace-collision and missing-diagnostic findings are closed at the
specification level. Runtime verification and reviews are separate obligations.

## Implemented

- Neutral source-origin/location carriers and namespace-digest layout in the
  standalone stdlib-only cache package.
- Private admission probes and at most two storage candidates; fallback carries
  generated code, without retrying producer exceptions.
- One shared code LRU, dependency invalidation, and reentry fence across routes.
- Bounded routing preferences and frozen public diagnostic snapshots; clearing
  maintains tracked locations only and preserves invalidation fences.
- Lifecycle default-on startup configuration, an explicit off switch, authoritative
  root override, source-local preference, and private mirrored home fallback.
- Fresh-process canonical Lifecycle reuse through explicit, local, and home
  routes, with generation forbidden on the warm path.
- A repeatable non-GUI Pyrolyze startup driver using copied sources and temporary
  homes, not the active workspace or real user cache.

YIDL core remains independent. No Pyrolyze runtime, Astichi, generated module,
or checked-in generated golden was changed. Pyrolyze YAML preferences remain a
separate application-bootstrap proposal.

## Verification So Far

Local macOS checks (not cross-platform release approval):

| Gate | Result |
| --- | --- |
| Shared cache suite, Python 3.12 / 3.13 / 3.14 / 3.15 alpha | 57 passed on each |
| Lifecycle cache/configuration/fault checks, Python 3.12 / 3.13 / 3.15 alpha, native | 47 passed on each |
| Lifecycle cache/configuration/fault checks, Python 3.14, both engines | 47 passed on each |
| Full Lifecycle, Python 3.14, default-on with isolated explicit root, native | 434 passed, 46 skipped |
| Lifecycle adapter/configuration/input mypy | Three modules pass |
| Shared mypy | Seven modules pass |
| Shared and Lifecycle wheel/sdist | Both build successfully |
| Rebuilt installed cache/Lifecycle wheels, default-on, all three placements | Cold two misses; fresh warm two hits, zero generation, current bindings; explicit clearing before decoration removes both artifacts |

Fault coverage includes unsafe/readonly local storage, replaced directory
symlinks, admission-probe cleanup failure, failed local publication followed by a
home hit or miss, both-route failure, bounded failure messages/history,
cross-route invalidation/reentry, scoped maintenance, namespace case/Unicode
separation, and producer exceptions that must not become fallback signals.

The default-on full suite uses an isolated explicit root to avoid side effects;
automatic local/home success is proven by the canonical fresh-process fixture,
not inferred from that explicit-root suite.

## Pending Gates

Automatic measurements are recorded in Lifecycle's startup evidence: corrected
context medians are 2.552 to 0.426 seconds locally, and 2.738 to 0.497 seconds
through home fallback (5.99x / 5.51x). Every warm process has thirteen hits and
zero generation.

Initial implementation reviews found five P2 issues and one P3 wording issue;
all are mapped to the bounded `CacheLocationImplementation-RemPlan.md` correction.
The original failures reproduced before the fix. Corrected shared tests pass 54
on Python 3.12 through 3.15 alpha; Lifecycle focused tests pass 46 on both engines
and all four interpreter versions. Corrected wheels pass all three routes, with
pre-decoration explicit clearing verified in a fresh installed-wheel process.
These results do not self-close reviewer findings.

The earlier broader Python-engine run has the previously observed owned-field
source-hygiene-name golden mismatch with caching disabled (426 pass, 46 skip,
one failure); no golden was changed. The intermediate native run exposed two
fault tests switching to the Python engine inside an already initialized process.
Their uncached baseline failed before reaching the cache. They now compare real
disabled/enabled decoration in a fresh process with engine selection at startup;
the final native full suite passes without compiler changes or skipped faults.

Both original State findings and all Code findings were independently closed in
round 2. State found a further non-architectural maintenance preflight defect:
inaccessible ancestry was mistaken for absence on Python 3.14 and raised an
untyped exception on 3.12. The second bounded correction reproduced both, uses
explicit error-aware metadata inspection, and verifies typed failure, process
collection draining, preserved fences/counters, untouched artifacts/neighbors,
and successful cleanup after permissions are restored. Round 3
[Code](CacheLocationImplementation-ReviewCode-3.md) and
[State](CacheLocationImplementation-ReviewState-3.md) both report GO at the exact
34-file `CacheLocationImplementationTuple-3.md`, with no open findings and no
new architectural root. This accepts the uncommitted content-pinned runtime
draft only. Two later documentation-only updates record review status and
distinguish historical startup measurements from automatic-placement results;
their current bytes are pinned for the sequential Surface review.

The sequential [Surface review](CacheLocationImplementation-ReviewSurface.md)
reports GO with two nonblocking P3 documentation findings. Both have been
addressed and exercised in the [follow-up evidence](CacheLocationSurfaceFollowups.md);
the [supplementary Surface review](CacheLocationImplementation-ReviewSurface-2.md)
reports GO and closes both P3 findings at its updated four-document tuple.
Runtime tuple 3 has not moved. The independently reproduced non-cache native README example
failure is recorded there alongside the known Python-engine golden discrepancy.

Implementation and Surface DRAFT review gates are complete, with no open findings.
The operator authorized the local checkpoint commit; adoption remains separate.
No active cleanup
workspace, Pyrolyze runtime, Astichi source, or generated golden was changed.
No default-on release or settled-tree acceptance is claimed yet. Implementation
review used a disclosed content-hash-pinned draft exception before commit
authorization; recording the reviewed bytes in Git does not retrospectively
change those review reports into settled-tree acceptance.
