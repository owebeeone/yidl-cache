# Windows Persistence — CODE-AXIS REVIEW

**Review object:** Windows persistent compiled-code cache amendment at yidl-cache `aaa55ffba0f1cf63089da313fdf4e8316501a505`, including controlling `dev-docs/WindowsPersistence.md`; unchanged Lifecycle cache-only overlay at `e979f2412b809e2a8a60eefb942790cef1e715ff`. Committed first-remediation checkpoint.

**Baseline:** Original cache implementation base `a4ae595e0f9835a86dadec3bedebd383ebf9ae2f`; previous reviewed cache checkpoint `6d91a0cec59bb926e4ffb627847a6e1562b0dc9e`. Lifecycle base `77b0dd574404e314fecc46069a54f8fcedb9555d`. Sources were inspected through pinned Git objects, complete changed-file reads, and range diffs. Reference source objects remain Astichi `ce47c629973d8e5a6340ceaa89b0bc3e8788d5fe` and YIDL `ee5ded0854aa5b1fc0ddfa7213b765009b63bb95`.

**Date:** 2026-10-23

**Axis:** Code — architecture, interfaces, call graphs, compatibility, ABI, resource lifetime, and required Surface analysis. Independent, adversarial, read-only. The other axis runs in parallel; nothing here relies on its current-round review. Filed verbatim by the lane owner.

**Verdict: GO** — Code P2-1 is closed. The prior State P3-1 correction also withstands Code inspection. No new findings. The first-round pre-commit-to-GO condition is satisfied.

---

## Prior-finding closure table

| ID | Disposition claimed | Verified on corrected tree | Status |
| --- | --- | --- | --- |
| Code P2-1: substituted drive hides physical ancestors | Validate the held anchor as an actual volume root; reject directory-backed or unprovable roots before admission/decoding. | Retraced the original private, inheritance-enabled artifact below an ancestor with non-inheritable untrusted `WRITE_DAC`. The substituted anchor now fails `require_volume_root()` before child traversal or artifact access. The committed regression preserves that precise setup and the separate actual-Windows evidence records RED reaching forbidden unmarshalling, followed by GREEN authoritative bypass and trusted-home fallback. | **Closed.** |
| State P3-1: concurrency test requires two Windows publications despite a permitted sharing conflict | Accept only the documented Windows sharing-conflict loser while retaining safe handles, correct code, cleanup, and a fresh-reader hit; preserve POSIX expectations. | Retraced the successful-rename/exclusive-handle-open interleaving against the unchanged backend and the new deterministic test. It holds the first published handle until the contender performs its real rename, restricts errors to the controlled conflict outcomes, checks miss/bypass diagnostics and both returned code objects, then requires a generation-forbidden disk hit and no temporary files. | **Correction verified on the Code axis.** The original State reviewer issues its separate re-verdict. |

## Changed-range analysis

The remediation range changes sixteen paths: ten correction/test/policy/evidence files and six prior-review or owner-audit outputs. The complete implementation-base-to-revised range contains twenty-four paths, including those audit documents; the continuation prompt's retained fourteen-path parenthetical describes the original implementation range.

Actual runtime changes are confined to:

- One `GetFinalPathNameByHandleW` binding in `windows_api.py`.
- `require_volume_root()` in `windows_storage.py:133–149`.
- Its invocation on the already-held anchor in `directory_handle()` before volume/trust admission and child traversal.

Tests add substituted-root and unknown-root regressions, deterministic publication-conflict coverage, and platform-specific expectations in the existing concurrency test. Current policy and amendment describe the supported-root restriction; remediation evidence is separately recorded.

The shared storage dispatch, codec, request identity, routing, diagnostics, model, POSIX trust code, and public exports are byte-identical to the previous reviewed checkpoint. Lifecycle has no remediation diff.

**NEW ARCHITECTURAL root: none. Materially changed review premise: none.** The correction enforces the previously required complete-ancestry premise through conservative root admission. It does not implement substituted-drive support, reopen resolved paths, replace traversal/publication algorithms, change sharing modes, or alter public interfaces, wire compatibility, routing, generation, or consumer binding.

No change outside the accepted dispositions requires broader implementation authority.

## 0. Evidence base

This review produced only this report. No file/Git writes, product execution, tests, builds, installs, remote access, cache operations, ACL changes, or drive mappings were performed.

Both required heads matched at the start and end:

- Cache: `aaa55ffba0f1cf63089da313fdf4e8316501a505`
- Lifecycle: `e979f2412b809e2a8a60eefb942790cef1e715ff`

Lifecycle remained clean. Cache working-tree additions were only the two permitted current-round prompts. The other axis's current-round prompt/report was not read.

