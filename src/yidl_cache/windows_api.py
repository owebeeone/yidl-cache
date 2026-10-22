"""Handle-only Windows file/ACL primitives; loaded lazily on Windows.

The numeric values here are Windows SDK constants and information classes,
not cache result tags. Unsupported APIs/filesystems fail closed at the adapter.
"""

from __future__ import annotations

from contextlib import contextmanager
import ctypes as c
from ctypes import wintypes as w
from functools import lru_cache
from typing import Iterator


class UnicodeString(c.Structure):
    _fields_ = [("length", w.USHORT), ("maximum", w.USHORT), ("buffer", w.LPWSTR)]


class ObjectAttributes(c.Structure):
    _fields_ = [
        ("length", w.ULONG),
        ("root", w.HANDLE),
        ("name", c.POINTER(UnicodeString)),
        ("flags", w.ULONG),
        ("security", w.LPVOID),
        ("qos", w.LPVOID),
    ]


class IoStatus(c.Structure):
    _fields_ = [("status", w.LPVOID), ("information", c.c_size_t)]


class FileInformation(c.Structure):
    _fields_ = [
        ("attributes", w.DWORD),
        ("created", w.FILETIME),
        ("accessed", w.FILETIME),
        ("modified", w.FILETIME),
        ("volume", w.DWORD),
        ("size_high", w.DWORD),
        ("size_low", w.DWORD),
        ("links", w.DWORD),
        ("index_high", w.DWORD),
        ("index_low", w.DWORD),
    ]


class RenameInformation(c.Structure):
    _fields_ = [
        ("replace", w.BYTE),
        ("root", w.HANDLE),
        ("length", w.DWORD),
        ("name", w.WCHAR * 1),
    ]


class DirectoryInformation(c.Structure):
    _fields_ = [
        ("next", w.DWORD),
        ("index", w.DWORD),
        ("created", c.c_longlong),
        ("accessed", c.c_longlong),
        ("modified", c.c_longlong),
        ("changed", c.c_longlong),
        ("size", c.c_longlong),
        ("allocation", c.c_longlong),
        ("attributes", w.DWORD),
        ("name_length", w.DWORD),
        ("ea_size", w.DWORD),
        ("short_length", w.BYTE),
        ("short_name", w.WCHAR * 12),
        ("file_id", c.c_longlong),
        ("name", w.WCHAR * 1),
    ]


class Acl(c.Structure):
    _fields_ = [
        ("revision", w.BYTE),
        ("reserved", w.BYTE),
        ("size", w.USHORT),
        ("count", w.USHORT),
        ("reserved2", w.USHORT),
    ]


class AceHeader(c.Structure):
    _fields_ = [("kind", w.BYTE), ("flags", w.BYTE), ("size", w.USHORT)]


