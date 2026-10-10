# Generated Code Cache Location Policy

Status: R2 DRAFT for focused independent review. The operator has authorized
default-on caching in this isolated lane. This specifies that change, not an
already verified implementation, and does not authorize a commit or push.
The existing uncommitted adapter is still opt-in until this work is implemented.

## Intent And Ownership

Avoid requiring a cache-directory setting for ordinary use. Prefer private
module-adjacent storage, with a private user-directory fallback when installed
code is read-only. An explicit directory overrides automatic placement. Cache
failure must never prevent otherwise valid class generation.

`yidl-cache` owns neutral location layout, safe candidate selection, and routed
artifact I/O. It still has standard-library-only dependencies and knows nothing
about Lifecycle, YIDL, Astichi, or environment-variable names. Lifecycle owns
its environment parsing and the module-origin supplied to the shared policy.
Other generators can provide their own configuration and origins.

Retain the accepted generation/binding boundary, dependency fingerprint,
timestamp/size invalidation, artifact envelope, atomic replacement, and private
storage checks. Nothing here freezes live classes or runtime values.

Controlling references:

- [Shared cache contract](../docs/CachePolicy.md).
- [Generated-code cache plan](../../yidl/dev-docs/YidlGeneratedCodeCachePlan.md).
- [Lifecycle adapter](../../yidl-lifecycle/dev-docs/LifecycleCodeCache.md).
- [Startup evidence](../../yidl-lifecycle/dev-docs/LifecycleCodeCacheStartup.md).

## Lifecycle Configuration

Read configuration once, before the first decoration. Restart to change it.
Add `YIDL_LIFECYCLE_CACHE` with exactly `on` and `off` as nonempty values;
surrounding whitespace and case are normalized. Empty is equivalent to unset.
`YIDL_LIFECYCLE_CACHE_DIR` is a storage-root override, not a filename and not an
off-switch. An empty directory value is equivalent to unset; preserve literal
spaces in nonempty paths.

Lifecycle becomes default-on; explicit disable always wins:

| Enable setting | Directory setting | Effective behavior |
| --- | --- | --- |
| `off` | Any | No cache lookup, dependency inventory, or directory creation. |
| `on` | Unset | Enabled with automatic placement. |
| `on` | Nonempty | Enabled under the explicit root only. |
| Unset | Nonempty | Enabled under the explicit root only. |
| Unset | Unset | Enabled with automatic placement. |
| Invalid nonempty enable value | Any | Disable cache use; retain a typed configuration diagnostic. |

The default changes, not directory-based callers' successful behavior. A
directory specifies placement; removing it now selects automatic placement,
not disable. `off` is the dedicated opt-out.

Resolve a relative override against the working directory captured at adapter
initialization, not at each decoration. Expand the current user's `~` shorthand;
do not expand `$VARIABLES` or another user's `~name`. Normalize relative dot and
parent components lexically before descriptor traversal; do not resolve symlinks
in the explicit cache root. Storage still rejects symlink components. Failure
to expand a requested home or normalize configuration disables cache use and
retains a diagnostic, rather than breaking a valid decorator import.

Python's `sys.pycache_prefix` and `sys.dont_write_bytecode` control CPython's
ordinary bytecode cache, not this custom artifact store. They neither configure
nor disable it; document the dedicated `off` setting alongside automatic placement.

Expose `cache_configuration()` in Lifecycle as a frozen configuration snapshot:
effective enabled flag, explicit root if present, default user root if available,
and an optional typed configuration problem. Existing hit/miss/bypass counters
remain available; request evidence is exposed separately as specified below.
No automatic logs are introduced.

### Pyrolyze Application Settings (Separate Follow-Up)

A Pyrolyze-owned `~/.pyrolyze/config.yaml` could provide application preferences,
including Lifecycle cache enablement and placement. It must be read by Pyrolyze
bootstrap before importing decorators, with explicit environment settings taking
precedence over file settings and then library defaults. YAML schema, parsing,
validation, and Pyrolyze bootstrap changes are not part of this cache checkpoint.
Neither shared cache nor Lifecycle reads a Pyrolyze configuration file or depends
on Pyrolyze. This leaves other decorator consumers independent.

## Module Origin

Lifecycle obtains an origin without importing the author module or inspecting
source text. Look up the already-loaded module named by `cls.__module__` in
`sys.modules`. Use a regular `.py`/`.pyw` file from its `__spec__.origin`; if that
is unavailable, use a regular `.py`/`.pyw` `__file__`. No valid source means an
unknown-file origin, including notebook/interactive, frozen, archive-only, or
sourceless modules. A real `__main__` file qualifies normally.