Before implementation or design inspection, I reread the public README, `docs/CachePolicy.md`, and Lifecycle's `dev-docs/LifecycleCodeCache.md`. The first-round cold Surface assessment remains available in the preserved Code report.

Inspected evidence includes:

- Both complete prior-round reports, the merged remediation plan, and remediation evidence Markdown/JSON.
- All changed runtime code and its complete surrounding modules: `windows_api.py` and `windows_storage.py`.
- Complete new `tests/test_windows_roots.py` and `tests/test_windows_publication.py`, plus the revised generated-code tests.
- The amendment/policy/development-index changes and original/owner audit outputs.
- The unchanged shared storage/routing/codec and Lifecycle integration dependencies already read completely in round one, with committed-byte comparisons confirming preservation.
- Both initial and remediation evidence manifests, including original-counterexample descriptions, platform results, engine-selection/native-call records, source hashes, and qualification limits.

Inspection-only `python3 -B` checks:

- Matched all nine revised package hashes and all nine revised cache-test hashes.
- Matched all nine RED-runtime hashes against the previous reviewed checkpoint.
- Parsed those Python sources in memory without importing reviewed product code.
- Matched both unchanged Lifecycle test-overlay hashes and parsed those files.
- Matched the qualified-Windows source record against all nine cache modules and twelve Lifecycle source modules.
- Confirmed that the original evidence manifest is unchanged.
- Confirmed preservation of the seven shared cache modules outside the two Windows modules.

Five of the six preserved audit/snapshot hashes match current files. The recorded owner-checkpoint snapshot hash does not describe the current checkpoint, which includes subsequent lane-owner remediation-status additions. I did not use that snapshot hash to authenticate the current owner checkpoint or qualify runtime bytes. Preserved reports, original prompts, and original implementation evidence match their recorded hashes.

Actual Windows outcomes discussed below are recorded implementation evidence, not independently rerun tests. Raw execution logs are represented by hashes in the manifest and were not retrieved during this review.

## Problem, requirement provenance, and scope

The original problem was absent Windows persistence: the deliberate non-POSIX trust guard returned safe bypass where the Lifecycle diagnostic expected a persistent home-route hit. Generation and transactions continued to work.

The operator authorized closing that implementation gap, recording a reviewable checkpoint, and running this review cycle. The resulting requirements remain real Windows persistence, fresh-process generation-forbidden reuse, safe rejection of unknown trust/capabilities, preservation of Mac/Linux behavior, and explicit Python/native-Rust evidence.

The first-round Code finding identified a missing prerequisite within that existing trust contract: a drive-letter spelling did not establish that traversal began at a physical volume root. The selected remedy is appropriately local. It rejects unsupported anchors using an existing Windows API on the held object rather than widening support or introducing a different traversal architecture.

The recorded small Windows probe distinguished a real volume root from a directory-backed anchor using normalized volume-GUID paths. The committed implementation follows that supported stdlib `ctypes` route. No dependency, infrastructure, global ACL, registry, or host-policy prerequisite was introduced.

Implementation remains confined to yidl-cache and the existing three-file Lifecycle overlay. Lifecycle runtime/annotation code, YIDL, Astichi/native engines, other consumers, Undoable, Pyrolyze, GWZ, and infrastructure remain reference-only.

NTFS-only storage remains a bounded capability limit. Reported ReFS-source-to-NTFS-home reuse satisfies the practical source-volume requirement without requiring ReFS persistence. No requirement-provenance or scope-authorization blocker remains.

## 2. Invariant analysis

### The original substituted-root counterexample is defeated

The regression at `tests/test_windows_roots.py:105–190` does not replace the original counterexample with a permissive leaf:

- It seeds a valid artifact using trusted ordinary storage.
- It enables inheritance on the relevant existing directories/artifact.
- It verifies private effective access and absence of DACL protection.
- It places the non-inheritable unsafe controller grant above the mapping target.
- It establishes physical-route rejection before exercising the substituted spelling.

On the corrected flow, the opened anchor is retained and passed directly to `GetFinalPathNameByHandleW`. The binding has the appropriate handle, writable UTF-16 buffer, capacity, flags, and DWORD return types.

The validator requests normalized volume-GUID naming and accepts only the complete canonical volume-root shape, with no descendant components. Failed calls, oversized results, and non-root reports reject conservatively. The fixed-size buffer is sufficient for the accepted root grammar; larger reports are rejected rather than retried or trusted.

This agrees with Microsoft's [final-path-by-handle contract](https://learn.microsoft.com/en-us/windows/win32/api/fileapi/nf-fileapi-getfinalpathnamebyhandlew). The result is used only to establish the held object's root premise. No resolved pathname is reopened.

