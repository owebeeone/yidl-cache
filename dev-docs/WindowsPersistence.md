# Windows Persistence Amendment — 2026-10-23

## Authority and boundary

After the diagnosis below, the operator explicitly directed closing the
implementation gap: “we'd better fix that implementation gap”. This separately
authorizes Windows storage/trust implementation, necessary cache tests and
current policy updates, and cache-only Lifecycle integration tests/docs. It does
not reinterpret the earlier location specification or review tuple as already
accepting Windows persistence.

The patch changes this package's storage boundary and its tests/documentation.
Lifecycle changes are confined to `tests/test_lifecycle_code_cache.py`,
`tests/test_cache_location_failures.py`, and `dev-docs/LifecycleCodeCache.md` in
that repository. YIDL, Astichi/native engines, Lifecycle annotation work, other
consumers, dependencies, infrastructure, and GWZ metadata remain reference-only.
No commits, installs into the original host environments, publication, or remote
source-tree changes were performed for this fix. Disposable source copies and
cache/ACL fault artifacts were used for verification.

This is an uncommitted implementation draft, not independent review acceptance
or release qualification. [The evidence manifest](WindowsPersistenceEvidence.json)
pins the runtime/test bytes and reference revisions used below.

## Historical failure and RED

The original candidate was cache `a4ae595e0f9835a86dadec3bedebd383ebf9ae2f`
and Lifecycle `ee5ba633efdeac9fbdd74cfe67ecd975eab8a26d`. All seven installed
cache Python files, the Lifecycle adapter, and the failing test were compared
with the corresponding Git objects and matched byte-for-byte on Windows.

The public diagnostic test expected a home-route `CacheHit` after failed local
publication. Both routes actually failed earlier, at admission, with
`CacheStorageError("private-directory trust is not implemented on this platform")`.
The final outcome was correctly `CacheBypass`, `generated=True`, no selected
location, two attempted/failed routes, and
`CacheLocationError("no usable cache location")`. The old policy explicitly
required that safe bypass. Code generation and Lifecycle transactions still
worked under both engines; persistence was the missing capability.

The first implementation RED removed the POSIX-only guard from the existing
canonical independent-record fixture, without weakening its assertions. On the
actual Windows host it failed: the cold request returned `CacheBypass` instead
of `CacheMiss`. The fixture's next process forbids generation and requires a
disk `CacheHit`, so an in-memory hit cannot satisfy it.

Windows fault tests were added before the storage implementation. Subsequent
focused RED checks exposed cleanup after failed new-file trust inspection and
unpaired-UTF-16 enumeration; both were corrected and retained as regressions.
The existing Lifecycle failed-publication/fallback diagnostic assertion remains
unchanged and passes with the new storage path.

## Feasibility and component boundary

A disposable actual-Windows ctypes probe confirmed all of the following before
selecting the implementation:

- The system temporary volume is NTFS and reports persistent ACL enforcement.
- Its ordinary private temporary-directory ACL grants SYSTEM, Administrators,
  and OWNER RIGHTS. Windows ACLs cannot be treated as POSIX mode bits or banned
  wholesale.
- `NtCreateFile` can create/open a single child name relative to a held parent
  directory handle, without reparse processing.
- Omitting delete sharing from those directory handles blocks ancestor rename
  with Windows sharing error 32.

`windows_api.py` owns ctypes ABI declarations, token identity, and protected
security-descriptor creation. `windows_storage.py` owns Windows trust checks,
handle traversal, bounded I/O, publication, and maintenance. `storage.py` selects
that backend on Windows while retaining the existing shared envelope codec and
all POSIX operations. Runtime dependencies remain standard-library-only.
Request identities, envelope bytes, consumer ownership, and generation routing
were not redesigned.

The standard system-drive root is owned by Windows Modules Installer on this
host. Read-only service inspection verified its fixed service SID and LocalSystem
account. That principal is accepted for ancestor control only. Leaf cache access
remains restricted to the user, LocalSystem, and Administrators.

## Implemented invariants

