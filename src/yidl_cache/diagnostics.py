from __future__ import annotations

from dataclasses import dataclass

from yidl_cache.locations import CacheLocation
from yidl_cache.model import (
    CacheBypass,
    CacheError,
    CacheHit,
    CacheMiss,
    CacheStorageError,
)


@dataclass(frozen=True)
class CacheProblem:
    kind: type[CacheError]
    message: str

    @classmethod
    def from_error(cls, error: CacheError) -> CacheProblem:
        return cls(type(error), str(error)[:1024])


@dataclass(frozen=True)
class LocationFailure:
    location: CacheLocation
    problem: CacheProblem


class CacheLocationError(CacheStorageError):
    def __init__(self, failures: tuple[LocationFailure, ...]) -> None:
        super().__init__("no usable cache location")
        self.failures = failures


@dataclass(frozen=True)
class CacheDiagnostic:
    request_digest: str | None
    namespace: str
    selected: CacheLocation | None
    attempted: tuple[CacheLocation, ...]
    failures: tuple[LocationFailure, ...]
    outcome: type[CacheHit] | type[CacheMiss] | type[CacheBypass]
    generated: bool
    problem: CacheProblem | None = None
    rejected_entry: CacheProblem | None = None
