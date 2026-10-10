# Cache Location Policy: Safety Review

Date: 2026-10-10  
Axis: Safety  
Object: R1 DRAFT specification, not implementation acceptance.

## Evidence base

Inspection was confined to `grip-pyrolyze-wz-codecache-fixed`. Read the workspace `AGENTS.md`, `AGENTS_GWZ.md`, and owning `yidl-cache/AGENTS.md`. No current-round peer report was read or requested. No files, Git state, or agents were created or modified; no tests or builds ran.

All twelve SHA-256 pins matched at the start and end. The review tuple did not move.

Paths below are relative to the named repository:

| Repository | Path | SHA-256 |
| --- | --- | --- |
| yidl-cache | `dev-docs/CacheLocationPolicyPlan.md` | `44017c42524bc73c2ca49262a29b444b450b5f5a576a60506db541d910043ac1` |
| yidl-cache | `docs/CachePolicy.md` | `7c3f87e5b488e1887ded7ef65d81b6e19f0bd1801dee7e6f14d3c3a292083f31` |
| yidl-cache | `src/yidl_cache/cache.py` | `da095ec52ba69abf8a9a4612a3cda7c06065c34a88dc06910a86a3bc5e4ff4db` |
| yidl-cache | `src/yidl_cache/model.py` | `64e9d8a247c683288ca3d4af432eafaf98a9905b5447e119f4512362ab719f68` |
| yidl-cache | `src/yidl_cache/storage.py` | `dd150a61475954780e6d2dcc3a086b0a90af2146de2f0b0d1cd60496885e92d0` |
| yidl-cache | `src/yidl_cache/trust.py` | `d8d46e6a041fdd761a459f3fb3b5e77f834baff652b485f3c246af789f5a8686` |
| yidl-lifecycle | `src/yidl_lifecycle/lifecycle.py` | `c6a79db6378e70a1622587dfdfdb71acd63707a3a3c00e0767f5547e42f17484` |
| yidl-lifecycle | `src/yidl_lifecycle/lifecycle_code_cache.py` | `4940d82c807bbd2d1f62a7ad58998ab59651858626cdf487f13746c7317b7dc0` |
| yidl-lifecycle | `src/yidl_lifecycle/lifecycle_cache_inputs.py` | `f3e1e7a9c2a03eca3fd0a931df63c8dc3fa40225c90b7cc825e5c8c908d0391c` |
| yidl-lifecycle | `dev-docs/LifecycleCodeCache.md` | `de88e9f4c9f4b5ee770a44f227edb2b5894cfc33e96a6d655e4cb92deacc3cac` |
| yidl-lifecycle | `dev-docs/LifecycleCodeCacheStartup.md` | `3c35260e1b7cffdf0e3770e4b9af1d324393c44847f083e1c859a8741368a6a2` |
| yidl | `dev-docs/YidlGeneratedCodeCachePlan.md` | `d770295bf4d30c5d80de3f93c417664705d5471267b00c9196eba992ec4a2a37` |

Process deviation: the operator explicitly authorized content-hash-pinned, uncommitted draft review instead of the review-loop skill's committed-object requirement. The draft records this at `dev-docs/CacheLocationPolicyPlan.md:262`. This report does not grant implementation acceptance, an interface freeze, publication, or verified activation.

Existing uncommitted runtime sources were context only, not a diff under review. Findings below concern the specified design; reproductions are design-derived sequences, not executed tests.

## Findings (P0-P3)

No P0 or P1 findings.

### P2-1: Namespace directories alias on case-insensitive filesystems

**Location:** `dev-docs/CacheLocationPolicyPlan.md:113` specifies percent encoding that leaves ASCII letters unchanged; clearing is scoped by namespace directory at line 219 and promises not to clear another consumer at line 223.

**Root cause and invariant:** The namespace encoding is not injective under filesystem name comparison. Directory separation therefore cannot enforce the promised cross-consumer clearing isolation.

**Reproduction:**
1. On a case-insensitive macOS filesystem, two consumers use the same explicit root with namespaces `Alpha` and `alpha`.
2. Both names satisfy the existing request contract and remain unchanged by the specified encoding.
3. Both routes consequently use the same physical namespace directory. Their request digests differ, so their artifacts coexist.
4. Consumer `Alpha` clears its namespace directory. Recognized-name deletion also removes consumer `alpha`'s artifacts.

**Impact:** Recoverable cross-consumer cache deletion and forced regeneration. Full request identities prevent accidental code reuse, but do not protect directory-wide maintenance.

