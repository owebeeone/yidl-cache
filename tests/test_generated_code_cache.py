from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
from threading import Barrier
from types import CodeType

import pytest

from yidl_cache import CacheBypass
from yidl_cache import CacheDependencyError
from yidl_cache import CacheDisabledError
from yidl_cache import CacheHit
from yidl_cache import CacheMiss
from yidl_cache import CacheReentryError
from yidl_cache import CacheRequest
from yidl_cache import CacheStorageError
from yidl_cache import DependencyInventory
from yidl_cache import GeneratedCodeCache


def produce(cache_request: CacheRequest) -> CodeType:
    return compile(
        "answer = 42",
        cache_request.compilation.filename,
        "exec",
        flags=cache_request.compilation.flags,
        dont_inherit=cache_request.compilation.dont_inherit,
        optimize=cache_request.compilation.optimize,
    )


@pytest.mark.skipif(os.name != "posix", reason="persistent trust checks are POSIX-only")
def test_independent_record_fixture_reuses_code_in_a_fresh_process(
    tmp_path: Path,
) -> None:
    project = Path(__file__).resolve().parents[1]
    fixture = project / "tests" / "fixtures" / "record_process.py"
    environment = dict(os.environ, PYTHONPATH=str(project / "src"))

    def run(value: int, forbid_generation: str) -> dict[str, object]:
        result = subprocess.run(
            [
                sys.executable,
                str(fixture),
                str(tmp_path / "cache"),
                str(value),
                forbid_generation,
            ],
            cwd=tmp_path,
            env=environment,
            text=True,
            capture_output=True,
            check=True,
        )
        return json.loads(result.stdout)

    assert run(10, "no") == {
        "result": "CacheMiss",
        "generation_calls": 1,
        "values": [10, 11],
        "consumer_imports": [],
    }
    assert run(99, "yes") == {
        "result": "CacheHit",
        "generation_calls": 0,
        "values": [99, 100],
        "consumer_imports": [],
    }


def test_disabled_cache_does_not_create_storage(
    tmp_path: Path, cache_request: CacheRequest
) -> None:
    directory = tmp_path / "cache"
    cache = GeneratedCodeCache(directory)
    result = cache.get(cache_request, lambda: produce(cache_request))
    assert isinstance(result, CacheBypass)
    assert isinstance(result.reason, CacheDisabledError)
    assert not directory.exists()
    assert cache.statistics.bypasses == 1


def test_missing_dependency_inventory_bypasses(
    tmp_path: Path, cache_request: CacheRequest
) -> None:
    cache = GeneratedCodeCache(tmp_path / "cache", enabled=True)
    result = cache.get(
        replace(cache_request, dependencies=None), lambda: produce(cache_request)
    )
    assert isinstance(result, CacheBypass)
    assert isinstance(result.reason, CacheDependencyError)


@pytest.mark.parametrize(
    "error", [ValueError("generation"), SystemExit("exit"), KeyboardInterrupt()]
)
def test_producer_errors_propagate_unchanged(
    tmp_path: Path, cache_request: CacheRequest, error: BaseException
) -> None:
    cache = GeneratedCodeCache(tmp_path / "cache", enabled=True)

    def fail() -> CodeType:
        raise error

    with pytest.raises(type(error)) as caught:
        cache.get(cache_request, fail)
    assert caught.value is error
    assert (
        cache.statistics.hits
        == cache.statistics.misses
        == cache.statistics.bypasses
        == 0
    )


def test_storage_failure_preserves_generated_code(
    tmp_path: Path, cache_request: CacheRequest
) -> None:
    occupied = tmp_path / "not-a-directory"
    occupied.write_text("unrelated", encoding="utf-8")
    cache = GeneratedCodeCache(occupied, enabled=True)
    code = produce(cache_request)
    result = cache.get(cache_request, lambda: code)
    assert isinstance(result, CacheBypass)
    assert isinstance(result.reason, CacheStorageError)
    assert result.code is code
    assert occupied.read_text(encoding="utf-8") == "unrelated"


@pytest.mark.skipif(os.name != "posix", reason="persistent trust checks are POSIX-only")
def test_dependency_edit_suppresses_publication_until_restart(
    tmp_path: Path, cache_request: CacheRequest
) -> None:
    cache = GeneratedCodeCache(tmp_path / "cache", enabled=True)
    dependency = tmp_path / "generator.py"

    def edit_during_generation() -> CodeType:
        dependency.write_text("changed generator revision\n", encoding="utf-8")
        return produce(cache_request)

    result = cache.get(cache_request, edit_during_generation)
    assert isinstance(result, CacheBypass)
    assert isinstance(result.reason, CacheDependencyError)
    assert not list((tmp_path / "cache").glob("*.ycode"))
    fresh_inventory = DependencyInventory.capture({"generator": dependency})
    changed_request = replace(cache_request, dependencies=fresh_inventory)
    assert isinstance(
        cache.get(changed_request, lambda: produce(cache_request)), CacheBypass
    )
    restarted = GeneratedCodeCache(tmp_path / "cache", enabled=True)
    assert isinstance(
        restarted.get(changed_request, lambda: produce(cache_request)), CacheMiss
    )


