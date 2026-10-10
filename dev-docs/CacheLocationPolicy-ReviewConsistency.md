# Cache Location Policy: Consistency Review

Date: 2026-10-10  
Object: R1 DRAFT specification only  
Verdict: **NO-GO for design readiness**

## Evidence base

Inspection was confined to `grip-pyrolyze-wz-codecache-fixed`. Paths below are relative to the owning `yidl-cache` repository.

Read workspace `../AGENTS.md`, `../AGENTS_GWZ.md`, and owning `AGENTS.md`. All twelve supplied SHA-256 pins matched at review start and end, including the final check after the operator update:

| File | SHA-256 |
| --- | --- |
| `dev-docs/CacheLocationPolicyPlan.md` | `44017c42524bc73c2ca49262a29b444b450b5f5a576a60506db541d910043ac1` |
| `docs/CachePolicy.md` | `7c3f87e5b488e1887ded7ef65d81b6e19f0bd1801dee7e6f14d3c3a292083f31` |
| `src/yidl_cache/cache.py` | `da095ec52ba69abf8a9a4612a3cda7c06065c34a88dc06910a86a3bc5e4ff4db` |
| `src/yidl_cache/model.py` | `64e9d8a247c683288ca3d4af432eafaf98a9905b5447e119f4512362ab719f68` |
| `src/yidl_cache/storage.py` | `dd150a61475954780e6d2dcc3a086b0a90af2146de2f0b0d1cd60496885e92d0` |
| `src/yidl_cache/trust.py` | `d8d46e6a041fdd761a459f3fb3b5e77f834baff652b485f3c246af789f5a8686` |
| `../yidl-lifecycle/src/yidl_lifecycle/lifecycle.py` | `c6a79db6378e70a1622587dfdfdb71acd63707a3a3c00e0767f5547e42f17484` |
| `../yidl-lifecycle/src/yidl_lifecycle/lifecycle_code_cache.py` | `4940d82c807bbd2d1f62a7ad58998ab59651858626cdf487f13746c7317b7dc0` |
| `../yidl-lifecycle/src/yidl_lifecycle/lifecycle_cache_inputs.py` | `f3e1e7a9c2a03eca3fd0a931df63c8dc3fa40225c90b7cc825e5c8c908d0391c` |
| `../yidl-lifecycle/dev-docs/LifecycleCodeCache.md` | `de88e9f4c9f4b5ee770a44f227edb2b5894cfc33e96a6d655e4cb92deacc3cac` |
| `../yidl-lifecycle/dev-docs/LifecycleCodeCacheStartup.md` | `3c35260e1b7cffdf0e3770e4b9af1d324393c44847f083e1c859a8741368a6a2` |
| `../yidl/dev-docs/YidlGeneratedCodeCachePlan.md` | `d770295bf4d30c5d80de3f93c417664705d5471267b00c9196eba992ec4a2a37` |

**Process deviation:** The operator-authorized content-hash tuple substitutes for the review-loop skill’s committed-draft requirement, as disclosed at draft lines 262–269. No committed-object acceptance is claimed.

Existing uncommitted sources were contract context, not a diff under review. Their lack of proposed functionality is not a finding. No current-round peer report was read or requested. No files, agents, tests, builds, or commits were created or run.

## Findings (P0–P3)

No P0 or P1 finding was established.

### P2-1: Hashed namespaces lack a disjoint representation

**Location:** `dev-docs/CacheLocationPolicyPlan.md:113–131`; clearing guarantee at lines 219–223.  
**Violated invariant:** Different consumers must not share a maintenance directory that permits one consumer to clear another’s artifacts.

**Counterexample:** Let namespace `N` be 181 ASCII letters. Its encoded component exceeds the threshold. An untagged hexadecimal SHA-256 component satisfies the instruction to hash it into one fixed-length component. Let another consumer’s literal namespace be that hexadecimal digest. Both namespaces are valid under `src/yidl_cache/model.py:110–123`, but this permitted layout maps both to the same namespace directory.

**Impact:** Request identities still prevent cross-namespace code hits, but namespace-scoped clearing deletes both consumers’ recognized artifacts. Existing maintenance recognizes filenames rather than checking envelope namespaces (`src/yidl_cache/storage.py:229–241`).

**Required correction:** Specify the namespace hash algorithm and a representation disjoint from ordinary encoded namespaces. An ordinary, short namespace must not be able to impersonate the hashed form. Apply this consistently to explicit, local, and home layouts.

**Closure test:** Populate isolated caches for an oversized namespace and a literal namespace matching its proposed hash spelling. Assert distinct directories; clear either consumer and verify the other’s artifacts survive and remain reusable.

### P2-2: Required location diagnostics have no specified retrieval surface

**Location:** `dev-docs/CacheLocationPolicyPlan.md:71–74, 128–132, 188–199, 215`.  
**Violated invariant:** Retained candidate failures and selected-layout evidence must be inspectable through supported consumer diagnostics, without automatic logging.

