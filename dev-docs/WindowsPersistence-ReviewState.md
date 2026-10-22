# Windows Persistence — STATE-AXIS REVIEW

**Review object:** Windows persistent compiled-code cache implementation; controlling DRAFT `dev-docs/WindowsPersistence.md` at cache commit `6d91a0cec59bb926e4ffb627847a6e1562b0dc9e`.

**Baseline:** `yidl-cache` range `a4ae595e0f9835a86dadec3bedebd383ebf9ae2f..6d91a0cec59bb926e4ffb627847a6e1562b0dc9e`; `yidl-lifecycle` cache-only overlay `77b0dd574404e314fecc46069a54f8fcedb9555d..e979f2412b809e2a8a60eefb942790cef1e715ff`. Source objects were read with `git show`; both reviewed HEADs matched the required tuple at the beginning and end.

**Date:** 2026-10-23

**Axis:** State — durable-state semantics, crash/failure ordering, races, trust boundaries, restart legality, and maintenance confinement. Independent, adversarial, read-only. The other axis runs in parallel; nothing here relies on it. Filed verbatim by the lane owner.

**Verdict: GO** — no P0, P1, or P2 findings. One nonblocking P3 finding concerns a Windows concurrency-test assertion that can fail under an allowed sharing-conflict interleaving. Review is complete.

---

## 0. Evidence base

The following inspection was performed without modifying files, importing reviewed product code, running tests/builds, accessing remote hosts, or mutating Git.

