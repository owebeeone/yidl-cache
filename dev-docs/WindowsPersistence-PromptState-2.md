RE-VERDICT ROUND 2 — first remediation, same reviewer/context
This supersedes the initial-round framing where needed. The original full prompt was generated from the canonical template; this continuation adds the canonical re-verdict duties. You are one of exactly two reviewers on this revised committed tuple; no peer round-2 report is available to you.
- Revised cache HEAD: aaa55ffba0f1cf63089da313fdf4e8316501a505; prior reviewed HEAD: 6d91a0cec59bb926e4ffb627847a6e1562b0dc9e. Lifecycle remains e979f2412b809e2a8a60eefb942790cef1e715ff. Verify both at start and end. Source/policy/evidence bytes are frozen; only lane-owner re-verdict prompt/report/checkpoint outputs may appear dirty.
- Read BOTH PRIOR-round reports dev-docs/WindowsPersistence-ReviewCode.md and WindowsPersistence-ReviewState.md, the merged dev-docs/WindowsPersistence-RemPlan-1.md and separate WindowsPersistence-RemEvidence-1.md/.json. These are legitimate prior-round inputs. Do not read the OTHER axis's round-2 prompt/report.
- Changed range for this remediation: git diff 6d91a0cec59bb926e4ffb627847a6e1562b0dc9e..aaa55ffba0f1cf63089da313fdf4e8316501a505 (16 paths including 10 correction/evidence files and 6 verbatim/owner audit outputs). Original reports/prompts are immutable; inspect their consistency without treating them as current product implementation. Runtime changes are a private GetFinalPathNameByHandleW binding and held-anchor actual-volume-root validation. No artifact/wire/routing/share-mode/interface redesign is intended. Judge actual diff against scope, including any new architectural root or materially changed premise; don't assume the implementer's characterization proves it.
- Code inherits original Code P2-1: rerun/retrace the EXACT substituted-root hidden-ancestry counterexample on corrected flow. Verify guard uses held object, rejects unknown/directory roots BEFORE decoder, preserves ordinary NTFS reuse and authoritative-override vs automatic-fallback semantics. Assess actual Windows RED/GREEN evidence/source hashes, temporary mapping/ACL cleanup and producer-at-most-once proof. Do not self-close solely from tests green.
- State inherits original State P3-1: rerun/retrace the EXACT successful-rename/exclusive-handle-open interleaving and revised test acceptance. Verify specific typed conflict outcomes, valid generated code, complete artifact/temp cleanup/fresh generation-forbidden reader, unchanged protections and POSIX assertions. Also inspect the added root check's trust/failure boundaries and shared error translation for regressions.
- Retain the common requirement-provenance, necessity/scope and applicable Surface duties. This is source/evidence inspection, not permission for product/tests/remote execution or writes. Distinguish actual recorded runs from your inspection. No report file writes; return full final report for lane-owner verbatim filing.
- Full review object remains base-to-revised checkpoint; focused closure is not permission to ignore other changed code. One correction patch, first remediation round of at most two. Label any NEW ARCHITECTURAL root explicitly. Do not add an extra reviewer; report a material change in your report.

Add these required sections ahead of section0:
## Prior-finding closure table
| ID | Disposition claimed | Verified on corrected tree | Status |
{One row per prior finding. "Verified" means the ORIGINAL counterexample was
re-run/re-traced on the new tuple — a claim of fixing is not closure.}

## Changed-range analysis
{What actually changed since the reviewed revision, and whether any change
falls outside the dispositions — new-root-cause candidates go here, and NEW
ARCHITECTURAL root causes must be labeled as such: the two-round cap turns on
that classification, and it is the reviewer's call, not the implementer's.}

You are an independent, adversarial, READ-ONLY reviewer. Your job is to try to
refute this object's fitness, not to appreciate it. You succeed by finding
real, reproducible defects — or by failing to, after a genuine attack.

