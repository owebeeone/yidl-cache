"""Private local-NTFS storage with object-relative, non-reparsing handles.

Ancestors stay open without delete sharing until the operation finishes. File
reads deny write/delete sharing; publication/deletion address verified handles.
No path-based file I/O occurs after opening the drive root.
"""

from __future__ import annotations

from contextlib import contextmanager
import ctypes as c
from ctypes import wintypes as w
import os
from pathlib import Path
import re
from typing import Iterator

from yidl_cache.model import CacheArtifactError, CacheStorageError
from yidl_cache.windows_api import (
    AceHeader,
    Acl,
    DirectoryInformation,
    FileInformation,
    IoStatus,
    ObjectAttributes,
    RenameInformation,
    UnicodeString,
    api,
)

_READ_CONTROL = 0x00020000
_SYNCHRONIZE = 0x00100000
_DELETE = 0x00010000
_DIRECTORY_ACCESS = _READ_CONTROL | _SYNCHRONIZE | 0x0081
_REPARSE = 0x400
_DIRECTORY = 0x10
# Public traversal/data access on ancestors is harmless with locked names.
# Unknown rights, GENERIC_ALL, WRITE_DAC and WRITE_OWNER are not admitted.
_ANCESTOR_ACCESS = 0xE0000000 | _READ_CONTROL | _SYNCHRONIZE | _DELETE | 0x01FF


def require_private(handle: int, user: str, *, ancestor: bool = False) -> None:
    """Verify ownership and effective grants, allowing public ancestor traversal.

    Ancestors must not delegate ACL/owner control to an untrusted principal:
    otherwise inherited permissions could be propagated into existing children.
    """
    system = api()
    owner, dacl, descriptor = w.LPVOID(), w.LPVOID(), w.LPVOID()
    error = system.security.GetSecurityInfo(
        handle,
        1,
        0x00000005,
        c.byref(owner),
        None,
        c.byref(dacl),
        None,
        c.byref(descriptor),
    )
    if error:
        raise c.WinError(error)
    try:
        system.check(system.security.IsValidSecurityDescriptor(descriptor))
        trusted = {user, "S-1-5-18", "S-1-5-32-544"}
        if ancestor:
            # Windows Modules Installer is a LocalSystem service and owns the
            # standard system drive root. This does not admit arbitrary services.
            trusted.add(
                "S-1-5-80-956008885-3418522649-1831038044-1853292631-2271478464"
            )
        if system.sid(owner.value) not in trusted:
            raise CacheStorageError("Windows cache object has an untrusted owner")
        if not dacl:
            raise CacheStorageError("Windows cache object has an unrestricted DACL")
        system.check(system.security.IsValidAcl(dacl))
        acl = c.cast(dacl, c.POINTER(Acl)).contents
        for index in range(acl.count):
            pointer = w.LPVOID()
            system.check(system.security.GetAce(dacl, index, c.byref(pointer)))
            header = c.cast(pointer, c.POINTER(AceHeader)).contents
            if header.flags & 0x08:  # INHERIT_ONLY_ACE is not effective here.
                continue
            if header.kind not in (0, 1) or header.size < 16:
                raise CacheStorageError(
                    "unsupported Windows cache access-control entry"
                )
            # ACCESS_ALLOWED_ACE / ACCESS_DENIED_ACE: header, ACCESS_MASK, SID.
            mask = w.DWORD.from_address(pointer.value + 4).value
            sid = system.sid(pointer.value + 8)
            unsafe = mask & ~_ANCESTOR_ACCESS if ancestor else mask
            if header.kind == 0 and unsafe and sid not in trusted | {"S-1-3-4"}:
                # OWNER RIGHTS resolves only to the already verified owner.
                # Deny ACEs are never used to justify an otherwise unsafe grant.
                raise CacheStorageError(
                    "Windows cache ACL grants an untrusted principal"
                )
    finally:
        system.kernel.LocalFree(descriptor)


def information(handle: int, *, directory: bool) -> FileInformation:
    system = api()
    if system.kernel.GetFileType(handle) != 1:  # FILE_TYPE_DISK
        raise CacheStorageError("Windows cache object is not a disk object")
    result = FileInformation()
    system.check(system.kernel.GetFileInformationByHandle(handle, c.byref(result)))
    if result.attributes & (_REPARSE | 0x40):
        raise CacheStorageError(
            "Windows cache reparse/device objects are not supported"
        )
    if bool(result.attributes & _DIRECTORY) != directory:
        raise CacheStorageError("Windows cache object has an unexpected file type")
    if not directory and result.links != 1:
        raise CacheStorageError("Windows cache entry must have exactly one hard link")
    return result


