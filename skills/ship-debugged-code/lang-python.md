# Python Debugging Idioms

## Built-in Debugger

- Use `breakpoint()` (Python 3.7+) — drops into `pdb` at the call site; respects the `PYTHONBREAKPOINT` env var (set to `ipdb.set_trace` for ipdb, `0` to disable)
- Useful `pdb` commands: `n` (next), `s` (step into), `c` (continue), `l` (list), `p expr` (print), `pp expr` (pretty print), `w` (where — show stack), `u`/`d` (up/down frame), `b file:line` (set breakpoint), `b file:line, condition` (conditional)
- For post-mortem debugging on an uncaught exception: `python -m pdb -c continue script.py` runs until exception, then drops into pdb at the failure site
- Inside a running program after a caught exception: `import pdb; pdb.post_mortem()` enters pdb at the last traceback

## Better Alternatives

- `ipdb` — pdb with IPython integration (autocomplete, syntax highlighting); `pip install ipdb` and `import ipdb; ipdb.set_trace()`
- `pudb` — full-screen TUI debugger with variable/stack panes; great for stepping through complex logic
- `IDE debuggers` — PyCharm and VS Code's Python extension support breakpoints, conditional breakpoints, exception breakpoints, expression evaluation, and remote debugging

## Stack Traces

- `traceback` module: `traceback.print_exc()` inside `except` to print the current exception's stack
- Python 3.11+ adds **fine-grained error locations** (`^^^^` underlines the failing expression in the traceback) — read these carefully, they often point at the exact attribute access or call that failed
- `from e` preserves the cause chain when re-raising: `raise CustomError("context") from e` — the original is shown in the traceback as "The above exception was the direct cause"
- Use `sys.excepthook = custom_hook` to globally capture unhandled exceptions (e.g., log to Sentry)

## Logging for Debugging

- Use the `logging` module, not `print()`. Configure with `logging.basicConfig(level=logging.DEBUG, format="%(asctime)s %(name)s %(levelname)s %(message)s")` during investigation
- `logger.exception(msg)` automatically attaches the current exception's stack trace — use inside `except` blocks
- Use **structured logging** for production debugging: `structlog` or stdlib `logging` with a JSON formatter
- Lazy-format messages: `logger.debug("got user %s", user)` — the formatter runs only if DEBUG is enabled, unlike f-strings

## Inspecting State

- `repr(obj)` shows the unambiguous representation; `str(obj)` shows the readable one — prefer `repr` for debugging
- `vars(obj)` returns `obj.__dict__` for simple state dump
- `dir(obj)` lists all attributes/methods — useful when you do not know what is on an object
- `type(obj).__mro__` shows the method resolution order — useful when inheritance is confusing
- `inspect.getsource(obj)` shows the source of a function/class — useful for understanding library behavior in place
- For dataclasses/Pydantic models: `asdict(obj)` / `obj.model_dump()` for structured view

## Common Python Bug Patterns

- **Mutable default arguments**: `def f(items=[])` shares the list across calls. Symptom: the function "remembers" things between unrelated calls. Fix: use `None` and create inside.
- **Late-binding closures in loops**: `funcs = [lambda: i for i in range(3)]` all return 2. Fix: `lambda i=i: i`.
- **Integer caching tricks**: `is` works for small ints (-5 to 256) but not large ones in CPython. Symptom: equality test sometimes works. Fix: always use `==`.
- **`__init__` returning a value**: silently ignored; instance remains the default. Fix: `__init__` returns None.
- **Generator exhaustion**: a generator can be iterated only once. Symptom: second `for` loop is empty. Fix: convert to `list` or rebuild the generator.
- **Circular import surfacing as `ImportError`**: usually because one module imports a name that another module has not yet defined at import time. Fix: move the import inside the function, or restructure.
- **`async def` accidentally called as sync**: returns a coroutine object instead of running. Symptom: `<coroutine object f at 0x...>` warning or silent no-op. Fix: `await f()` or `asyncio.run(f())`.
- **`datetime` naive vs aware**: comparing naive (no tzinfo) with aware raises TypeError. Fix: always use `datetime.now(tz=timezone.utc)` or equivalent.

## Profiling

- `cProfile` for CPU profiling: `python -m cProfile -s cumulative script.py | head -30`
- `py-spy` (sampling profiler, attaches to running processes without code changes): `py-spy record -o profile.svg --pid 12345`
- `tracemalloc` for memory: `tracemalloc.start(); ...; snapshot = tracemalloc.take_snapshot()`
- `memory-profiler` decorator `@profile` for line-by-line memory usage

## Remote / Production Debugging

- `debugpy` for VS Code remote attach: `import debugpy; debugpy.listen(("0.0.0.0", 5678)); debugpy.wait_for_client()`
- `manhole` for attaching to a running production process via Unix socket
- For containerized: `kubectl exec` + `py-spy dump --pid 1` gets a stack snapshot without code changes
- Never enable `pdb.set_trace()` in production code paths — it will hang the process

## Bisection

- `git bisect run pytest tests/test_login.py::test_valid_login` — bisect over commits, fail when the test fails
- Make sure the test exits 0 on good and non-zero on bad; `pytest -x` makes this work for most cases

## Common Traps

- **Forgetting to `await` an async function**: passes type check, returns coroutine, never executes. Lint with `pylint`/`ruff` rule for unawaited coroutines.
- **`except:` without specifying type**: catches `KeyboardInterrupt` and `SystemExit`. Always catch specific types.
- **F-strings in log calls**: `logger.debug(f"user {user}")` formats even when DEBUG is off, wasting CPU. Use lazy `%s` formatting.
- **Reusing a `MagicMock` across tests**: state leaks between tests, breaking isolation. Use fresh mocks per test.
