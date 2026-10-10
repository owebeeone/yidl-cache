# Surface Review

**Verdict**
GO for the content-pinned DRAFT Surface checkpoint, with two open P3 documentation findings. No P0, P1, or P2 was established. This is not settled-tree or release acceptance.

**Pinned Object**
Lane: `grip-pyrolyze-wz-codecache-fixed`. Object: default-on automatic Lifecycle compiled-code caching.
Lifecycle baseline: `c2502f1a7a565624f20cf930fde92f581b123e9f`. Cache repository: unborn, with the disclosed uncommitted DRAFT exception.

Start and end checks matched. `git rev-parse HEAD` returned the Lifecycle baseline and exited 128 for unresolved cache `HEAD`. `shasum -a256` returned this unchanged tuple:

| Document | SHA256 |
| --- | --- |
| `yidl-cache/README.md` | `974b0f9a8f79f67ba3f940061eb38c45d591e4ff2dd6e12b14c5659e3c76f876` |
| `yidl-cache/docs/CachePolicy.md` | `6aa61e417d553e112ffa65fdcfb9f226836dcc8dc9fdc82a76e30a62d2f75859` |
| `yidl-lifecycle/README.md` | `01e94982fdcf09acf695ecbdcbca146e04a52459a7a111b760ed137ad322421e` |
| `yidl-lifecycle/dev-docs/LifecycleCodeCache.md` | `8c7cf228c8ba73552f7d9e88e0204707a08c75c2e4da893bcd214ebf62637b87` |

**Method**
One independent, sequential Surface review and one bounded first-day walkthrough: use, inspect reuse, select storage, disable, and clear. Only the four pinned documents were inspected. No source, plans, peer reports, additional reviewers, full-suite runs, or architecture review.

Existing member virtual-environment interpreters executed documented fixtures and public snippets. No repository edits, installations, builds, Git mutations, or persistent environment changes occurred. Bytecode writing was suppressed; HOME and artifacts remained under canonical external temporary directories.

**Walkthrough**
Commands below normalize temporary roots as `$T`. `$PY` denotes the current member’s `.venv/bin/python`. Working directories were the relevant member roots; every process used `PYTHONDONTWRITEBYTECODE=1`, `-B`, and isolated HOME.

```sh
# yidl-cache; README.md:61-71
$PY -B tests/fixtures/record_process.py "$T/record-cache" 10 no
$PY -B tests/fixtures/record_process.py "$T/record-cache" 99 yes
# yidl-lifecycle; dev-docs/LifecycleCodeCache.md:160-169
YIDL_LIFECYCLE_CACHE_DIR="$T/proof" $PY -B tests/data/cache/lifecycle_process.py 10 no
YIDL_LIFECYCLE_CACHE_DIR="$T/proof" $PY -B tests/data/cache/lifecycle_process.py 90 yes
```

- Shared fixture: both exited 0. Cold reported `CacheMiss`, one generation, values `[10,11]`; warm reported `CacheHit`, zero generation, values `[99,100]`.
- Lifecycle fixture: both exited 0. Cold reported two generations and two misses; warm reported zero generation, two hits, and current value 90.
- The documented public configuration/statistics/diagnostics APIs showed enabled explicit routing. Cold snapshots had `generated=True`; warm snapshots had `generated=False`.
- An unusable explicit override produced typed storage bypasses without home artifacts. The fixture’s cold-count assertion failed because it expected misses rather than bypasses.
- With `off` and the populated override, statistics were `None`, diagnostics empty, and clearing returned 0. Re-enabling preserved two generation-free hits.
- Enabled explicit-root clearing before decoration returned 2. The next generation-forbidden fixture exited 1 with `warm hit attempted generation`, confirming removal.

**Findings**
**P3-1: Disabled Clearing Is Undocumented**
- Location: `yidl-lifecycle/dev-docs/LifecycleCodeCache.md:124-149`, especially the explicit-root maintenance statement at lines 140-141.
- Root cause and violated invariant: the maintenance contract omits that disabled Lifecycle makes `clear_code_cache()` a no-op. Users cannot distinguish “nothing remained” from “maintenance was disabled.”
- Reproduction: seed the fixture above, then run `YIDL_LIFECYCLE_CACHE=off YIDL_LIFECYCLE_CACHE_DIR="$T/proof" $PY -B -c 'from yidl_lifecycle.lifecycle_code_cache import clear_code_cache; print(clear_code_cache())'`. Observed result: `0`. An enabled warm invocation against that root still reports two generation-free hits; enabled clearing removes both.
- Impact: a disable-then-clear attempt quietly retains reusable artifacts. This is a documentation defect, not a request to broaden the chosen cleanup scope.
- Required correction: document retained artifacts and disabled clearing explicitly. Provide clear-before-disable sequencing or an enabled maintenance-only process targeting the explicit root.
- Closure test: follow the revised instructions against a seeded root, verify removal and disabled operation, then verify cold generation after re-enablement. Preserve documented automatic-route limitations.

**P3-2: Shared Construction Requires Guessing**
- Location: `yidl-cache/README.md:26-44` and `yidl-cache/docs/CachePolicy.md:5-15,43-54`.
- Root cause and violated invariant: the standalone library lacks an executable consumer example. Inventory, request, compilation-context, and location-policy construction are described without sufficient invocation details for docs-only use.
- Reproduction: follow these documents to create a new producer. The fixture runs, but `DependencyInventory.capture(...)` remains a placeholder and complete request construction requires guessing signatures or inspecting excluded source.
- Impact: the documented proof demonstrates reuse without giving a new consumer a docs-only path to invoke the library.
- Required correction: add one complete public-API example covering dependency capture, input digest, compilation context, request, deferred producer, explicit activation, routing, diagnostics, and clearing.
- Closure test: execute that example unchanged in two fresh processes against external storage; require one cold generation and a generation-free warm hit, without consulting fixture source.

**Invariants**
- Shared-package activation is opt-in; Lifecycle activation is default-on.
- Directory routing is distinct from enablement; Lifecycle `off` wins over its override.
- Generation diagnostics distinguish avoided generation from hit counters.
- Enabled explicit-root cleanup works before decoration; statistics remain cumulative.
- Annotation eligibility, timestamp/size identity, restart requirements, unsupported persistence, and bounded cleanup are discoverable.

**Risks**
- Automatic source-local and home-fallback reuse were not runtime-verified; repository-local artifacts were prohibited, and the fixture walkthrough used explicit storage.
- The README’s lazy-field `Config` example failed identically with caching enabled and disabled, reporting unavailable native materialization. Fixtures passed; no cache-specific cause was established. Running that example required information beyond the pinned docs.
- Unusable-root clearing raised `CacheLocationError` and cleared diagnostic history. Attempting cleanup does not establish successful removal.
- Windows persistence, actual Linux/Windows approval, commits, publication, adoption, and the chosen policy outcomes remain deferred.
