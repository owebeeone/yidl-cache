"""Opt-in compiled-code artifact caching, independent of code generators."""

from yidl_cache.cache import GeneratedCodeCache
from yidl_cache.diagnostics import (
    CacheDiagnostic,
    CacheLocationError,
    CacheProblem,
    LocationFailure,
)
from yidl_cache.locations import (
    CacheLocation,
    CacheLocationPolicy,
    ExplicitLocation,
    HashedSourceLocation,
    MirroredSourceLocation,
    ModuleLocalLocation,
    SourceOrigin,
    UnknownModuleLocation,
)
from yidl_cache.model import CacheArtifactError
from yidl_cache.model import CacheBypass
from yidl_cache.model import CacheDependencyError
from yidl_cache.model import CacheDisabledError
from yidl_cache.model import CacheError
from yidl_cache.model import CacheHit
from yidl_cache.model import CacheIdentityError
from yidl_cache.model import CacheMiss
from yidl_cache.model import CacheReentryError
from yidl_cache.model import CacheRequest
from yidl_cache.model import CacheStatistics
from yidl_cache.model import CacheStorageError
from yidl_cache.model import CompilationContext
from yidl_cache.model import DependencyInventory

__all__ = [
    "CacheArtifactError",
    "CacheBypass",
    "CacheDependencyError",
    "CacheDisabledError",
    "CacheError",
    "CacheHit",
    "CacheIdentityError",
    "CacheMiss",
    "CacheReentryError",
    "CacheRequest",
    "CacheStatistics",
    "CacheStorageError",
    "CompilationContext",
    "DependencyInventory",
    "GeneratedCodeCache",
    "CacheDiagnostic",
    "CacheLocation",
    "CacheLocationError",
    "CacheLocationPolicy",
    "CacheProblem",
    "ExplicitLocation",
    "HashedSourceLocation",
    "LocationFailure",
    "MirroredSourceLocation",
    "ModuleLocalLocation",
    "SourceOrigin",
    "UnknownModuleLocation",
]
