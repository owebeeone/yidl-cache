# Cache Location Policy: Consistency Review R2

Date: 2026-10-10  
Object: `dev-docs/CacheLocationPolicyPlan.md`, R2 DRAFT  
Lane: `grip-pyrolyze-wz-codecache-fixed`  
Verdict: **GO for specification readiness only**

## Findings

No open P0, P1, P2, or P3 Consistency finding was established. The inherited counterexamples are resolved at the specification level. Runtime implementation and regression-test closure are not claimed.

## Evidence And Review Boundary

Read workspace `AGENTS.md`, `AGENTS_GWZ.md`, owning `yidl-cache/AGENTS.md`, review-loop `SKILL.md`, the prior Consistency report, the correctly hyphenated `dev-docs/CacheLocationPolicy-RemPlan.md`, and every pinned source/document below.

All thirteen supplied hashes matched at both review start and end. Paths below are relative to the owning `yidl-cache` repository.

| File | Verified SHA-256 |
| --- | --- |
| `dev-docs/CacheLocationPolicyPlan.md` | `1cf2f73ab60de0fd0cae2a9fec8d306c33ead9fc5ecc4ba969f9c287bd2fcafc` |
| `dev-docs/CacheLocationPolicy-RemPlan.md` | `4d3404e7b12227049fd0572c728a933c4a36472bd13c383316984a371e4c4253` |
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

**Disclosed process exception:** Content hashes replace the review-loop requirement for a committed draft. This is not settled-tree acceptance, release approval, an interface freeze, or verified default activation.

This fresh same-axis reviewer independently retraced the inherited findings. No current-round peer report or original active lane was accessed. Only inspection commands were used; no files, Git state, tests, builds, or agents were created or changed.

## Prior-Finding Closure

R2 locations refer to `dev-docs/CacheLocationPolicyPlan.md`. “Closed” below means closed for this draft-design review; implementation proofs remain required.

| R1 Finding | Original Counterexample Retraced Against R2 | Disposition And Remaining Proof |
| --- | --- | --- |
| P2-1: Namespace representation collision | For oversized namespace `N`, let `H = SHA256(N)`. R2 lines 121–125 map them to `ns-SHA256(N)` and `ns-SHA256(H)`, respectively. The literal hash spelling no longer impersonates the hashed representation, subject to the stated digest assumption. All placement modes use this rule. | **Closed in specification.** Populate both namespaces and prove clearing either preserves the other's artifacts. |
| P2-2: Diagnostics unavailable | Local publication fails after generation, followed by a home hit; alternatively, both routes fail. Lines 236–255 now expose public immutable request snapshots containing locations, failures, outcome, and generation evidence. Exhausted routes return typed failure snapshots. | **Closed in specification.** Retrieve both sequences through the public accessor; verify counters, `generated=True` for the generated fallback hit, repeated-request history, the 32-entry bound, and no logs. |
| P3-1: Controlling amendments missing | Automatic placement contradicts the old explicit-directory requirement and removed-directory disable instructions; a generated fallback hit contradicts unqualified generation-skipping language. Lines 316–333 now require replacement configuration instructions, qualified hit semantics, and historical measurement labeling. | **Closed in specification.** Walk all configuration rows and generated fallback hits against the amended documents during implementation. Existing pinned documents are not claimed already updated. |
| P3-2: Routing-only construction undefined | Unknown origin and unavailable home yield no candidate. Lines 215–224 now permit `directory=None`, define omitted routing, and make explicit `locations=()` authoritative storage bypass without an invented directory. | **Closed in specification.** With caching enabled, verify generation once, typed storage bypass, no directory creation, inert clearing, and retained legacy constructor/get behavior. |

## Changed-Range Analysis

Changes were assessed against the prior report and merged remediation obligations, rather than treating the remediation plan as self-certifying.

| R2 Range | Consistency Analysis |
| --- | --- |
| Lines 32–72 | Default-on is explicit, including unset/unset. `off` overrides every directory setting; invalid enable values disable with configuration evidence. Empty values, path spaces, startup-relative resolution, and CPython bytecode controls have stated semantics. |
| Lines 84–157 | Origin discovery remains separate from generation identity. Namespace hashing is uniform; source, unknown-origin, explicit-root, and long-origin layouts retain distinct specified roles. Prototype entries remain untouched. |
| Lines 159–211 | Admission and operation-time trust checks coexist with bounded fallback. Publication failure carries already-generated code; successful fallback determines the single final counter outcome without claiming generation was avoided. |
| Lines 213–263 | Routing-only construction and legacy single-directory calls coexist. Routes share code capacity, invalidation, and reentry state. Diagnostics distinguish memory hits and generated fallback hits; clearing has bounded tracked-location scope and preserves invalidation. |
| Lines 265–333 | Test checkpoints cover the changed controls, routing failures, exceptions, counters, bounds, and clearing. Disabled benchmarks explicitly use `off`; controlling-document amendments and authorization boundaries are enumerated. |

## Additional Adversarial Checks

- Traced local admission failure, authoritative override failure, corrupt local entry, publication failure followed by home hit/miss, and exhaustion of both candidates. No contradictory producer-invocation or final-outcome requirement was established.
- Checked memory reuse, routing-preference eviction, cross-directory producer fences, and clearing. Placement changes do not redefine request identity or reactivate an invalidated producer.
- Checked producer exception propagation and fresh execution/binding against the pinned consumer contracts. Shared-cache diagnostics describe completed cache requests, not successful class construction.
- Checked enable/disable and storage/clear lifecycle pairs, option defaults, and public diagnostic retrieval. No missing counterpart or unspecified changed default was established.

## Verdict And Remaining Gates

**GO:** R2 is internally consistent and fit to implement on the reviewed axis. All four inherited Consistency counterexamples have specification-level corrections.

No tests or builds were run or inspected as new implementation evidence. Required regression proofs, controlling-document edits, platform trust checks, automatic-policy performance measurements, and later implementation/user-surface acceptance remain outstanding. This verdict does not authorize active-lane changes, commits, pushes, publication, or weaker storage trust.
