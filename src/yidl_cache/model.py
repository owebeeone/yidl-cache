from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
import hashlib
import importlib.util
import json
from pathlib import Path
import re
import sys
from types import CodeType


class CacheError(Exception):
    """An optional cache operation could not be used safely."""


class CacheDisabledError(CacheError):
    """The caller has not enabled caching."""


class CacheStorageError(CacheError):
    """Storage is unavailable or its trust cannot be established."""


class CacheArtifactError(CacheError):
    """An artifact is corrupt, incompatible, or not safe to persist."""


class CacheDependencyError(CacheError):
    """Generation provenance is missing or changed within this process."""


class CacheIdentityError(CacheError):
    """The request has no supported deterministic cache identity."""


class CacheReentryError(CacheError):
    """This thread is already producing the same request."""


@dataclass(frozen=True)
class CompilationContext:
    filename: str
    flags: int = 0
    dont_inherit: bool = True
    optimize: int = -1


@dataclass(frozen=True)
class DependencyStamp:
    name: str
    path: Path
    mtime_ns: int
    size: int


@dataclass(frozen=True)
class DependencyInventory:
    stamps: tuple[DependencyStamp, ...]
    digest: str

    @classmethod
    def capture(cls, files: Mapping[str, Path]) -> DependencyInventory:
        """Capture once, before importing or using the producer's generator."""
        stamps = []
        try:
            for name, path in sorted(files.items()):
                if not isinstance(name, str) or not name:
                    raise CacheDependencyError(
                        "dependency names must be nonempty strings"
                    )
                resolved = Path(path).resolve(strict=True)
                metadata = resolved.stat()
                if not resolved.is_file():
                    raise CacheDependencyError("generation dependencies must be files")
                stamps.append(
                    DependencyStamp(
                        name, resolved, metadata.st_mtime_ns, metadata.st_size
                    )
                )
        except OSError as error:
            raise CacheDependencyError(
                "cannot inspect generation dependencies"
            ) from error
        encoded = json_bytes(
            [[stamp.name, stamp.mtime_ns, stamp.size] for stamp in stamps]
        )
        return cls(tuple(stamps), hashlib.sha256(encoded).hexdigest())

    def unchanged(self) -> bool:
        try:
            return all(
                (metadata := stamp.path.stat()).st_mtime_ns == stamp.mtime_ns
                and metadata.st_size == stamp.size
                for stamp in self.stamps
            )
        except OSError:
            return False


@dataclass(frozen=True)
class CacheRequest:
    namespace: str
    generator_revision: str
    input_digest: str
    compilation: CompilationContext
    dependencies: DependencyInventory | None

    def identity(self) -> dict[str, object]:
        if self.dependencies is None:
            raise CacheDependencyError("dependency inventory is unavailable")
        if not all(
            isinstance(value, str) and 0 < len(value) <= 1024
            for value in (
                self.namespace,
                self.generator_revision,
                self.compilation.filename,
            )
        ):
            raise CacheIdentityError(
                "namespace, revision, and filename require bounded strings"
            )
        if (
            not isinstance(self.input_digest, str)
            or re.fullmatch(r"[0-9a-f]{64}", self.input_digest) is None
        ):
            raise CacheIdentityError("input_digest must be a normalized SHA-256 digest")
        if type(self.compilation.flags) is not int or self.compilation.flags < 0:
            raise CacheIdentityError("compilation flags must be nonnegative integers")
        if (
            type(self.compilation.dont_inherit) is not bool
            or not self.compilation.dont_inherit
        ):
            raise CacheIdentityError("cached compilation must not inherit caller flags")
        if type(
            self.compilation.optimize
        ) is not int or self.compilation.optimize not in (-1, 0, 1, 2):
            raise CacheIdentityError("unsupported compilation optimization setting")
        return {
            "format": 1,
            "namespace": self.namespace,
            "generator_revision": self.generator_revision,
            "input_digest": self.input_digest,
            "dependencies": self.dependencies.digest,
            "python": [sys.implementation.name, *sys.version_info[:3]],
            "cache_tag": sys.implementation.cache_tag,
            "magic": importlib.util.MAGIC_NUMBER.hex(),
            "compilation": {
                "filename": self.compilation.filename,
                "flags": self.compilation.flags,
                "dont_inherit": self.compilation.dont_inherit,
                "optimize": (
                    sys.flags.optimize
                    if self.compilation.optimize == -1
                    else self.compilation.optimize
                ),
            },
        }


@dataclass(frozen=True)
class CacheHit:
    code: CodeType


@dataclass(frozen=True)
class CacheMiss:
    code: CodeType
    rejected_entry: CacheArtifactError | None = None


@dataclass(frozen=True)
class CacheBypass:
    code: CodeType
    reason: CacheError


@dataclass(frozen=True)
class CacheStatistics:
    hits: int = 0
    misses: int = 0
    bypasses: int = 0


def json_bytes(value: object) -> bytes:
    return json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=True
    ).encode("ascii")