def require_ntfs(handle: int) -> None:
    system = api()
    filesystem = c.create_unicode_buffer(32)
    flags = w.DWORD()
    system.check(
        system.kernel.GetVolumeInformationByHandleW(
            handle, None, 0, None, None, c.byref(flags), filesystem, len(filesystem)
        )
    )
    if filesystem.value != "NTFS" or not flags.value & 0x00000008:
        raise CacheStorageError(
            "Windows cache requires local NTFS with persistent ACLs"
        )


def open_relative(
    parent: int,
    name: str,
    access: int,
    *,
    directory: bool = False,
    create: bool = False,
    exclusive: bool = False,
    security: w.LPVOID | None = None,
) -> int:
    # A single NT name, never a path, stream, device name or traversal.
    if not name or name in {".", ".."} or any(char in name for char in "\\/:\x00"):
        raise CacheStorageError("unsupported Windows cache path component")
    if name.endswith((".", " ")):
        raise CacheStorageError("ambiguous Windows cache path component")
    system = api()
    buffer = c.create_unicode_buffer(name)
    length = len(name.encode("utf-16-le", errors="surrogatepass"))
    if length > 65532:
        raise CacheStorageError("Windows cache path component is too long")
    unicode = UnicodeString(length, length + 2, c.cast(buffer, w.LPWSTR))
    attributes = ObjectAttributes(
        c.sizeof(ObjectAttributes), parent, c.pointer(unicode), 0x40, security, None
    )
    result, status = w.HANDLE(), IoStatus()
    # Synchronous I/O, no reparse processing, and required directory/file type.
    options = 0x20 | 0x00200000 | (0x1 if directory else 0x40)
    disposition = 2 if exclusive else (3 if create else 1)
    # Directory names cannot be replaced while any ancestor handle is live.
    # Read handles deny writes/deletes. New/delete handles are exclusive.
    sharing = 3 if directory else (0 if access & (_DELETE | 0x2) else 1)
    system.check_status(
        system.native.NtCreateFile(
            c.byref(result),
            access | _SYNCHRONIZE,
            c.byref(attributes),
            c.byref(status),
            None,
            0x10 if directory else 0x80,
            sharing,
            disposition,
            options,
            None,
            0,
        )
    )
    assert result.value is not None
    return result.value


@contextmanager
def directory_handle(
    directory: Path, *, create: bool = True
) -> Iterator[tuple[int, str, w.LPVOID]]:
    if (
        re.fullmatch(r"[A-Za-z]:\\", directory.anchor) is None
        or ".." in directory.parts
    ):
        raise CacheStorageError("Windows cache requires an absolute local drive path")
    system = api()
    if system.kernel.GetDriveTypeW(directory.anchor) != 3:  # DRIVE_FIXED
        raise CacheStorageError("Windows cache requires a fixed local drive")
    handles: list[int] = []
    try:
        user = system.user_sid()
        with system.private_security(user) as security:
            root = system.kernel.CreateFileW(
                "\\\\?\\" + directory.anchor,
                _DIRECTORY_ACCESS,
                3,
                None,
                3,
                0x02000000 | 0x00200000,
                None,
            )
            if root == c.c_void_p(-1).value:
                system.check(False)
            handles.append(root)
            information(root, directory=True)
            require_ntfs(root)
            require_private(root, user, ancestor=True)
            for component in directory.parts[1:]:
                handle = open_relative(
                    handles[-1],
                    component,
                    _DIRECTORY_ACCESS,
                    directory=True,
                    create=create,
                    security=security,
                )
                handles.append(handle)
                information(handle, directory=True)
                require_private(handle, user, ancestor=True)
            require_private(handles[-1], user)
            yield handles[-1], user, security
    finally:
        for handle in reversed(handles):
            system.kernel.CloseHandle(handle)


@contextmanager
def private_file(
    directory: int,
    name: str,
    user: str,
    security: w.LPVOID,
    *,
    create: bool = False,
    delete_access: bool = False,
) -> Iterator[int]:
    access = _READ_CONTROL | 0x80 | (_DELETE if delete_access else 0)
    access |= 0x2 if create else 0x1
    handle = open_relative(
        directory, name, access, create=create, exclusive=create, security=security
    )
    verified = False
    try:
        information(handle, directory=False)
        require_private(handle, user)
        verified = True
        yield handle
    finally:
        try:
            if create and not verified:
                delete(handle)
        finally:
            api().kernel.CloseHandle(handle)


