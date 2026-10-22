# Windows Persistence — CODE-AXIS REVIEW

**Review object:** Windows persistent compiled-code cache amendment at yidl-cache `6d91a0cec59bb926e4ffb627847a6e1562b0dc9e`, including controlling `dev-docs/WindowsPersistence.md`; Lifecycle cache-only overlay at `e979f2412b809e2a8a60eefb942790cef1e715ff`. Committed review checkpoint; implementation documents retain their precommit draft wording.

**Baseline:** yidl-cache `a4ae595e0f9835a86dadec3bedebd383ebf9ae2f`; yidl-lifecycle `77b0dd574404e314fecc46069a54f8fcedb9555d`. Pinned content was inspected with `git show`, alongside complete file reads and baseline-to-object diffs. Reference source objects: Astichi `ce47c629973d8e5a6340ceaa89b0bc3e8788d5fe`; YIDL `ee5ded0854aa5b1fc0ddfa7213b765009b63bb95`.

**Date:** 2026-10-23

**Axis:** Code — architecture, interfaces, call graphs, compatibility, ABI, resource lifetime, and required Surface analysis. Independent, adversarial, read-only. The other axis runs in parallel; nothing here relies on it. Filed verbatim by the lane owner.

**Verdict: NO-GO** — one P2 finding blocks acceptance. I pre-commit to GO on a revision that resolves P2-1 as specified.

---

## 0. Evidence base

The deliverable of this review is this report. No implementation, test, dependency, infrastructure, or repository mutation was authorized or performed.

The exact cache and Lifecycle heads matched the review tuple at both start and end. Lifecycle remained clean. Cache working-tree additions were confined to the lane owner's permitted review/prompt/checkpoint documents; none was treated as reviewed runtime content. The peer's current-round prompt and report were not read.

The inspected diff contains fourteen cache paths and exactly these three Lifecycle overlay paths:

- `dev-docs/LifecycleCodeCache.md`
- `tests/test_cache_location_failures.py`
- `tests/test_lifecycle_code_cache.py`

Before code or design inspection, I read `README.md`, `docs/CachePolicy.md`, and Lifecycle's `dev-docs/LifecycleCodeCache.md` cold, as required for Surface duty.

The evidence inspected included:

- All of `src/yidl_cache/windows_api.py` (335 lines), `windows_storage.py` (402 lines), and `storage.py` (358 lines).
- Complete cache routing, model, location, diagnostic, trust, and public-export modules.
- All five changed cache test files, their shared fixture/configuration, and the canonical independent-record producer.
- Both changed Lifecycle test files, the unchanged configuration tests, canonical Lifecycle process fixture, consumer adapter and startup configuration modules, and relevant decoration/generation/execution call sites.
- The complete Windows amendment and evidence manifest; location policy plan/checkpoint; historical shared-cache checkpoint; README and development index.
- Pinned YIDL generation-facade source and Astichi source context, without substituting moving dependency heads for the named reference objects.

A read-only Python invocation parsed the eighteen manifest-listed package/test/overlay Python files in memory and checked their committed bytes against the manifest. All eighteen digests matched; parsing succeeded. It imported no reviewed product code and wrote nothing.

Official Microsoft contracts were consulted for drive-letter mappings, final handle paths, NT relative opens, security inspection, inherited-ACE propagation, rename information, and directory enumeration. Relevant sources are linked at the findings and invariant analysis below.

No product execution, test run, build, remote-host access, ACL mutation, cache mutation, or report-file write was performed. Platform test counts and engine traces below are reported implementation evidence, independently checked for correspondence to committed source and manifest bytes, not independently rerun results.

## Problem, requirement provenance, and scope

The original observed failure was a diagnostic expecting a persistent home-route hit on Windows while the implementation deliberately rejected non-POSIX storage trust. Generation and transactions continued to work; persistence did not.

The operator's direction to fix that implementation gap authorizes a Windows storage/trust backend and necessary cache tests/policy/evidence, plus the three bounded Lifecycle overlay files. It does not authorize weakening the diagnostic, removing persistence requirements, changing compiler engines, or redesigning generation and runtime binding.

The remedy is localized appropriately:

- Windows ABI and security-descriptor operations reside in `windows_api.py`.
- Windows traversal, trust, publication, reading, and maintenance reside in `windows_storage.py`.
- `storage.py` dispatches lazily and retains the common artifact codec.
- Existing consumer routing and generation/binding ownership remain intact.

No new dependency or infrastructure prerequisite was introduced. The amendment reports an actual Windows feasibility probe for the stdlib `ctypes` route before implementation. Source inspection confirms that this route uses standard-library facilities and existing Windows APIs. No demonstrated necessity for broader component changes emerged.

YIDL, Astichi/native engines, generic Lifecycle generation and annotation implementations, Undoable, Pyrolyze, GWZ, and other consumers remain reference-only. The committed overlay respects that boundary.

