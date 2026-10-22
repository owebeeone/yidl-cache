from __future__ import annotations

import builtins
from dataclasses import replace
import errno
import os
from pathlib import Path
import sys

import pytest

from yidl_cache import (
    CacheBypass,
    CacheDependencyError,
    CacheHit,
    CacheLocationError,
    CacheLocationPolicy,
    CacheStorageError,
    GeneratedCodeCache,
    SourceOrigin,
)

pytestmark = pytest.mark.skipif(
    sys.platform not in {"darwin", "linux", "win32"},
    reason="unsupported storage trust platform",
)


def code_for(request):
    return compile("value = 7", request.compilation.filename, "exec", dont_inherit=True)


@pytest.mark.skipif(sys.platform == "win32", reason="POSIX descriptor I/O injection")
@pytest.mark.parametrize("stage", ["open", "read"])
def test_local_read_io_failure_uses_existing_home_without_generation(
    tmp_path, cache_request, monkeypatch, stage
):
    locations = CacheLocationPolicy(user_root=tmp_path / "home").locations_for(
        cache_request.namespace, SourceOrigin(tmp_path / "models.py", "models")
    )
    for location in locations:
        GeneratedCodeCache(location.directory, enabled=True).get(
            cache_request, lambda: code_for(cache_request)
        )
    original_open, original_fdopen = os.open, os.fdopen
    local_descriptors = set()

    def checked_open(path, flags, *args, **kwargs):
        parent = kwargs.get("dir_fd")
        local = (
            parent is not None
            and os.fstat(parent).st_ino == locations[0].directory.stat().st_ino
        )
        artifact = str(path).endswith(".ycode")
        if stage == "open" and local and artifact:
            raise OSError(errno.EIO, "injected read access failure")
        descriptor = original_open(path, flags, *args, **kwargs)
        if local and artifact:
            local_descriptors.add(descriptor)
        return descriptor

    class BrokenStream:
        def __init__(self, stream):
            self.stream = stream

        def __enter__(self):
            return self

        def __exit__(self, *args):
            self.stream.close()

        def read(self, *args):
            raise OSError(errno.EIO, "injected stream failure")

    def checked_fdopen(descriptor, *args, **kwargs):
        stream = original_fdopen(descriptor, *args, **kwargs)
        local = descriptor in local_descriptors
        local_descriptors.discard(descriptor)
        return BrokenStream(stream) if stage == "read" and local else stream

    monkeypatch.setattr(os, "open", checked_open)
    monkeypatch.setattr(os, "fdopen", checked_fdopen)
    cache = GeneratedCodeCache(enabled=True, memory_capacity=0)
    result = cache.get(
        cache_request, lambda: pytest.fail("home should hit"), locations=locations
    )
    assert isinstance(result, CacheHit)
    evidence = cache.diagnostics[-1]
    assert evidence.selected == locations[1] and evidence.attempted == locations
    assert not evidence.generated and len(evidence.failures) == 1
    assert evidence.failures[0].problem.kind is CacheStorageError
    assert evidence.rejected_entry is None


@pytest.mark.skipif(sys.platform != "darwin", reason="macOS ACL backend")
def test_unavailable_ctypes_bypasses_both_candidates(
    tmp_path, cache_request, monkeypatch
):
    original = builtins.__import__

    def unavailable(name, *args, **kwargs):
        if name == "ctypes":
            raise ImportError("No module named '_ctypes'")
        return original(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", unavailable)
    locations = CacheLocationPolicy(user_root=tmp_path / "home").locations_for(
        cache_request.namespace, SourceOrigin(tmp_path / "models.py", "models")
    )
    calls = []
    cache = GeneratedCodeCache(enabled=True)
    result = cache.get(
        cache_request,
        lambda: calls.append(1) or code_for(cache_request),
        locations=locations,
    )
    assert isinstance(result, CacheBypass) and calls == [1]
    assert cache.statistics.bypasses == 1
    assert len(cache.diagnostics[-1].failures) == 2
    assert all(
        item.problem.kind is CacheStorageError
        for item in cache.diagnostics[-1].failures
    )
    assert not list(tmp_path.rglob("*.ycode"))


@pytest.mark.skipif(
    not hasattr(os, "getuid") or os.getuid() == 0,
    reason="requires non-root directory access checks",
)
@pytest.mark.parametrize("tracked", [False, True])
def test_inaccessible_clear_reports_failure_and_drains_process_state(
    tmp_path, cache_request, tracked
):
    root = tmp_path / "cache"
    directory = root / "entries"
    seeded = GeneratedCodeCache(directory, enabled=True)
    seeded.get(cache_request, lambda: code_for(cache_request))
    artifact = next(directory.glob("*.ycode"))
    neighbor = root / "keep.txt"
    neighbor.write_text("keep")
    cache = seeded if tracked else GeneratedCodeCache(directory, enabled=True)
    if tracked:

        def change():
            (tmp_path / "generator.py").write_text("changed dependency\n")
            return code_for(cache_request)

        cache.get(replace(cache_request, input_digest="f" * 64), change)
        assert cache._memory and cache._preferences and cache.diagnostics
    counters = cache.statistics
    fences = set(cache._disabled_producers)
    root.chmod(0)
    try:
        with pytest.raises(CacheLocationError) as caught:
            cache.clear()
    finally:
        root.chmod(0o700)
    failures = caught.value.failures
    assert len(failures) == 1 and failures[0].problem.kind is CacheStorageError
    assert not cache._memory and not cache._preferences and not cache.diagnostics
    assert cache.statistics == counters and cache._disabled_producers == fences
    assert artifact.is_file() and neighbor.read_text() == "keep"
    assert cache.clear() == 1
    if tracked:
        result = cache.get(cache_request, lambda: code_for(cache_request))
        assert isinstance(result, CacheBypass)
        assert isinstance(result.reason, CacheDependencyError)


def test_clear_absent_directory_does_not_create_storage(tmp_path):
    directory = tmp_path / "absent" / "entries"
    assert GeneratedCodeCache(directory, enabled=True).clear() == 0
    assert not directory.parent.exists()