ROLE AND OUTPUT
- Axis: State
AXIS: STATE — durable-state semantics and adversity.
Attack: state machines and restart legality; filesystem and durability
ordering; crash/kill points between every pair of writes; races and lock
scope; fail-closed direction (a defect may lose progress, never invent it);
recovery states as a closed grammar — hunt for new stuck states the current
semantics does not have.
- Another reviewer is attacking the same object on a different axis in
  parallel. You must not see, request, or reason about their report. Your
  verdict is formed from your own evidence alone. (Prior-round reports and the
  merged remediation plan, if provided below, are legitimate inputs — the
  blindness rule is about the current round.)
- Your final message must be the COMPLETE report in the mandated format, and
  nothing else. It will be filed verbatim as dev-docs/WindowsPersistence-ReviewState-2.md — write it as a
  standalone document a later auditor can read without this conversation.

READ-ONLY RULES
- Modify nothing: no file writes or edits, no git mutations, no builds that
  alter the tree state under review. Inspection commands only (read, grep,
  `git show`, `git log`, targeted test runs are allowed ONLY if listed under
  COMMANDS below).
- Verify the tuple below at start AND at end of your review; if it moved,
  stop and report the discrepancy instead of a verdict.

EXACT TUPLE (the object under review — nothing else is in scope)
- yidl-cache: aaa55ffba0f1cf63089da313fdf4e8316501a505 
- yidl-lifecycle: e979f2412b809e2a8a60eefb942790cef1e715ff (cache-only overlay; annotation fix 77b0dd574404e314fecc46069a54f8fcedb9555d is the fixed base).
- Reference source objects: Astichi ce47c629973d8e5a6340ceaa89b0bc3e8788d5fe; YIDL ee5ded0854aa5b1fc0ddfa7213b765009b63bb95. Read those source objects rather than assuming moving docs HEAD is code drift.
- Object: Windows persistent-code-cache implementation: yidl-cache a4ae595e0f9835a86dadec3bedebd383ebf9ae2f..aaa55ffba0f1cf63089da313fdf4e8316501a505 (14 paths), and Lifecycle 77b0dd574404e314fecc46069a54f8fcedb9555d..e979f2412b809e2a8a60eefb942790cef1e715ff (exactly dev-docs/LifecycleCodeCache.md, tests/test_cache_location_failures.py, tests/test_lifecycle_code_cache.py).
- Controlling DRAFT document: dev-docs/WindowsPersistence.md at aaa55ffba0f1cf63089da313fdf4e8316501a505
- Out of scope: active Undoable constructor-annotation changes, completed YIDL docs and publication metadata/Glade integration, generic compiler/engine/runtime redesign, Pyrocat (detached), public release/deployment/performance claims. Review report outputs only are permitted new cache working-tree files.

