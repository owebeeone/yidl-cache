# Cache Location Implementation Review: Code

**Verdict: NO-GO**

Three P2 defects remain open. No P0 or P1 finding was established.

## Object And Boundary Verification

Reviewed independently on the Code axis, without accessing the current-round peer report or spawning other reviewers.

- Isolated lane: `grip-pyrolyze-wz-codecache-fixed`.
- Lifecycle base: `c2502f1a7a565624f20cf930fde92f581b123e9f`.
- `yidl-cache`: unborn repository; `git rev-parse --verify HEAD` failed at both boundaries.
- Object: initial standalone cache and Lifecycle adapter, including automatic routing and authorized default-on behavior.
- Controlling specification: R2 `yidl-cache/dev-docs/CacheLocationPolicyPlan.md`.
- All 30 SHA-256 pins below matched at review start and review end. No tuple movement occurred.

This is a content-pinned, uncommitted implementation DRAFT review under the disclosed process exception. It is not settled-tree, interface-freeze, activation, or release acceptance.

## Evidence

All pinned runtime source and tests were read, together with the controlling specification, shared policy, Lifecycle integration document, public READMEs, packaging declarations, and relevant Lifecycle call-site context.

The permitted suites were independently run on Python 3.14.3/macOS, with `PYTHONDONTWRITEBYTECODE=1` inherited by subprocesses:

- Shared cache: **51 passed**, 1.14 seconds.
- Focused Lifecycle tests with `YIDL_LIFECYCLE_CACHE=off` and `ASTICHI_LOWER_ENGINE=native`: **40 passed**, 4.47 seconds.

Additional probes used temporary directories outside the repositories. They reproduced the findings below without modifying reviewed files. The malformed-metadata decorator comparison succeeded using the Python engine; an initial native-engine attempt stopped during uncached materialization and was not attributed to this cache object.

The supplied other-interpreter, full-suite, mypy, build, and benchmark evidence was not independently rerun. No builds, environment changes, Git mutations, report writes, or original-workspace inspection were performed.

## Findings

### P2-1: Origin Metadata Exceptions Escape Into Valid Decoration

**Location:** `yidl-lifecycle/src/yidl_lifecycle/lifecycle_cache_configuration.py:75–89`, particularly the unrestricted `getattr(spec, "origin", None)` at line 79. Called before generation by `lifecycle_code_cache.py:75–78`.

**Root cause:** Origin discovery invokes arbitrary metadata attribute access outside its failure boundary. `_path()` handles unusable paths, but exceptions obtaining the path never reach that protection.

**Violated invariant:** R2 lines 100–103 require inconsistent or unusable module metadata to select unknown-file placement. Optional caching must not prevent otherwise valid class generation.

**Original counterexample:** Register a synthetic `ModuleType("broken_metadata")` in `sys.modules`, with no `__file__`, and assign this object to its `__spec__`:

```python
class BrokenSpec:
    @property
    def origin(self):
        raise ValueError("origin unavailable")
```

Give an otherwise valid class that module name and a string-annotated field with default `7`. With the adapter disabled, decoration and construction returned `7`. With a temporary-root `LifecycleCodeCache` enabled, the same decoration raised the bare `ValueError("origin unavailable")` before the producer ran.

**Impact:** Default-on caching adds a decoration failure for metadata that the uncached decorator does not require. The error also bypasses the normal class-context diagnostics.

**Required correction:** Treat unsupported or inaccessible specification metadata as unavailable origin information. Avoid invoking arbitrary descriptors where possible; contain ordinary metadata-inspection failures without swallowing producer exceptions. Continue through the documented `__file__` fallback or unknown-file route.

**Closure/regression:** Add a focused malformed-spec test and a decorator-level off/on comparison. Without a valid file, origin resolution must return `SourceOrigin(None, module_name)` and enabled decoration must still succeed. Verify that origin discovery neither reads source nor imports generators.

### P2-2: Artifact Read I/O Failures Never Reach Routing Fallback

