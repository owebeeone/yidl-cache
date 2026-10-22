from __future__ import annotations

import os
from pathlib import Path
import subprocess
import sys

import pytest

from yidl_cache import (
    CacheArtifactError,
    CacheBypass,
    CacheHit,
    CacheLocationError,
    CacheMiss,
    CacheStorageError,
    GeneratedCodeCache,
)

pytestmark = pytest.mark.skipif(sys.platform != "win32", reason="Windows storage")


def code_for(request):
    return compile("value = 7", request.compilation.filename, "exec", dont_inherit=True)


def acl(path, *arguments):
    subprocess.run(["icacls", str(path), *arguments], check=True, capture_output=True)


@pytest.mark.parametrize("target", ["directory", "artifact"])
def test_untrusted_read_access_is_never_deserialized(
    tmp_path, cache_request, monkeypatch, target
):
    import marshal

    directory = tmp_path / "cache"
    seeded = GeneratedCodeCache(directory, enabled=True, memory_capacity=0)
    assert isinstance(
        seeded.get(cache_request, lambda: code_for(cache_request)), CacheMiss
    )
    artifact = next(directory.glob("*.ycode"))
    path = directory if target == "directory" else artifact
    acl(path, "/grant", "*S-1-1-0:(R)")
    before = subprocess.check_output(["icacls", str(path)])
    monkeypatch.setattr(
        marshal, "loads", lambda _: pytest.fail("unsafe deserialization")
    )
    result = seeded.get(cache_request, lambda: code_for(cache_request))
    if target == "directory":
        assert isinstance(result, CacheBypass)
        assert isinstance(result.reason, CacheLocationError)
        assert "untrusted principal" in result.reason.failures[0].problem.message
        assert subprocess.check_output(["icacls", str(path)]) == before
    else:
        assert isinstance(result, CacheMiss)
        assert isinstance(result.rejected_entry, CacheArtifactError)


@pytest.mark.parametrize("parent", [False, True])
def test_junctions_bypass_without_touching_targets(tmp_path, cache_request, parent):
    outside = tmp_path / "outside"
    outside.mkdir()
    link = tmp_path / "junction"
    subprocess.run(
        ["cmd", "/d", "/c", "mklink", "/J", str(link), str(outside)],
        check=True,
        capture_output=True,
    )
    try:
        directory = link / "entries" if parent else link
        result = GeneratedCodeCache(directory, enabled=True).get(
            cache_request, lambda: code_for(cache_request)
        )
        assert isinstance(result, CacheBypass)
        assert isinstance(result.reason, CacheLocationError)
        assert not list(outside.iterdir())
        with pytest.raises(CacheLocationError):
            GeneratedCodeCache(directory).clear()
    finally:
        link.rmdir()


def test_hardlink_entry_is_replaced_without_reading_target(
    tmp_path, cache_request, monkeypatch
):
    import marshal

    directory = tmp_path / "cache"
    seed = GeneratedCodeCache(directory, enabled=True)
    assert isinstance(
        seed.get(cache_request, lambda: code_for(cache_request)), CacheMiss
    )
    artifact = next(directory.glob("*.ycode"))
    outside = tmp_path / "outside"
    os.link(artifact, outside)
    before = outside.read_bytes()
    monkeypatch.setattr(
        marshal, "loads", lambda _: pytest.fail("hard-link deserialization")
    )
    result = GeneratedCodeCache(directory, enabled=True).get(
        cache_request, lambda: code_for(cache_request)
    )
    assert isinstance(result, CacheMiss)
    assert isinstance(result.rejected_entry, CacheArtifactError)
    assert outside.read_bytes() == before
    assert artifact.stat().st_nlink == outside.stat().st_nlink == 1


def test_failed_publication_cleans_private_temporary_file(
    tmp_path, cache_request, monkeypatch
):
    from yidl_cache import windows_storage

    def fail(*args):
        raise OSError("injected publication failure")

    monkeypatch.setattr(windows_storage, "replace", fail)
    directory = tmp_path / "cache"
    result = GeneratedCodeCache(directory, enabled=True).get(
        cache_request, lambda: code_for(cache_request)
    )
    assert isinstance(result, CacheBypass)
    assert isinstance(result.reason, CacheStorageError)
    assert not list(directory.iterdir())


