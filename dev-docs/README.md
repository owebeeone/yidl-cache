# Development Documentation

The current cross-project plan and input audit are maintained in the neighboring
YIDL repository:

- [Generated code cache plan](../../yidl/dev-docs/YidlGeneratedCodeCachePlan.md).
- [Generation input audit](../../yidl/dev-docs/YidlGeneratedCodeCacheInputAudit.md).
- [Cache location policy draft](CacheLocationPolicyPlan.md): module-local
  preference, private home fallback, consumer controls, and review gates.
- [Location implementation checkpoint](CacheLocationPolicyCheckpoint.md):
  accepted specification, implementation progress, and remaining gates.
- [Windows persistence amendment](WindowsPersistence.md): separately authorized
  NTFS storage/trust implementation, TDD and real-platform evidence, and limits.
- [Windows remediation 1 evidence](WindowsPersistence-RemEvidence-1.md): actual
  substituted-root and publication counterexamples, bounded corrections, and
  separately pinned revised-platform checks; independent re-verdicts pending.

This repository owns the independent cache package. Consumer adapters stay in
their own projects; YIDL core does not acquire a cache dependency.

Current checkpoint: initial shared-cache implementation and an independent
fresh-process record fixture. Lifecycle's default-on adapter is implemented in its
own project. Representative non-GUI startup measurements are recorded;
cross-platform approval, implementation review, and publication remain pending.

See [cache policy](../docs/CachePolicy.md) for the implemented contract and trust
boundaries. Shared activation remains explicit; Lifecycle chooses default-on.

See [shared cache checkpoint](SharedCacheCheckpoint.md) for verification evidence,
reproduction commands, and the next integration boundary.

[Lifecycle integration](../../yidl-lifecycle/dev-docs/LifecycleCodeCache.md)
records the consumer fingerprint, configuration, and fresh-process proof.

[Startup measurements](../../yidl-lifecycle/dev-docs/LifecycleCodeCacheStartup.md)
record disabled/cold/warm medians, ranges, phase costs, and reproduction.
