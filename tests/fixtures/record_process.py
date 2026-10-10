from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sys
from types import CodeType

from yidl_cache import CacheRequest
from yidl_cache import CompilationContext
from yidl_cache import DependencyInventory
from yidl_cache import GeneratedCodeCache


def generate_record(request: CacheRequest) -> CodeType:
    import ast

    initializer = ast.FunctionDef(
        name="__init__",
        args=ast.arguments(
            posonlyargs=[],
            args=[ast.arg(arg="self"), ast.arg(arg="value")],
            vararg=None,
            kwonlyargs=[],
            kw_defaults=[],
            kwarg=None,
            defaults=[ast.Name(id="default", ctx=ast.Load())],
        ),
        body=[
            ast.Assign(
                targets=[
                    ast.Attribute(
                        value=ast.Name(id="self", ctx=ast.Load()),
                        attr="value",
                        ctx=ast.Store(),
                    ),
                ],
                value=ast.Name(id="value", ctx=ast.Load()),
            ),
        ],
        decorator_list=[],
        type_params=[],
    )
    builder = ast.FunctionDef(
        name="build_record",
        args=ast.arguments(
            posonlyargs=[],
            args=[ast.arg(arg="default")],
            vararg=None,
            kwonlyargs=[],
            kw_defaults=[],
            kwarg=None,
            defaults=[],
        ),
        body=[
            ast.ClassDef(
                name="Record",
                bases=[],
                keywords=[],
                body=[initializer],
                decorator_list=[],
                type_params=[],
            ),
            ast.Return(value=ast.Name(id="Record", ctx=ast.Load())),
        ],
        decorator_list=[],
        type_params=[],
    )
    module = ast.fix_missing_locations(ast.Module(body=[builder], type_ignores=[]))
    return compile(
        module,
        request.compilation.filename,
        "exec",
        flags=request.compilation.flags,
        dont_inherit=request.compilation.dont_inherit,
        optimize=request.compilation.optimize,
    )


def main() -> None:
    directory, value, forbid_generation = sys.argv[1:]
    request = CacheRequest(
        namespace="independent.records",
        generator_revision="1",
        input_digest=hashlib.sha256(b"record with bound default").hexdigest(),
        compilation=CompilationContext(filename="<independent-record>"),
        dependencies=DependencyInventory.capture({"producer": Path(__file__)}),
    )
    generation_calls = 0

    def produce() -> CodeType:
        nonlocal generation_calls
        generation_calls += 1
        if forbid_generation == "yes":
            raise AssertionError("warm process must not generate or compile")
        return generate_record(request)

    cache = GeneratedCodeCache(Path(directory), enabled=True)
    result = cache.get(request, produce)
    first_namespace = {"__name__": "independent.first"}
    second_namespace = {"__name__": "independent.second"}
    exec(result.code, first_namespace)
    exec(result.code, second_namespace)
    first = first_namespace["build_record"](int(value))
    second = second_namespace["build_record"](int(value) + 1)
    assert first is not second
    assert first.__module__ == "independent.first"
    assert second.__module__ == "independent.second"
    print(
        json.dumps(
            {
                "result": type(result).__name__,
                "generation_calls": generation_calls,
                "values": [first().value, second().value],
                "consumer_imports": sorted(
                    name
                    for name in ("yidl", "astichi", "yidl_lifecycle", "pyrolyze")
                    if name in sys.modules
                ),
            },
        ),
    )


if __name__ == "__main__":
    main()
