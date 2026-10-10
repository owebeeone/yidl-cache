from __future__ import annotations

from dataclasses import replace
import hashlib
import json
import marshal
import os
from pathlib import Path
import struct
import subprocess
import sys
from types import SimpleNamespace
from types import CodeType

import pytest

from yidl_cache import CacheArtifactError
from yidl_cache import CacheBypass
from yidl_cache import CacheHit
from yidl_cache import CacheIdentityError
from yidl_cache import CacheMiss
from yidl_cache import CacheRequest
from yidl_cache import CacheStorageError
from yidl_cache import DependencyInventory
from yidl_cache import GeneratedCodeCache
from yidl_cache import storage

pytestmark = pytest.mark.skipif(
    os.name != "posix", reason="persistent trust checks are POSIX-only"
)


def code_for(cache_request: CacheRequest) -> CodeType:
    return compile(
        "value = 7", cache_request.compilation.filename, "exec", dont_inherit=True
    )


@pytest.fixture
def artifact(tmp_path: Path, cache_request: CacheRequest) -> Path:
    cache = GeneratedCodeCache(tmp_path / "cache", enabled=True, memory_capacity=0)
    assert isinstance(
        cache.get(cache_request, lambda: code_for(cache_request)), CacheMiss
    )
    return next((tmp_path / "cache").glob("*.ycode"))


def edit_header(data: bytes, changes: dict[str, object]) -> bytes:
    prefix = 14
    length = struct.unpack(">I", data[10:prefix])[0]
    header = json.loads(data[prefix : prefix + length])
    header.update(changes)
    updated = json.dumps(header).encode("utf-8")
    return (
        data[:10] + struct.pack(">I", len(updated)) + updated + data[prefix + length :]
    )


@pytest.mark.parametrize(
    "damage",
    ["truncated", "checksum", "header", "identity", "oversize", "unicode-checksum"],
)
def test_rejects_invalid_envelopes_before_deserialization(
    tmp_path: Path,
    cache_request: CacheRequest,
    artifact: Path,
    monkeypatch: pytest.MonkeyPatch,
    damage: str,
) -> None:
    data = artifact.read_bytes()
    if damage == "truncated":
        broken = data[:-1]
    elif damage == "checksum":
        broken = data[:-1] + bytes([data[-1] ^ 1])
    elif damage == "header":
        broken = data[:10] + struct.pack(">I", 65536) + data[14:]
    elif damage == "identity":
        broken = edit_header(data, {"identity": {}})
    elif damage == "oversize":
        broken = edit_header(data, {"length": 1 << 40})
    else:
        broken = edit_header(data, {"sha256": "\u2603"})
    artifact.write_bytes(broken)

    def forbid_load(_: bytes) -> CodeType:
        pytest.fail("invalid envelope must be rejected before marshal.loads")

    monkeypatch.setattr(marshal, "loads", forbid_load)
    cache = GeneratedCodeCache(tmp_path / "cache", enabled=True, memory_capacity=0)
    result = cache.get(cache_request, lambda: code_for(cache_request))
    assert isinstance(result, CacheMiss)
    assert isinstance(result.rejected_entry, CacheArtifactError)


def test_rejects_non_code_payload(
    tmp_path: Path, cache_request: CacheRequest, artifact: Path
) -> None:
    data = artifact.read_bytes()
    length = struct.unpack(">I", data[10:14])[0]
    header = json.loads(data[14 : 14 + length])
    payload = marshal.dumps({"not": "code"})
    header.update(length=len(payload), sha256=hashlib.sha256(payload).hexdigest())
    updated = json.dumps(header).encode("ascii")
    artifact.write_bytes(
        data[:10] + struct.pack(">I", len(updated)) + updated + payload
    )
    cache = GeneratedCodeCache(tmp_path / "cache", enabled=True, memory_capacity=0)
    result = cache.get(cache_request, lambda: code_for(cache_request))
    assert isinstance(result, CacheMiss)
    assert isinstance(result.rejected_entry, CacheArtifactError)


def test_refuses_nonprivate_directory(
    tmp_path: Path, cache_request: CacheRequest
) -> None:
    directory = tmp_path / "cache"
    directory.mkdir(mode=0o777)
    directory.chmod(0o777)
    cache = GeneratedCodeCache(directory, enabled=True)
    result = cache.get(cache_request, lambda: code_for(cache_request))
    assert isinstance(result, CacheBypass)
    assert isinstance(result.reason, CacheStorageError)
    assert directory.stat().st_mode & 0o777 == 0o777
    assert list(directory.iterdir()) == []


@pytest.mark.parametrize("parent_link", [False, True])
def test_refuses_symlink_directory_components(
    tmp_path: Path,
    cache_request: CacheRequest,
    parent_link: bool,
) -> None:
    target = tmp_path / "actual"
    target.mkdir(mode=0o700)
    link = tmp_path / "link"
    link.symlink_to(target, target_is_directory=True)
    directory = link / "cache" if parent_link else link
    result = GeneratedCodeCache(directory, enabled=True).get(
        cache_request, lambda: code_for(cache_request)
    )
    assert isinstance(result, CacheBypass)
    assert isinstance(result.reason, CacheStorageError)
    assert list(target.iterdir()) == []