class WindowsApi:
    def __init__(self) -> None:
        self.kernel = c.WinDLL("kernel32", use_last_error=True)
        self.security = c.WinDLL("advapi32", use_last_error=True)
        self.native = c.WinDLL("ntdll")
        self._bind(
            self.kernel,
            "CreateFileW",
            w.HANDLE,
            w.LPCWSTR,
            w.DWORD,
            w.DWORD,
            w.LPVOID,
            w.DWORD,
            w.DWORD,
            w.HANDLE,
        )
        self._bind(self.kernel, "CloseHandle", w.BOOL, w.HANDLE)
        self._bind(self.kernel, "LocalFree", w.LPVOID, w.LPVOID)
        self._bind(self.kernel, "GetCurrentProcess", w.HANDLE)
        self._bind(self.kernel, "GetCurrentThread", w.HANDLE)
        self._bind(self.kernel, "GetFileType", w.DWORD, w.HANDLE)
        self._bind(self.kernel, "GetDriveTypeW", w.UINT, w.LPCWSTR)
        self._bind(
            self.kernel,
            "GetFileInformationByHandle",
            w.BOOL,
            w.HANDLE,
            c.POINTER(FileInformation),
        )
        self._bind(
            self.kernel,
            "GetVolumeInformationByHandleW",
            w.BOOL,
            w.HANDLE,
            w.LPWSTR,
            w.DWORD,
            w.LPVOID,
            w.LPVOID,
            c.POINTER(w.DWORD),
            w.LPWSTR,
            w.DWORD,
        )
        self._bind(
            self.kernel,
            "GetFileInformationByHandleEx",
            w.BOOL,
            w.HANDLE,
            c.c_int,
            w.LPVOID,
            w.DWORD,
        )
        self._bind(
            self.kernel,
            "SetFileInformationByHandle",
            w.BOOL,
            w.HANDLE,
            c.c_int,
            w.LPVOID,
            w.DWORD,
        )
        self._bind(
            self.kernel,
            "ReadFile",
            w.BOOL,
            w.HANDLE,
            w.LPVOID,
            w.DWORD,
            c.POINTER(w.DWORD),
            w.LPVOID,
        )
        self._bind(
            self.kernel,
            "WriteFile",
            w.BOOL,
            w.HANDLE,
            w.LPVOID,
            w.DWORD,
            c.POINTER(w.DWORD),
            w.LPVOID,
        )
        self._bind(self.kernel, "FlushFileBuffers", w.BOOL, w.HANDLE)
        self._bind(
            self.security,
            "OpenProcessToken",
            w.BOOL,
            w.HANDLE,
            w.DWORD,
            c.POINTER(w.HANDLE),
        )
        self._bind(
            self.security,
            "OpenThreadToken",
            w.BOOL,
            w.HANDLE,
            w.DWORD,
            w.BOOL,
            c.POINTER(w.HANDLE),
        )
        self._bind(
            self.security,
            "GetTokenInformation",
            w.BOOL,
            w.HANDLE,
            c.c_int,
            w.LPVOID,
            w.DWORD,
            c.POINTER(w.DWORD),
        )
        self._bind(
            self.security,
            "ConvertSidToStringSidW",
            w.BOOL,
            w.LPVOID,
            c.POINTER(w.LPWSTR),
        )
        self._bind(
            self.security,
            "ConvertStringSecurityDescriptorToSecurityDescriptorW",
            w.BOOL,
            w.LPCWSTR,
            w.DWORD,
            c.POINTER(w.LPVOID),
            w.LPVOID,
        )
        self._bind(
            self.security,
            "GetSecurityInfo",
            w.DWORD,
            w.HANDLE,
            c.c_int,
            w.DWORD,
            c.POINTER(w.LPVOID),
            w.LPVOID,
            c.POINTER(w.LPVOID),
            w.LPVOID,
            c.POINTER(w.LPVOID),
        )
        self._bind(self.security, "IsValidSecurityDescriptor", w.BOOL, w.LPVOID)
        self._bind(self.security, "IsValidAcl", w.BOOL, w.LPVOID)
        self._bind(self.security, "IsValidSid", w.BOOL, w.LPVOID)
        self._bind(
            self.security, "GetAce", w.BOOL, w.LPVOID, w.DWORD, c.POINTER(w.LPVOID)
        )
        self._bind(
            self.native,
            "NtCreateFile",
            w.LONG,
            c.POINTER(w.HANDLE),
            w.DWORD,
            c.POINTER(ObjectAttributes),
            c.POINTER(IoStatus),
            w.LPVOID,
            w.ULONG,
            w.ULONG,
            w.ULONG,
            w.ULONG,
            w.LPVOID,
            w.ULONG,
        )
        self._bind(
            self.native,
            "NtSetInformationFile",
            w.LONG,
            w.HANDLE,
            c.POINTER(IoStatus),
            w.LPVOID,
            w.ULONG,
            c.c_int,
        )
        self._bind(self.native, "RtlNtStatusToDosError", w.ULONG, w.LONG)

    @staticmethod
    def _bind(library: c.CDLL, name: str, result: type, *arguments: type) -> None:
        function = getattr(library, name)
        function.restype = result
        function.argtypes = list(arguments)

    @staticmethod
    def check(success: object) -> None:
        if not success:
            raise c.WinError(c.get_last_error())

    def check_status(self, status: int) -> None:
        if status < 0:
            raise c.WinError(self.native.RtlNtStatusToDosError(status))

    def sid(self, pointer: int) -> str:
        self.check(self.security.IsValidSid(pointer))
        result = w.LPWSTR()
        self.check(self.security.ConvertSidToStringSidW(pointer, c.byref(result)))
        try:
            assert result.value is not None
            return result.value
        finally:
            self.kernel.LocalFree(result)

    def user_sid(self) -> str:
        # Do not cache a principal across impersonation/token changes.
        token = w.HANDLE()
        if not self.security.OpenThreadToken(
            self.kernel.GetCurrentThread(), 0x0008, True, c.byref(token)
        ):
            if c.get_last_error() != 1008:  # ERROR_NO_TOKEN
                self.check(False)
            self.check(
                self.security.OpenProcessToken(
                    self.kernel.GetCurrentProcess(), 0x0008, c.byref(token)
                )
            )
        try:
            length = w.DWORD()
            self.security.GetTokenInformation(token, 1, None, 0, c.byref(length))
            self.check(length.value)
            buffer = c.create_string_buffer(length.value)
            self.check(
                self.security.GetTokenInformation(
                    token, 1, buffer, len(buffer), c.byref(length)
                )
            )
            return self.sid(c.cast(buffer, c.POINTER(w.LPVOID)).contents.value)
        finally:
            self.kernel.CloseHandle(token)

    @contextmanager
    def private_security(self, user: str) -> Iterator[w.LPVOID]:
        # Protected DACL: no permissions are inherited from a shared ancestor.
        text = f"O:{user}D:P(A;OICI;FA;;;{user})(A;OICI;FA;;;SY)(A;OICI;FA;;;BA)"
        descriptor = w.LPVOID()
        self.check(
            self.security.ConvertStringSecurityDescriptorToSecurityDescriptorW(
                text, 1, c.byref(descriptor), None
            )
        )
        try:
            yield descriptor
        finally:
            self.kernel.LocalFree(descriptor)


@lru_cache(maxsize=1)
def api() -> WindowsApi:
    return WindowsApi()
