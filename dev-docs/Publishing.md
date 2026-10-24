# Cache release preparation and publication

## Scope and publisher identity

The operator authorized release setup in Cache, YIDL and Lifecycle and selected
LGPL-2.1 for all three. Cache changes cover packaging metadata, license, GEARU
configuration and publishing guidance/workflow. Cache runtime code and its
standard-library-only dependency boundary are unchanged. Astichi and other
projects remain reference-only. No commit, push, tag, GitHub release or package
upload is performed by this setup task.

The pending publisher identifies `owebeeone/yidl-cache`, workflow `publish.yml`,
environment `Any`. The upload job uses official PyPA OIDC publishing with
job-local `id-token: write`, no token secret and no environment requirement.
Astichi's separate `pypi` environment is unchanged.

## Preparation and behavior

The package declares SPDX `LGPL-2.1-only`, includes the license text in both
artifact formats and retains its README as the PyPI description. Source and
issue URLs are declared. The development classifier now reflects the existing
alpha implementation. No runtime dependencies were added.

`gearu.toml`, `.release.env` and `RELEASE.md` configure the selected preparation
route. Checks install the candidate, test Python 3.12–3.14, build the wheel from
the sdist and require strict Twine validation. Release lock refresh and checks
ignore development source overrides. Configuration loading is verified; a full
`gearu plan 0.1.0` needs a clean committed checkout and has not been run against
this uncommitted setup.

Manual workflow runs build and verify without uploading. A published GitHub
release checks out its exact tag, requires `v` plus the package version, and
uploads only after all gates pass. Each artifact is installed independently
outside the checkout using only declared dependencies. The canonical producer
runs in fresh cold and warm processes, with new runtime values and generation
forbidden on the warm run. A separate Ubuntu matrix runs the source suite on
CPython 3.12, 3.13 and 3.14.

The upload job downloads those verified artifacts without rebuilding. Actions
are pinned to upstream commits, publishing is restricted to this repository's
release events and concurrency does not cancel an active upload. Existing
versions are not silently skipped. The workflow does not itself create a tag
or GitHub release. See `RELEASE.md` for authorized GEARU operations.

## Local verification and release sequence

Preparation date: 2026-10-25. Source baseline:
`f8d883a40d49105ba37fcfdf76d38d1b23af6ea8` plus this uncommitted setup.
Local matrix: macOS arm64, CPython 3.12.12, 3.13.12 and 3.14.3;
Black 26.3.1 and pytest 8.4.2.

- Wheel and sdist build and pass strict Twine validation; metadata, license and
  package contents are inspected.
- Both fresh artifact installations pass the canonical producer's cold/warm
  sequence: one generation with values 10/11, then zero generations with values
  99/100. Neither process imports YIDL, Astichi, Lifecycle or Pyrolyze.
- Each interpreter passes 57 source tests with 29 platform-specific skips.
  Logs are ignored `build/release-tests-<python>.log` files. Windows-only cases
  remain skipped on macOS; this does not replace prior Windows qualification.
- Workflow syntax and positive/negative version-tag checks are verified locally.
  No hosted Actions run or OIDC exchange is claimed.

A local probe using the macOS temporary-directory alias bypassed caching and
failed the deliberately strict warm-run assertion. Repeating it with the
canonical resolved temporary path passed. This is a path-policy limitation,
not a packaging defect: the cache refuses unusable private directories. Use a
canonical private cache path for consumer probes; do not weaken the trust policy
to make the test pass. It does not block this setup or qualify a new filesystem.

Commit and review the setup, then run the build-only hosted verification.
Publish Cache 0.1.0 first, confirm PyPI availability and a fresh registry-only
install, then proceed to YIDL 0.1.0 and finally Lifecycle 0.1.0. Local checks do
not themselves authorize publication or qualify new platforms/filesystems.