**Required correction:** Specify namespace layout that remains distinct under supported filesystem equivalence, for example a fixed lowercase digest of the exact namespace bytes for every namespace. Short-name and oversized-name layouts must also occupy disjoint naming domains.

**Closure test:** In an isolated case-insensitive filesystem, publish entries for `Alpha` and `alpha` under one root, clear each independently, and verify the other's artifacts and subsequent disk hits survive. Also cover an oversized namespace against a short namespace resembling its hashed component.

### P2-2: Retained request failures have no specified consumer-facing retrieval interface

**Location:** `dev-docs/CacheLocationPolicyPlan.md:71` exposes configuration problems and counters; line 192 requires retained candidate failures, line 196 requires both failure reasons, and line 215 introduces bounded diagnostic history without specifying its retrieval surface.

**Root cause and invariant:** The specification defines diagnostic retention but omits the public interface for observing it. Counters and a configuration snapshot cannot convey request-specific typed failures or selected-layout evidence.

**Reproduction:**
1. Configuration is valid and the local candidate is admitted.
2. Generation succeeds, but local publication fails; fallback finds a compatible home artifact.
3. The specified final outcome is one hit. The configuration snapshot remains problem-free.
4. The preserved `CacheHit` carrier contains only code, and Lifecycle's pinned `compiled_lifecycle_code` extracts `.code` (`src/yidl_lifecycle/lifecycle_code_cache.py:131`).
5. Implementing only the named public surfaces leaves the operator unable to retrieve the local failure or distinguish this generated fallback hit from a generation-free hit. Exhausted-storage reasons likewise disappear at the Lifecycle boundary.

**Impact:** The promised typed diagnostics are inaccessible through the specified consumer controls. Operators cannot diagnose failed publication, abandoned probes, or why automatic placement changed without inspecting private state.

**Required correction:** Specify a named public, frozen request-diagnostic snapshot/accessor, including its return shape and history lifecycle. It must expose selected layout, attempted-candidate failures, final outcome, and whether generation occurred. Preserve the 32-entry bound and avoid retaining exceptions with traceback frames or live runtime objects.

**Closure test:** Through public Lifecycle APIs only, inspect local-publication-failure/home-hit and both-candidates-fail cases. Assert typed reasons, accurate generation evidence, one logical counter outcome, bounded history, and no automatic logging.

## Invariant analysis

- **Executable trust:** Lines 149 and 163 require ownership, private permissions, ACL checks, no-follow traversal, and renewed trust enforcement per operation. Admission is explicitly not a permanent certificate. No additional unsafe-deserialization permission was established.
- **Fallback and producer execution:** Lines 174 and 182 restrict fallback causes and require carrying already-produced code. Both-location failure cannot justify a second producer invocation; producer exceptions must propagate unchanged.
- **Invalidation and reentry:** Lines 211 and 220 require shared fences across routes, preserve invalidation through clearing, and prohibit per-location cache instances. Location eviction cannot reactivate a disabled producer.
- **Origin and bounds:** Origin is placement metadata, not executable provenance. Component encoding, anchor removal, long-origin hashing, and separate bounded LRUs address traversal and accumulation. Namespace equivalence remains defective as P2-1.
- **Controls:** Explicit roots are authoritative; missing home/storage preserves generation. The pinned draft's `off` row forbids lookup, dependency inventory, and directory creation. Diagnostic observability remains incomplete as P2-2.
- These are specification constraints, not proof that the uncommitted implementation satisfies them on any platform.

## Risks and next action

Revise the specification to resolve P2-1 and P2-2, then repin the review tuple. Implementation review must subsequently exercise real macOS/Linux trust gates and the specified replacement, cleanup, fallback, reentry, and invalidation fault cases. Windows persistence and broader disk maintenance remain deferred.

The operator's subsequent authorization makes caching default-on part of this work and **supersedes the requirement for another operator default-approval decision**. The unchanged R1 text still contains that requirement at lines 6, 42, 50, 53, and 251. A revised specification must reconcile those clauses and related activation language while preserving explicit `off`, override precedence, safe bypass, and verification gates. Default-on is authorized, not already implemented or verified. This review made no activation or file changes.

## Verdict

**NO-GO for design readiness only:** P2-1 and P2-2 remain open.

I pre-commit to GO on a revision that resolves P2-1 and P2-2 as specified and reflects the operator's default-on authorization without claiming implementation or verification.
