# YIDL Cache

Standalone compiled-code artifact cache for code-generating applications.

## Status

Initial shared cache implementation, with a fresh-process generated-record
fixture and focused failure tests. Lifecycle's default-on consumer adapter is now
implemented in its own project, with
[measured non-GUI startup gains](../yidl-lifecycle/dev-docs/LifecycleCodeCacheStartup.md).
Automatic placement is implemented locally against a dual-reviewed specification.
Code and state review accepted the content-pinned implementation draft; see the
[checkpoint](dev-docs/CacheLocationPolicyCheckpoint.md) for evidence and gates.
Sequential user-surface review also reports GO, with documentation follow-ups
recorded in the checkpoint. Cross-platform approval, commits, and publication remain pending.

## Intended Boundary

The cache stores compatible compiled module code and returns it to a
consumer. The consumer supplies its input fingerprint and deferred generation
callback, then executes the code and binds current runtime values itself.

Runtime code depends only on the standard library, not YIDL, Astichi,
YIDL Lifecycle, or Pyrolyze. The first integration is YIDL Lifecycle;
YIDL core remains independent.

## API Boundary

- `CacheRequest`: consumer namespace/revision, normalized input digest,
  compilation settings, and captured generation dependencies.
- `DependencyInventory.capture(...)`: timestamp/size inventory established once
  before importing or using the generator.
- `GeneratedCodeCache(directory=None, enabled=False)`: optional persistence and bounded
  in-process code reuse. Enabling is explicit.
- `CacheLocationPolicy`: optional explicit root or local/user fallback candidates,
  without reading environment variables or discovering source modules.
- `cache.get(request, producer, locations=...)`: returns `CacheHit`, `CacheMiss`, or `CacheBypass`,
  each containing compiled module code. Normal hits skip the producer; a final
  fallback hit can follow generation and failed local publication. Inspect the
  diagnostic `generated` flag, not hit counters alone. Producer callbacks run
  outside cache locks.
- `cache.statistics`: immutable hit/miss/bypass counters.
- `cache.diagnostics`: bounded immutable location/outcome/failure snapshots.
- `cache.clear()`: explicit maintenance of tracked locations and memory state,
  never a recursive scan of all consumer caches.

Each consumer owns its input schema, generation callback, execution namespace,
and live-value binding. Unknown input encodings should bypass, not use arbitrary
object serialization. See [cache policy](docs/CachePolicy.md) for storage trust,
invalidation, and platform limitations.

## Consumer Example

This complete `consumer_example.py` example uses only public APIs. The shape
digest excludes the runtime value; the producer file itself is a dependency.
The explicit root is routed to the consumer namespace, and constructor
registration makes that leaf available to maintenance before a lookup.

```python
import hashlib
from pathlib import Path
import sys

from yidl_cache import (
    CacheLocationPolicy,
    CacheRequest,
    CompilationContext,
    DependencyInventory,
    GeneratedCodeCache,
    SourceOrigin,
)

directory, value, forbid = sys.argv[1:4]
context = CompilationContext(filename="<example-record>")
request = CacheRequest(
    namespace="example.records",
    generator_revision="1",
    input_digest=hashlib.sha256(b"record(value: int)").hexdigest(),
    compilation=context,
    dependencies=DependencyInventory.capture({"producer": Path(__file__)}),
)
locations = CacheLocationPolicy(override_root=Path(directory).absolute()).locations_for(
    request.namespace, SourceOrigin(None, __name__)
)
cache = GeneratedCodeCache(locations[0].directory, enabled=True)
generation_calls = 0

def produce():
    global generation_calls
    generation_calls += 1
    if forbid == "yes":
        raise AssertionError("warm process must not generate")
    source = (
        "def build_record(default):\n"
        "    class Record:\n"
        "        def __init__(self, value=default):\n"
        "            self.value = value\n"
        "    return Record\n"
    )
    return compile(source, context.filename, "exec", flags=context.flags,
                   dont_inherit=context.dont_inherit, optimize=context.optimize)

result = cache.get(request, produce, locations=locations)
classes = []
for offset in (0, 1):
    namespace = {"__name__": "example.records"}
    exec(result.code, namespace)
    classes.append(namespace["build_record"](int(value) + offset))
assert classes[0] is not classes[1]
print(type(result).__name__, generation_calls, [cls().value for cls in classes])
print(cache.statistics, cache.diagnostics[-1])
if "clear" in sys.argv[4:]:
    print("removed", cache.clear())
```

From the consumer project, using a new private root for the cold invocation:

```sh
python consumer_example.py scratch/example-cache 10 no
python consumer_example.py scratch/example-cache 99 yes
python consumer_example.py scratch/example-cache 99 yes clear
```

Expected summaries: `CacheMiss 1 [10, 11]`, then `CacheHit 0 [99, 100]`.
The third invocation hits then removes the one artifact. A new `no` invocation
after clearing generates again. The diagnostic's `generated` flag identifies
generation independently of the outcome type. Run with this package installed
in the consumer environment; the development fixture below is a separate proof.

## Development

From this repository root:

```sh
uv sync --extra dev
uv run python -m pytest
uv build
```

Run the independent producer twice to demonstrate a fresh-process hit:

```sh
uv run python tests/fixtures/record_process.py scratch/demo-cache 10 no
uv run python tests/fixtures/record_process.py scratch/demo-cache 99 yes
```

The first invocation generates when no compatible entry exists. The second
forbids generation, binds the new value, and checks fresh class identity. Neither
imports YIDL, Astichi, Lifecycle, or Pyrolyze. This fixture is a correctness proof,
not a representative lifecycle performance benchmark.

- `src/yidl_cache/`: package implementation.
- `tests/`: cache fault coverage and the canonical independent-producer fixture.
- `docs/`: user documentation.
- `dev-docs/`: current design and implementation guidance.
- `scratch/`: ignored local experiments.

See [development guidance](dev-docs/README.md) for the accepted plan.