**Location:** `yidl-cache/src/yidl_cache/storage.py:117–123`; routing distinguishes location failures at `cache.py:174–181`.

**Root cause:** `ArtifactStorage.read()` collapses every caught `OSError`, except missing files, into an artifact-corruption rejection. Actual storage I/O failure is therefore indistinguishable from an invalid envelope.

**Violated invariant:** R2 lines 186–191 distinguish storage-access failures, which try home, from invalid artifacts, which regenerate at the selected location. Candidate failures must remain visible in diagnostics.

**Original counterexample:** Seed compatible artifacts at both local and home candidates. Use a fresh cache with memory reuse disabled. Inject `OSError(errno.EIO, ...)` only when opening the local `.ycode` file, identified through its directory descriptor; leave admission, publication, and home reads functional.

Observed result:

```text
CacheMiss
producer calls = 1
attempts = [ModuleLocalLocation]
candidate failures = 0
rejected entry = CacheArtifactError("cannot read cache entry safely")
```

An independent read of the home candidate returned `CacheHit`.

**Impact:** A healthy fallback artifact is ignored. Generation runs unnecessarily, the final outcome is wrong for the required routing sequence, and diagnostics misidentify unavailable storage as artifact corruption.

**Required correction:** Separate storage-access/I/O failures from artifact corruption and unsafe-entry rejection. Preserve missing-entry behavior and same-location regeneration for genuinely invalid entries; propagate actual I/O failures as `CacheStorageError` so routing can record the failure and try home.

**Closure/regression:** Inject a local-only `EIO` at artifact open and stream read with a valid home entry. Require one final hit, zero producer calls, both candidates attempted, one typed location failure, and `generated=False`. Retain the existing corrupt-envelope and unsafe-entry regeneration tests.

### P2-3: Explicit-Root Clearing Cannot Clean Prior-Process Entries Before Lookup

**Location:** `yidl-lifecycle/src/yidl_lifecycle/lifecycle_code_cache.py:49–53`, `:88–89`, and `:200–202`; shared maintenance enumerates only preferences and `_default` at `yidl-cache/src/yidl_cache/cache.py:307–310`.

**Root cause:** Lifecycle always constructs a routing-only shared cache without a constructor directory. Its configured explicit namespace directory is therefore unknown to maintenance until a request populates routing preferences.

**Violated invariant:** R2 line 257 requires explicit-root clearing to target the consumer’s namespace directory. The subsequent tracked-location restriction is expressly for automatic placement.

**Original counterexample:** Seed one recognized artifact under the configured root’s `yidl_lifecycle.builder` namespace directory. Start a fresh process with caching on and that explicit root. Before any decoration, call the public `clear_code_cache()` API.

Observed:

```text
configuration enabled = True
removed = 0
remaining artifacts = 1
```

A second programmatic adapter against a previously populated explicit root reproduced the same result.

**Impact:** The explicit maintenance API cannot clear known persisted entries after restart unless callers first perform cache lookups. Unsupported-input bypasses likewise do not register the explicit location. This leaves the explicit write/clear lifecycle incomplete.

**Required correction:** Register the configured namespace leaf as an explicit maintenance target independently of request history, without performing initialization I/O or broadening cleanup to the override root. Preserve disabled behavior, namespace isolation, automatic tracked-location bounds, and producer fences. Align the Lifecycle clearing documentation with R2’s explicit/automatic distinction.

**Closure/regression:** Populate entries in a prior process, then invoke public clearing before the first decoration in a fresh explicitly configured process. Require removal of recognized files only from that namespace. Preserve another namespace, unrelated files, legacy flat-root entries, and untracked automatic locations.

### P3-1: Public READMEs Incorrectly Equate Hits With Avoided Generation

**Location:** `yidl-cache/README.md:34–36` and `yidl-lifecycle/README.md:54–55`.

**Root cause:** Public summaries retain unconditional statements that the producer runs only on misses/bypasses and that a hit skips assembly and compilation.

