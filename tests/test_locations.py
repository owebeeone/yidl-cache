from __future__ import annotations

from dataclasses import replace
import hashlib
from pathlib import Path
import sys

import pytest

from yidl_cache import (
    CacheBypass,
    CacheDependencyError,
    CacheHit,
    CacheLocationError,
    CacheLocationPolicy,
    CacheMiss,
    CacheRequest,
    CacheStorageError,
    GeneratedCodeCache,
    SourceOrigin,
)
from yidl_cache.storage import ArtifactStorage


def code_for(request: CacheRequest):
    return compile("value = 7", request.compilation.filename, "exec", dont_inherit=True)


def routes(tmp_path: Path, namespace: str):
    source = tmp_path / "source" / "models.py"
    source.parent.mkdir(exist_ok=True)
    source.write_text("# source\n", encoding="utf-8")
    return CacheLocationPolicy(user_root=tmp_path / "home").locations_for(
        namespace, SourceOrigin(source, "models")
    )


def test_namespace_encoding_cannot_alias_case_or_literal_digest(tmp_path):
    long_name = "N" * 181
    names = (
        "Alpha",
        "alpha",
        "\u00e9",
        "e\u0301",
        long_name,
        hashlib.sha256(long_name.encode()).hexdigest(),
    )
    policy = CacheLocationPolicy(override_root=tmp_path)
    directories = [
        policy.locations_for(name, SourceOrigin(None, "models"))[0].directory
        for name in names
    ]
    assert len({str(path).casefold() for path in directories}) == len(names)
    assert all(
        path.name.startswith("ns-") and len(path.name) == 67 for path in directories
    )


def test_unknown_source_and_long_source_have_bounded_home_layouts(tmp_path):
    policy = CacheLocationPolicy(user_root=tmp_path / "home")
    unknown = policy.locations_for("records", SourceOrigin(None, "../odd/module"))
    assert len(unknown) == 1
    assert "modules" in unknown[0].directory.parts
    origin = SourceOrigin(tmp_path / ("x" * 200) / "model.py", "models")
    home = policy.locations_for("records", origin)[1].directory
    assert home.parts[-2] == "by-digest"
    assert ".." not in home.parts


pytestmark = pytest.mark.skipif(
    sys.platform not in {"darwin", "linux", "win32"},
    reason="unsupported storage trust platform",
)


def test_empty_routing_never_uses_constructor_directory(tmp_path, cache_request):
    directory = tmp_path / "unused"
    cache = GeneratedCodeCache(directory, enabled=True)
    result = cache.get(cache_request, lambda: code_for(cache_request), locations=())
    assert isinstance(result, CacheBypass)
    assert isinstance(result.reason, CacheLocationError)
    assert not directory.exists()
    assert cache.diagnostics[-1].generated
    assert cache.diagnostics[-1].attempted == ()


def test_routing_only_without_home_generates_once_without_io(tmp_path, cache_request):
    locations = CacheLocationPolicy().locations_for(
        "records", SourceOrigin(None, "models")
    )
    calls = []
    cache = GeneratedCodeCache(enabled=True)
    result = cache.get(
        cache_request,
        lambda: calls.append(1) or code_for(cache_request),
        locations=locations,
    )
    assert isinstance(result, CacheBypass)
    assert calls == [1]
    assert cache.statistics.bypasses == 1
    assert cache.clear() == 0


@pytest.mark.skipif(
    sys.platform == "win32", reason="POSIX permission/syscall mechanics"
)
def test_unsafe_local_leaf_falls_back_without_mutating_it(tmp_path, cache_request):
    locations = routes(tmp_path, cache_request.namespace)
    local = locations[0].directory
    local.mkdir(parents=True, mode=0o700)
    local.chmod(0o777)
    cache = GeneratedCodeCache(enabled=True)
    result = cache.get(
        cache_request, lambda: code_for(cache_request), locations=locations
    )
    assert isinstance(result, CacheMiss)
    diagnostic = cache.diagnostics[-1]
    assert diagnostic.selected == locations[1]
    assert len(diagnostic.failures) == 1
    assert diagnostic.failures[0].problem.kind is CacheStorageError
    assert local.stat().st_mode & 0o777 == 0o777
    assert not list(local.iterdir())