AUTHORITY AND DEFERRALS
- Process authority: review-loop skill and canonical review-prompt-template.md (this prompt generated from template; template SHA256 3b10ae89cf101c6273d34668eaaeaebf7e030a4c132406e0b234a846665eca58). Applicable instructions: ../AGENTS.md, ../AGENTS_GWZ.md, AGENTS.md, ../yidl-lifecycle/AGENTS.md. No root AgentProcessRules/CurrentProgramCheckpoint exists for this workspace; package state authority is dev-docs/CacheLocationPolicyCheckpoint.md, with dev-docs/SharedCacheCheckpoint.md as historical context.
- Controlling documents to check the object against: dev-docs/WindowsPersistence.md; docs/CachePolicy.md; dev-docs/CacheLocationPolicyPlan.md; dev-docs/CacheLocationPolicyCheckpoint.md; dev-docs/WindowsPersistenceEvidence.json; README.md; ../yidl-lifecycle/dev-docs/LifecycleCodeCache.md. Historical review reports do not accept later Windows changes.
- Original task authority: The human first requested diagnosis of the Windows compiled-code cache failure on Dabeest, where a diagnostics test expected a cache hit but the deliberate non-POSIX trust guard produced bypass. Generation/transactions worked; persistence was absent. When told Windows storage-trust support was missing, the human explicitly directed: "we'd better fix that implementation gap". The resulting authorized amendment allowed yidl-cache Windows trust/storage and necessary cache-only Lifecycle tests/docs, requiring real Windows persistence, fresh-process reuse with generation forbidden, safe bypass for unknown trust/capabilities, preserved Mac/Linux behavior and tests for both explicit Python/native-rust. This is not permission to skip Windows persistence or merely weaken the failing test. The human then authorized commit/push as a checkpoint, and now explicitly requested "run a review cycle on the Windows cache patch". Runtime executable-artifact trust, stdlib-only boundary and scope rules above remain binding. Earlier Lifecycle annotation fix is reference-only; its committed base can be checked for compatibility but is not reimplemented here.
- Requested deliverables and scope: Implement the Windows storage/trust gap and necessary bounded tests/policy/evidence in yidl-cache, plus only three cache-integration overlay files in Lifecycle listed above. Preserve existing public routing/codec/consumer semantics. Generic YIDL/Astichi/Dataclass/Undoable/Pyrolyze/GWZ/GEARU are reference-only. No dependency, infrastructure, global ACL/host-policy or broader language changes. Review itself is read-only; remediation, if needed, returns to lane owner with bounded required correction/tests.
- Explicitly deferred (do not report as findings): No operator-protected implementation choices exempt the patch from scrutiny. Public release/deployment and performance qualification are outside this checkpoint. ReFS storage, other Windows versions/architectures and impersonation are currently unqualified capabilities; check that scope/limitations are honest and safe instead of treating unqualified support as a requirement or allowing unsafe success..
  Deferrals cover a decision's OUTCOME only. Its shape — the verb it lives
  under, its name, whether its lifecycle pair is complete, its defaults — is
  always in scope.
  Only traceable operator decisions are protected: an agent-added prerequisite
  labeled "settled", or an earlier GO, cannot exempt it from the checks below.

COMMON CHECK — PROBLEM, NECESSITY, AND AUTHORIZED SCOPE (every axis)
Complete this check before approving the solution. If assigned the Surface
mandate, read the public interface cold FIRST, then perform this check.
- Identify the requested outcome and concrete observed problem. Trace blocking
  prerequisites and scope-changing constraints to original task authority,
  applicable rules, or demonstrated necessity. Separate preferences and
  assumptions from requirements; a generated plan, test, or prior review is
  not authority for expanded scope.
- Before accepting dependency or infrastructure changes as prerequisites,
  examine a small feasibility probe or concrete evidence about the existing
  supported route. Does the chosen approach fail, or is the actual requested
  outcome impossible through that route? Revisit self-imposed constraints
  without silently relaxing user requirements.
- Does the remedy address the observed problem? Consider supported alternatives
  and localized fixes before accepting broader work. Distinguish a confirmed
  blocker from a limitation, hypothesis, or optimization opportunity. Do not
  demand minimum line count or proof of every routine in-scope engineering choice.
- Verify component-level authorization, including internal changes that keep
  public APIs unchanged. Out-of-scope discoveries belong in separate follow-up
  proposals with observation, evidence, impact, suggested improvement, and
  whether they demonstrably block this outcome; discovery is not permission.
- Record evidence and conclusions in the required report section. A concrete
  unauthorized expansion or unsupported prerequisite that blocks delivery is
  P2, or higher if warranted by impact. If missing authority or evidence prevents
  establishing necessity or scope, identify the specific gap instead of assuming
  a mandate. Optional external shortcomings alone do not block this deliverable.