| Boundary | Windows enforcement |
| --- | --- |
| Supported storage | Fixed local NTFS volume, persistent-ACL flag, required system APIs; other capabilities fail closed |
| Private access | Handle-based owner/DACL inspection; only trusted effective grants; OWNER RIGHTS resolves to an already verified owner |
| Inheritance | Ordinary inherited ACLs are accepted when private; new objects get a protected explicit DACL; no existing ACL repair |
| Ancestor control | Trusted owner and no untrusted DACL/owner-control or unknown-rights grants; prevents unsafe inherited-ACL propagation |
| Traversal | One non-reparsing component per parent-relative open; every ancestor handle remains open without delete sharing |
| Entries | Disk regular file, no reparse/device attribute, exactly one hard link; inspection and I/O use the same handle |
| Read | Denies write/delete sharing, checks physical size before a bounded read, then uses the existing checked decoder |
| Publication | Exclusive private same-directory temporary object, flush, atomic handle-relative rename, bounded cleanup |
| Maintenance | Handle-relative enumeration/deletion of recognized private objects in tracked directories only; unrelated names/directories preserved |
| Failure | Typed storage/artifact errors retain normal generation, fallback, producer-at-most-once behavior, and bounded diagnostics |

Unsafe effective allow entries are rejected even if a deny seems to cancel
them. Unsupported effective ACE types and null DACLs bypass. Ancestors can be
publicly traversable/readable, but cannot delegate security-descriptor control to
untrusted principals. Reads/writes recheck actual storage trust even after a
route has been admitted. Existing process-memory hit semantics are unchanged.

