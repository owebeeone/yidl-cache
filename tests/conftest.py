from __future__ import annotations

import hashlib
from pathlib import Path

import pytest

from yidl_cache import CacheRequest
from yidl_cache import CompilationContext
from yidl_cache import DependencyInventory


@pytest.fixture
def cache_request(tmp_path: Path) -> CacheRequest:
    dependency = tmp_path / "generator.py"
    dependency.write_text("generator revision one\n", encoding="utf-8")
    return CacheRequest(
        namespace="tests.records",
        generator_revision="1",
        input_digest=hashlib.sha256(b"record shape one").hexdigest(),
        compilation=CompilationContext(filename="<test-record>"),
        dependencies=DependencyInventory.capture({"generator": dependency}),
    )