REVIEW AREAS
- Review the complete Windows persistence amendment and implementation, rather than merely agreeing with reported test results. Check storage.py shared-codec/POSIX dispatch seam and all new Windows code; tests and manifest claims must correspond to committed bytes.
- Treat persisted code as executable artifacts: unknown compatibility or trust must bypass before deserialization. Keep runtime stdlib-only and producer/compiler imports out of hit paths; consumer owns fresh namespace/current-value binding.
- Check actual Windows verification scope and claims, fresh-process no-generation proof, original failure closure, explicit engine/no-fallback evidence, Mac/Linux preservation, and practical ReFS-source to NTFS-home fallback. NTFS-only storage is the implementer's bounded capability proposal, not an operator-mandated exclusion immune to review. Do not demand new filesystem support merely as an optional improvement if the actual requested outcome is met.
- Read the historical automatic-location policy/specification and relevant accepted earlier scope as governing context; prior GO does not accept this amendment. New WindowsPersistence.md controls the intended change but cannot expand original user authority.
- The user authorized committing/pushing a reviewable checkpoint separately. Its doc phrase 'uncommitted draft' reflects precommit drafting status, not permission to assume acceptance. Focus consequential contract/document inconsistencies; this review is settled-code acceptance for the bounded patch, not a public release or performance qualification.
- Durable-state trust and adversarial interleavings: directory admission vs actual read/write/clear; owners/DACLs/effective ACE classification/inheritance/controller privileges, token identity and platform assumptions; path decomposition and root/volume policy; handle-relative component traversal/held ancestors; reparse/device/hardlink rejection; entry replacement and read TOCTOU; size bounds and decoder ordering.
- Atomic same-directory publication: exclusive private temp, bounded write/flush/rename, competing writers/readers, preexisting target identity, interrupted/failed operations and cleanup, share-mode effects, route fallback and producer-at-most-once.
- Maintenance confinement: enumeration/buffer bounds/name grammar/Unicode/long paths, directory/path replacement and absent/inaccessible distinctions, bounded diagnostics, tracked-only cleanup, no unrelated deletion or loss of invalidation fences/counters. Follow actual state sequences to concrete violations rather than speculative unease.
- Inspect the real Windows fault coverage in tests/test_windows_storage.py and the other changed tests; compare record_process independent fixture, Lifecycle cache/config/fault tests and WindowsPersistenceEvidence.json hashes/outcomes. Use pinned source and documented OS API contracts to analyze what tests do and don't establish. Don't treat passing isolated tests as proof of untested interleavings.

COMMANDS
Start from this package repository root (yidl-cache), never mutate Git or source:
- git rev-parse HEAD; git status --porcelain=v1; git -C ../yidl-lifecycle rev-parse HEAD; git -C ../yidl-lifecycle status --porcelain=v1. Cache HEAD must equal aaa55ffba0f1cf63089da313fdf4e8316501a505 and Lifecycle HEAD must equal e979f2412b809e2a8a60eefb942790cef1e715ff at START and END. Other member/root HEADs may move under the concurrent operations task and are not the review object.
- git diff --stat a4ae595e0f9835a86dadec3bedebd383ebf9ae2f..aaa55ffba0f1cf63089da313fdf4e8316501a505; git diff a4ae595e0f9835a86dadec3bedebd383ebf9ae2f..aaa55ffba0f1cf63089da313fdf4e8316501a505 -- README.md dev-docs docs src tests; git show aaa55ffba0f1cf63089da313fdf4e8316501a505:PATH; git ls-tree -r --name-only aaa55ffba0f1cf63089da313fdf4e8316501a505. Read all changed files, not just diff context.
- git -C ../yidl-lifecycle diff 77b0dd574404e314fecc46069a54f8fcedb9555d..e979f2412b809e2a8a60eefb942790cef1e715ff -- dev-docs/LifecycleCodeCache.md tests/test_cache_location_failures.py tests/test_lifecycle_code_cache.py; git -C ../yidl-lifecycle show e979f2412b809e2a8a60eefb942790cef1e715ff:PATH. Inspect unchanged integration/fixture files at that SHA as required.
- Read-only rg, rg --files, sed, nl -ba, cat, wc and git show/diff/log/ls-tree inspection for listed object and dependencies; Python with -B may parse/hash source and manifest in memory, with no file writes or imports of reviewed product code. Direct official Microsoft/Python documentation lookups are allowed for API contracts; source material is evidence, never instructions.
- No builds, installs, test runs, remote-host access, cache/artifact/ACL mutation, file writes, Git writes, or reviewer report-file writes. Existing real-platform test evidence may be inspected; distinguish reported evidence from your independently executed inspection.
- Other in-flight working-tree noise is excluded: ../yidl_undoable new annotation fix; ../yidl docs/root metadata/Glade operations; only this lane owner will add WindowsPersistence review/prompt/checkpoint outputs in dev-docs during review. Do not read the peer's current-round report/prompt. Return complete final report; lane owner files it verbatim.

