# Cache Policy

## Consumer Contract

The consumer supplies an explicit namespace, generator revision, normalized
SHA-256 input digest, `CompilationContext`, and `DependencyInventory`. Normalize
generation inputs by an explicit schema; do not hash arbitrary `repr`, addresses,
or serialize live classes/defaults/callbacks. Include every shape decision that
changes emitted code. Values proved to be runtime-only are bound by the consumer
after loading code, not by this package.

The producer returns a module `CodeType` compiled with the requested filename,
flags, `dont_inherit=True`, and optimization setting. It should keep heavy
generator imports inside the deferred callback. Exceptions raised by the producer
propagate unchanged. The cache does not execute code, own namespaces, retain
callbacks, or handle subsequent class construction errors.

The request identity also includes the cache format, interpreter implementation
and version, bytecode magic/cache tag, and effective compilation optimization.
Different namespaces cannot accidentally share entries.

## Dependency Invalidation

Capture a deterministic inventory of named files once, before importing/using
the generator. Include all source, template, and selected native dependencies
that can affect code. A producer adapter owns that inventory; the cache does not
discover YIDL or Lifecycle packages.

Warm lookups do not stat those dependencies. A miss checks the inventory once
before publication. An observed edit prevents publication and disables that
producer on this cache instance until restart. An instance also rejects changing
the captured identity of an already used producer. Consumers should keep one
cache and inventory alive for their process, not recreate them to evade this
policy. Clearing entries does not reactivate a disabled producer.

This is timestamp-and-size invalidation, not content identity. Edits preserving
both, including an edit/restore between observations, can produce a stale hit.
Restart after generator changes; explicitly clear or disable caching when needed.
There is no hot reload guarantee.

## Storage Trust

The shared cache is off unless `enabled=True`; it reads no consumer environment
variables. `GeneratedCodeCache(directory=None, enabled=False)` supports either
one constructor directory or per-request locations. With neither, it bypasses.
Passing `locations=()` explicitly also bypasses prior memory entries; it does not
fall back to the constructor directory.

`CacheLocationPolicy` computes neutral candidates from `SourceOrigin` metadata.
An explicit override root is authoritative. Without an override, a known absolute
source gets a module-local candidate under `__pycache__/yidl_cache`, followed by
the optional user root. Unknown origins use only the optional user root. Consumers
own source discovery, activation, and startup-anchored absolute roots; this package
does not discover user modules or choose a home directory.

Every namespace becomes `ns-<SHA-256 of exact namespace UTF-8 bytes>`. No case
folding or Unicode normalization is performed. User fallback mirrors an encoded
volume and source path, including the source filename, beneath `sources/`.
Components exceeding 180 encoded bytes or paths exceeding 1500 bytes use
`sources/by-digest/<source-path-digest>` instead. Unknown origins use
`modules/<module-name-digest>`. Artifact names remain complete identity digests
with the `.ycode` extension; these envelopes are not CPython `.pyc` files.

At most two candidates are permitted. Admission creates and removes an exclusive
private probe; `os.access` alone is not sufficient. Admission preferences and
failure snapshots are LRU-bounded to 32 routes. A usable fallback stays preferred
while its route is tracked, but actual reads/writes still recheck trust. The cache
never repairs an unsafe existing directory. No shared insecure fallback is used.

On macOS and Linux, the directory must be owned by the current user and have
no group/other permission bits. Newly created directories use mode `0700` and
entries use `0600`. Existing permissions are not silently repaired. Directory
components are walked through descriptors without following symlinks; parent
traversal is rejected. Entries must be owned private regular files, not symlinks
or hard links. Nonblocking opens prevent special files from hanging a lookup.

Extended ACLs are conservatively rejected, even when the mode bits look private.
macOS inspection uses its system ACL API via standard-library `ctypes`; Linux
inspection checks ACL attributes through descriptor-based extended-attribute
access. If inspection is unavailable, persistence bypasses.

Windows persistence supports fixed local NTFS volumes with persistent ACLs and
the required system APIs. It uses ordinary drive-letter paths, including long
paths. The held drive anchor must resolve to an actual volume root, verified by
its normalized volume-GUID path before admission, traversal, reading, or
maintenance. Directory-backed substituted drives and roots whose identity
cannot be established bypass; they cannot hide physical ancestry behind a drive
letter. Validation does not reopen a canonicalized pathname.

ReFS, FAT, network shares, removable drives, device/extended namespace
prefixes, alternate streams, parent traversal, and ambiguous trailing dots/spaces
bypass. A source file may live on an unsupported volume: automatic placement can
still use a trusted NTFS home fallback. An explicit unsupported root remains
authoritative and bypasses rather than silently selecting another root.