Capture a relative author path against the startup working directory. Resolve
author-file symlinks to the real source location, once per tracked origin; this
locates the source, not executable cache trust. Do not read its contents, hash
live objects, or add this path to the generation fingerprint. The existing
normalized facts remain authoritative for generated code; current runtime values
are still bound after loading it.

Pass an immutable neutral `SourceOrigin(path: Path | None, module_name: str)`
to the shared policy. A missing/unreadable source or inconsistent/unusable module
metadata selects unknown-file placement. Do not fall back to the generator's
directory or the current working directory as an invented author origin.

## Directory Selection And Layout

Within a consumer namespace, automatic candidates are ordered:

1. For a known source: `<source-directory>/__pycache__/yidl_cache/<namespace>/`.
2. User fallback: `~/.yidl/cache/<namespace>/sources/<mirrored-source-path>/`.

For unknown-file origins, omit candidate 1 and use
`~/.yidl/cache/<namespace>/modules/<module-name-digest>/`.
If the user's home cannot be determined, omit the home candidate. No usable
candidate means ordinary generation with a storage bypass, not an import failure.

An explicit root replaces both automatic candidates:
`<override-root>/<namespace>/`. It is authoritative. If unusable, bypass storage;
do not silently write to another location against the operator's choice.

The namespace component is always `ns-` followed by the lowercase SHA-256 digest
of the exact namespace UTF-8 bytes, regardless of length. There is no literal
namespace component and no separate short/long namespace representation. This
avoids case-folding/Unicode filesystem aliases and literal-versus-hash collisions
for consumer-scoped maintenance (subject to the ordinary digest assumption).
Only source-path/volume components use percent encoding.
Encode path components independently, including `%`, separators, control bytes,
and punctuation other than ASCII letters/digits, `_`, `-`, and `.`. Never permit
`.` or `..` as whole components. Home mirroring strips the absolute anchor and
places a separately encoded volume marker before the remaining components, so
an absolute source path cannot replace the user root. Example schematic:

```text
Source:     <source-root>/demo/models.py
Local:      <source-root>/demo/__pycache__/yidl_cache/ns-<namespace-digest>/<key>.ycode
Fallback:   ~/.yidl/cache/ns-<namespace-digest>/sources/<volume>/<source-components>/models.py/<key>.ycode
Override:   <configured-root>/ns-<namespace-digest>/<key>.ycode
Interactive: ~/.yidl/cache/ns-<namespace-digest>/modules/<module-digest>/<key>.ycode
```

For an encoded volume/path component exceeding 180 bytes, or a mirrored
relative origin path exceeding 1500 bytes, replace that origin layout with
`sources/by-digest/<sha256-of-canonical-source-path>/`. Record the selected layout in diagnostic
evidence. Volume representation must distinguish POSIX root, Windows drive, and
UNC share; Windows persistence remains unsupported until its trust gate passes.
Unknown-origin module digests use exact module-name UTF-8 bytes.

Artifact basenames remain the complete existing request-identity digest plus
`.ycode`. That identity already contains namespace, definition shape, compiled
filename, generator dependencies, and Python compatibility. Multiple classes
in one module therefore coexist. Do not persist one ambiguous artifact named
only after the module. The envelope is not standard CPython `.pyc`; keep the
honest custom extension. Filename prettification is outside this change.

New explicit-root namespace directories do not read/move/delete the current
prototype's flat-root entries. That development-format transition costs one
miss; old files remain untouched. No released cache format is being migrated.

## Trust, Failure, And Fallback

Writability is insufficient. Preserve owner, private-mode, ACL, regular-file,
no-symlink/no-hard-link, bounds, identity, and integrity checks. Create only
required directories, with `0700`, and artifacts/probes with `0600`. Do not
chmod an existing `__pycache__`, source directory, home, or cache directory.
Existing ordinary `__pycache__` permissions are allowed because the artifact
leaf `<namespace>` is private. Existing unsafe leaves are rejected unchanged.

Admit a candidate using the existing descriptor-based walk and an exclusive
temporary write/remove probe inside the final directory, not `os.access` or a
race-prone check followed by ordinary pathname writes. A probe must not overwrite
anything. Its cleanup is bounded; inability to remove it rejects that candidate
and retains a diagnostic. Recognized probe names are eligible for explicit
maintenance; no lookup scans for abandoned files.