def test_open_ancestors_and_entry_remain_bound_during_read(
    tmp_path, cache_request, monkeypatch
):
    from yidl_cache import windows_storage

    directory = tmp_path / "cache"
    assert isinstance(
        GeneratedCodeCache(directory, enabled=True).get(
            cache_request, lambda: code_for(cache_request)
        ),
        CacheMiss,
    )
    original = windows_storage.read_bytes
    attempts = []

    def attempt_replacement(handle, maximum):
        for source in (directory, tmp_path, next(directory.glob("*.ycode"))):
            with pytest.raises(PermissionError):
                source.rename(source.with_name(source.name + "-moved"))
            attempts.append(source)
        return original(handle, maximum)

    monkeypatch.setattr(windows_storage, "read_bytes", attempt_replacement)
    result = GeneratedCodeCache(directory, enabled=True, memory_capacity=0).get(
        cache_request, lambda: pytest.fail("must read existing entry")
    )
    assert isinstance(result, CacheHit)
    assert len(attempts) == 3


def test_untrusted_ancestor_cannot_propagate_permissions(tmp_path, cache_request):
    parent = tmp_path / "ancestor"
    parent.mkdir()
    acl(parent, "/grant", "*S-1-1-0:(WDAC)")
    directory = parent / "cache"
    result = GeneratedCodeCache(directory, enabled=True).get(
        cache_request, lambda: code_for(cache_request)
    )
    assert isinstance(result, CacheBypass)
    assert "untrusted principal" in result.reason.failures[0].problem.message
    assert not directory.exists()


def test_denied_access_is_typed_and_maintenance_does_not_escape(
    tmp_path, cache_request
):
    from yidl_cache.windows_api import api

    directory = tmp_path / "cache"
    assert isinstance(
        GeneratedCodeCache(directory, enabled=True).get(
            cache_request, lambda: code_for(cache_request)
        ),
        CacheMiss,
    )
    artifact = next(directory.glob("*.ycode"))
    before = artifact.read_bytes()
    principal = "*" + api().user_sid()
    acl(directory, "/deny", principal + ":(RD)")
    try:
        cache = GeneratedCodeCache(directory, enabled=True)
        result = cache.get(cache_request, lambda: code_for(cache_request))
        assert isinstance(result, CacheBypass)
        with pytest.raises(CacheLocationError):
            cache.clear()
    finally:
        acl(directory, "/remove:d", principal)
    assert artifact.read_bytes() == before


def test_replaced_directory_after_admission_never_follows_junction(
    tmp_path, cache_request, monkeypatch
):
    from yidl_cache.windows_storage import WindowsStorage

    directory = tmp_path / "cache"
    original = directory.with_name("original")
    outside = tmp_path / "outside"
    outside.mkdir()
    read = WindowsStorage.read

    def replace_before_read(self, *args):
        directory.rename(original)
        subprocess.run(
            ["cmd", "/d", "/c", "mklink", "/J", str(directory), str(outside)],
            check=True,
            capture_output=True,
        )
        return read(self, *args)

    monkeypatch.setattr(WindowsStorage, "read", replace_before_read)
    try:
        result = GeneratedCodeCache(directory, enabled=True).get(
            cache_request, lambda: code_for(cache_request)
        )
        assert isinstance(result, CacheBypass)
        assert not list(outside.iterdir())
        assert not list(original.iterdir())
    finally:
        if directory.is_junction():
            directory.rmdir()


@pytest.mark.parametrize("phase", ["admission", "temporary"])
def test_failed_trust_inspection_cleans_new_objects(
    tmp_path, cache_request, monkeypatch, phase
):
    from yidl_cache import windows_storage

    original = windows_storage.require_private

    def fail(handle, user, **kwargs):
        if not kwargs.get("ancestor"):
            info = windows_storage.FileInformation()
            system = windows_storage.api()
            system.check(
                system.kernel.GetFileInformationByHandle(
                    handle, windows_storage.c.byref(info)
                )
            )
            if not info.attributes & 0x10:
                raise CacheStorageError("injected trust API failure")
        return original(handle, user, **kwargs)

    directory = tmp_path / "cache"
    if phase == "temporary":
        windows_storage.WindowsStorage(directory).admit()
        monkeypatch.setattr(windows_storage.WindowsStorage, "admit", lambda _: None)
    monkeypatch.setattr(windows_storage, "require_private", fail)
    result = GeneratedCodeCache(directory, enabled=True).get(
        cache_request, lambda: code_for(cache_request)
    )
    assert isinstance(result, CacheBypass)
    assert not list(directory.iterdir())


