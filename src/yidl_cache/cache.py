from __future__ import annotations

from collections import OrderedDict, deque
from collections.abc import Callable
from dataclasses import dataclass, field, replace
import hashlib
from pathlib import Path
from threading import RLock, local
from types import CodeType

from yidl_cache.diagnostics import (
    CacheDiagnostic,
    CacheLocationError,
    CacheProblem,
    LocationFailure,
)
from yidl_cache.locations import CacheLocation
from yidl_cache.model import (
    CacheArtifactError,
    CacheBypass,
    CacheDependencyError,
    CacheDisabledError,
    CacheError,
    CacheHit,
    CacheMiss,
    CacheReentryError,
    CacheRequest,
    CacheStatistics,
    CacheStorageError,
    json_bytes,
)
from yidl_cache.storage import ArtifactStorage


@dataclass(frozen=True)
class _Preference:
    selected: CacheLocation | None
    failures: tuple[LocationFailure, ...]


@dataclass
class _RequestTrace:
    namespace: str
    key: str | None = None
    selected: CacheLocation | None = None
    attempted: list[CacheLocation] = field(default_factory=list)
    failures: list[LocationFailure] = field(default_factory=list)
    generated: bool = False
    rejection: CacheArtifactError | None = None

    def failed(self, location: CacheLocation, error: CacheStorageError) -> None:
        self.failures.append(LocationFailure(location, CacheProblem.from_error(error)))