def read_bytes(handle: int, maximum: int) -> bytes:
    metadata = information(handle, directory=False)
    size = metadata.size_low | metadata.size_high << 32
    if size > maximum:
        raise CacheArtifactError("cache entry exceeds the configured size bound")
    buffer = c.create_string_buffer(size + 1)
    read = w.DWORD()
    api().check(api().kernel.ReadFile(handle, buffer, len(buffer), c.byref(read), None))
    if read.value != size:
        raise CacheArtifactError("Windows cache entry changed size while reading")
    return buffer.raw[: read.value]


def write_bytes(handle: int, data: bytes) -> None:
    written = w.DWORD()
    system = api()
    system.check(
        system.kernel.WriteFile(handle, data, len(data), c.byref(written), None)
    )
    if written.value != len(data):
        raise CacheStorageError("incomplete Windows cache write")
    system.check(system.kernel.FlushFileBuffers(handle))


def delete(handle: int) -> None:
    pending = w.BYTE(True)  # FILE_DISPOSITION_INFO.DeleteFile is BOOLEAN.
    api().check(
        api().kernel.SetFileInformationByHandle(
            handle, 4, c.byref(pending), c.sizeof(pending)
        )
    )


def replace(handle: int, directory: int, name: str) -> None:
    encoded = name.encode("utf-16-le", errors="surrogatepass")
    buffer = c.create_string_buffer(c.sizeof(RenameInformation) + len(encoded))
    info = c.cast(buffer, c.POINTER(RenameInformation)).contents
    info.replace, info.root, info.length = 1, directory, len(encoded)
    c.memmove(
        c.addressof(buffer) + RenameInformation.name.offset, encoded, len(encoded)
    )
    status = IoStatus()
    api().check_status(
        api().native.NtSetInformationFile(
            handle, c.byref(status), buffer, len(buffer), 10
        )
    )


def names(handle: int) -> Iterator[str]:
    system = api()
    buffer = c.create_string_buffer(64 * 1024)
    restart = True
    while True:
        if not system.kernel.GetFileInformationByHandleEx(
            handle, 11 if restart else 10, buffer, len(buffer)
        ):
            if c.get_last_error() == 18:  # ERROR_NO_MORE_FILES
                return
            system.check(False)
        restart = False
        offset = 0
        while True:
            if offset + DirectoryInformation.name.offset > len(buffer):
                raise CacheStorageError("invalid Windows cache directory enumeration")
            info = DirectoryInformation.from_buffer(buffer, offset)
            start = offset + DirectoryInformation.name.offset
            end = start + info.name_length
            if info.name_length % 2 or end > len(buffer):
                raise CacheStorageError("invalid Windows cache directory name")
            yield buffer.raw[start:end].decode("utf-16-le", errors="surrogatepass")
            if info.next == 0:
                break
            if info.next < DirectoryInformation.name.offset or info.next % 8:
                raise CacheStorageError("invalid Windows cache directory offset")
            offset += info.next


class WindowsStorage:
    def __init__(self, directory: Path) -> None:
        self.directory = directory

    def read(self, name: str, maximum: int) -> bytes | None:
        with directory_handle(self.directory) as (directory, user, security):
            try:
                with private_file(directory, name, user, security) as handle:
                    return read_bytes(handle, maximum)
            except FileNotFoundError:
                return None
            except CacheStorageError as error:
                raise CacheArtifactError(str(error)) from error

    def admit(self) -> None:
        with directory_handle(self.directory) as (directory, user, security):
            name = ".probe-" + os.urandom(12).hex() + ".tmp"
            with private_file(
                directory, name, user, security, create=True, delete_access=True
            ) as handle:
                try:
                    write_bytes(handle, b"probe")
                finally:
                    delete(handle)

    def write(self, name: str, data: bytes) -> None:
        with directory_handle(self.directory) as (directory, user, security):
            temporary = name + "." + os.urandom(12).hex() + ".tmp"
            with private_file(
                directory, temporary, user, security, create=True, delete_access=True
            ) as handle:
                published = False
                try:
                    write_bytes(handle, data)
                    replace(handle, directory, name)
                    published = True
                finally:
                    if not published:
                        delete(handle)

    def clear(
        self, entry_pattern: re.Pattern[str], probe_pattern: re.Pattern[str]
    ) -> int:
        try:
            with directory_handle(self.directory, create=False) as (
                directory,
                user,
                security,
            ):
                removed = 0
                for name in names(directory):
                    if entry_pattern.fullmatch(name) or probe_pattern.fullmatch(name):
                        try:
                            with private_file(
                                directory, name, user, security, delete_access=True
                            ) as handle:
                                delete(handle)
                                removed += 1
                        except FileNotFoundError:
                            pass
                return removed
        except FileNotFoundError:
            return 0
