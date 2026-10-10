from __future__ import annotations

from contextlib import contextmanager
from dataclasses import dataclass
import errno
import hashlib
import hmac
import json
import marshal
import os
from pathlib import Path
import re
import stat
import struct
from types import CodeType
from typing import Iterator

from yidl_cache.model import CacheArtifactError
from yidl_cache.model import CacheStorageError
from yidl_cache.model import json_bytes
from yidl_cache.trust import require_no_extended_acl

_MAGIC = b"YIDLCACHE\x01"
_HEADER_LIMIT = 16 * 1024
_ENTRY_NAME = re.compile(r"[0-9a-f]{64}\.ycode(?:\.[0-9a-f]{24}\.tmp)?")
_PROBE_NAME = re.compile(r"\.probe-[0-9a-f]{24}\.tmp")


@dataclass(frozen=True)
class ReadResult:
    code: CodeType | None = None
    rejection: CacheArtifactError | None = None


class ArtifactStorage:
    def __init__(self, directory: Path, max_payload_bytes: int) -> None:
        self.directory = directory.absolute()
        self.max_payload_bytes = max_payload_bytes

    @contextmanager
    def _directory(self, *, create: bool = True) -> Iterator[int]:
        if os.name != "posix" or not hasattr(os, "O_NOFOLLOW"):
            raise CacheStorageError(
                "private-directory trust is not implemented on this platform"
            )
        if ".." in self.directory.parts:
            raise CacheStorageError(
                "cache directories must not contain parent traversal"
            )
        descriptor = None
        try:
            # Walk through directory descriptors so no ancestor symlink can be
            # followed or substituted between inspection and artifact access.
            flags = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW
            descriptor = os.open(self.directory.anchor, flags)
            for component in self.directory.parts[1:]:
                try:
                    child = os.open(component, flags, dir_fd=descriptor)
                except FileNotFoundError:
                    if not create:
                        raise
                    try:
                        os.mkdir(component, mode=0o700, dir_fd=descriptor)
                    except FileExistsError:
                        pass
                    child = os.open(component, flags, dir_fd=descriptor)
                os.close(descriptor)
                descriptor = child
            metadata = os.fstat(descriptor)
            if metadata.st_uid != os.getuid() or stat.S_IMODE(metadata.st_mode) & 0o077:
                raise CacheStorageError(
                    "cache directory must be owned by this user and private (0700)"
                )
            require_no_extended_acl(descriptor)
            yield descriptor
        except OSError as error:
            raise CacheStorageError("cannot access private cache directory") from error
        finally:
            if descriptor is not None:
                os.close(descriptor)

    def read(self, key: str, identity: dict[str, object]) -> ReadResult:
        with self._directory() as directory:
            descriptor = None
            try:
                descriptor = os.open(
                    key + ".ycode",
                    os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK,
                    dir_fd=directory,
                )
                metadata = os.fstat(descriptor)
                if (
                    not stat.S_ISREG(metadata.st_mode)
                    or metadata.st_uid != os.getuid()
                    or stat.S_IMODE(metadata.st_mode) & 0o077
                    or metadata.st_nlink != 1
                ):
                    raise CacheArtifactError(
                        "cache entry is not a private owned regular file"
                    )
                try:
                    require_no_extended_acl(descriptor)
                except CacheStorageError as error:
                    raise CacheArtifactError(
                        "cache entry ACL trust is not established"
                    ) from error
                maximum = len(_MAGIC) + 4 + _HEADER_LIMIT + self.max_payload_bytes
                if metadata.st_size > maximum:
                    raise CacheArtifactError(
                        "cache entry exceeds the configured size bound"
                    )
                with os.fdopen(descriptor, "rb") as stream:
                    descriptor = None
                    data = stream.read(maximum + 1)
                return ReadResult(code=self._decode(data, identity))
            except FileNotFoundError:
                return ReadResult()
            except CacheArtifactError as error:
                return ReadResult(rejection=error)
            except OSError as error:
                if error.errno == errno.ELOOP:
                    return ReadResult(
                        rejection=CacheArtifactError("cache entry cannot be a symlink")
                    )
                raise CacheStorageError("cannot read cache storage") from error
            finally:
                if descriptor is not None:
                    os.close(descriptor)

    def admit(self) -> None:
        """Test private writable storage without overwriting an existing entry."""
        with self._directory() as directory:
            name = ".probe-" + os.urandom(12).hex() + ".tmp"
            created = False
            try:
                descriptor = os.open(
                    name,
                    os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW,
                    0o600,
                    dir_fd=directory,
                )
                created = True
                try:
                    require_no_extended_acl(descriptor)
                    os.write(descriptor, b"probe")
                finally:
                    os.close(descriptor)
            except OSError as error:
                raise CacheStorageError(
                    "cannot probe writable cache directory"
                ) from error
            finally:
                if created:
                    try:
                        os.unlink(name, dir_fd=directory)
                    except OSError as error:
                        raise CacheStorageError(
                            "cannot clean cache admission probe"
                        ) from error

    def _decode(self, data: bytes, identity: dict[str, object]) -> CodeType:
        prefix = len(_MAGIC) + 4
        if len(data) < prefix or data[: len(_MAGIC)] != _MAGIC:
            raise CacheArtifactError("unknown or truncated cache format")
        header_length = struct.unpack(">I", data[len(_MAGIC) : prefix])[0]
        if header_length > _HEADER_LIMIT or len(data) < prefix + header_length:
            raise CacheArtifactError("invalid cache header size")
        try:
            header = json.loads(data[prefix : prefix + header_length])
        except (ValueError, UnicodeError, RecursionError) as error:
            raise CacheArtifactError("invalid cache header") from error
        if not isinstance(header, dict) or set(header) != {
            "identity",
            "length",
            "sha256",
        }:
            raise CacheArtifactError("unsupported cache header fields")
        length = header["length"]
        if type(length) is not int or not 0 <= length <= self.max_payload_bytes:
            raise CacheArtifactError("invalid payload size")
        payload = data[prefix + header_length :]
        if (
            json_bytes(header["identity"]) != json_bytes(identity)
            or len(payload) != length
        ):
            raise CacheArtifactError("incompatible identity or truncated payload")
        checksum = header["sha256"]
        if (
            not isinstance(checksum, str)
            or re.fullmatch(r"[0-9a-f]{64}", checksum) is None
            or not hmac.compare_digest(hashlib.sha256(payload).hexdigest(), checksum)
        ):
            raise CacheArtifactError("payload integrity check failed")
        try:
            code = marshal.loads(payload)
        except (ValueError, TypeError, EOFError, RecursionError) as error:
            raise CacheArtifactError("invalid serialized code") from error
        if (
            not isinstance(code, CodeType)
            or code.co_name != "<module>"
            or code.co_freevars
        ):
            raise CacheArtifactError("artifact is not compiled module code")
        context = identity["compilation"]
        assert isinstance(context, dict)
        if code.co_filename != context["filename"]:
            raise CacheArtifactError("compiled filename does not match request")
        _check_constants(code)
        return code

    def write(self, key: str, identity: dict[str, object], code: CodeType) -> None:
        _check_constants(code)
        try:
            payload = marshal.dumps(code)
        except (ValueError, TypeError, RecursionError) as error:
            raise CacheArtifactError("code cannot be serialized") from error
        if len(payload) > self.max_payload_bytes:
            raise CacheArtifactError(
                "compiled code exceeds the configured payload bound"
            )
        header = json_bytes(
            {
                "identity": identity,
                "length": len(payload),
                "sha256": hashlib.sha256(payload).hexdigest(),
            }
        )
        if len(header) > _HEADER_LIMIT:
            raise CacheArtifactError("cache identity exceeds the header bound")
        artifact = _MAGIC + struct.pack(">I", len(header)) + header + payload
        with self._directory() as directory:
            temporary = key + ".ycode." + os.urandom(12).hex() + ".tmp"
            try:
                descriptor = os.open(
                    temporary,
                    os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW,
                    0o600,
                    dir_fd=directory,
                )
                with os.fdopen(descriptor, "wb") as stream:
                    require_no_extended_acl(stream.fileno())
                    stream.write(artifact)
                    stream.flush()
                    os.fsync(stream.fileno())
                os.replace(
                    temporary,
                    key + ".ycode",
                    src_dir_fd=directory,
                    dst_dir_fd=directory,
                )
            except OSError as error:
                raise CacheStorageError("cannot publish cache entry") from error
            finally:
                try:
                    os.unlink(temporary, dir_fd=directory)
                except FileNotFoundError:
                    pass
                except OSError as error:
                    raise CacheStorageError(
                        "cannot clean temporary cache entry"
                    ) from error

    def clear(self) -> int:
        try:
            self.directory.lstat()
        except FileNotFoundError:
            return 0
        except OSError as error:
            raise CacheStorageError(
                "cannot inspect cache maintenance directory"
            ) from error
        with self._directory(create=False) as directory:
            removed = 0
            for name in os.listdir(directory):
                if (
                    _ENTRY_NAME.fullmatch(name) is not None
                    or _PROBE_NAME.fullmatch(name) is not None
                ):
                    try:
                        os.unlink(name, dir_fd=directory)
                        removed += 1
                    except FileNotFoundError:
                        pass
            return removed


def _check_constants(value: object, depth: int = 0) -> None:
    if depth > 100:
        raise CacheArtifactError("compiled constants exceed the nesting bound")
    if isinstance(value, CodeType):
        for constant in value.co_consts:
            _check_constants(constant, depth + 1)
    elif isinstance(value, (tuple, frozenset)) and type(value) in (tuple, frozenset):
        for item in value:
            _check_constants(item, depth + 1)
    elif value is not Ellipsis and type(value) not in (
        type(None),
        bool,
        int,
        float,
        complex,
        str,
        bytes,
    ):
        raise CacheArtifactError(
            "compiled constants contain unsupported runtime objects"
        )