- Read applicable workspace/package instructions: `../AGENTS.md`, `../AGENTS_GWZ.md`, `AGENTS.md`, `../yidl-lifecycle/AGENTS.md`, and both relevant development indexes.
- Verified initial cache and Lifecycle HEADs against the exact required tuple. Initial cache working-tree additions were the review prompts; Lifecycle was clean. The final verification returned the same HEADs. The additional review-checkpoint file at the end was permitted lane-owner output and was not read.
- Inspected the complete cache diff and all 14 changed files, including complete changed test files rather than only changed hunks.
- Read all of `src/yidl_cache/windows_api.py` (335 lines), `src/yidl_cache/windows_storage.py` (402 lines), and `src/yidl_cache/storage.py`, including the unchanged shared codec/POSIX implementation.
- Read unchanged routing, locking, diagnostics, invalidation, and placement machinery in `cache.py`, `diagnostics.py`, and `locations.py`.
- Read all of `tests/test_windows_storage.py` (481 lines), the independent `record_process.py` fixture, and the changed artifact, generated-code, location, and location-failure test files.
- Read `WindowsPersistence.md`, `WindowsPersistenceEvidence.json`, `CachePolicy.md`, `CacheLocationPolicyPlan.md`, `CacheLocationPolicyCheckpoint.md`, `SharedCacheCheckpoint.md`, and `README.md`.
- Confirmed that the Lifecycle overlay contains exactly the three authorized paths. Read those three files in full at its pinned HEAD, plus its unchanged cache adapter and canonical `tests/data/cache/lifecycle_process.py` fixture.
- Inspected reference source through the pinned Astichi and YIDL objects, including Astichi’s explicit engine-selection/fallback handling and YIDL’s assembly-runtime imports. Moving dependency documentation HEADs were not treated as runtime drift.
- Ran an inspection-only `python3 -B` script that retrieved committed source with `git show`, parsed it in memory, and recalculated every source/test hash in the evidence manifest. All 18 source/test entries matched, including both Lifecycle overlays.
- Consulted official Microsoft contracts for [NtCreateFile](https://learn.microsoft.com/en-us/windows/win32/api/winternl/nf-winternl-ntcreatefile), [FILE_RENAME_INFORMATION](https://learn.microsoft.com/en-us/windows-hardware/drivers/ddi/ntifs/ns-ntifs-_file_rename_information), [directory enumeration](https://learn.microsoft.com/en-us/windows/win32/api/winbase/nf-winbase-getfileinformationbyhandleex), and [automatic ACE propagation](https://learn.microsoft.com/en-us/windows/win32/secauthz/automatic-propagation-of-inheritable-aces).

Real-platform outcomes below are recorded implementation evidence, not tests independently executed during this review. Raw remote logs were not retrieved; their manifest hashes were read.

## Problem, requirement provenance, and scope

The observed failure was a missing implementation capability: the prior Windows backend deliberately rejected persistence before admission, so the diagnostic test obtained a safe bypass where it expected a home-route hit. Generation and Lifecycle transactions continued to work. The operator’s subsequent direction to fix that implementation gap authorizes actual Windows persistence, bounded cache tests/policy/evidence, and the three specified Lifecycle integration files.

The implemented remedy addresses that problem without changing generation, request identities, envelope format, consumer binding, dependency inventories, or routing ownership. The runtime remains standard-library-only. No dependency or infrastructure change is presented as a prerequisite.

The chosen Windows route has concrete feasibility evidence: handle-relative creation/opening, ancestor rename exclusion, and usable NTFS ACL inspection were probed on the actual Windows host. A Windows-specific backend is a localized remedy for capabilities that POSIX ownership/mode checks cannot establish.

NTFS-only storage is an implementation limitation, not an operator exemption from review. It is acceptable for this checkpoint because the evidence records actual persistence and fresh-process generation-forbidden reuse on NTFS, including ReFS source files routed to an NTFS home. Explicit unsupported storage still bypasses authoritatively. The requested outcome therefore does not demonstrably require ReFS storage support or host-policy changes.

Authorized implementation is confined to `yidl-cache` and the three named Lifecycle overlay paths. Astichi, YIDL, annotation work, other consumers, infrastructure, and GWZ remain reference-only. The inspected changes respect that boundary.

No blocking requirement-provenance or scope-authorization gap was found. Broader Windows qualification, ReFS storage, publication, performance qualification, and unrelated compiler/consumer shortcomings remain outside this deliverable.

## 1. Findings

### [P3-1] Concurrent-publication test requires two misses despite a permitted Windows sharing failure

**Location:** `tests/test_generated_code_cache.py:190–215`, especially the all-`CacheMiss` assertion at lines 207–209. Relevant backend behavior is `windows_storage.py:161–163`, `private_file()` at lines 243–259, and `WindowsStorage.write()` at lines 365–378.

**Violated invariant:** A concurrency test must accept the documented safe outcomes of the supported backend and must not depend on the scheduler avoiding a legitimate sharing conflict.

The patch enables this existing test on Windows by removing its POSIX-only skip. Its barrier synchronizes producer callbacks, but it does not ensure that one writer closes its published handle before the competing replacement occurs.

A concrete interleaving is:

1. Both requests finish their reads as misses and cross the producer barrier.
2. Writer A flushes its private temporary file and successfully renames it to the final artifact name.
3. Suspend A after rename succeeds but before `private_file()` closes the handle. That handle remains exclusive: the creation path requested sharing zero.
4. Writer B attempts to replace the same final name while A’s handle remains open.
5. Windows rejects the replacement. B cleans its temporary object and returns the documented typed storage bypass.
6. A closes its handle and returns a miss. A complete artifact remains available for the final fresh-reader assertion.

Microsoft’s [rename contract](https://learn.microsoft.com/en-us/windows-hardware/drivers/ddi/ntifs/ns-ntifs-_file_rename_information) establishes the conflict with an open destination; this implementation does not request POSIX replacement semantics. The policy explicitly permits transient sharing conflicts to cause fallback/bypass. Consequently, the product’s safe behavior can fail the new Windows test.

**Impact:** Scheduling-dependent Windows test failures can incorrectly signal corruption or a backend regression. The recorded passing run does not exercise or exclude this interleaving.

**Required correction:** Make the test’s Windows expectations reflect the contract: require valid generated code for both callers, at least one successful publication, only the documented typed bypass for a sharing-conflict loser, a subsequent generation-forbidden hit, and no abandoned temporary files. Preserve stronger POSIX assertions where appropriate. Do not weaken handle protections merely to satisfy the test.

**Closure/regression test:** On Windows, deterministically hold A after its successful underlying rename while B completes its replacement attempt, then release A. Assert the expected miss/bypass outcomes, bounded typed diagnostics, temporary cleanup, and a fresh-reader hit. This reproduction sequence is derived from inspected code and the API contract; it was not executed during this read-only review.

## 2. Invariant analysis

### Executable-artifact trust precedes decoding

Directory and entry trust checks occur before the Windows backend returns bytes to the shared decoder. File inspection rejects reparse/device objects, unexpected types, and multiple hard links. Reads check physical size before allocation/read and retain a handle that denies competing writes/deletes.

The shared decoder still checks envelope structure, identity, declared length, and integrity before unmarshalling. The Windows amendment does not introduce producer imports into that path or assume ownership of execution namespaces/current values.

Attempts to find a path from an untrusted directory/file grant to deserialization failed in the inspected flow. The fault suite includes unsafe directory and artifact ACLs with deserialization forbidden, physical oversize rejection, and invalid shared envelopes.

### ACL control and traversal remain bounded

The implementation distinguishes private leaf access from publicly traversable ancestors. It verifies trusted ownership and rejects untrusted effective leaf grants. Ancestors additionally reject untrusted security-descriptor control and unknown rights rather than assuming that held names alone prevent inherited ACL changes.

This matters because [Windows propagates inheritable ACE changes to existing descendants](https://learn.microsoft.com/en-us/windows/win32/secauthz/automatic-propagation-of-inheritable-aces). New objects receive protected descriptors, while existing objects are checked without repair.

Each subsequent path component is opened as one relative name from a held parent. Ancestor handles exclude delete sharing until the operation finishes. Admission does not confer permanent disk trust: read, write, and clear independently reopen and verify storage. The post-admission junction replacement and held-ancestor tests correspond to those boundaries.

The backend intentionally trusts the current user and system administrators. Same-user ACL mutation is therefore not an attack that this policy claims to exclude.

### Publication and crash states fail closed

The publication sequence is exclusive temporary creation, trust inspection, bounded write, flush, and same-directory handle-relative rename. Readers address only final artifact names.

The relevant interrupted states remain within a closed recovery grammar:

- Before temporary creation: prior artifact or absence.
- During writing or before successful rename: prior artifact/absence plus an ignored recognized temporary file.
- After rename: a complete published artifact, subject to ordinary filesystem crash durability.
- Failed publication/cleanup: typed failure; any remaining temporary/probe name is eligible for explicit maintenance.

The patch does not claim power-loss durability stronger than it establishes. Loss of a cache entry is permissible; loading an unchecked partial entry is not. A damaged/truncated envelope is rejected and regenerated.

Competing writers can produce redundant code or encounter a typed sharing conflict. Neither interleaving requires partial publication or unsafe reuse. The defect in P3-1 is the test’s stronger expectation, not evidence of an unsafe storage outcome.

### Routing, generation, and fences survive failures

Windows `OSError` failures are translated at the shared storage seam. The unchanged routing layer carries freshly generated code to another candidate, keeping generation outside fallback handlers. Producer exceptions remain distinct from storage failures.

The shared reentry and invalidation state spans all routes. Clearing drains memory/preferences/diagnostics while preserving producer fences and cumulative counters. Windows maintenance failures enter that existing typed path.

The original failing Lifecycle diagnostic assertion remains intact. The pinned fixture forbids warm generation and AST compilation and exercises current bindings and transactions. The evidence manifest records explicit Python and native-Rust selections, empty fallback metadata, and native-call evidence; these claims are materially stronger than hit counters alone.

### Maintenance stays confined

Maintenance uses held directory handles, bounded enumeration buffers, exact recognized-name patterns, and verified file handles. It does not recurse into neighboring directories. Unsafe recognized objects cause typed failure rather than target traversal.

Absent directories return without creation; denied access is not silently reclassified as absence. The Windows fault tests cover access denial, junctions, multi-buffer enumeration, long paths, unrelated names with unpaired UTF-16 units, and bounded probe cleanup.

No concrete escape, unrelated deletion, fence loss, or new unrecoverable maintenance state was established.

### POSIX behavior remains isolated

The Windows dispatch precedes the existing POSIX implementation; the shared codec is retained. Inspection found no altered POSIX storage algorithm. The manifest’s macOS and Linux suite outcomes support preservation, while Windows-specific mechanics are separately exercised. This is evidence for the bounded amendment, not a full release matrix.

## 3. Risks and next action

The review establishes no blocking State defect. P3-1 should be corrected with a deterministic Windows sharing-conflict regression so future verification does not depend on favorable scheduling.

Residual limits remain explicit: the new backend was exercised on Windows 11 AMD64 with CPython 3.13.5; other Windows versions/architectures and impersonation are not qualified. ReFS storage and unsupported ACL forms bypass. Power-loss behavior was analyzed from ordering rather than independently fault-injected. The recorded platform runs and native binary were not independently rerun or retrieved in this review.

The next action is to incorporate this State GO into the lane’s combined review decision, carrying P3-1 as a bounded nonblocking test correction. This verdict accepts only the exact reviewed amendment; it does not authorize release, publication, broader platform claims, or changes to reference-only components.