@pytest.mark.skipif(os.name != "posix", reason="persistent trust checks are POSIX-only")
def test_same_key_reentry_does_not_deadlock(
    tmp_path: Path, cache_request: CacheRequest
) -> None:
    cache = GeneratedCodeCache(tmp_path / "cache", enabled=True)
    inner_results = []

    def reenter() -> CodeType:
        inner_results.append(cache.get(cache_request, lambda: produce(cache_request)))
        return produce(cache_request)

    assert isinstance(cache.get(cache_request, reenter), CacheMiss)
    assert isinstance(inner_results[0], CacheBypass)
    assert isinstance(inner_results[0].reason, CacheReentryError)


@pytest.mark.skipif(os.name != "posix", reason="persistent trust checks are POSIX-only")
def test_different_key_recursion_is_allowed(
    tmp_path: Path, cache_request: CacheRequest
) -> None:
    cache = GeneratedCodeCache(tmp_path / "cache", enabled=True)
    inner = replace(cache_request, input_digest=hashlib.sha256(b"inner").hexdigest())

    def reenter() -> CodeType:
        assert isinstance(cache.get(inner, lambda: produce(inner)), CacheMiss)
        return produce(cache_request)

    assert isinstance(cache.get(cache_request, reenter), CacheMiss)
    assert cache.statistics.misses == 2


@pytest.mark.skipif(os.name != "posix", reason="persistent trust checks are POSIX-only")
def test_concurrent_misses_publish_complete_entries(
    tmp_path: Path, cache_request: CacheRequest
) -> None:
    directory = tmp_path / "cache"
    rendezvous = Barrier(2)

    def run() -> object:
        cache = GeneratedCodeCache(directory, enabled=True, memory_capacity=0)

        def wait_and_generate() -> CodeType:
            rendezvous.wait(timeout=10)
            return produce(cache_request)

        return cache.get(cache_request, wait_and_generate)

    with ThreadPoolExecutor(max_workers=2) as executor:
        futures = [executor.submit(run) for _ in range(2)]
        assert all(
            isinstance(future.result(timeout=15), CacheMiss) for future in futures
        )
    cache = GeneratedCodeCache(directory, enabled=True, memory_capacity=0)
    assert isinstance(
        cache.get(cache_request, lambda: pytest.fail("must reuse complete entry")),
        CacheHit,
    )
    assert not list(directory.glob("*.tmp"))


@pytest.mark.skipif(os.name != "posix", reason="persistent trust checks are POSIX-only")
def test_memory_cache_is_bounded_and_clear_is_explicit(
    tmp_path: Path, cache_request: CacheRequest
) -> None:
    cache = GeneratedCodeCache(tmp_path / "cache", enabled=True, memory_capacity=1)
    second = replace(cache_request, input_digest=hashlib.sha256(b"second").hexdigest())
    first_code = cache.get(cache_request, lambda: produce(cache_request)).code
    cache.get(second, lambda: produce(second))
    assert (
        cache.get(cache_request, lambda: pytest.fail("disk entry should exist")).code
        is not first_code
    )
    assert cache.clear() == 2
    assert isinstance(
        cache.get(cache_request, lambda: produce(cache_request)), CacheMiss
    )


@pytest.mark.skipif(os.name != "posix", reason="persistent trust checks are POSIX-only")
def test_namespace_and_compile_context_are_part_of_the_key(
    tmp_path: Path, cache_request: CacheRequest
) -> None:
    cache = GeneratedCodeCache(tmp_path / "cache", enabled=True, memory_capacity=0)
    variants = (
        cache_request,
        replace(cache_request, namespace="other.records"),
        replace(
            cache_request, compilation=replace(cache_request.compilation, optimize=1)
        ),
        replace(
            cache_request,
            compilation=replace(cache_request.compilation, filename="<another-record>"),
        ),
    )
    for variant in variants:
        assert isinstance(cache.get(variant, lambda: produce(variant)), CacheMiss)
    assert len(list((tmp_path / "cache").glob("*.ycode"))) == len(variants)
