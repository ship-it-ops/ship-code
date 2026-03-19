# Python Clean Code Idioms

## Naming Conventions

- `snake_case` for functions, methods, variables, modules
- `PascalCase` for classes
- `UPPER_SNAKE_CASE` for constants
- `_leading_underscore` for private/internal
- `__dunder__` for special methods only

## Type Hints

- Add type hints to all function signatures (parameters and return types)
- Use `X | None` syntax (Python 3.10+). For 3.9 codebases, add `from __future__ import annotations`
- Use lowercase generic syntax: `list[str]`, `dict[str, int]` (Python 3.9+) over `List[str]`, `Dict[str, int]`
- Prefer `Sequence`, `Mapping`, `Iterable` over concrete types in function parameters
- Use `TypeVar` and generics for reusable typed functions

## Data Structures

- Prefer `dataclasses` or `NamedTuple` over raw dicts for structured data
- Use `enum.Enum` for fixed sets of values
- Prefer `attrs` or `pydantic` for validated data with complex invariants

## Error Handling

- Raise specific exceptions, never bare `raise` or `raise Exception`
- Never use bare `except:` — always catch specific exceptions
- Use `try/except/else/finally` properly (else = no exception path)
- Prefer EAFP (Easier to Ask Forgiveness than Permission) over LBYL
- Use custom exception classes for domain errors
- The "no null return" rule applies to your own functions. Returning `None` from a private filter/search helper is acceptable when the type hint makes optionality explicit (`-> Transaction | None`). Prefer exceptions for error states; use `None` only for "not found" / "absent" semantics.

## Resource Management

- Always use `with` statements for file handles, locks, DB connections
- Implement `__enter__`/`__exit__` or use `contextlib.contextmanager`
- Use `signal.signal(signal.SIGTERM, handler)` for graceful shutdown in containerized environments. `atexit` does NOT handle SIGTERM — it only triggers on interpreter shutdown.

## Common Traps

- **Mutable default arguments**: `def f(items=[])` shares the list across calls. Use `None` default and create inside the function.
- **Late binding closures**: `lambda: x` in a loop captures the variable, not the value. Use default arg `lambda x=x: x`.
- **Circular imports**: Restructure modules or use local imports inside functions.
- **`is` vs `==`**: `is` checks identity, `==` checks equality. Only use `is` for `None`, `True`, `False`.
- **String concatenation in loops**: Use `''.join()` or f-strings instead of `+=`.

## Pythonic Patterns

- List/dict/set comprehensions over `map`/`filter` when readable
- Generator expressions for large sequences
- `enumerate()` instead of manual counter
- `zip()` for parallel iteration
- Walrus operator `:=` for assignment in expressions (Python 3.8+)
- `pathlib.Path` over `os.path` string manipulation
- f-strings over `.format()` or `%` formatting

## Function Design

- Keep functions short — ideally under 20 lines
- Use `*` to force keyword-only arguments for clarity
- Return early to avoid deep nesting
- Use `functools.lru_cache` for expensive pure functions
- Avoid `*args, **kwargs` unless writing decorators or wrappers

## Module Organization

- One class per file is not required — group related small classes together
- Use `__all__` to define public API of a module
- Place imports at the top: stdlib, third-party, local (separated by blank lines)
- Avoid wildcard imports (`from module import *`)

## Async Patterns

- Use `async def` / `await` for I/O-bound operations (web requests, DB queries, file I/O)
- **Never call blocking I/O inside `async def`** — no `open()`, `requests.get()`, `time.sleep()`. Use `aiofiles`, `httpx`, `asyncio.sleep()`, or run in executor
- Use `asyncio.gather()` for concurrent independent operations
- Use `async with` for async context managers (e.g., `aiohttp.ClientSession`)
- Entry point: `asyncio.run(main())` (Python 3.7+)

## Testing Conventions

- Use `pytest` as the test runner. Name test files `test_*.py`, test functions `test_should_*` or `test_<behavior>_when_<condition>`
- Use `@pytest.fixture` for setup. Understand scope hierarchy: `function` (default), `class`, `module`, `session`
- Use `conftest.py` for shared fixtures — fixtures are inherited by all tests in the directory and below
- Use `@pytest.mark.parametrize` with `ids=` for readable failure output
- Use `pytest.raises(ExceptionType, match="regex")` for exception assertions
- Use `tmp_path` fixture for filesystem tests (auto-cleaned)
- Use `monkeypatch` for environment variables; prefer fakes over `unittest.mock.patch` for service dependencies
- Use `@pytest.mark.asyncio` for async test functions (requires `pytest-asyncio`)
- Use `freezegun` or `time-machine` for time-dependent tests
