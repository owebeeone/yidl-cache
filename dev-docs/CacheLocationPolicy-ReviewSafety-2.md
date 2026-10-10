# Cache Location Policy: R2 Safety Review

Date: 2026-10-10  
Axis: Safety  
Object: `yidl-cache/dev-docs/CacheLocationPolicyPlan.md`, R2 DRAFT  
Lane: `grip-pyrolyze-wz-codecache-fixed`

## Verdict

**GO for draft-design readiness only.** Both inherited Safety P2 counterexamples are resolved by the R2 specification. No additional P0, P1, P2, or P3 finding was established.

This does not accept runtime implementation, verify default activation, freeze an interface, approve a release, or authorize commits/pushes. Default-on implementation in the isolated lane is operator-authorized; that decision was not relitigated.

## Evidence And Tuple

Read root `AGENTS.md`, `AGENTS_GWZ.md`, owning `yidl-cache/AGENTS.md`, the `review-loop` skill, the prior R1 Safety report, the merged remediation plan, and every pinned source/context document. The current peer report and original active lane were not inspected. No modifications, tests/builds, Git mutations, or additional agents were performed.

This completed review supersedes the earlier stopped attempt. Following the operator's path correction, the authoritative remediation input was `CacheLocationPolicy-RemPlan.md`. All thirteen pins matched at the beginning and end of the resumed review; no tuple movement was observed.

Paths below are relative to the named repository. Every row matched at both boundaries.

| Repository | Path | SHA256 |
| --- | --- | --- |
| yidl-cache | `dev-docs/CacheLocationPolicy-RemPlan.md` | `4d3404e7b12227049fd0572c728a933c4a36472bd13c383316984a371e4c4253` |
| yidl-cache | `dev-docs/CacheLocationPolicyPlan.md` | `1cf2f73ab60de0fd0cae2a9fec8d306c33ead9fc5ecc4ba969f9c287bd2fcafc` |
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

The operator-disclosed content-hash review exception replaces the skill's committed-object requirement for this draft only. Counterexamples below were traced through text, not executed. References to “Plan” mean `yidl-cache/dev-docs/CacheLocationPolicyPlan.md`.

## Prior-Finding Closure

This fresh same-axis reviewer replaces the original reviewer. Closure is limited to the draft specification; runtime regression obligations remain unverified.

| R1 finding | Original counterexample retrace against R2 | Disposition and regression obligation |
| --- | --- | --- |
| **P2-1: Namespace directory aliases** | `Alpha` and `alpha` no longer remain literal directory names. Plan:121–126 requires one lowercase SHA256 representation of exact namespace UTF-8 bytes for every length. Case-folding and Unicode normalization cannot collapse distinct digest spellings. An oversized namespace and a short namespace resembling its hash component also undergo the same hashing rule, eliminating the former mixed-representation collision, subject to the ordinary digest assumption. Plan:257–261 scopes clearing. | **Closed in specification.** Implementation must publish both namespaces on case-insensitive storage, clear each independently, and prove the other's artifacts and disk hits survive. Include oversized/literal-hash-spelling and Unicode-normalization cases. |
| **P2-2: Retained failures inaccessible to consumers** | For local publication failure followed by a home hit, Plan:236–251 provides public `cache_diagnostics()`/`GeneratedCodeCache.diagnostics`, selected layout, attempted locations, typed failures, final hit outcome, and `generated=True`. Lifecycle returning only `.code` therefore no longer eliminates the specified retrieval path. For both candidates failing, Plan:208–209 and 247–248 requires a typed `CacheLocationError` containing both frozen failure snapshots. | **Closed in specification.** Through public Lifecycle APIs, verify both sequences, one producer invocation, one final counter outcome, accurate generation evidence, oldest-first 32-entry retention including repeats, clear/reset behavior, bounded messages, no retained exceptions/tracebacks, and no automatic logs. |

## Changed-Range Analysis

A committed predecessor was unavailable through `git show HEAD:dev-docs/CacheLocationPolicyPlan.md`. This is a semantic changed-range review using the legitimate R1 Safety report and remediation record, not a mechanical Git diff. All eleven source/context hashes also match those recorded in R1.

| R2 range | Safety assessment |
| --- | --- |
| Plan:32–72 | Default-on is explicit. `off` wins over any directory setting; invalid enable values disable with a typed diagnostic. Explicit roots remain authoritative. Configuration is captured once, and removing a directory selects automatic placement rather than pretending to disable caching. |
| Plan:121–126 | Uniform namespace hashing closes the maintenance-isolation defect without changing request identity or relying on filesystem case sensitivity. |
| Plan:215–234 | Optional constructor directory and omitted-versus-empty routes are specified. `locations=()` cannot fall back to the constructor directory. Routing changes placement only; one cache/inventory retains shared code, reentry, and invalidation state. |
| Plan:236–255 | Public immutable request diagnostics replace private-only retention. Generation evidence distinguishes fallback hits from generation-free hits; history and messages are bounded, and producer exceptions do not create misleading completed outcomes. |
| Plan:316–333 | Required controlling-document amendments cover default/disable instructions, generated fallback hits, diagnostics, and historical benchmark labeling. They are implementation obligations, not claims that pinned context documents already changed. |

## Independent Safety Attack

| Concrete sequence attacked | Contract result |
| --- | --- |
| Local leaf is unsafe, or permissions/ACLs/path change after admission. | Plan:161–178 preserves trust checks on each operation, descriptor-held access, rejection without permission repair, and no unsafe deserialization. Admission is not a permanent certificate. |
| Trusted local artifact is corrupt; regeneration succeeds but publication fails. | Plan:186–198 regenerates at the selected trusted location, then permits one storage-failure fallback carrying already-produced code. Neither artifact rejection nor fallback authorizes a second producer invocation. |
| Both automatic locations fail, or an explicit root fails while home is usable. | Plan:117–119 and 208–211 preserves fresh generation, prohibits overriding the explicit-root choice, and reports exhausted-route failures without introducing implicit memory-only caching. |
| A producer edit is observed, then routing preferences are evicted or `clear()` runs. | Plan:180–188, 228–234, and 253–263 preserves the shared invalidation fence. Eviction, route switching, and clearing cannot reactivate that producer. |
| Same-key recursion or a producer exception occurs during a routed request. | Plan:186–198 preserves reentry/error direction rather than treating either as storage fallback. Callbacks remain subject to the existing outside-lock contract; exceptions propagate without a second invocation or final success counter. |
| No source/home exists; diagnostics exceed 32 completions; a later request hits memory. | Plan:100–115 and 215–255 permits an empty route without an invented author directory, bounds preference/history retention, and records memory hits with no disk attempts and `generated=False`. |

## Findings And Remaining Gates

**No open P0–P3 Safety findings.** The attack did not establish an additional contract-permitted defect.

Actual macOS/Linux trust, replacement/ACL races, cleanup failures, at-most-once fallback, cross-route fences, namespace-scoped clearing, and public diagnostic lifetime tests remain implementation gates under Plan:265–296. No concurrently written tests were inspected or credited. Windows persistence, Pyrolyze YAML implementation, broad disk maintenance, and publication remain deferred.