**Sequence:** A local publication fails after generation; a compatible home artifact supplies the final hit. The required counter reports one hit. The specified configuration snapshot contains configuration, not request-location evidence. Existing `CacheHit` contains only code (`src/yidl_cache/model.py:162–164`), and Lifecycle discards the result wrapper (`../yidl-lifecycle/src/yidl_lifecycle/lifecycle_code_cache.py:124–131`).

**Impact:** The design requires bounded failure/layout evidence but specifies no way for a Lifecycle caller to obtain it. Likewise, when both locations fail, counters and configuration cannot expose the promised two storage reasons. The missing surface is in the proposal, not a defect in the existing adapter.

**Required correction:** Specify a supported, bounded diagnostic snapshot accessor, or an equivalent consumer-facing result contract. Define how callers obtain selected layout, attempted candidates, retained failure reasons, and evidence distinguishing a fallback hit that generated from one that did not.

**Closure test:** Inject local publication failure followed by a home hit, then failure of both candidates. Retrieve the evidence through the public surface, verify final counters and generation evidence, and exercise the 32-entry bound without logs.

### P3-1: Controlling-document amendments are not enumerated

**Location:** `dev-docs/CacheLocationPolicyPlan.md:26–31, 33–74, 182–194, 227–251`.  
**Violated invariant:** A specification changing controlling contracts must identify their exact replacements or qualifications.

**Walkthrough:** With the new enable setting `on` and no directory override, the draft selects automatic placement. However, `docs/CachePolicy.md:43–45` requires an explicit directory, while `../yidl-lifecycle/dev-docs/LifecycleCodeCache.md:35–36, 88` says an unset directory disables caching. Its lines 9–11 also say a hit skips assembly and compilation, which is false for the newly specified post-generation fallback hit.

**Impact:** Implementers and operators receive conflicting configuration, disable, and counter interpretations from documents still listed as controlling references.

**Required correction:** Add an explicit amendment list covering shared persistence selection, Lifecycle configuration/disable instructions, and routed hit/publication-failure semantics. Preserve existing single-directory contracts through appropriate qualifications.

**Closure test:** Walk every configuration-table row and the generation-then-fallback-hit sequence against the proposed replacement documentation; each must give one consistent outcome.

### P3-2: Routing-only construction and empty routing are unspecified

**Location:** `dev-docs/CacheLocationPolicyPlan.md:104–107, 203–214`.  
**Violated invariant:** Every enabled configuration must have a defined construction and request path, including no usable storage candidate.

**Sequence:** Enable automatic caching for an unknown-file origin when home discovery fails. The policy returns no candidate, but the retained constructor requires a directory and immediately converts it to `Path` (`src/yidl_cache/cache.py:28–42`). The draft does not define a routing-only construction strategy or distinguish empty `locations` from omitted routing.

**Impact:** Adapters must invent an inert directory or additional bypass machinery. Different choices can lose the shared request diagnostics or accidentally reuse a default storage route.

**Required correction:** Define an inert construction strategy or a no-default-directory mode. Specify that empty routing means storage bypass, not fallback to the constructor directory; omitted routing must preserve ordinary single-directory behavior.

**Closure test:** Exercise enabled automatic caching with unknown origin and unavailable home: generation once, one typed storage bypass, no directory creation. Retain legacy constructor/get behavior and verify clearing never targets an inert placeholder.

## Invariant analysis

- The enable table coherently normalizes `on`/`off`, preserves nonempty path spaces, and gives `off` precedence over directory opt-in.
- Module-origin discovery remains separate from generation identity and current-value binding. No source-content fingerprint is introduced.
- Descriptor trust checks, authoritative override failure, producer-at-most-once fallback, and producer-wide invalidation fences are mutually compatible as specified.
- Existing `GeneratedCodeCache(directory, enabled=False, memory_capacity=32, ...)` and ordinary `get(request, producer)` remain feasible. Routing-only initialization needs P3-2.
- Scoped `clear_code_cache()` has an explicit bounded reach and preserves invalidation. Namespace aliasing defeats its consumer-isolation guarantee.
- Code, decision, and diagnostic entry counts are bounded. Retained diagnostic carriers should also exclude exception traceback graphs and live producer values.
- Counter outcomes are defined, but their interpretation and supporting evidence require P2-2 and P3-1.
- These conclusions are static contract analysis, not runtime or platform verification.

## Risks and next action

Revise the specification to resolve the findings; no implementation edits are requested by this report.

**Operator update:** Default-on is now authorized as part of this work. This supersedes R1’s later-default-approval clause. The revised specification must reflect that authorization, including enabled automatic placement for unset/unset configuration. The pinned R1 bytes remain unchanged; default-on is not already implemented or verified.

Preserve explicit `off`, invalid-setting disable behavior, storage trust, and the existing implementation/platform verification gates. Windows persistence, broader disk maintenance, and filename prettification remain deferred.

## Verdict

**NO-GO for design readiness:** P2-1 and P2-2 are open.

I pre-commit to GO on a revision resolving P2-1, P2-2, P3-1, and P3-2 as specified and reflecting the operator-authorized default-on update. That verdict would approve specification readiness only, not implementation acceptance, verification, commits, or activation status.
