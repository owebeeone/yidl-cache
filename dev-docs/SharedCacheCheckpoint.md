# Shared Cache Checkpoint

## Scope

The initial standalone implementation is complete in `model.py`, `cache.py`,
`storage.py`, and `trust.py` under `src/yidl_cache/`. The cache stores compiled
module code, never classes, namespaces, defaults, or other live consumer values.

No Lifecycle adapter, YIDL core dependency, Pyrolyze runtime change, default
activation, application performance claim, or publication is included in this
checkpoint. The work remains uncommitted.

## Verification

The local macOS test matrix passed:

| Interpreter | Result |
| --- | --- |
| CPython 3.12.12 | 33 passed |
| CPython 3.13.12 | 33 passed |
| CPython 3.14.3 | 33 passed |
| CPython 3.15.0a5 | 33 passed |

The canonical record fixture proves a miss followed by a fresh-process disk
hit with generation forbidden. Each execution builds fresh classes and binds
the current supplied defaults. Neither process imports YIDL, Astichi, Lifecycle,
or Pyrolyze. The same proof passed against an isolated installed wheel containing
only the standalone distribution.

Focused fault coverage includes malformed and incompatible artifacts, bounded
reads, dependency edits, producer exception propagation, recursion, concurrent
publication, unsafe directory permissions, symlinks, hard-link policy, a real
macOS extended ACL, and unsupported-platform bypass. Checksum and identity
validation precede unmarshalling.

Wheel and source distribution builds, Black checks, and mypy checks of all five
source modules passed. Linux ACL inspection and Windows bypass still need actual
operating-system CI; the local interpreter matrix is not cross-platform release
approval.

## Reproduction

Run from this repository's root:

```sh
uv sync --extra dev
uv run python -m pytest -q
uv run --with mypy python -m mypy src
uv run python -m black --check src tests
uv build
```

Additional interpreter runs:

```sh
PYTHONPATH=src uv run --no-project --python 3.13 --with pytest python -m pytest -q
PYTHONPATH=src uv run --no-project --python 3.14 --with pytest python -m pytest -q
PYTHONPATH=src uv run --no-project --python 3.15 --with pytest python -m pytest -q
```

Fresh-process demonstration using separate current defaults:

```sh
uv run python tests/fixtures/record_process.py scratch/demo-cache 10 no
uv run python tests/fixtures/record_process.py scratch/demo-cache 99 yes
```

The first command reports `CacheMiss`, one generation call, and values `[10, 11]`.
The second reports `CacheHit`, zero generation calls, and values `[99, 100]`.
The second command fails if it tries to generate. This is a correctness fixture,
not a startup benchmark.

## Next Checkpoint

Review the shared contract, then add the opt-in Lifecycle adapter in its own
repository. The adapter must supply the complete generation fingerprint and
dependency inventory, retain current validation and generation diagnostics,
execute cached code in a fresh namespace, and bind current runtime values.

Only then measure representative cold, warm, and disabled startup paths. Cache
correctness here does not establish a Lifecycle performance improvement or
justify default activation.

## Follow-On Integration

Lifecycle's opt-in adapter is now implemented as a separate checkpoint. See
[consumer verification](../../yidl-lifecycle/dev-docs/LifecycleCodeCache.md).
This does not add consumer dependencies to the cache package.
Separate [startup evidence](../../yidl-lifecycle/dev-docs/LifecycleCodeCacheStartup.md)
now records local fresh-process savings for the thirteen-class Pyrolyze context
and Tk six-control workloads, without GUI creation. Those later measurements do
not expand this initial checkpoint's verification or approve default activation.

The later [automatic-location checkpoint](CacheLocationPolicyCheckpoint.md)
records the operator-directed default-on Lifecycle amendment, its accepted
specification, and new runtime verification. Shared activation remains explicit;
the original checkpoint above is historical evidence, not the new gate status.