The implementation uses the documented
[user-mode NtCreateFile contract](https://learn.microsoft.com/en-us/windows/win32/api/winternl/nf-winternl-ntcreatefile),
[handle security inspection](https://learn.microsoft.com/en-us/windows/win32/api/aclapi/nf-aclapi-getsecurityinfo),
[handle-relative rename information](https://learn.microsoft.com/en-us/windows-hardware/drivers/ddi/ntifs/ns-ntifs-_file_rename_information),
and [directory-handle enumeration](https://learn.microsoft.com/en-us/windows/win32/api/winbase/nf-winbase-getfileinformationbyhandleex).
The ancestor check accounts for Windows'
[propagation of inheritable ACEs](https://learn.microsoft.com/en-us/windows/win32/secauthz/automatic-propagation-of-inheritable-aces).

## Fixed-candidate verification

The Windows candidate was an isolated source copy imported through an explicit
`PYTHONPATH`, using the existing interpreter and reference dependencies. The
original installed cache and source trees were not replaced. Lifecycle runtime
and fixtures were reconstructed from its pinned original commit, with only the
two cache-test files overlaid; the concurrent annotation fix was excluded.
Mac Lifecycle verification used the same pinned copy. Linux cache verification
used a disposable source copy and the existing interpreter, without installing
or changing anything in the ongoing platform task's environment.

While this work was running, the separate annotation task was committed at
Lifecycle `77b0dd574404e314fecc46069a54f8fcedb9555d`. A second isolated copy of
that reference commit, with the same two cache-test overlays, also passed the
same focused scope: Windows 45 passed/2 skipped on each engine, and Mac 47 passed
on each engine. This is a separately identified compatibility check; it does not
replace the original-candidate diagnosis or attribute that task's changes to
this cache patch. YIDL's local HEAD advanced through documentation/evidence
commits; its `src` bytes still match the original YIDL candidate.

| Check | Actual result |
| --- | --- |
| Windows 11 build 26200, AMD64, CPython 3.13.5: complete cache suite | 64 passed, 17 skipped |
| Windows Lifecycle cache/configuration/fault suite, explicit Python | 45 passed, 2 skipped |
| Windows same Lifecycle scope, explicit native Rust | 45 passed, 2 skipped |
| macOS arm64, CPython 3.14.3: complete cache suite | 57 passed, 24 skipped |
| macOS arm64, CPython 3.12.12: pinned Lifecycle focused scope, Python | 47 passed |
| macOS same Lifecycle scope, native Rust | 47 passed |
| Linux aarch64, CPython 3.13.5: complete cache suite | 55 passed, 26 skipped |

Skips cover the other operating system's mechanics, Linux/macOS-specific ACL
checks, and POSIX descriptor/chmod fault injection. Neither Windows persistence
nor the original failing diagnostic is skipped. Windows counterparts exercise
real ACLs, junctions, denied access, and handle operations. The two remaining
Windows Lifecycle skips are chmod-only inaccessible-ancestor and macOS ACL tests.

The canonical Lifecycle fixture passes cold/warm through explicit, source-local,
and home placements. Each cold process generates twice and reports two misses;
each fresh warm process forbids generation/AST compilation, has two hits and zero
generation, binds the new runtime value, and exercises transactions and bindings.
Mirrored home paths reached 395 characters; storage succeeded using relative
handles, and the test inspects them using the extended-path filesystem spelling.

An additional isolated proof copied the canonical source onto the host's ReFS
workspace volume and supplied a temporary NTFS user home. On **both** explicit
engines, local ReFS storage failed with a retained typed reason, the selected
route was `MirroredSourceLocation`, and the fresh warm process still hit twice
without generation. Each engine used fresh storage, so one engine's artifacts
could not mask the other's generation path.

Requested and selected cold engines matched with no fallback. Native profiling
recorded 95 `lower_template_package_v2_from_registered_template` calls, 95
`compile_validate_source` calls, and two
`assembly_state_materialize_to_python_ast` calls in that proof. The Windows
native binary SHA-256 was
`db81f125ed30c3b39eea2160c2f296493b2aee59ff712f187e9aa540d3572da6`.
Warm processes imported none of Astichi, the generated Lifecycle producer, or
`yidl.generation.data_def_sys`; they performed no native compilation calls.

Fault coverage includes real unsafe read grants, unsafe ancestor ACL control,
read-denied directories, permission rechecking after admission, actual home
fallback without repair, replaced directory/junction paths, a reparse entry,
hard links, malformed/incompatible/oversized artifacts before deserialization,
concurrent publication, failed rename/probe/trust-inspection cleanup, unavailable
APIs/unknown-filesystem reports, 600-entry multi-buffer maintenance, long paths,
non-BMP components, and unrelated names containing unpaired UTF-16 units.
The unknown-filesystem/API cases are fault injection, not claims of production
support for those configurations; actual ReFS bypass was checked separately.

Black, whitespace/diff checks, and AST parsing of every package module and test
cover the disabled Windows branch on the Mac as well. Mypy was not available in
the existing workspace environment; no new dependency was installed for it.

## Reproduction and limits

From the cache repository, with a supported interpreter and pytest available:

```sh
PYTHONDONTWRITEBYTECODE=1 PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python -m pytest -q -p no:cacheprovider
```

On Windows use PowerShell environment assignments, then the same Python/pytest
arguments. Run the three cache-only Lifecycle files from its repository with
`ASTICHI_LOWER_ENGINE=python`, then a fresh process with `native-rust`:
`tests/test_lifecycle_code_cache.py`, `tests/test_cache_configuration.py`, and
`tests/test_cache_location_failures.py`. The canonical fixture controls isolated
homes on both POSIX and Windows and forbids generation in its warm child process.

ReFS storage support is a separate optional qualification/implementation project.
It does not block persistence for sources there when the NTFS home fallback is
available. An explicit ReFS override deliberately bypasses, as do unknown
filesystems, UNC/device namespace roots, removable drives, unsupported ACE forms,
untrusted owners/security controllers, or unsafe entries. These are limitations,
not repaired host settings. No filesystem policy, registry, or global ACL was
changed.

Windows sharing conflicts may cause transient fallback/bypass; the implementation
does not retry indefinitely or relax handle protections. On this host ordinary
Python path enumeration/temporary-directory cleanup can miss long paths without
the extended spelling; cache maintenance itself handles them and remains
confined. This task did not change Python or host long-path policy.

Only Windows 11 AMD64/CPython 3.13.5 was exercised for the new backend. Other
Windows versions/architectures, impersonated tokens, and unsupported ACL forms
are not newly qualified. Full compiler/consumer matrices, performance benchmarks,
wheel publication, settled-tree acceptance, and independent security/code review
remain separate. The known unrelated Python-engine owned-field golden mismatch
and concurrent annotation work were not changed or represented as cache fixes.