class GeneratedCodeCache:
    """Optional compiled-code reuse. Never execute code or retain producers."""

    def __init__(
        self,
        directory: Path | None = None,
        *,
        enabled: bool = False,
        memory_capacity: int = 32,
        max_payload_bytes: int = 16 * 1024 * 1024,
    ) -> None:
        if type(memory_capacity) is not int or memory_capacity < 0:
            raise ValueError("memory_capacity must be a nonnegative integer")
        if type(max_payload_bytes) is not int or max_payload_bytes <= 0:
            raise ValueError("max_payload_bytes must be a positive integer")
        self._enabled = enabled
        self._memory_capacity = memory_capacity
        self._max_payload_bytes = max_payload_bytes
        self._default = (
            None if directory is None else CacheLocation(Path(directory).absolute())
        )
        self._memory: OrderedDict[str, tuple[CodeType, CacheLocation]] = OrderedDict()
        self._preferences: OrderedDict[tuple[CacheLocation, ...], _Preference] = (
            OrderedDict()
        )
        self._diagnostics: deque[CacheDiagnostic] = deque(maxlen=32)
        self._lock = RLock()
        self._threads = local()
        self._statistics = CacheStatistics()
        self._producer_dependencies: dict[tuple[str, str], str] = {}
        self._disabled_producers: set[tuple[str, str]] = set()

    @property
    def statistics(self) -> CacheStatistics:
        with self._lock:
            return self._statistics

    @property
    def diagnostics(self) -> tuple[CacheDiagnostic, ...]:
        with self._lock:
            return tuple(self._diagnostics)

    def get(
        self,
        request: CacheRequest,
        produce: Callable[[], CodeType],
        *,
        locations: tuple[CacheLocation, ...] | None = None,
    ) -> CacheHit | CacheMiss | CacheBypass:
        trace = _RequestTrace(request.namespace)
        active = getattr(self._threads, "active", None)
        if active is None:
            active = self._threads.active = set()

        def generate() -> CodeType:
            trace.generated = True
            added = trace.key is not None and trace.key not in active
            if added:
                active.add(trace.key)
            try:
                return _generate(request, produce)
            finally:
                if added:
                    active.remove(trace.key)

        if not self._enabled:
            return self._finish(
                CacheBypass(generate(), CacheDisabledError("cache is disabled")), trace
            )
        try:
            identity = request.identity()
            self._check_producer(request)
        except CacheError as error:
            return self._finish(CacheBypass(generate(), error), trace)
        key = trace.key = hashlib.sha256(json_bytes(identity)).hexdigest()
        if key in active:
            return self._finish(
                CacheBypass(
                    generate(),
                    CacheReentryError("same-key generation is already active"),
                ),
                trace,
            )
        route = (
            locations
            if locations is not None
            else (() if self._default is None else (self._default,))
        )
        if not route:
            return self._finish(CacheBypass(generate(), CacheLocationError(())), trace)
        if len(route) > 2:
            return self._finish(
                CacheBypass(
                    generate(),
                    CacheStorageError("at most two cache locations are supported"),
                ),
                trace,
            )
        with self._lock:
            memory = self._memory.get(key)
            if memory is not None:
                self._memory.move_to_end(key)
                trace.selected = memory[1]
                return self._finish(CacheHit(memory[0]), trace)
            preference = self._preferences.get(route)
            if preference is not None:
                self._preferences.move_to_end(route)
        trace.failures = list(preference.failures) if preference is not None else []
        code: CodeType | None = None
        if preference is None:
            candidates = route
        elif preference.selected is None:
            candidates = ()
        else:
            candidates = route[route.index(preference.selected) :]
        for location in candidates:
            trace.selected = location
            trace.attempted.append(location)
            storage = ArtifactStorage(location.directory, self._max_payload_bytes)
            try:
                if preference is None or preference.selected != location:
                    storage.admit()
                self._prefer(route, location, tuple(trace.failures))
                entry = storage.read(key, identity)
            except CacheStorageError as error:
                trace.failed(location, error)
                continue
            trace.rejection = entry.rejection or trace.rejection
            if entry.code is not None:
                try:
                    self._check_producer(request)
                except CacheError as error:
                    return self._finish(CacheBypass(code or generate(), error), trace)
                self._remember(key, entry.code, location)
                return self._finish(CacheHit(entry.code), trace)
            if code is None:
                # Producer exceptions must stay outside all storage fallback handlers.
                code = generate()
                dependencies = request.dependencies
                assert dependencies is not None
                if not dependencies.unchanged():
                    with self._lock:
                        self._disabled_producers.add(
                            (request.namespace, request.generator_revision)
                        )
                    return self._finish(
                        CacheBypass(
                            code,
                            CacheDependencyError(
                                "dependencies changed during generation; restart to cache again"
                            ),
                        ),
                        trace,
                    )
            try:
                self._check_producer(request)
                storage.write(key, identity, code)
            except CacheStorageError as error:
                trace.failed(location, error)
                continue
            except CacheError as error:
                return self._finish(CacheBypass(code, error), trace)
            self._remember(key, code, location)
            return self._finish(CacheMiss(code, trace.rejection), trace)
        self._prefer(route, None, tuple(trace.failures))
        trace.selected = None
        return self._finish(
            CacheBypass(code or generate(), CacheLocationError(tuple(trace.failures))),
            trace,
        )

    def bypass(
        self, namespace: str, produce: Callable[[], CodeType], reason: CacheError
    ) -> CacheBypass:
        """Record a consumer identity failure before a cache request can be formed."""
        trace = _RequestTrace(namespace, generated=True)
        result = self._finish(CacheBypass(produce(), reason), trace)
        assert isinstance(result, CacheBypass)
        return result

    def _check_producer(self, request: CacheRequest) -> None:
        dependencies = request.dependencies
        assert dependencies is not None
        producer = (request.namespace, request.generator_revision)
        with self._lock:
            if producer in self._disabled_producers:
                raise CacheDependencyError(
                    "persistent producer use is disabled until restart"
                )
            existing = self._producer_dependencies.setdefault(
                producer, dependencies.digest
            )
            if existing != dependencies.digest:
                self._disabled_producers.add(producer)
                raise CacheDependencyError(
                    "producer identity cannot be relabeled within a process"
                )

    def _prefer(
        self,
        route: tuple[CacheLocation, ...],
        selected: CacheLocation | None,
        failures: tuple[LocationFailure, ...],
    ) -> None:
        with self._lock:
            self._preferences[route] = _Preference(selected, failures)
            self._preferences.move_to_end(route)
            while len(self._preferences) > 32:
                self._preferences.popitem(last=False)

    def _remember(self, key: str, code: CodeType, location: CacheLocation) -> None:
        if self._memory_capacity:
            with self._lock:
                self._memory[key] = (code, location)
                self._memory.move_to_end(key)
                while len(self._memory) > self._memory_capacity:
                    self._memory.popitem(last=False)

    def _finish(
        self, result: CacheHit | CacheMiss | CacheBypass, trace: _RequestTrace
    ) -> CacheHit | CacheMiss | CacheBypass:
        diagnostic = CacheDiagnostic(
            trace.key,
            trace.namespace[:1024] if type(trace.namespace) is str else "<unsupported>",
            trace.selected,
            tuple(trace.attempted),
            tuple(trace.failures),
            type(result),
            trace.generated,
            (
                CacheProblem.from_error(result.reason)
                if isinstance(result, CacheBypass)
                else None
            ),
            (
                None
                if trace.rejection is None
                else CacheProblem.from_error(trace.rejection)
            ),
        )
        with self._lock:
            self._statistics = replace(
                self._statistics,
                hits=self._statistics.hits + isinstance(result, CacheHit),
                misses=self._statistics.misses + isinstance(result, CacheMiss),
                bypasses=self._statistics.bypasses + isinstance(result, CacheBypass),
            )
            self._diagnostics.append(diagnostic)
        return result

    def clear(self) -> int:
        """Maintain tracked locations only; producer invalidation survives clearing."""
        with self._lock:
            locations = {location for route in self._preferences for location in route}
            if self._default is not None:
                locations.add(self._default)
        removed = 0
        failures = []
        for location in locations:
            try:
                removed += ArtifactStorage(
                    location.directory, self._max_payload_bytes
                ).clear()
            except CacheStorageError as error:
                failures.append(
                    LocationFailure(location, CacheProblem.from_error(error))
                )
        with self._lock:
            self._memory.clear()
            self._diagnostics.clear()
            self._preferences.clear()
        if failures:
            raise CacheLocationError(tuple(failures))
        return removed


def _generate(request: CacheRequest, produce: Callable[[], CodeType]) -> CodeType:
    code = produce()
    if not isinstance(code, CodeType) or code.co_name != "<module>" or code.co_freevars:
        raise TypeError("producer must return compiled module code")
    if code.co_filename != request.compilation.filename:
        raise ValueError("producer's compiled filename differs from the request")
    return code