The reported ReFS-source-to-NTFS-home proof addresses the practical source-volume case without requiring new ReFS storage support. NTFS-only storage is a bounded capability choice, subject to safe rejection of capabilities whose trust has not been established. P2-1 concerns such a missing rejection; it does not demand support for another filesystem or new infrastructure.

## 1. Findings

### [P2-1] A substituted drive root skips physical ancestors required by the trust policy

**Location:** `src/yidl_cache/windows_storage.py:187–226`, particularly the drive-root open at lines 199–213 and traversal beginning at `directory.parts[1:]`.

**Violated invariant:** Every physical ancestor must have trusted ownership and must not delegate DACL or ownership control to an untrusted principal. Unknown path/trust capabilities must bypass before persisted executable content is decoded.

`directory_handle()` assumes that a syntactically ordinary drive-letter anchor is the filesystem's actual root. It checks the drive type, opens that anchor, checks the resulting directory and volume, and traverses only the remaining lexical components.

Windows drive letters can instead name directories. Microsoft documents that `subst` associates a path with a drive letter, while DOS-device mappings resolve drive letters through object-namespace junctions. A substituted drive backed by a fixed NTFS directory still satisfies the present drive-type and filesystem checks. Its underlying target directory need not have a filesystem reparse attribute. Consequently, `information(root)` does not establish that the opened directory is a volume root. See Microsoft's [subst contract](https://learn.microsoft.com/en-nz/windows-server/administration/windows-commands/subst) and [QueryDosDevice contract](https://learn.microsoft.com/en-us/windows/win32/api/fileapi/nf-fileapi-querydosdevicew).

**Credible reproduction/state sequence, source-traced rather than executed:**

1. On fixed local NTFS, arrange a trusted-user-owned ancestor that grants an untrusted SID non-inheritable `WRITE_DAC`.
2. Beneath it, arrange otherwise private, trusted-user-owned directories and an existing private artifact with ordinary inheritance enabled. Those effective leaf ACLs are accepted by this implementation and its documented contract.
3. Map an unused drive letter to a descendant below the unsafe ancestor.
4. Access the cache through the ordinary physical spelling: traversal encounters the unsafe ancestor and bypasses.
5. Access the same cache through the substituted drive spelling: traversal starts below that ancestor, so the unsafe controller is never inspected. A valid existing artifact can reach the shared decoder.

This distinction follows directly from which objects the traversal opens and checks; the implementation contains no substituted-root detection or physical-root verification.

