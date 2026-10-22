# Windows Persistence — STATE-AXIS REVIEW

**Review object:** Windows persistent compiled-code cache amendment at `yidl-cache` commit `aaa55ffba0f1cf63089da313fdf4e8316501a505`, including controlling DRAFT `dev-docs/WindowsPersistence.md`; unchanged Lifecycle cache-only overlay at `e979f2412b809e2a8a60eefb942790cef1e715ff`.

**Baseline:** Original cache base `a4ae595e0f9835a86dadec3bedebd383ebf9ae2f`; previous reviewed cache checkpoint `6d91a0cec59bb926e4ffb627847a6e1562b0dc9e`; Lifecycle base `77b0dd574404e314fecc46069a54f8fcedb9555d`. Sources were inspected through pinned Git objects and read-only file inspection.

**Date:** 2026-10-23

**Axis:** State — durable-state semantics, trust, failure ordering, races, recovery, restart legality, and maintenance confinement. Independent, adversarial, read-only. The other axis runs in parallel; nothing here relies on its current-round report. Filed verbatim by the lane owner.

**Verdict: GO** — both prior counterexamples are addressed on the inspected tree. No P0, P1, or P2 finding remains on this axis. One new nonblocking P3 concerns a stale checkpoint digest in the remediation manifest. Review complete; not blocked.

---

## Prior-finding closure table

| ID | Disposition claimed | Verified on corrected tree | Status |
| --- | --- | --- | --- |
| Code P2-1 | Verify the held anchor is an actual volume root; reject substituted directory roots before admission/decoding. | Retraced the original unsafe-physical-ancestor/substituted-drive sequence through the corrected call graph. The alias’s held directory handle fails exact volume-root validation before child traversal, probe creation, or decoding. Recorded Windows RED/GREEN evidence and the regression fixture use the original inherited-private-descendant premise. | Satisfied in this independent State assessment. The Code reviewer issues its own closure verdict. |
| State P3-1 | Accept only documented Windows publication-conflict outcomes, preserving protections and POSIX expectations. | Retraced the exact successful-rename/exclusive-handle-open interleaving in the deterministic test. The first writer remains inside its original exclusive context while the contender invokes the real rename. Assertions require one miss, one typed bypass, valid code, bounded diagnostics, cleanup, and a generation-forbidden disk hit. | Closed. |

## Changed-range analysis

The remediation range contains sixteen paths: ten correction/policy/evidence files and six original-review or lane-owner audit outputs.

Runtime changes are confined to:

- One `GetFinalPathNameByHandleW` ctypes binding in `windows_api.py`.
- A bounded `require_volume_root()` check in `windows_storage.py`, called on the already-held anchor before volume/ACL admission and child traversal.

Test changes revise the ordinary concurrent-publication expectation and add focused Windows root-validation and deterministic publication-conflict files. Policy and amendment updates describe the supported-root restriction and distinguish original from revised evidence.

The shared codec, Windows dispatch seam, routing, diagnostics, producer fences, sharing modes, publication algorithm, and Lifecycle repository remain unchanged. Their relevant committed bytes were compared directly.

The actual base-to-revised checkpoint contains twenty-four cache paths once review/audit additions and the two new regression files are included. The continuation prompt’s retained “14 paths” description refers to the original implementation scope; inspection used the actual Git ranges.

**Architectural classification:** No NEW ARCHITECTURAL root and no materially changed review premise were established. The root guard enforces the existing complete-ancestry premise through conservative rejection. It does not introduce physical-path reopening, substituted-drive support, a new mutation boundary, or a storage/routing redesign. The new P3-2 below is evidence bookkeeping, not an architectural root.

## 0. Evidence base

This continuation retained the original review context and inspected the revised committed object.

