# Diagnose a cache lookup

A bypass normally preserves the producer's generated code. It means persistence
was not usable, not that class generation failed. Producer exceptions still
propagate. Begin with the [consumer example](../README.md#consumer-example),
then inspect the result and bounded diagnostics after its lookup:

```python
print(type(result).__name__)
print(cache.statistics)
for decision in cache.diagnostics:
    print(decision)
```

| Observation | Meaning and next step |
| --- | --- |
| `CacheMiss` on the first run | Expected for a new identity. A later process should hit if storage and dependencies remain compatible. |
| `CacheBypass` with location failures | Inspect the attempted path and typed reason. Confirm a canonical private directory on a supported filesystem. |
| Explicit root failed | Overrides are authoritative. Fix/select that root; an automatic home fallback is not chosen for you. |
| Path uses a symlink, including a temporary-directory alias | Descriptor-based traversal rejects symlink components. Supply the canonical intended path when that matches your trust policy. |
| Existing directory is not private or has unsupported ACLs | The cache does not repair it. Choose a new private directory you control; do not weaken the trust policy. |
| Warm-run assertion says the producer ran | Check bypass/invalidation reasons before interpreting this as corrupt code. The example intentionally forbids generation on that run. |
| Hit count increased after generation | A fallback hit can follow failed local publication. Inspect the diagnostic's `generated` flag. |
| `CacheMiss.rejected_entry` is present | An incompatible/damaged entry was rejected and regenerated. The rejection is retained for diagnosis. |
| Edits appear stale | Restart after generator changes. Timestamp/size-preserving edits can evade invalidation; explicitly clear or disable as needed. |
| `clear()` leaves files | It visits only tracked locations and recognized entries, preserving unrelated/untracked files. It is not a recursive root cleaner. |

On macOS/Linux, private leaves need the current owner and no group/other mode
bits; extended ACLs are conservatively rejected. Windows persistence requires
trusted fixed local NTFS and acceptable ownership/DACLs. Unsupported storage
bypasses; a consumer can offer a valid fallback candidate, but the shared package
neither discovers a home directory nor reads application environment controls.

`clear()` can report maintenance failures. Its bounded scope and diagnostics do
not establish complete deletion of every consumer cache. See the
[full policy](CachePolicy.md) for invalidation, trust, fallback and maintenance
rules. Cache checks do not sandbox code from a malicious same-user process.
