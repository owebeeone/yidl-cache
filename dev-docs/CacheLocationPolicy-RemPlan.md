# Cache Location Policy R1 Remediation

Status: proposed R2 correction; originating findings are not self-closed.
R1 reports are filed verbatim. Both axes independently found namespace isolation
and diagnostic retrieval defects; this is blind convergence, not duplicate work.

| Finding | Disposition | Closure obligation |
| --- | --- | --- |
| Safety P2-1 | Accept; always digest exact namespace bytes. | Alpha/alpha layouts differ on case-insensitive storage; clearing either preserves the other. |
| Consistency P2-1 | Accept; use one digest representation for every length. | Long namespace and literal hash spelling cannot share a directory. |
| Both axes P2-2 | Accept; named frozen bounded public request snapshots. | Public retrieval exposes both failed routes, generation-then-fallback-hit evidence, final counters, history bounds, and no logs. |
| Consistency P3-1 | Accept; enumerate controlling-document replacements. | Walk every enable table row and generated fallback hit against updated documentation. |
| Consistency P3-2 | Accept; optional constructor directory and empty/omitted route distinction. | No source and no home generates once with typed bypass, no directory; legacy calls still work. |

Operator amendments: unset/unset now enables automatic placement; explicit off
still wins. The suggested Pyrolyze YAML file remains a separately owned bootstrap
follow-up, not a shared-cache dependency or unrequested Pyrolyze edit.

R2 changes an API/default contract. Fresh peer-blind Consistency/Safety reviewers
replace the original two under review-loop Step 5.5. They inherit and verify every
open finding on their own axis. Draft content hashes remain the disclosed object;
no commit, publication, implementation acceptance, or platform proof is claimed.