def test_long_path_maintenance_uses_handles_and_keeps_neighbors(
    tmp_path, cache_request
):
    directory = tmp_path.joinpath(*("component-" + str(i) + "x" * 40 for i in range(5)))
    result = GeneratedCodeCache(directory, enabled=True).get(
        cache_request, lambda: code_for(cache_request)
    )
    assert isinstance(result, CacheMiss)
    extended = Path("\\\\?\\" + str(directory))
    neighbor = extended / "keep.txt"
    neighbor.write_text("keep")
    assert GeneratedCodeCache(directory).clear() == 1
    assert list(extended.iterdir()) == [neighbor]


def test_maintenance_enumerates_multiple_buffers_without_crawling(tmp_path):
    from yidl_cache.windows_storage import WindowsStorage

    directory = tmp_path / "cache"
    WindowsStorage(directory).admit()
    for i in range(600):
        (directory / (".probe-" + f"{i:024x}" + ".tmp")).write_bytes(b"")
    neighbor = directory / "keep"
    neighbor.mkdir()
    sentinel = neighbor / ("a" * 64 + ".ycode")
    sentinel.write_text("keep")
    assert GeneratedCodeCache(directory).clear() == 600
    assert sentinel.read_text() == "keep"


def test_probe_cleanup_failure_is_bounded_and_maintainable(
    tmp_path, cache_request, monkeypatch
):
    from yidl_cache import windows_storage

    original = windows_storage.delete
    calls = []

    def fail(handle):
        calls.append(1)
        raise OSError("injected probe cleanup failure")

    directory = tmp_path / "cache"
    monkeypatch.setattr(windows_storage, "delete", fail)
    cache = GeneratedCodeCache(directory, enabled=True)
    result = cache.get(cache_request, lambda: code_for(cache_request))
    assert isinstance(result, CacheBypass)
    assert calls == [1]
    monkeypatch.setattr(windows_storage, "delete", original)
    assert cache.clear() == 1
    assert not list(directory.iterdir())


def test_physical_size_bound_precedes_read(tmp_path, cache_request, monkeypatch):
    from yidl_cache.windows_api import api

    directory = tmp_path / "cache"
    assert isinstance(
        GeneratedCodeCache(directory, enabled=True).get(
            cache_request, lambda: code_for(cache_request)
        ),
        CacheMiss,
    )
    artifact = next(directory.glob("*.ycode"))
    artifact.write_bytes(b"x" * (32 * 1024))
    monkeypatch.setattr(
        api().kernel, "ReadFile", lambda *args: pytest.fail("oversized read")
    )
    result = GeneratedCodeCache(directory, enabled=True, max_payload_bytes=1024).get(
        cache_request, lambda: code_for(cache_request)
    )
    assert isinstance(result, CacheMiss)
    assert isinstance(result.rejected_entry, CacheArtifactError)


def test_missing_trust_api_bypasses_before_creating_storage(
    tmp_path, cache_request, monkeypatch
):
    from yidl_cache import windows_api

    def unavailable():
        raise AttributeError("missing Windows trust API")

    monkeypatch.setattr(windows_api, "api", unavailable)
    directory = tmp_path / "cache"
    result = GeneratedCodeCache(directory, enabled=True).get(
        cache_request, lambda: code_for(cache_request)
    )
    assert isinstance(result, CacheBypass)
    assert "APIs are unavailable" in result.reason.failures[0].problem.message
    assert not directory.exists()


def test_unknown_filesystem_bypasses_before_creating_storage(
    tmp_path, cache_request, monkeypatch
):
    from ctypes import cast, POINTER, wintypes
    from yidl_cache.windows_api import api

    def unsupported(
        handle, volume, length, serial, component, flags, filesystem, capacity
    ):
        filesystem.value = "unknown"
        cast(flags, POINTER(wintypes.DWORD)).contents.value = 0
        return True

    monkeypatch.setattr(api().kernel, "GetVolumeInformationByHandleW", unsupported)
    directory = tmp_path / "cache"
    result = GeneratedCodeCache(directory, enabled=True).get(
        cache_request, lambda: code_for(cache_request)
    )
    assert isinstance(result, CacheBypass)
    assert "NTFS" in result.reason.failures[0].problem.message
    assert not directory.exists()


