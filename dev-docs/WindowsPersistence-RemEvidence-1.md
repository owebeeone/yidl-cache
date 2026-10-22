# Windows persistence remediation 1 — implementation evidence

Date: 2026-10-23. Status: **one uncommitted correction; independent re-verdicts
pending**. Neither finding is self-closed. The original combined gate remains
NO-GO until the lane owner receives the required re-verdicts.

## Authority, object and boundary

This implements the two dispositions in
[the merged round-1 plan](WindowsPersistence-RemPlan-1.md). The exact initial
review objects are cache `6d91a0cec59bb926e4ffb627847a6e1562b0dc9e` and the
reference Lifecycle overlay `e979f2412b809e2a8a60eefb942790cef1e715ff`.
The full [Code](WindowsPersistence-ReviewCode.md) and
[State](WindowsPersistence-ReviewState.md) reports were read before editing and
remain unchanged, as do their prompts and the original evidence manifest.

Allowed changes are confined to this package's existing Windows root admission,
one existing ABI binding, narrow trust/concurrency tests, and current
policy/evidence. Lifecycle, YIDL, Astichi, all annotation work and other consumers,
dependencies, infrastructure, and GWZ metadata are reference-only. No Git
mutation, build, install, original remote source/environment change, registry or
host-policy change was performed. Actual Windows testing used a new disposable
candidate source tree; ACL faults and drive mappings involved test objects only.

[The remediation manifest](WindowsPersistence-RemEvidence-1.json) pins all revised
package/test bytes, the immutable reference overlay, engine proof and log
digests separately from the initial historical manifest.

## Original-counterexample results

| Finding | Actual Windows RED before correction | Implemented check / observed GREEN |
| --- | --- | --- |
| Code P2-1 | Ordinary physical access bypassed the untrusted ancestor. The same seeded artifact through a temporary substituted drive reached the forbidden `marshal.loads` hook. | Held-anchor volume-root validation rejects the alias before admission/decoding, preserves the artifact, and permits independent ordinary-NTFS home fallback with one producer call. A fresh generation-forbidden home request hits. |
| State P3-1 | With the first writer suspended after successful rename and before closing its exclusive handle, the second real replacement failed with Windows error 5. Outcomes were one `CacheMiss` and one `CacheBypass`, failing the original two-miss expectation. | The deterministic test requires exactly those safe miss/bypass outcomes, executable correct code for both callers, one typed sharing failure, bounded diagnostics, no abandoned temporaries and a fresh generation-forbidden hit. The ordinary concurrency test retains the stronger POSIX assertion. |

The initial two-test RED run produced two genuine failures in 0.12 seconds.
There was no capability skip or artificial replacement error: the first failure
was the reviewed route reaching the shared decoder, and the second came from
the actual Windows rename operation under the specified held-handle ordering.
The fixed focused run passed all three targeted tests (including the ordinary
concurrency test).

### P2-1 setup and confinement

The regression first seeds a valid artifact using ordinary trusted NTFS storage.
It enables ordinary ACL inheritance on the cache path and artifact, then verifies
both private effective access and absence of `SE_DACL_PROTECTED` using the actual
security descriptor. An ancestor above the mapping target receives a
non-inheritable Everyone `WRITE_DAC` grant. Descendant effective ACLs remain
private, reproducing the review's precise omitted-ancestry premise rather than
substituting an already-permissive leaf.

The test checks `GetLogicalDrives` and current-user `QueryDosDeviceW` before
selecting an unused letter. On this host it selected `Z:`. `subst` creates that
one mapping; cleanup first verifies that its target still matches the object the
test created, removes only that mapping, and verifies its absence. RED and GREEN
both recorded creation and removal. The unsafe grant is removed in `finally`.
No original mapping, workspace ACL, registry entry, or host policy is altered.

After the fix the authoritative alias override returns one generated
`CacheBypass` with a typed root-validation failure and one bounded diagnostic;
no decoder call occurs. Alias maintenance also fails conservatively. Automatic
placement instead selects a separate trusted ordinary-volume home, generates at
most once, then hits there from a fresh cache with generation forbidden. Explicit
home maintenance removes its one artifact; the original inheritance-enabled
artifact remains byte-for-byte unchanged and no temporary entries remain.

### P3-1 deterministic ordering

The test wraps the existing rename function without changing its arguments or
sharing flags. Both requests reach a producer barrier as misses. A lock chooses
the first writer; after its real rename succeeds, an event holds it inside the
existing exclusive-handle context. The contender then performs its real rename,
records the native failure, and releases the first writer only after that
attempt. All waits have bounds and the release event is also set on failure.

