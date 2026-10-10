# Cache Surface Follow-Up Evidence

The sequential Surface review reports GO at its four-document tuple, with two
nonblocking P3 documentation findings. Runtime source and interfaces remain
byte-identical to implementation tuple 3. This is not settled-tree or release
acceptance.

## Corrections And Owner Evidence

- P3-1: Lifecycle README and integration documentation now state that disabling
  retains artifacts and makes clearing a no-op. The documented enabled
  maintenance-only command precedes disabling, and automatic tracked-route
  limitations are unchanged.
- The rebuilt installed-wheel fixture seeded two builders in an isolated root.
  Disabled clearing returned zero and subsequent warm reuse still hit both.
  Enabled maintenance removed two; disabled real class construction succeeded
  with statistics `None`; re-enablement generated two fresh builders.
- P3-2: the shared README now has a complete public-API consumer example,
  including dependency capture, identity, compilation, routing, deferred
  generation, fresh runtime binding, diagnostics and maintenance.
- Its Python block was extracted unchanged into ignored
  `scratch/location-doc-example/consumer_example.py` and executed in fresh
  processes against an external private temporary root. Summaries were
  `CacheMiss 1 [10, 11]`, `CacheHit 0 [99, 100]`, a further warm hit with
  `removed 1`, and `CacheMiss 1 [101, 102]` after clearing.

These were owner observations submitted for originating-reviewer verification.
The [supplementary Surface report](CacheLocationImplementation-ReviewSurface-2.md)
now reports GO, closes both P3 findings, and independently replays the complete
shared example. It discloses which owner wheel observations were not repeated.
Runtime source remains unchanged, and no review finding remains open.

## Separate Compiler Evidence

The Surface review also reported the existing Lifecycle lazy-field README
`Config` example failing native materialization with caching enabled and disabled.
The owner independently reproduced it with caching disabled in the Lifecycle
environment. It is outside this cache object; no compiler/template change or
golden replacement was made. The canonical cache fixture and native full suite
still pass. The known Python-engine owned-field source-name snapshot discrepancy
also reproduces with caching disabled.

Reproduce the native example from the Lifecycle repository:

```bash
YIDL_LIFECYCLE_CACHE=off ASTICHI_LOWER_ENGINE=native .venv/bin/python -c '
from yidl_lifecycle.lifecycle import lazy, lifecycle
@lifecycle
class Config:
    items: list[int] = lazy(default_factory=list)
    cache: dict[str, int] = lazy(default_factory=dict, mutable=True)
'
```

This raises a class-context definition error when native scope materialization
cannot produce a composable. It is recorded for a separate bounded compiler
investigation, not concealed by regenerating goldens or disabling a safety gate.