Cache directories and entries must have a trusted owner and a non-null DACL.
Effective allow entries may grant access only to the current token's user,
LocalSystem, or built-in Administrators. OWNER RIGHTS is accepted only after
verifying the owner. Both explicit and inherited ordinary allow/deny entries are
supported; an unsafe allow is rejected even if a deny appears to cancel it.
Unknown effective ACE forms bypass. Inherit-only entries are not effective on
the object being checked. Existing ACLs are never repaired. New directories,
probes, and temporary entries receive an explicit protected DACL granting full
access to the user, LocalSystem, and Administrators, without inheriting broader
access from their parent.

Every ancestor must also have a trusted owner and must not delegate DACL or
ownership control to an untrusted principal. Ancestors additionally recognize
the Windows Modules Installer (TrustedInstaller) service as a system principal;
this does not admit arbitrary service identities or relax leaf privacy. Public
data/traversal rights on ancestors are permitted. These checks prevent an
untrusted ancestor controller from propagating new inherited grants into an
existing cache object.

Traversal opens one component at a time relative to held directory handles,
without reparse processing. Ancestors remain open without delete sharing for
the whole operation. Reparse points, junctions, device objects, and unexpected
file types are rejected; entries must have exactly one hard link. Entry trust
and size are checked on the same handle used for reading, which denies write
and delete sharing until the bounded read finishes. These checks precede envelope
decoding and unmarshalling. Windows sharing violations are typed storage
failures and follow the normal fallback/bypass policy.

Windows publication exclusively creates a private same-directory temporary
entry, flushes its handle, and atomically renames that open object relative to
the held destination directory. Cleanup and maintenance delete verified objects
by handle. Maintenance enumerates only the selected directory and never follows
recognized reparse/hard-link entries or crawls neighboring directories; an unsafe
recognized object causes a typed maintenance failure. Unrelated names remain,
including names containing unpaired UTF-16 units.

Unknown platforms, filesystems, ACL forms, or unavailable trust APIs retain a
conservative typed bypass. The [Windows implementation evidence](../dev-docs/WindowsPersistence.md)
records the tested platform and remaining qualification limits. This Windows
amendment follows separate operator authorization; it does not reinterpret the
earlier macOS/Linux-only acceptance as Windows approval.

The threat model trusts the current user and the system administrator. These
checks do not protect against a malicious same-user process, a compromised
interpreter, or a file-system implementation that misreports its access controls.
Do not use this as a sandbox for untrusted executable artifacts.

## Artifact And Failure Policy

A versioned envelope contains exact request/compatibility metadata, payload
length, and a SHA-256 integrity digest. Headers and payloads have bounds; the
default payload limit is 16 MiB and the header limit is 16 KiB. Metadata, length,
and checksum checks precede unmarshalling. The decoded object must be module
code with the requested filename and only supported immutable code constants.
A checksum detects accidental corruption, not malicious replacement.

A writer uses a private exclusive same-directory temporary file and atomic
replacement. Readers do not read temporary files. Concurrent misses can generate
redundantly, but publish complete entries. Failed writes attempt one bounded
temporary-file cleanup; process crashes can leave temporary files for explicit
`clear()` maintenance. Cleanup failure is reported as a bypass, not retried forever.

Unavailable or untrusted storage preserves normal generation. Invalid entries
are regenerated, with the rejection retained on `CacheMiss.rejected_entry`.
Admission, directory-access, or publication failures try the next candidate,
carrying any freshly generated code so the producer is called at most once.
Producer exceptions propagate unchanged and never trigger fallback, including
producer-raised `CacheStorageError`. Artifact rejection regenerates at the same
trusted location, while dependency invalidation bypasses without switching roots.
If every candidate fails, `CacheBypass` contains the fresh code and a
`CacheLocationError` with frozen per-location reasons. No messages are logged.

One final hit, miss, or bypass is counted per completed request. A hit found after
local publication failure may have performed generation already; counters alone
do not prove generation was avoided. `cache.diagnostics` returns the last 32
immutable `CacheDiagnostic` snapshots, oldest first, including repeated requests.
Each records selected/attempted locations, outcome type, generation flag, and
typed failure/rejection summaries. Messages are bounded to 1024 characters;
exception objects, tracebacks, producer closures, and code are not retained there.

The in-process code cache is LRU-bounded (32 entries by default; zero disables
it). Routing uses one code LRU and one invalidation/reentry fence across all
locations. No directory scan occurs on a lookup. Explicit `clear()` visits only
the constructor directory and candidates in the currently tracked 32 routes. It
removes recognized artifact/temporary/probe names, clears memory/preferences/
diagnostic history even if maintenance fails, and preserves producer fences.
Unrelated files and evicted/untracked directories remain. A clear failure retains
frozen location reasons; it does not silently broaden maintenance to a root crawl.
Callbacks run outside cache locks; same-key reentry bypasses caching, while
different-key recursion and concurrent misses are allowed.
