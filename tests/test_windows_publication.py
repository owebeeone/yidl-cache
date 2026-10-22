from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
import sys
from threading import Barrier, Event, Lock

import pytest

from yidl_cache import (
    CacheBypass,
    CacheHit,
    CacheLocationError,
    CacheMiss,
    CacheStorageError,
    GeneratedCodeCache,
)

pytestmark = pytest.mark.skipif(
    sys.platform != "win32", reason="Windows publication sharing"
)


def test_exclusive_published_handle_allows_only_typed_sharing_bypass(
    tmp_path, cache_request, monkeypatch
):
    from yidl_cache import windows_storage

    original = windows_storage.replace
    first_published, contender_finished = Event(), Event()
    lock, rendezvous = Lock(), Barrier(2)
    order, failures = [], []

    def hold_first(handle, directory, name):
        with lock:
            first = not order
            order.append(1)
        if first:
            original(handle, directory, name)
            first_published.set()
            assert contender_finished.wait(10), "contender never attempted replacement"
        else:
            assert first_published.wait(10), "first writer never published"
            try:
                original(handle, directory, name)
            except OSError as error:
                failures.append(error.winerror)
                raise
            finally:
                contender_finished.set()

    monkeypatch.setattr(windows_storage, "replace", hold_first)
    directory = tmp_path / "cache"

    def run():
        cache = GeneratedCodeCache(directory, enabled=True, memory_capacity=0)

        def produce():
            rendezvous.wait(10)
            return compile(
                "answer = 42",
                cache_request.compilation.filename,
                "exec",
                dont_inherit=True,
            )

        result = cache.get(cache_request, produce)
        return result, cache.diagnostics

    with ThreadPoolExecutor(max_workers=2) as pool:
        futures = [pool.submit(run) for _ in range(2)]
        try:
            results = [future.result(15) for future in futures]
        finally:
            contender_finished.set()
    print(
        "DETERMINISTIC_OUTCOMES",
        [type(result).__name__ for result, _ in results],
        failures,
    )
    assert sorted(type(result).__name__ for result, _ in results) == [
        "CacheBypass",
        "CacheMiss",
    ]
    assert len(failures) == 1 and failures[0] in {5, 32}
    for result, diagnostics in results:
        namespace = {}
        exec(result.code, namespace)
        assert namespace["answer"] == 42
        assert len(diagnostics) == 1
        evidence = diagnostics[0]
        assert evidence.generated and evidence.outcome is type(result)
        assert len(evidence.attempted) == 1
        if isinstance(result, CacheBypass):
            assert isinstance(result.reason, CacheLocationError)
            assert len(evidence.failures) == 1
            assert evidence.failures[0].problem.kind is CacheStorageError
            assert "publish" in evidence.failures[0].problem.message
            assert len(evidence.failures[0].problem.message) <= 1024
        else:
            assert not evidence.failures
    fresh = GeneratedCodeCache(directory, enabled=True, memory_capacity=0)
    assert isinstance(
        fresh.get(cache_request, lambda: pytest.fail("must hit")), CacheHit
    )
    assert not fresh.diagnostics[-1].generated
    assert not list(directory.glob("*.tmp"))