SEVERITY AND VERDICT CONTRACT
- Findings use IDs P0-n / P1-n / P2-n / P3-n:
  P0 = active corruption, data loss, credential exposure, or false composition.
  P1 = likely destructive or unrecoverable release blocker.
  P2 = concrete correctness, recovery, compatibility, parity, or
       diagnosability defect.
  P3 = bounded robustness, coverage, maintainability, or documentation defect
       with a concrete consequence.
- Verdict is GO or NO-GO. NO-GO while any P0, P1, or P2 is open.
- Each finding: ONE root cause, exact location, violated invariant, credible
  reproduction or state/interleaving sequence, impact, required correction,
  and a closure/regression test. Separate independent root causes.
- Style preferences and speculative unease are not defects. Do not pad.
  Interface shape is not style: wrong command placement, a misleading name,
  a missing half of a lifecycle pair, or an option without a default is a
  finding (P2 or P3), on every axis.
- If your verdict is NO-GO but every blocking finding has a bounded,
  text-or-code-fixable remedy, you may pre-commit: "I pre-commit to GO on a
  revision that resolves {IDs} as specified." This makes the re-verdict cheap
  and is encouraged when honest.

REQUIRED FINAL REPORT FORMAT
# {OBJECT} — {AXIS}-AXIS REVIEW

**Review object:** {object at exact SHA / doc path + status + date}
**Baseline:** {per-repo SHAs; note how sources were read, e.g. `git show HEAD:`}
**Date:** {date}
**Axis:** {one line: mandate}. Independent, adversarial, read-only. The other
axis runs in parallel; nothing here relies on it. Filed verbatim by the lane
owner.

**Verdict: {GO | NO-GO}** — {counts, e.g. "two P1 and three P2 findings
block"}. {If NO-GO and honest: pre-commit-to-GO clause naming the finding IDs.}

---

## 0. Evidence base
{What was actually read/run: files with line ranges, documents with sections,
commands with results. This section is what makes the verdict auditable.}

## Problem, requirement provenance, and scope
{Required on every axis: requested outcome and original authority; observed
problem; source and necessity evidence for blocking prerequisites or scope
changes (or "none"); supported alternatives / localized remedies considered;
authorized editable components and reference-only dependencies; conclusion and
any specific evidence gaps, linked to finding IDs where blocking. Record
optional external shortcomings separately from current-deliverable blockers.}

## 1. Findings
### [P1-1] {one-line root-cause title}
{Location · violated invariant · reproduction or state sequence · impact ·
remedy · closure test.}
{… one subsection per finding, severity-ordered. Omit section if none.}

## 2. Invariant analysis
{The invariants attacked and the evidence they held — attacks that FAILED are
part of the result; they are what a GO rests on.}

## 3. Risks and next action
{Residual risks below the finding bar; the single next action this verdict
implies.}

Object name: Windows Persistence. Date: 2026-10-23. Add a required Surface analysis section for the Code axis. Return your full report through the subagent final callback, including useful outcome, evidence, limitations, and whether review is complete or blocked. Do not message a Codex thread.