The host returned access-denied error 5 for the open-destination conflict.
Tests permit only the documented open-target conflict codes 5/32 at the actual
replacement call, with a corresponding typed publication bypass. They do not
accept arbitrary bypasses, two failed publications, or malformed returned code.
The ordinary concurrency test applies this allowance only on Windows; POSIX
still requires both writers to publish. Product sharing modes are unchanged.

## Localized correction and premise accounting

`windows_api.py` adds only the standard-library ctypes signature for
`GetFinalPathNameByHandleW`. `windows_storage.py` calls a bounded validator on
the already-held anchor before volume/trust admission or child traversal. The
validator asks for `FILE_NAME_NORMALIZED | VOLUME_NAME_GUID`, accepts exactly a
volume-GUID root with no path components, and rejects oversized, unrecognized
or unavailable reports conservatively. It does not resolve a pathname and then
reopen it; subsequent operations remain relative to the same protected handle.

A small actual-Windows API probe distinguished the ordinary volume root
(49-character GUID root) from a backing directory (101-character GUID-prefixed
path). Focused tests also cover a short non-root report, an oversized report and
an unavailable API response before any cache directory or decoding is permitted.
See Microsoft's [final-path-by-handle contract](https://learn.microsoft.com/en-us/windows/win32/api/fileapi/nf-fileapi-getfinalpathnamebyhandlew).

This enforces the existing complete-physical-ancestry premise by narrowing root
admission. It does not add directory-backed drive support, a physical-path
reopening algorithm, shared interfaces, architecture, mutation boundaries, wire
formats, routing, generation/binding behavior, or a new platform capability.
The local call graph adds one read-only anchor check and its existing-system-API
binding. No replacement of the protected publication/cleanup algorithms is
involved. The previously missing platform assumption is now explicit in the
current public policy. Reviewer reuse/premise classification belongs to the
lane owner; this report does not make an independent closure decision.

## Revised verification boundary

| Check | Actual result |
| --- | --- |
| Windows 11 build 26200, AMD64, CPython 3.13.5: full cache suite | 69 passed, 17 skipped |
| Windows Lifecycle cache/configuration/fault scope at reference `e979f24`, explicit Python | 45 passed, 2 skipped |
| Same reference and scope, explicit native Rust | 45 passed, 2 skipped |
| macOS arm64 CPython 3.14.3: full cache suite | 57 passed, 29 skipped |
| Linux aarch64 CPython 3.13.5: full cache suite | 55 passed, 31 skipped |

Skips are other-platform or POSIX-specific mechanics. Neither counterexample,
Windows persistence, nor the original Lifecycle public diagnostic is skipped.
The unchanged canonical fixture proves cold generation then fresh-process disk
hits for explicit, local, and home placement on each engine. Both ordinary-root
persistence and the existing junction/ancestor, unsafe-ACL, hard-link, corruption,
bounded-read, cleanup and confined-maintenance checks pass.

The separate actual ReFS-source-to-NTFS-home proof was repeated with this cache
candidate and the immutable Lifecycle reference. For each explicit engine, a
fresh isolated home receives two cold misses, then a new process returns two
hits with zero generation/AST compilation and current runtime values. Retained
local failure reasons still state the NTFS capability requirement. Each engine
has independent storage. Explicit ReFS storage remains a typed safe bypass.

Cold engine requests and selections match with empty fallback metadata. The
native process records 95 Rust lowering calls, 95 compile-validation calls, and
two native Python-AST materializations. The native binary remains SHA-256
`db81f125ed30c3b39eea2160c2f296493b2aee59ff712f187e9aa540d3572da6`.
Warm processes import none of Astichi, the generated Lifecycle producer or
`yidl.generation.data_def_sys` and perform no native compilation calls. No native
binary was rebuilt. Reference Astichi and YIDL source identities remain the
initially qualified `ce47c629` and `ee5ded08` runtime bytes.

Black, whitespace/diff checks, AST parsing (including disabled Windows code),
standalone-import-boundary checks and source/hash verification accompany the
platform evidence. The shared codec, POSIX algorithms and Lifecycle repository
have no remediation diff. Original report/prompt and evidence bytes are retained.

The qualification remains Windows 11 AMD64/CPython 3.13.5. Other Windows versions,
architectures, impersonation, ReFS storage, performance, crash/power-loss testing,
full consumer matrices, and release activation are not newly qualified. This
patch is prepared for the lane owner to settle and for the original reviewers to
issue focused re-verdicts; it does not itself change the review gate.