**Violated invariant:** R2 lines 194–205 permit generation before a successful fallback hit and prohibit claiming that such a hit avoided generation. Lines 325–328 explicitly require the README qualification.

**Original counterexample:** Seed home, then fail local publication after generation. The existing passing shared fallback test and Lifecycle public-diagnostics test establish `CacheHit` with one producer invocation and `generated=True`.

**Impact:** README readers can incorrectly treat hit counts as proof that generation was skipped, despite the implementation’s correct diagnostic distinction.

**Required correction:** Qualify avoided generation with `generated=False`; explain that a final fallback hit can follow generation and failed publication.

**Closure/regression:** Verify the revised wording against the existing post-generation fallback-hit tests. Additional duplicate success-path tests are unnecessary.

## Invariant Analysis

- **Namespace isolation:** Exact UTF-8 namespace bytes are always SHA-256 digested into `ns-` components. Case, Unicode-normalization, and literal/digest collision tests passed.
- **Dependency direction:** The shared runtime is standard-library-only. Lifecycle owns configuration, inventory, origin discovery, generation, execution, and binding.
- **Fingerprint and freshness:** The adapter explicitly projects class/field/method facts, ordering, provider names, transaction topology, builder parameters, compilation context, and engine environment. No fingerprint collision was established. The canonical fresh-process fixture passed explicit, local, and home reuse while binding changed runtime values.
- **Disable and anchoring:** Off precedence, no dependency inventory/directory creation, invalid-setting diagnostics, literal directory whitespace, and startup-relative anchoring passed the focused checks.
- **Fallback and fences:** Publication fallback carries already-produced code, preserves producer exceptions, and uses shared invalidation/reentry state. Read-access fallback remains defective under P2-2.
- **Diagnostics and outcomes:** Public immutable diagnostics are accessible, bounded, and distinguish generated fallback hits. Completed-request counters remain singular in tested fallback paths. P2-2 loses the required location-failure classification.
- **Clearing:** Shared tracked-route maintenance is bounded and namespace-scoped. Lifecycle’s unvisited explicit target is missing under P2-3.
- **Origins:** Normal discovery uses loaded metadata and filesystem inspection, not source contents or author-module imports. Malformed metadata handling fails under P2-1.
- **Paths:** No concrete machine-specific absolute path added in the pinned material was identified.

## Risks And Next Action

Resolve P2-1, P2-2, and P2-3 with their original counterexamples and regression checks, then re-pin the revised object for focused closure review. Correct P3-1 in the same revision.

**I pre-commit to GO on a revision that resolves the specific finding IDs as specified.**

That commitment concerns this bounded Code-axis DRAFT review only. Publication, settled-tree acceptance, active application adoption, actual Linux/Windows OS CI, and the disclosed timestamp/size and hot-reload limitations remain outside this verdict.

## Verified SHA-256 Manifest

The following exact tuple matched at **both** verification boundaries:

```text
1cf2f73ab60de0fd0cae2a9fec8d306c33ead9fc5ecc4ba969f9c287bd2fcafc  yidl-cache/dev-docs/CacheLocationPolicyPlan.md
6aa61e417d553e112ffa65fdcfb9f226836dcc8dc9fdc82a76e30a62d2f75859  yidl-cache/docs/CachePolicy.md
4255a01631404717ffd6a04b6ab2a6a3bdbfc13a0fd78b56047b86c488b58db4  yidl-cache/README.md
8d44658de3d6116e687b74ace8d9b2311764406b860e6dd34c5f7e5cdcb8c368  yidl-cache/pyproject.toml
700e696fe05ead148665d1c497a17d1339a313c2bed9e7e0b11e97c9881d3aae  yidl-cache/uv.lock
f8b1871fa6cbfee324a4d43b2ea35d99b437c418b82e5eb0952028c0b591b0d8  yidl-cache/src/yidl_cache/__init__.py
a74b10352c1f0ef06636fbc750149fbe6c763c9df324823a1b265b70a0edf7f2  yidl-cache/src/yidl_cache/cache.py
64e9d8a247c683288ca3d4af432eafaf98a9905b5447e119f4512362ab719f68  yidl-cache/src/yidl_cache/model.py
9f2742f6008d2f8866973a04904ef2a2ce927e6e72eced470539937b66aaea3b  yidl-cache/src/yidl_cache/storage.py
d8d46e6a041fdd761a459f3fb3b5e77f834baff652b485f3c246af789f5a8686  yidl-cache/src/yidl_cache/trust.py
6806bbdd91d6a1bb0a7d1aa3190bd537ba8bae339f1197dff145e60cdd90230b  yidl-cache/src/yidl_cache/locations.py
92337545446eb168d6191eb408fd55aafa0a6e471c38a5b4a4b417ad59e37f85  yidl-cache/src/yidl_cache/diagnostics.py
56a47e58d0352a8fc9bb07a65975e17971c33f6d26f3aff9c89e9b596e74902d  yidl-cache/tests/conftest.py
0a38c0c68acd3829ba2b50e126c519e11a1a5260a0a21305148fdb7b56c08ddd  yidl-cache/tests/test_generated_code_cache.py
ea18e239e211ea7567fcb4bc3c92615f94eaef2a5470d044439da1f232ff3264  yidl-cache/tests/test_artifact_failures.py
e11a9092cec2db8c7fc692a5569300e2926c2947e4c37d1b4997b7f03e9a2186  yidl-cache/tests/test_locations.py
bf5160d65c1bf5205739aa700f9076312cc8f97aa72fd4558b060af57179f8e2  yidl-cache/tests/fixtures/record_process.py
c6a79db6378e70a1622587dfdfdb71acd63707a3a3c00e0767f5547e42f17484  yidl-lifecycle/src/yidl_lifecycle/lifecycle.py
1d4012eb419ac52779c0f30dc70bafb16ef2e8fc1db9b8120acac273e9e6a5b1  yidl-lifecycle/src/yidl_lifecycle/lifecycle_code_cache.py
f3e1e7a9c2a03eca3fd0a931df63c8dc3fa40225c90b7cc825e5c8c908d0391c  yidl-lifecycle/src/yidl_lifecycle/lifecycle_cache_inputs.py
0a8d215b1b043f64ba016dab1bf230fc2c4eb00f555bc2b8cf39bb21f9ff42f1  yidl-lifecycle/src/yidl_lifecycle/lifecycle_cache_configuration.py
033cee2f6aca816aa4fbf3778633fce40a7b9fbd2c9c800c1d0e5f100fd6ecc7  yidl-lifecycle/tests/test_lifecycle_code_cache.py
1f64277fbf5fd9c8bf8a4be8b66809bf720cfcdda0e4b720e5ddf9c44ec252c0  yidl-lifecycle/tests/test_cache_configuration.py
ffb5970e5a54b594a40de1cf63a59caf36223a684b9c7583d793eaf1de02bfba  yidl-lifecycle/tests/data/cache/lifecycle_process.py
ca7b42fc916c410ee3569ff60441642f030da3f4222acf4882a146138b87c910  yidl-lifecycle/tests/data/perf/benchmark_lifecycle_startup.py
aa08f98fc284d49413d74cc6b455e202a90da1e63d6beb9b5dabb48340fb53df  yidl-lifecycle/pyproject.toml
d9fe575eda2685edde8bc95fe6b78625a524f4a0dff63311b1b2006d816726e2  yidl-lifecycle/uv.lock
cde30da28cbee878ccd1cbf820e1b6968745e2f09650b5389df91e4903b482f4  yidl-lifecycle/README.md
0f41fed95c8cc92a7cfaa3bf23b1b0aaa22ea272dc85966db98345e55410e648  yidl-lifecycle/dev-docs/LifecycleCodeCache.md
5ac98e61ce42d18ea8ba71ff460a7d9f0b9e17be67ac90f51d8333ced32bfa54  yidl-lifecycle/tests/data/perf/README.md
```
