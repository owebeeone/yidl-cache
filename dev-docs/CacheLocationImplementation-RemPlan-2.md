# Cache Location Implementation Remediation 2

This is the second bounded correction. Code reported GO at
`CacheLocationImplementationTuple-2.md`; State closed its original findings but
reported one new, explicitly non-architectural P2. No settled-tree, commit,
publication, or cross-platform acceptance is claimed.

| Finding | Disposition | Closure evidence |
| --- | --- | --- |
| State R2 P2-3: inaccessible clear preflight | Replace boolean existence checks with explicit non-following metadata inspection. Only genuine absence returns zero; other inspection errors become `CacheStorageError`, allowing existing shared maintenance to drain process collections and report bounded frozen reasons. Do not change descriptor traversal, artifact recognition, namespace scope, or producer fences. | Real inaccessible-ancestor tests for tracked and fresh targets: typed failure, empty memory/preferences/history, unchanged cumulative counters and producer fences, surviving artifacts/neighbors, and successful clearing after permissions are restored. Fresh Lifecycle adapter and genuinely absent-root checks cover the consumer boundary. Run on Python 3.12 and 3.14. |

The full native suite separately found a test-harness problem: two new metadata
fault tests changed the assembly engine after compiled templates were loaded.
Move the real disabled/enabled decorator comparison into a fresh subprocess
with its engine selected before import. Keep the original factory-generation
and bypass assertions; no compiler changes, mocked ASTs, or skipped failures.

The merged patch contains only this storage correction and narrow tests. Public
interfaces, artifact format, activation, routing, dependencies, and trust policy
are unchanged. The originating State reviewer verifies its original sequence;
Code checks the changed range without reopening the accepted architecture.
User-surface review remains a separate sequential step.