Selection and subsequent operations both enforce trust. Keep the directory
descriptor open through each complete read/probe/write operation. An admitted
path is not a permanent trust certificate after close. Permissions, ACLs, or
directory replacement between operations can still cause safe rejection.

Automatic selection can try at most two candidates. Cache the preference/failure
decision in a bounded, process-local LRU keyed by canonical candidate tuple
(capacity 32 initially). A selected home fallback stays preferred while tracked,
even if the source later becomes writable. Eviction permits a fresh admission;
it must not reset producer invalidation or retain live classes/modules.

On a storage-access/publication failure at an automatic local location, try the
home candidate once. Do not retry for unsupported identity/dependencies, an
observed generator edit, same-key reentry, or a producer/consumer exception.
An invalid artifact is regenerated at its selected trusted location, not treated
as a reason to switch locations. If that regeneration cannot be published there,
the storage-failure fallback rule applies. Never deserialize an unsafe artifact
before trying a different directory.

If publication fails after generation, carry that already-produced code into
the fallback attempt. The producer callback runs at most once per logical
request, even when both locations fail. A fallback hit can return compatible
cached code; a fallback miss can persist the already-produced code. Producer
exceptions propagate normally without fallback or a second invocation.

Count one final hit/miss/bypass per logical request, not one per attempted
directory. Count final artifact outcome as today: successful fallback hit is a
hit, successful fallback publication a miss, exhausted storage a bypass. Generation
callback counts remain separate, so a fallback hit after failed publication may
have generated once. Retain candidate failures in bounded diagnostics; never
claim such a hit avoided generation. Concurrent processes may both generate,
as in the current cache; redundant work is not globally locked.

If both candidates fail, return fresh code and a typed storage-location failure
containing both reasons. Normal generation, execution, and class binding remain
valid. Memory hits use previously admitted code and do not probe disk again;
do not introduce a new unbounded or implicit memory-only cache on bypass.

## Shared API And Lifetime

Retain `GeneratedCodeCache(directory, ...)` and ordinary `get(request, producer)`
for existing explicit single-directory consumers. Also allow construction with
`directory=None` (the default) for routing-only consumers; no placeholder path or
directory I/O is performed. Add a neutral immutable
candidate carrier and an optional keyword-only `locations=` routing argument
to `get`. Supplying it overrides only storage placement for that request; it
does not change request identity, the producer namespace/revision, or code binding.
Omitted `locations` uses the constructor directory, or an empty route when no
directory was supplied. Explicit `locations=()` means storage bypass and must
not fall back to a constructor directory. Routes contain at most two candidates.
The shared location policy returns these candidates; it never reads Lifecycle
environment variables or imports modules to discover an origin.

Lifecycle keeps one shared cache object and one process dependency inventory.
All locations share the existing capacity-32 code LRU, producer dependency fences,
reentry state, and request counters. Do not create an independent cache object
per module/directory or relax an observed-edit fence by switching locations.
Location decisions and diagnostic history are separately bounded to 32 entries.
No module objects, classes, callables, traceback frames, or runtime defaults are
retained in placement decisions. Cache hits do not rescan generator dependencies.

Expose `GeneratedCodeCache.diagnostics` and Lifecycle `cache_diagnostics()` as
oldest-first immutable tuples of the most recent 32 completed request snapshots,
including repeated requests. Disabled Lifecycle returns an empty tuple. Each
frozen `CacheDiagnostic` contains request digest (or None if identity failed),
namespace, selected `CacheLocation` (or None), attempted candidate locations,
candidate failures, final outcome type (`CacheHit`, `CacheMiss`, or
`CacheBypass`), and `generated: bool`. An optional final problem or rejected-entry
problem explains non-location failures. Location layout is represented by typed
carriers rather than undocumented string flags. A `CacheProblem` stores only the
exception type and bounded message (1024 characters); never an exception instance,
traceback, code object, live class, callable, or runtime value. Failure snapshots
use these problems. Existing result wrappers remain unchanged; exhausted routes
return a `CacheLocationError` with those frozen failure snapshots.

Memory hits record no attempted disk candidates and `generated=False`. A
post-generation fallback hit records both attempts/failures and `generated=True`.
Producer exceptions propagate unchanged and do not add a completed-request
snapshot or counter outcome. `clear()` clears diagnostic history and routing
preferences after attempting tracked-location maintenance, while preserving
producer invalidation. Diagnostic retrieval performs no I/O and logs nothing.

