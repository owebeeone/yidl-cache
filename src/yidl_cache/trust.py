from __future__ import annotations

import errno
from functools import lru_cache
import os
import sys
from typing import TYPE_CHECKING

from yidl_cache.model import CacheStorageError

if TYPE_CHECKING:
    import ctypes


_DARWIN_ACL_TYPE_EXTENDED = 0x00000100
_LINUX_ACL_ATTRIBUTES = frozenset(
    (
        "system.posix_acl_access",
        "system.posix_acl_default",
        "system.nfs4_acl",
        "system.richacl",
    ),
)


def require_no_extended_acl(descriptor: int) -> None:
    """Conservatively reject ACL-managed artifacts rather than interpret grants."""
    if sys.platform == "darwin":
        try:
            import ctypes
        except ImportError as error:
            raise CacheStorageError("macOS ACL inspection is unavailable") from error

        library = _darwin_acl_library()
        ctypes.set_errno(0)
        acl = library.acl_get_fd_np(descriptor, _DARWIN_ACL_TYPE_EXTENDED)
        if not acl:
            if ctypes.get_errno() == errno.ENOENT:
                return
            raise CacheStorageError("cannot establish macOS ACL trust")
        library.acl_free(acl)
        raise CacheStorageError("extended ACLs are not supported for cache storage")
    if sys.platform.startswith("linux"):
        try:
            attributes = os.listxattr(descriptor)
        except OSError as error:
            raise CacheStorageError("cannot establish Linux ACL trust") from error
        if _LINUX_ACL_ATTRIBUTES.intersection(attributes):
            raise CacheStorageError("extended ACLs are not supported for cache storage")
        return
    raise CacheStorageError("ACL trust checks are not implemented on this platform")


@lru_cache(maxsize=1)
def _darwin_acl_library() -> ctypes.CDLL:
    try:
        import ctypes

        library = ctypes.CDLL(None, use_errno=True)
        library.acl_get_fd_np.argtypes = [ctypes.c_int, ctypes.c_int]
        library.acl_get_fd_np.restype = ctypes.c_void_p
        library.acl_free.argtypes = [ctypes.c_void_p]
        library.acl_free.restype = ctypes.c_int
        return library
    except (ImportError, OSError, AttributeError) as error:
        raise CacheStorageError("macOS ACL inspection is unavailable") from error
