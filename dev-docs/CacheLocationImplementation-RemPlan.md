# Cache Location Implementation Remediation

Round: one bounded correction; original reviewed object is
`CacheLocationImplementationTuple.md`. Both initial implementation axes are NO-GO.
No acceptance, commit, or publication is claimed.

## Dispositions

| Finding | Disposition | Original counterexample / closure |
| --- | --- | --- |
| Code P2-1: origin metadata descriptors raise | Fix metadata inspection: read only supported plain module/spec dictionaries, treating arbitrary spec metadata as unavailable. Preserve `__file__` fallback. | Broken `__spec__.origin` property must not run or prevent origin fallback/decorating a valid class. |
| Code P2-2: real artifact-read I/O failure misclassified | Distinguish actual storage access/read failures from missing, corrupt, or unsafe entries. Preserve same-location regeneration for symlink/special-entry and invalid-envelope rejection. | Inject local-only `EIO` at open and stream read; a valid home entry must hit with zero producer calls and one location failure. |
| Code P2-3: explicit clear depends on prior lookup | Supply the explicit consumer namespace leaf as the shared cache's constructor maintenance target, without startup I/O. Automatic mode remains tracked-only. | Fresh configured process clears prior artifacts before decorating; preserve another namespace, unrelated/legacy entries, and automatic untracked locations. |
| Code P3-1: hit wording claims no generation | Qualify README hit semantics using the diagnostic generation flag. | Existing generated fallback-hit regressions remain the behavior proof; wording must agree. |
| State P2-1: unavailable ctypes escapes ACL trust | Convert ACL-backend import unavailability to typed storage failure, with no relaxation of checks. | Inject missing `_ctypes`; one normal producer call, one bypass, two bounded candidate reasons, no artifacts; public Lifecycle diagnostics remain available. |
| State P2-2: unencodable module name escapes | Convert unsupported location encodings to a typed cache bypass in the consumer, without changing exact UTF-8 namespace hashing. | Source-less module with a surrogate name still decorates; one producer call/bypass/frozen diagnostic, while producer exceptions stay unchanged. |

The lane owner independently reproduced State P2-2 before the State report.
Both axes reject failure escape into valid decoration from distinct causes;
those findings are corrected together without broad exception swallowing.

## Boundary

No cache format, default policy, public routing signature, trust relaxation, or
mutation boundary changes are proposed. Current public contracts are made
consistent with their accepted specification. Same-axis reviewers will verify
their original counterexamples on the revised tuple. This is not a new
architectural proposal.

Add narrow fault regressions, run the shared and focused Lifecycle gates on both
engines, rerun the supported interpreter matrix, and retain canonical cold/warm
binding proofs. Updated code causes legitimate cache misses; benchmark evidence
from the earlier object remains labeled by its reviewed tuple, with a corrected
object rerun recorded separately. No golden regeneration is authorized or needed.
