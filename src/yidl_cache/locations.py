from __future__ import annotations

from dataclasses import dataclass
import hashlib
from pathlib import Path
from urllib.parse import quote


@dataclass(frozen=True)
class SourceOrigin:
    path: Path | None
    module_name: str


@dataclass(frozen=True)
class CacheLocation:
    directory: Path


@dataclass(frozen=True)
class ExplicitLocation(CacheLocation):
    pass


@dataclass(frozen=True)
class ModuleLocalLocation(CacheLocation):
    pass


@dataclass(frozen=True)
class MirroredSourceLocation(CacheLocation):
    pass


@dataclass(frozen=True)
class HashedSourceLocation(CacheLocation):
    pass


@dataclass(frozen=True)
class UnknownModuleLocation(CacheLocation):
    pass


@dataclass(frozen=True)
class CacheLocationPolicy:
    override_root: Path | None = None
    user_root: Path | None = None

    def locations_for(
        self, namespace: str, origin: SourceOrigin
    ) -> tuple[CacheLocation, ...]:
        component = "ns-" + _digest(namespace)
        if self.override_root is not None:
            return (ExplicitLocation(self.override_root / component),)
        locations: list[CacheLocation] = []
        source = origin.path
        if source is not None and source.is_absolute():
            locations.append(
                ModuleLocalLocation(
                    source.parent / "__pycache__" / "yidl_cache" / component
                )
            )
        if self.user_root is None:
            return tuple(locations)
        root = self.user_root / component
        if source is None or not source.is_absolute():
            locations.append(
                UnknownModuleLocation(root / "modules" / _digest(origin.module_name))
            )
        else:
            volume = (
                "posix-root"
                if source.anchor == "/"
                else "volume-" + _encode(source.anchor)
            )
            parts = (volume, *(_encode(part) for part in source.parts[1:]))
            if (
                any(len(part.encode("utf-8")) > 180 for part in parts)
                or len("/".join(parts).encode("utf-8")) > 1500
            ):
                locations.append(
                    HashedSourceLocation(
                        root / "sources" / "by-digest" / _digest(str(source))
                    )
                )
            else:
                locations.append(
                    MirroredSourceLocation(root / "sources" / Path(*parts))
                )
        return tuple(locations)


def _digest(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _encode(component: str) -> str:
    if component in {".", ".."}:
        return "%2E" * len(component)
    return quote(component, safe="._-", encoding="utf-8", errors="strict")