@pytest.mark.parametrize("fallback_hit", [False, True])
def test_publication_fallback_calls_producer_once_and_records_final_outcome(
    tmp_path, cache_request, monkeypatch, fallback_hit
):
    locations = routes(tmp_path, cache_request.namespace)
    if fallback_hit:
        seed = GeneratedCodeCache(locations[1].directory, enabled=True)
        seed.get(cache_request, lambda: code_for(cache_request))
    original = ArtifactStorage.write

    def fail_local(self, *args):
        if self.directory == locations[0].directory:
            raise CacheStorageError("injected local publication failure")
        return original(self, *args)

    monkeypatch.setattr(ArtifactStorage, "write", fail_local)
    calls = []
    cache = GeneratedCodeCache(enabled=True, memory_capacity=0)
    result = cache.get(
        cache_request,
        lambda: calls.append(1) or code_for(cache_request),
        locations=locations,
    )
    outcome = CacheHit if fallback_hit else CacheMiss
    assert isinstance(result, outcome)
    assert calls == [1]
    diagnostic = cache.diagnostics[-1]
    assert diagnostic.generated and diagnostic.outcome is outcome
    assert diagnostic.selected == locations[1]
    assert diagnostic.attempted == locations
    assert len(diagnostic.failures) == 1
    assert cache.statistics.hits + cache.statistics.misses == 1
    assert cache.statistics.bypasses == 0


def test_all_failed_routes_preserve_reasons_and_bound_diagnostics(
    tmp_path, cache_request, monkeypatch, capsys
):
    locations = routes(tmp_path, cache_request.namespace)

    def fail(self):
        raise CacheStorageError("unavailable " + "x" * 2000)

    monkeypatch.setattr(ArtifactStorage, "admit", fail)
    cache = GeneratedCodeCache(enabled=True)
    for _ in range(40):
        result = cache.get(
            cache_request, lambda: code_for(cache_request), locations=locations
        )
        assert isinstance(result, CacheBypass)
        assert isinstance(result.reason, CacheLocationError)
        assert len(result.reason.failures) == 2
    assert cache.statistics.bypasses == 40
    assert len(cache.diagnostics) == 32
    assert all(
        len(failure.problem.message) <= 1024
        for failure in cache.diagnostics[-1].failures
    )
    assert capsys.readouterr() == ("", "")


@pytest.mark.skipif(
    sys.platform == "win32", reason="POSIX permission/syscall mechanics"
)
def test_permissions_are_rechecked_after_admission(tmp_path, cache_request):
    locations = routes(tmp_path, cache_request.namespace)
    cache = GeneratedCodeCache(enabled=True, memory_capacity=0)
    cache.get(cache_request, lambda: code_for(cache_request), locations=locations)
    locations[0].directory.chmod(0o777)
    result = cache.get(
        cache_request, lambda: code_for(cache_request), locations=locations
    )
    assert isinstance(result, CacheMiss)
    assert cache.diagnostics[-1].selected == locations[1]


def test_dependency_fence_survives_route_switch_and_clear(tmp_path, cache_request):
    locations = routes(tmp_path, cache_request.namespace)
    cache = GeneratedCodeCache(enabled=True)

    def change():
        (tmp_path / "generator.py").write_text("changed\n", encoding="utf-8")
        return code_for(cache_request)

    result = cache.get(cache_request, change, locations=locations)
    assert isinstance(result, CacheBypass) and isinstance(
        result.reason, CacheDependencyError
    )
    cache.clear()
    other = routes(tmp_path, "other-directory")
    result = cache.get(cache_request, lambda: code_for(cache_request), locations=other)
    assert isinstance(result, CacheBypass) and isinstance(
        result.reason, CacheDependencyError
    )
    assert cache.diagnostics[-1].attempted == ()


def test_namespace_scoped_clear_preserves_other_consumers(tmp_path, cache_request):
    policy = CacheLocationPolicy(override_root=tmp_path / "shared")
    caches = []
    for name in ("Alpha", "alpha"):
        request = replace(cache_request, namespace=name)
        locations = policy.locations_for(name, SourceOrigin(None, "models"))
        cache = GeneratedCodeCache(enabled=True, memory_capacity=0)
        cache.get(request, lambda: code_for(request), locations=locations)
        caches.append((cache, request, locations))
    assert caches[0][0].clear() == 1
    cache, request, locations = caches[1]
    assert isinstance(
        cache.get(
            request, lambda: pytest.fail("other namespace erased"), locations=locations
        ),
        CacheHit,
    )


def test_routing_preference_eviction_does_not_reset_producer_fence(
    tmp_path, cache_request
):
    cache = GeneratedCodeCache(enabled=True, memory_capacity=0)
    for index in range(40):
        locations = CacheLocationPolicy(
            override_root=tmp_path / str(index)
        ).locations_for(cache_request.namespace, SourceOrigin(None, "models"))
        cache.get(cache_request, lambda: code_for(cache_request), locations=locations)
    assert len(cache._preferences) == 32
    assert len(cache.diagnostics) == 32
    changed = replace(
        cache_request, dependencies=replace(cache_request.dependencies, digest="other")
    )
    result = cache.get(changed, lambda: code_for(changed), locations=locations)
    assert isinstance(result, CacheBypass) and isinstance(
        result.reason, CacheDependencyError
    )