With an explicit root, clearing targets that consumer's namespace directory.
Automatic `clear_code_cache()` removes recognized artifacts/probes only from
locations tracked by this adapter in the current process, clears its code LRU,
and preserves its invalidation fence. It does not crawl every source tree/home
mirror, clear another consumer, or promise to remove evicted/unvisited locations.
Broader disk maintenance is deferred; manually removing known cache directories
is safe between processes. Restart remains necessary after generator edits.

## Implementation Checkpoints And Tests

1. **Neutral routing and storage.** Add candidate/layout carriers and descriptor
   admission with bounded preferences. Preserve single-directory callers.
   Prove local preference, private leaf creation beneath ordinary `__pycache__`,
   read-only/missing/unsafe local fallback, authoritative override bypass, missing
   home, encoded/long origins, bounded decision eviction, and namespace isolation.
2. **Lifecycle controls and origins.** Implement the precedence table and frozen
   configuration diagnostics. Extend the existing fresh-process canonical cache
   fixture with automatic placement and fallback, instead of duplicating its
   successful lifecycle assertions. Cover source-backed `__main__`, dynamic/no
   file, archives, symlinked author paths, cwd changes, invalid enable values,
   `~` expansion, disabled no-I/O, and directory-based legacy opt-in.
3. **Adversity and verification.** Fault-inject permission/ACL/path replacement
   after admission, read and publish failures, corrupt artifacts, full/unavailable
   fallback, and partial probe cleanup. Assert producer-at-most-once, original
   exception behavior, one logical counter outcome, global invalidation/reentry
   fences across directories, LRU bounds, and scoped clearing. Use actual
   macOS/Linux trust gates; Windows must safely bypass until separately verified.
4. **Performance and review.** Repeat the recorded thirteen-class and Tk probes
   in disabled, local-empty/local-warm, and fallback-empty/fallback-warm modes.
   Explicitly set `off` for disabled runs. Record location admission and origin
   costs, generation counts, ranges, and total startup. Preserve the existing
   substantial warm gain without changing generation code or security checks.
   Review implementation and user controls before claiming verified default-on.

All filesystem tests use isolated synthetic source/home/cache roots. Never
chmod real checkout/system files, create artifacts in the real user's home, or
depend only on `os.access` mocks. Use fault injection for precise write races;
use real private permissions and ACL checks for the platform trust gate.
Existing shared-cache, Lifecycle, backend, interpreter, and wheel/sdist proofs
remain required. Successful existing generated goldens must remain unchanged.

## Review Object And Activation Boundary

The requested review is a draft-design review, not settled-tree implementation
acceptance. Preserve uncommitted code and GWZ membership changes. Pin reviewed
document bytes by SHA-256 and pin the source-context file digests, rather than
committing unrelated or unauthorized work merely to obtain a Git revision.
Reports must disclose this deviation from the review-loop skill's committed
object requirement. Do not call the result a release, interface freeze, or
default-activation verification. A committed settled tuple and user-surface
review remain acceptance gates when the operator authorizes a commit. Default-on
implementation in this isolated lane is already authorized; publication is not.

Use two peer-blind readers on Consistency and Safety, file their reports, and
merge their findings. Remediation is bounded to at most two rounds; preserve
originating-finding closure. Review approval of this DRAFT means its specification
is fit to implement only. It does not authorize implementation in the active
LCM lane, commits, pushes, or weaker storage trust.

## Controlling-Document Amendments

This revision supersedes R1's deferred-default decision. During implementation,
update these documents in the same checkpoint; historical measurements remain
identified as opt-in measurements rather than silently reinterpreted:

- `docs/CachePolicy.md`: replace explicit-directory-only persistence with either
  that existing single-directory API or routed candidates; retain trust rules
  and explain generated fallback hits and diagnostic retrieval.
- `../yidl-lifecycle/dev-docs/LifecycleCodeCache.md` and package README: replace
  directory-required/removed-directory-disable instructions with the table above,
  automatic local/home placement, and explicit `off`; expose configuration and
  request diagnostics. Qualify "a hit skips generation" with `generated=False`.
- `../yidl-lifecycle/dev-docs/LifecycleCodeCacheStartup.md` and perf README: keep
  original numbers labeled as pre-policy opt-in evidence, add automatic-policy
  measurements, and make disabled benchmark runs explicitly select `off`.
- `../yidl/dev-docs/YidlGeneratedCodeCachePlan.md` and checkpoint indexes: record
  the consumer policy amendment without introducing a YIDL-core dependency.