- Starting and ending HEAD checks both returned cache `aaa55ffba0f1cf63089da313fdf4e8316501a505` and Lifecycle `e979f2412b809e2a8a60eefb942790cef1e715ff`. Lifecycle remained clean; cache additions were the permitted round-two prompts.
- Read both complete prior reports, the merged remediation plan, remediation evidence Markdown/JSON, and owner review checkpoint. No peer round-two prompt or report was read.
- Inspected the complete previous-to-current diff and actual base-to-current file inventory.
- Read the complete revised Windows runtime modules: `windows_api.py` (344 lines) and `windows_storage.py` (422 lines).
- Read the complete revised `test_generated_code_cache.py`, new `test_windows_publication.py` (106 lines), and new `test_windows_roots.py` (232 lines).
- Reviewed the policy/amendment/index changes against the original policy, scope, tests, canonical fixtures, shared storage, routing, invalidation, and consumer material inspected in round one.
- Used inspection-only `python3 -B` scripts to parse/hash committed bytes without importing product code or writing files. Eighteen revised package/test entries and the two unchanged Lifecycle overlays matched their declared source hashes and parsed successfully.
- Verified all nine RED runtime hashes against the previous reviewed runtime. The qualified Windows cache and Lifecycle source hashes matched their pinned objects.
- Verified the original reports, original prompts, and initial evidence hashes. The owner checkpoint digest did not match; this is recorded separately as P3-2.
- Confirmed identical previous/current bytes for shared `storage.py`, `cache.py`, `locations.py`, `diagnostics.py`, and the original evidence manifest.
- Consulted Microsoft’s [GetFinalPathNameByHandleW contract](https://learn.microsoft.com/en-us/windows/win32/api/fileapi/nf-fileapi-getfinalpathnamebyhandlew), supplementing the API contracts consulted during the initial review.

No product/test execution, builds, installs, remote access, ACL/cache mutation, Git mutation, or file/report writes were performed. Actual Windows RED/GREEN outcomes are recorded implementation evidence; they were not independently rerun. Raw logs are represented by manifest hashes and were not retrieved.

## Problem, requirement provenance, and scope

The original problem was absent Windows persistence behind a deliberate non-POSIX trust bypass. The operator authorized closing that implementation gap, including real persistence, generation-forbidden fresh-process reuse, safe rejection of unknown trust/capabilities, and bounded Lifecycle integration verification.

The remediation remains necessary and localized. The initial root assumption could omit security-controlling physical ancestors. Rejecting an anchor whose held-object identity does not establish an actual volume root closes that hole without adding substituted-drive support or changing dependencies/infrastructure.

The recorded API feasibility probe distinguishes an ordinary volume root from a directory-backed drive. This supports the existing stdlib/Windows route rather than requiring a broader implementation. The publication correction changes tests to recognize existing documented safe behavior; it does not relax the product’s protections.

Changes remain within `yidl-cache`. Lifecycle is unchanged from the previously authorized three-file overlay. Astichi, YIDL, annotation implementations, other consumers, infrastructure, and GWZ remain reference-only.

NTFS-only storage remains a bounded implementation limitation. Revised evidence records ordinary NTFS reuse and ReFS-source-to-NTFS-home fallback under both explicit engines. No requirement to add ReFS storage or broaden Windows qualification follows from either finding.

No blocking necessity, scope-authorization, or requirement-provenance gap was found.

## 1. Findings

### [P3-2] Remediation manifest’s preserved checkpoint digest does not match the committed checkpoint

**Location:** `dev-docs/WindowsPersistence-RemEvidence-1.json:254–260`, specifically the `WindowsPersistence-ReviewCheckpoint.md` entry at line 255.

**Violated invariant:** A manifest’s preservation digest must identify reproducible bytes and distinguish an earlier snapshot from the current owner-maintained audit document.

The manifest groups the checkpoint with preserved original reports, prompts, and evidence. Recalculating SHA-256 from the committed checkpoint produces a different digest from that entry. The other five entries in the group match.

**Reproduction:** Read the checkpoint at `aaa55ffba0f1cf63089da313fdf4e8316501a505`, calculate its SHA-256 in memory, and compare it with the manifest’s named entry. The mismatch is deterministic. The committed checkpoint contains owner remediation-status updates, so its legitimate mutable role differs from the immutable original reports/prompts.

**Impact:** Verification of the manifest’s audit-preservation group fails, and a later auditor cannot identify the checkpoint snapshot represented by the recorded digest from this entry alone. Runtime/test hash correspondence and the original report preservation checks still succeed; this does not invalidate either implementation closure.

**Required correction:** Update the digest to the intended committed checkpoint, or explicitly label it as a historical snapshot and provide a retrievable object containing those bytes. Do not modify the immutable original reports/prompts merely to make this group uniform.

**Closure check:** Recalculate all entries in the group against their explicitly identified objects and require exact matches. This is a metadata-only correction; product tests need not be repeated for it.

## 2. Invariant analysis

### Original publication interleaving is now tested directly

`test_windows_publication.py:33–49` selects the first writer under a lock, performs its real rename, and holds it before returning to the enclosing exclusive-handle context. The second writer waits for publication, invokes the real competing replacement, records its native error, and releases the first writer afterward. The test therefore recreates the original counterexample rather than injecting a synthetic publication exception.

The assertions require:

- Exactly one `CacheMiss` and one `CacheBypass`.
- One native replacement failure restricted to the controlled open-target conflict codes.
- Correct executable code for both callers.
- One generated diagnostic per request and a typed publication failure for the loser.
- A fresh memory-disabled reader hit with generation forbidden.
- No abandoned temporary files.

The ordinary concurrency test similarly permits only observed replacement failures corresponding to typed publication bypasses on Windows. It still requires at least one successful publication and keeps the original all-miss expectation on POSIX.

Recorded Windows RED reproduced one real miss and one real bypass, failing the former two-miss expectation. Recorded GREEN covers the corrected deterministic and ordinary tests. Source inspection independently establishes why the new assertions match that state sequence.

### Held-anchor validation closes the hidden-ancestry path

`windows_storage.py:133–149` queries the already-open anchor with normalized volume-GUID naming. It accepts only an exact GUID volume root, rejecting additional directory components and insufficient-buffer reports. Microsoft documents both the requested naming form and return-size/error behavior in [the API contract](https://learn.microsoft.com/en-us/windows/win32/api/fileapi/nf-fileapi-getfinalpathnamebyhandlew).

The guard runs at lines 229–233 after the root handle is recorded for cleanup, but before NTFS/ACL admission and traversal. Consequently:

- An alias hiding an unsafe physical ancestor fails before artifact decoding.
- Failure does not create child directories or admission probes.
- No canonicalized path is reopened.
- Oversized, unrecognized, unavailable, or missing-API cases fail conservatively.
- The same held anchor remains the parent of all accepted relative traversal.

The new regression preserves the original counterexample’s important distinction: descendants have private effective ACLs with inheritance enabled, while an omitted ancestor has non-inheritable untrusted `WRITE_DAC`. The correction therefore addresses the missing ancestry check rather than merely rejecting an already-unsafe leaf.

### Failure translation and routing remain sound

A root-validation `CacheStorageError` follows the existing location-failure route. API `OSError` failures are translated by the unchanged shared seam. Root failure occurs outside the entry-rejection conversion, so an untrusted route does not become an ordinary corrupt-artifact miss.

The substituted-root regression checks an authoritative override’s typed bypass before unmarshalling, maintenance rejection, separate ordinary-NTFS automatic fallback, one producer call, and generation-forbidden reuse at the fallback. Mapping identity is checked before removal, and the unsafe test grant is removed in `finally`.

No new lock, durable metadata, invalidation state, retry loop, or cleanup grammar is introduced.

### Publication, recovery, and maintenance protections remain intact

Exclusive temporary creation, protected security, bounded write, flush, handle-relative rename, failed-publication cleanup, and ancestor handle lifetime are unchanged. Sharing conflicts can lose a publication opportunity but do not expose partial artifacts.

Interrupted publication still leaves either a prior/final artifact or a recognized ignored temporary file. The shared decoder continues to reject damaged or incompatible artifacts before unmarshalling. No new crash state invents a successful entry.

Maintenance retains handle-relative enumeration/deletion, exact name recognition, typed unsafe-object failures, and tracked-location confinement. Shared clearing still preserves invalidation fences and cumulative counters.

### Persistence and compatibility evidence remains properly bounded

The revised manifest reports successful Windows cache checks and focused Lifecycle checks under explicit Python and native Rust, alongside Mac/Linux preservation. The canonical process fixture still forbids warm generation/AST compilation and binds current runtime values. Repeated ReFS-source-to-NTFS-home evidence records matching requested/selected engines without fallback and no warm producer imports or native compilation calls.

These recorded results correspond to the inspected source hashes. They do not independently qualify other Windows versions, architectures, impersonation, power-loss durability, performance, or deployment.

## 3. Risks and next action

Both original findings are closed in this State assessment. No new blocking state or recovery defect was established. The remaining P3-2 is confined to an audit-document digest; it does not change runtime trust or test evidence.

Qualification remains Windows 11 AMD64 with CPython 3.13.5. ReFS persistence, other Windows configurations, impersonation, and crash/power-loss testing remain outside the established evidence.

The next action is to combine this GO with the independent Code re-verdict and correct or explicitly qualify the stale checkpoint digest as a bounded documentation follow-up.

**Review complete; not blocked. The reviewed tuple remained unchanged.**