def test_producer_storage_exception_is_not_a_fallback_signal(tmp_path, cache_request):
    locations = routes(tmp_path, cache_request.namespace)
    error = CacheStorageError("this error belongs to the producer")
    calls = []
    cache = GeneratedCodeCache(enabled=True)

    def fail():
        calls.append(1)
        raise error

    with pytest.raises(CacheStorageError) as caught:
        cache.get(cache_request, fail, locations=locations)
    assert caught.value is error
    assert calls == [1]
    assert cache.diagnostics == ()
    assert (
        cache.statistics.hits
        == cache.statistics.misses
        == cache.statistics.bypasses
        == 0
    )
    assert not locations[1].directory.exists()


def test_explicit_empty_route_also_bypasses_previous_memory_hit(
    tmp_path, cache_request
):
    locations = routes(tmp_path, cache_request.namespace)
    cache = GeneratedCodeCache(enabled=True)
    cache.get(cache_request, lambda: code_for(cache_request), locations=locations)
    result = cache.get(cache_request, lambda: code_for(cache_request), locations=())
    assert isinstance(result, CacheBypass)
    assert cache.diagnostics[-1].generated


@pytest.mark.skipif(
    sys.platform == "win32", reason="POSIX permission/syscall mechanics"
)
def test_probe_cleanup_failure_is_bounded_and_maintainable(
    tmp_path, cache_request, monkeypatch
):
    import os

    locations = routes(tmp_path, cache_request.namespace)
    original = os.unlink

    def fail_probe(path, *args, **kwargs):
        if str(path).startswith(".probe-"):
            raise OSError("cannot remove probe")
        return original(path, *args, **kwargs)

    monkeypatch.setattr(os, "unlink", fail_probe)
    cache = GeneratedCodeCache(enabled=True)
    result = cache.get(
        cache_request, lambda: code_for(cache_request), locations=locations
    )
    assert isinstance(result, CacheBypass)
    assert len(result.reason.failures) == 2
    assert all("probe" in item.problem.message for item in result.reason.failures)
    monkeypatch.setattr(os, "unlink", original)
    assert cache.clear() == 2
    assert cache.diagnostics == ()


@pytest.mark.skipif(
    sys.platform == "win32", reason="POSIX permission/syscall mechanics"
)
def test_read_only_local_parent_falls_back_without_permission_repair(
    tmp_path, cache_request
):
    locations = routes(tmp_path, cache_request.namespace)
    parent = locations[0].directory.parent
    parent.mkdir(parents=True)
    parent.chmod(0o500)
    try:
        cache = GeneratedCodeCache(enabled=True)
        assert isinstance(
            cache.get(
                cache_request, lambda: code_for(cache_request), locations=locations
            ),
            CacheMiss,
        )
        assert cache.diagnostics[-1].selected == locations[1]
        assert parent.stat().st_mode & 0o777 == 0o500
    finally:
        parent.chmod(0o700)


@pytest.mark.skipif(
    sys.platform == "win32", reason="POSIX permission/syscall mechanics"
)
def test_symlink_replacement_after_admission_is_not_followed(tmp_path, cache_request):
    locations = routes(tmp_path, cache_request.namespace)
    cache = GeneratedCodeCache(enabled=True, memory_capacity=0)
    cache.get(cache_request, lambda: code_for(cache_request), locations=locations)
    local = locations[0].directory
    displaced = local.with_name("displaced")
    local.rename(displaced)
    target = tmp_path / "target"
    target.mkdir(mode=0o700)
    local.symlink_to(target, target_is_directory=True)
    assert isinstance(
        cache.get(cache_request, lambda: code_for(cache_request), locations=locations),
        CacheMiss,
    )
    assert cache.diagnostics[-1].selected == locations[1]
    assert list(target.iterdir()) == []


def test_same_request_reentry_is_fenced_across_locations(tmp_path, cache_request):
    from yidl_cache import CacheReentryError

    first = routes(tmp_path, cache_request.namespace)
    second = routes(tmp_path, "other-location")
    cache = GeneratedCodeCache(enabled=True)

    def produce():
        inner = cache.get(
            cache_request, lambda: code_for(cache_request), locations=second
        )
        assert isinstance(inner, CacheBypass)
        assert isinstance(inner.reason, CacheReentryError)
        assert cache.diagnostics[-1].attempted == ()
        return code_for(cache_request)

    assert isinstance(cache.get(cache_request, produce, locations=first), CacheMiss)
    assert not second[0].directory.exists()
