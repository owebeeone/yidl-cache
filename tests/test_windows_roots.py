from __future__ import annotations

from contextlib import contextmanager
import ctypes as c
from ctypes import wintypes as w
import marshal
import os
from pathlib import Path
import subprocess
import sys

import pytest

from yidl_cache import (
    CacheBypass,
    CacheHit,
    CacheLocationError,
    CacheLocationPolicy,
    CacheMiss,
    CacheStorageError,
    GeneratedCodeCache,
    SourceOrigin,
)

pytestmark = pytest.mark.skipif(sys.platform != "win32", reason="Windows root trust")


def acl(path, *arguments):
    subprocess.run(["icacls", str(path), *arguments], check=True, capture_output=True)


def dos_devices():
    kernel = c.WinDLL("kernel32", use_last_error=True)
    kernel.GetLogicalDrives.argtypes = []
    kernel.GetLogicalDrives.restype = w.DWORD
    kernel.QueryDosDeviceW.argtypes = [w.LPCWSTR, w.LPWSTR, w.DWORD]
    kernel.QueryDosDeviceW.restype = w.DWORD
    return kernel


def mapping(kernel, letter):
    buffer = c.create_unicode_buffer(32768)
    if kernel.QueryDosDeviceW(letter, buffer, len(buffer)):
        return buffer.value
    if c.get_last_error() == 2:  # ERROR_FILE_NOT_FOUND
        return None
    raise c.WinError(c.get_last_error())


@contextmanager
def substituted_drive(target):
    kernel = dos_devices()
    occupied = kernel.GetLogicalDrives()
    assert occupied, c.WinError(c.get_last_error())
    candidates = [
        letter + ":"
        for letter in reversed("DEFGHIJKLMNOPQRSTUVWXYZ")
        if not occupied & (1 << (ord(letter) - ord("A")))
        and mapping(kernel, letter + ":") is None
    ]
    assert candidates, "no unused current-user drive letter for isolated regression"
    letter = candidates[0]
    expected = "\\??\\" + str(target)
    subprocess.run(["subst", letter, str(target)], check=True, capture_output=True)
    try:
        assert mapping(kernel, letter).casefold() == expected.casefold()
        print("MAPPING_CREATED", letter)
        yield Path(letter + os.sep)
    finally:
        current = mapping(kernel, letter)
        assert (
            current is not None and current.casefold() == expected.casefold()
        ), "test mapping changed; refusing to remove an unknown mapping"
        subprocess.run(["subst", letter, "/D"], check=True, capture_output=True)
        assert mapping(kernel, letter) is None
        print("MAPPING_REMOVED", letter)


def verify_inherited_private_object(path):
    from yidl_cache.windows_api import api
    from yidl_cache.windows_storage import require_private

    system = api()
    control_api = system.security.GetSecurityDescriptorControl
    control_api.argtypes = [w.LPVOID, c.POINTER(w.USHORT), c.POINTER(w.DWORD)]
    control_api.restype = w.BOOL
    handle = system.kernel.CreateFileW(str(path), 0x20000, 3, None, 3, 0x02000000, None)
    assert handle != c.c_void_p(-1).value, c.WinError(c.get_last_error())
    descriptor, dacl = w.LPVOID(), w.LPVOID()
    try:
        require_private(handle, system.user_sid())
        error = system.security.GetSecurityInfo(
            handle, 1, 4, None, None, c.byref(dacl), None, c.byref(descriptor)
        )
        assert error == 0, c.WinError(error)
        flags, revision = w.USHORT(), w.DWORD()
        system.check(control_api(descriptor, c.byref(flags), c.byref(revision)))
        assert not flags.value & 0x1000, "fixture must allow ACL inheritance"
    finally:
        if descriptor:
            system.kernel.LocalFree(descriptor)
        system.kernel.CloseHandle(handle)