@pytest.mark.parametrize("network", [True, False])
def test_network_and_device_namespaces_bypass_before_io(
    network, cache_request, monkeypatch
):
    from yidl_cache.windows_api import api

    components = (
        ("unused-server", "unused-share", "cache")
        if network
        else (".", "pipe", "cache")
    )
    directory = Path(os.sep * 2 + os.sep.join(components))
    monkeypatch.setattr(
        api().kernel, "GetDriveTypeW", lambda *_: pytest.fail("namespace I/O")
    )
    result = GeneratedCodeCache(directory, enabled=True).get(
        cache_request, lambda: code_for(cache_request)
    )
    assert isinstance(result, CacheBypass)
    assert "local drive path" in result.reason.failures[0].problem.message


def test_maintenance_ignores_unrelated_non_unicode_filename(tmp_path):
    from yidl_cache.windows_storage import WindowsStorage

    directory = tmp_path / "cache"
    WindowsStorage(directory).admit()
    unrelated = directory / "keep-\udcff"
    unrelated.write_bytes(b"keep")
    assert GeneratedCodeCache(directory).clear() == 0
    assert unrelated.read_bytes() == b"keep"


def test_non_bmp_path_component_is_opened_without_truncation(tmp_path, cache_request):
    directory = tmp_path / "music-\U0001d11e"
    cache = GeneratedCodeCache(directory, enabled=True, memory_capacity=0)
    assert isinstance(
        cache.get(cache_request, lambda: code_for(cache_request)), CacheMiss
    )
    assert directory.is_dir()
    assert cache.clear() == 1


def test_unsafe_local_acl_uses_home_without_repair(tmp_path, cache_request):
    from yidl_cache import CacheLocationPolicy, SourceOrigin
    from yidl_cache.windows_storage import WindowsStorage

    locations = CacheLocationPolicy(user_root=tmp_path / "home").locations_for(
        cache_request.namespace, SourceOrigin(tmp_path / "models.py", "models")
    )
    local = locations[0].directory
    WindowsStorage(local).admit()
    acl(local, "/grant", "*S-1-1-0:(R)")
    before = subprocess.check_output(["icacls", str(local)])
    cache = GeneratedCodeCache(enabled=True, memory_capacity=0)
    result = cache.get(
        cache_request, lambda: code_for(cache_request), locations=locations
    )
    assert isinstance(result, CacheMiss)
    evidence = cache.diagnostics[-1]
    assert evidence.selected == locations[1]
    assert len(evidence.failures) == 1
    assert "untrusted principal" in evidence.failures[0].problem.message
    assert subprocess.check_output(["icacls", str(local)]) == before
    assert not list(local.iterdir())


def test_reparse_entry_never_reads_or_clears_target(
    tmp_path, cache_request, monkeypatch
):
    import marshal

    directory = tmp_path / "cache"
    assert isinstance(
        GeneratedCodeCache(directory, enabled=True).get(
            cache_request, lambda: code_for(cache_request)
        ),
        CacheMiss,
    )
    artifact = next(directory.glob("*.ycode"))
    artifact.unlink()
    outside = tmp_path / "outside"
    outside.mkdir()
    sentinel = outside / "keep.txt"
    sentinel.write_text("keep")
    subprocess.run(
        ["cmd", "/d", "/c", "mklink", "/J", str(artifact), str(outside)],
        check=True,
        capture_output=True,
    )
    monkeypatch.setattr(
        marshal, "loads", lambda _: pytest.fail("reparse deserialization")
    )
    try:
        cache = GeneratedCodeCache(directory, enabled=True)
        result = cache.get(cache_request, lambda: code_for(cache_request))
        assert isinstance(result, CacheBypass)
        with pytest.raises(CacheLocationError):
            cache.clear()
        assert sentinel.read_text() == "keep"
    finally:
        artifact.rmdir()