def test_symlink_entry_is_replaced_without_reading_its_target(
    tmp_path: Path,
    cache_request: CacheRequest,
    artifact: Path,
) -> None:
    outside = tmp_path / "outside"
    outside.write_bytes(artifact.read_bytes())
    artifact.unlink()
    artifact.symlink_to(outside)
    before = outside.read_bytes()
    cache = GeneratedCodeCache(tmp_path / "cache", enabled=True, memory_capacity=0)
    result = cache.get(cache_request, lambda: code_for(cache_request))
    assert isinstance(result, CacheMiss)
    assert isinstance(result.rejected_entry, CacheArtifactError)
    assert not artifact.is_symlink()
    assert outside.read_bytes() == before


def test_failed_atomic_replace_cleans_temporary_file(
    tmp_path: Path,
    cache_request: CacheRequest,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fail_replace(*args: object, **kwargs: object) -> None:
        raise OSError("injected replacement failure")

    monkeypatch.setattr(os, "replace", fail_replace)
    cache = GeneratedCodeCache(tmp_path / "cache", enabled=True)
    result = cache.get(cache_request, lambda: code_for(cache_request))
    assert isinstance(result, CacheBypass)
    assert isinstance(result.reason, CacheStorageError)
    assert list((tmp_path / "cache").iterdir()) == []


def test_unsupported_constant_is_not_persisted(
    tmp_path: Path, cache_request: CacheRequest
) -> None:
    code = code_for(cache_request).replace(co_consts=({"live": "dictionary"}, None))
    result = GeneratedCodeCache(tmp_path / "cache", enabled=True).get(
        cache_request, lambda: code
    )
    assert isinstance(result, CacheBypass)
    assert isinstance(result.reason, CacheArtifactError)
    assert result.code is code
    assert not list((tmp_path / "cache").glob("*.ycode"))


def test_payload_size_bound_is_a_bypass(
    tmp_path: Path, cache_request: CacheRequest
) -> None:
    cache = GeneratedCodeCache(tmp_path / "cache", enabled=True, max_payload_bytes=1)
    result = cache.get(cache_request, lambda: code_for(cache_request))
    assert isinstance(result, CacheBypass)
    assert isinstance(result.reason, CacheArtifactError)


def test_invalid_request_digest_is_a_bypass(
    tmp_path: Path, cache_request: CacheRequest
) -> None:
    cache = GeneratedCodeCache(tmp_path / "cache", enabled=True)
    result = cache.get(
        replace(cache_request, input_digest="unknown"), lambda: code_for(cache_request)
    )
    assert isinstance(result, CacheBypass)
    assert isinstance(result.reason, CacheIdentityError)


def test_warm_hit_does_not_stat_dependencies(
    tmp_path: Path,
    cache_request: CacheRequest,
    artifact: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def forbid_stat(_: DependencyInventory) -> bool:
        pytest.fail("warm lookup must not rescan producer dependencies")

    monkeypatch.setattr(DependencyInventory, "unchanged", forbid_stat)
    cache = GeneratedCodeCache(tmp_path / "cache", enabled=True, memory_capacity=0)
    assert isinstance(
        cache.get(cache_request, lambda: pytest.fail("must hit")), CacheHit
    )


def test_clear_keeps_unrelated_files(
    tmp_path: Path, cache_request: CacheRequest, artifact: Path
) -> None:
    unrelated = artifact.parent / "keep.txt"
    unrelated.write_text("keep", encoding="utf-8")
    assert GeneratedCodeCache(artifact.parent).clear() == 1
    assert unrelated.read_text(encoding="utf-8") == "keep"


def test_fifo_entry_cannot_block_lookup(
    tmp_path: Path,
    cache_request: CacheRequest,
    artifact: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    artifact.unlink()
    os.mkfifo(artifact, mode=0o600)
    original = os.open

    def checked_open(path: object, flags: int, *args: object, **kwargs: object) -> int:
        if path == artifact.name:
            assert flags & os.O_NONBLOCK, "entry open must not block on special files"
        return original(path, flags, *args, **kwargs)

    monkeypatch.setattr(os, "open", checked_open)
    result = GeneratedCodeCache(artifact.parent, enabled=True).get(
        cache_request,
        lambda: code_for(cache_request),
    )
    assert isinstance(result, CacheMiss)
    assert isinstance(result.rejected_entry, CacheArtifactError)


def test_platform_without_trust_checks_bypasses(
    tmp_path: Path,
    cache_request: CacheRequest,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(storage, "os", SimpleNamespace(name="unsupported"))
    result = GeneratedCodeCache(tmp_path / "cache", enabled=True).get(
        cache_request,
        lambda: code_for(cache_request),
    )
    assert isinstance(result, CacheBypass)
    assert isinstance(result.reason, CacheStorageError)
    assert not (tmp_path / "cache").exists()


@pytest.mark.skipif(sys.platform != "darwin", reason="macOS ACL regression")
def test_extended_acl_cannot_override_private_directory_modes(
    tmp_path: Path,
    cache_request: CacheRequest,
) -> None:
    directory = tmp_path / "cache"
    directory.mkdir(mode=0o700)
    subprocess.run(
        ["chmod", "+a", "everyone allow read,write", str(directory)], check=True
    )
    assert directory.stat().st_mode & 0o777 == 0o700
    result = GeneratedCodeCache(directory, enabled=True).get(
        cache_request,
        lambda: code_for(cache_request),
    )
    assert isinstance(result, CacheBypass)
    assert isinstance(result.reason, CacheStorageError)
    assert list(directory.iterdir()) == []