### Rejection occurs before executable-artifact access

All admission, read, write, and maintenance paths enter `directory_handle()`. The new check runs before child traversal, probe creation, artifact opening, or enumeration.

Root-validation `CacheStorageError` is raised outside the entry-rejection conversion inside `WindowsStorage.read()`. It therefore remains a storage-location failure, rather than becoming a corrupt-artifact regeneration signal at that root. API-call `OSError` also reaches the existing typed shared-storage translation.

An authoritative override has one candidate and bypasses. An automatic route can select the independent trusted home candidate. The routing implementation is unchanged, so producer-at-most-once handling and carried generated code are preserved.

The root regression checks authoritative bypass before unmarshalling, typed maintenance failure, unchanged original artifact bytes, automatic home selection, one producer call, a fresh cache's generation-forbidden disk hit, home cleanup, and absence of temporary files.

### Test setup and cleanup are bounded

The substituted-drive helper checks occupied drive letters and DOS-device mappings before selecting an unused letter. Cleanup verifies the mapping's identity before removing it and checks its absence afterward. The isolated unsafe ACL grant is removed in `finally`.

Recorded RED and GREEN runs include mapping creation/removal. The original-counterexample evidence is therefore materially stronger than an unknown-capability skip or an injected decoder result. The corrected unknown-root tests additionally cover unavailable, oversized, and non-root API reports before storage creation.

### Publication expectations now match the retained protections

The product's publication code and sharing flags are unchanged.

The deterministic regression at `tests/test_windows_publication.py:23–106` reproduces the prior State interleaving: the first real rename succeeds, its exclusive handle remains open, and the contender performs its real replacement before the first writer is released.

The test requires exactly one miss and one typed bypass, one controlled native conflict, correct executable code for both callers, bounded diagnostics, a fresh generation-forbidden hit, and no abandoned temporary entries. Its waits and failure-release paths are bounded.

The revised ordinary concurrency test at `tests/test_generated_code_cache.py:191–251` accepts a Windows bypass only when paired with an observed replacement conflict and successful publication. POSIX still requires both misses. This corrects the test contract without weakening storage protections.

### Compatibility and platform separation remain intact

The shared codec and identity modules are unchanged. Existing envelope/header/identity/length/checksum checks still precede unmarshalling. Consumer execution still owns fresh namespaces and current-value binding.

The new API remains inside the lazily loaded Windows backend. An unavailable binding takes the established conservative bypass path. Runtime dependencies remain standard-library-only, and producer imports remain outside cache-hit paths.

Recorded revised verification reports Windows cache results, unchanged focused Lifecycle checks on both explicit engines, and Mac/Linux preservation. The canonical Lifecycle fixture still uses fresh processes and forbids warm generation, AST compilation, and dependency rechecks.

The separate revised ReFS-source proof records independent storage per engine, matching explicit cold engine selection without fallback, native lowering/compilation activity on cold execution, and no producer imports/native compilation on warm execution. These are reported qualification results associated with matching revised source hashes, not tests independently executed by this reviewer.

## Surface analysis

This library adds no CLI. The applicable surface remains its Python API, Lifecycle startup settings, policy, diagnostics, and maintenance controls.

The first-use/configure/fallback/disable/clear walkthrough remains coherent:

- Shared caching requires explicit enablement; Lifecycle documents default-on behavior.
- Startup capture, relative-root anchoring, explicit-off precedence, and authoritative overrides remain clear.
- Automatic source-local/home selection and unsupported-storage bypass remain documented.
- Diagnostics distinguish generation from artifact outcome.
- Clearing is documented alongside disabling, including disabled maintenance being inert and automatic maintenance covering tracked routes only.

The amended policy now explains that the held anchor must prove to be an actual volume root, that directory-backed/unprovable roots bypass, and that validation does not reopen a canonicalized pathname. This accurately describes the correction and closes the earlier public-policy gap.

No new setting, public name, lifecycle pair, or default was introduced. No Surface defect was established. These conclusions are source-traced; examples were not executed during review.

## 3. Risks and next action

No blocking or nonblocking Code finding remains on this tuple. Code P2-1 is independently closed by retracing its original counterexample through the corrected held-object guard, supported by separately recorded actual-Windows RED/GREEN evidence.

Qualification remains bounded to the recorded Windows 11 AMD64/CPython 3.13.5 environment. Other Windows versions/architectures, impersonation, ReFS storage, power-loss qualification, performance, publication, deployment, and broader consumer matrices are not newly accepted.

The next action is to incorporate this Code GO and the separate State re-verdict into the lane's combined checkpoint decision. No further implementation change is required by this review.

**Review complete; not blocked. Both pinned heads remained unchanged.**