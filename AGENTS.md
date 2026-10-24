# AGENTS

## Scope

This repository owns the standalone `yidl-cache` distribution and `yidl_cache`
Python package.

## Boundaries

- Keep runtime dependencies limited to the Python standard library.
- Do not import YIDL, Astichi, YIDL Lifecycle, or Pyrolyze.
- Cache compiled code objects, not live classes, namespaces, or runtime values.
- Consumers own generation fingerprints, deferred generation callbacks,
  execution, validation, and binding of current runtime values.
- Keep expensive producer imports out of cache-hit paths.
- Treat persisted code as executable artifacts; unknown trust or compatibility
  means bypass, not unsafe deserialization.

## Implementation

- Prefer frozen dataclasses for neutral request/result carriers.
- Do not introduce enums or substitute magic string/integer status tags.
- Keep annotations precise and modules cohesive.
- Use red/green/refactor for behavior changes.
- Prefer a canonical generated-code fixture for successful integration behavior;
  use focused tests for cache mechanics, diagnostics, and fault cases.
- Do not store absolute filesystem paths in committed files.
- Follow workspace GWZ rules for membership, staging, and commits.

See `dev-docs/README.md` for the current implementation plan. Repository setup
does not authorize runtime implementation, default activation, or publication.

<!-- gearu:agents:start -->
## Releases

- This repository uses [Gearu](https://owebeeone.github.io/gearu/) for release
  preparation.
- Read `RELEASE.md` before planning or performing a release.
- `gearu plan VERSION` and `gearu plan --bump LEVEL` are read-only. Do not run
  `gearu release`, push a release tag, or create a GitHub Release unless the
  user explicitly requests it.
- Never move or reuse a release tag. Correct released content with a new version.
- Never publish directly to PyPI, crates.io, or npm from a local checkout.
  Registry publication belongs in the repository's release workflow.
<!-- gearu:agents:end -->