**Impact:** The same storage can receive opposite trust decisions solely because a drive-letter alias hides part of its ancestry. A controller of an omitted ancestor can propagate inheritable permissions into existing inheritance-enabled descendants. Microsoft documents both propagation into existing children and removal of inherited copies when a parent ACE is removed. Thus private effective ACLs observed later do not establish the required ancestry guarantee. Newly created protected objects do not remedy the separately supported case of existing, unprotected private objects. See [automatic propagation of inheritable ACEs](https://learn.microsoft.com/en-us/windows/win32/secauthz/automatic-propagation-of-inheritable-aces).

This is a trust-boundary correctness defect for persisted executable artifacts, not a request to qualify substituted drives.

**Required correction:** Establish that the initially opened anchor is an actual supported volume root before admitting the route. Conservatively reject directory-backed/substituted drive roots when that cannot be established. Alternatively, perform the complete physical ancestor walk with equivalent non-reparse and held-handle guarantees. A pathname-only canonicalization followed by unprotected reopening is insufficient. Document any resulting unsupported-root restriction. Microsoft's [final-path-by-handle API](https://learn.microsoft.com/en-us/windows/win32/api/fileapi/nf-fileapi-getfinalpathnamebyhandlew) describes a relevant handle-based distinction; this finding does not mandate a particular API.

**Closure/regression test:** Add an isolated actual-Windows substituted-drive test using the safe ancestry arrangement above. Assert typed bypass before deserialization for an authoritative override, or demonstrate equivalent complete physical-ancestry enforcement. Include automatic fallback to a separate trusted ordinary NTFS root, producer-at-most-once behavior, and bounded cleanup of the temporary drive mapping. Preserve ordinary-drive cold/warm reuse and existing junction/ancestor-ACL tests.

## 2. Invariant analysis

**Lazy isolation and dependency boundary hold.** POSIX execution does not import the Windows backend at runtime. `_windows()` converts unavailable imports/APIs into typed storage failure. Package runtime imports remain standard-library-only; no producer/compiler dependency was introduced into cache-hit paths.

**The artifact compatibility seam is preserved.** Request identity and envelope construction/decoding remain shared. Windows supplies bytes to the same bounded header, compatibility, length, checksum, module-code, filename, and constant checks. The patch does not create an alternate reader or silently change retained codec semantics.

**The ordinary relative-handle design is coherent.** After the initial anchor, child names are single components, separator/stream/traversal forms are rejected, objects are opened without normal reparse processing, and all traversed ancestor handles remain alive through the operation. Entries are checked on the handle used for reading. The protection therefore holds for the ancestry actually traversed; P2-1 identifies the missing initial-root premise. The signatures and use agree with Microsoft's [NtCreateFile contract](https://learn.microsoft.com/en-us/windows/win32/api/winternl/nf-winternl-ntcreatefile).

**ABI and resource ownership attacks found no additional defect.** The inspected declarations use pointer-sized handles and pointer fields, byte-counted UTF-16 names, signed NT status values, and the selected information-class layouts consistently. Token handles, security descriptors, SID strings, file handles, and ancestor handles have corresponding cleanup paths. The rename buffer's relative destination and delete access are consistent with the [FILE_RENAME_INFORMATION contract](https://learn.microsoft.com/en-us/windows-hardware/drivers/ddi/ntifs/ns-ntifs-_file_rename_information). This is source-level assessment, not independent qualification of another Windows ABI.

**Object trust checks otherwise fail conservatively.** Unknown effective ACE kinds, null DACLs, unsafe allow grants, untrusted owners, reparse/device objects, wrong object types, and entry hard links are rejected. Deny entries do not justify unsafe allow entries. Handle security buffers are freed in accordance with [GetSecurityInfo](https://learn.microsoft.com/en-us/windows/win32/api/aclapi/nf-aclapi-getsecurityinfo).

**Publication and maintenance remain bounded.** Temporary files are exclusively created with protected security, flushed, renamed by handle, and cleaned on failed publication. Failed new-file trust inspection attempts deletion before close. Maintenance uses handle enumeration, recognizes bounded name patterns, and leaves unrelated names/directories alone. The enumeration information classes correspond to the documented [GetFileInformationByHandleEx classes](https://learn.microsoft.com/en-us/windows/win32/api/winbase/nf-winbase-getfileinformationbyhandleex).

**Routing and consumer ownership are unchanged.** Storage failures follow the existing fallback path; generated code is carried across publication failure; producer exceptions remain outside storage handlers. One logical outcome is counted. Consumer execution still creates a fresh namespace and binds current harvested values. The canonical warm fixture forbids generation, AST compilation, and dependency rechecking, and checks producer-import absence.

**Reported platform evidence matches the intended proof shape.** The manifest reports Windows cache and focused Lifecycle results on both explicit engines, plus Mac/Linux preservation. Cold engine selections record the requested engine without fallback; native cold traces contain compilation/materialization calls, while warm traces contain no producer imports or native calls. Source inspection confirms that fresh child processes and generation-forbidden assertions prevent an in-process hit from satisfying those canonical proofs. This does not independently authenticate the raw logs, which are represented by hashes rather than included in the committed review object.

## Surface analysis

This package adds no CLI or command family; no CLI placement requirement applies. The review therefore used the documented Python API, Lifecycle settings, examples, diagnostics, and maintenance controls.

The cold walkthrough was understandable:

1. **First use:** install the package into the consumer environment; shared caching requires `enabled=True`, whereas Lifecycle explicitly documents default-on activation.
2. **Configure:** Lifecycle documents startup capture, relative-root anchoring, literal directory whitespace, current-user home expansion, and invalid-setting behavior.
3. **Fallback:** automatic source-local then home placement is explained, including unsupported ReFS source storage with a possible NTFS home route.
4. **Override:** an explicit root is authoritative and does not silently fall back.
5. **Disable:** `off` wins over a directory override and suppresses inventory/cache creation.
6. **Inspect:** counters and bounded diagnostics distinguish an artifact hit from actual generation avoidance.
7. **Undo/maintain:** clearing and disabling are documented together; disabled maintenance is explicitly inert, and an enabled explicit-root maintenance process is shown. Automatic maintenance honestly covers tracked routes rather than promising a global crawl.

The API/policy state defaults for enablement, memory capacity, artifact bounds, placement, and diagnostic retention. Maintenance scope and cumulative statistics are explained. No new Surface compatibility defect was established independently of P2-1's unsupported-root gap.

These were source-traced walkthroughs, not executed examples. Precommit “uncommitted draft” phrases are stale checkpoint wording, but they do not obscure activation controls or falsely claim release acceptance in this bounded review.

## 3. Risks and next action

The new backend's independently inspected scope is narrower than full platform qualification. Existing Windows execution evidence covers Windows 11 AMD64 with CPython 3.13.5; other versions/architectures, impersonation, and unsupported ACL/filesystem capabilities remain unqualified. Performance, deployment, publication, and the full compiler/consumer matrix remain outside this checkpoint.

The next action is bounded remediation of P2-1 in the cache backend, accompanying Windows regression evidence, and any necessary policy/evidence update, followed by verification of that correction. No compiler, engine, annotation, dependency, or infrastructure change is required by this finding.

**Review complete; not blocked. The pinned tuple did not move.**