def test_substituted_root_cannot_hide_unsafe_physical_ancestry(
    tmp_path, cache_request, monkeypatch
):
    unsafe = tmp_path / "unsafe"
    mapped = unsafe / "mapped"
    mapped.mkdir(parents=True)
    origin = SourceOrigin(None, "models")
    policy = CacheLocationPolicy(override_root=mapped / "entries")
    physical = policy.locations_for(cache_request.namespace, origin)
    code = compile(
        "value = 7", cache_request.compilation.filename, "exec", dont_inherit=True
    )
    seed = GeneratedCodeCache(enabled=True, memory_capacity=0)
    assert isinstance(
        seed.get(cache_request, lambda: code, locations=physical), CacheMiss
    )
    artifact = next(physical[0].directory.glob("*.ycode"))
    before = artifact.read_bytes()
    for path in (mapped / "entries", physical[0].directory, artifact):
        acl(path, "/inheritance:e")
        verify_inherited_private_object(path)
    acl(unsafe, "/grant", "*S-1-1-0:(WDAC)")
    try:
        calls = []

        def produce():
            calls.append(1)
            return code

        ordinary = GeneratedCodeCache(enabled=True, memory_capacity=0).get(
            cache_request, produce, locations=physical
        )
        assert isinstance(ordinary, CacheBypass) and calls == [1]
        assert "untrusted principal" in ordinary.reason.failures[0].problem.message
        print("PHYSICAL_ROUTE", type(ordinary).__name__)
        with substituted_drive(mapped) as drive:
            override = CacheLocationPolicy(
                override_root=drive / "entries"
            ).locations_for(cache_request.namespace, origin)

            def forbid_decode(_):
                pytest.fail("substituted drive reached unmarshalling")

            monkeypatch.setattr(marshal, "loads", forbid_decode)
            calls.clear()
            cache = GeneratedCodeCache(enabled=True, memory_capacity=0)
            result = cache.get(cache_request, produce, locations=override)
            assert isinstance(result, CacheBypass) and calls == [1]
            assert isinstance(result.reason, CacheLocationError)
            assert "volume root" in result.reason.failures[0].problem.message
            evidence = cache.diagnostics[-1]
            assert evidence.generated and evidence.attempted == override
            assert len(evidence.failures) == len(cache.diagnostics) == 1
            assert evidence.failures[0].problem.kind is CacheStorageError
            assert len(evidence.failures[0].problem.message) <= 1024
            with pytest.raises(CacheLocationError):
                GeneratedCodeCache(override[0].directory).clear()
            monkeypatch.undo()
            calls.clear()
            locations = CacheLocationPolicy(
                user_root=tmp_path / "trusted-home"
            ).locations_for(
                cache_request.namespace, SourceOrigin(drive / "models.py", "models")
            )
            fallback = GeneratedCodeCache(enabled=True, memory_capacity=0)
            result = fallback.get(cache_request, produce, locations=locations)
            assert isinstance(result, CacheMiss) and calls == [1]
            evidence = fallback.diagnostics[-1]
            assert evidence.selected == locations[1] and evidence.attempted == locations
            assert evidence.generated and len(evidence.failures) == 1
            assert "volume root" in evidence.failures[0].problem.message
            fresh = GeneratedCodeCache(enabled=True, memory_capacity=0)
            assert isinstance(
                fresh.get(
                    cache_request,
                    lambda: pytest.fail("home must hit"),
                    locations=locations,
                ),
                CacheHit,
            )
            assert not fresh.diagnostics[-1].generated
            assert GeneratedCodeCache(locations[1].directory).clear() == 1
            assert artifact.read_bytes() == before
            assert not list(mapped.rglob("*.tmp"))
    finally:
        acl(unsafe, "/remove:g", "*S-1-1-0")


@pytest.mark.parametrize("report", ["nonroot", "oversized", "unavailable"])
def test_unknown_anchor_report_bypasses_without_storage(
    tmp_path, cache_request, monkeypatch, report
):
    from yidl_cache.windows_api import api

    def unproven(handle, buffer, capacity, flags):
        assert flags == 1
        if report == "unavailable":
            c.set_last_error(50)  # ERROR_NOT_SUPPORTED
            return 0
        if report == "oversized":
            return capacity + 1
        buffer.value = (
            os.sep * 2
            + "?"
            + os.sep
            + "Volume{00000000-0000-0000-0000-000000000000}"
            + os.sep
            + "a"
        )
        return len(buffer.value)

    monkeypatch.setattr(api().kernel, "GetFinalPathNameByHandleW", unproven)
    monkeypatch.setattr(
        marshal, "loads", lambda _: pytest.fail("unproven root decoded")
    )
    directory = tmp_path / "cache"
    calls = []
    code = compile(
        "pass", cache_request.compilation.filename, "exec", dont_inherit=True
    )
    result = GeneratedCodeCache(directory, enabled=True).get(
        cache_request, lambda: calls.append(1) or code
    )
    assert isinstance(result, CacheBypass) and calls == [1]
    assert isinstance(result.reason, CacheLocationError)
    assert len(result.reason.failures) == 1
    assert result.reason.failures[0].problem.kind is CacheStorageError
    assert not directory.exists()
