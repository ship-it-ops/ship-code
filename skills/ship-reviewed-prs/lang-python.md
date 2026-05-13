# Python PR-Review Idioms

PR-review-specific patterns for Python. For file-level Python idioms (naming, error handling, async), defer to `ship-clean-code/lang-python.md`. This file covers the patterns each persona looks for in a *PR* context.

---

## SC — Senior Security Engineer (Python patterns)

### Auth/Authz (SC1)

- **Django**: new `path()` in `urls.py` without `@login_required` / `@permission_required` decorator on the view, or without DRF `permission_classes` on a ViewSet. Verify with `grep -E '@login_required|permission_classes' <view-file>`.
- **Flask**: new `@app.route` or `@blueprint.route` without `@login_required` (Flask-Login) or equivalent.
- **FastAPI**: new path operation without `Depends(get_current_user)` or `Security(...)` in the signature, on routes outside `/health`, `/metrics`, public docs.
- **Pattern that bypasses auth**: a view that calls `request.user` without first ensuring `request.user.is_authenticated`. Or `current_user` in Flask before checking `is_authenticated`.

### Injection (SC2)

- **SQL**: f-strings in `cursor.execute()`, `.raw()`, `connection.execute()`. Acceptable: parameterized queries via `cursor.execute("...", (param,))` or ORM `Model.objects.filter(field=value)`.
- **SQLAlchemy raw SQL**: `text(f"SELECT ... {var}")` is injection. `text("SELECT ... :v").bindparams(v=var)` is safe.
- **Shell command injection**: `subprocess.run(..., shell=True)` with any user-controllable input. Use `shell=False` (default) and pass argv list.
- **Template injection (SSTI)**: Jinja2 `Template(user_input).render()`. Should never accept user-controllable template strings.
- **Deserialization**: `pickle.loads()`, `yaml.load()` (without `SafeLoader`), `marshal.loads()` on user input.

### Secrets (SC3)

- `DJANGO_SECRET_KEY`, `SECRET_KEY`, `API_KEY`, `*_TOKEN`, `*_PASSWORD` assigned to a literal string at module level — should be `os.environ[...]` or read from secrets manager.
- New `.env` file committed. Files matching `.env*` should be in `.gitignore` and `git-secrets` should fail on these patterns; flag any PR that adds one.
- `requirements.txt` / `pyproject.toml` containing a Git URL with a token: `git+https://oauth:TOKEN@github.com/...`.

### Crypto misuse (SC4)

- `hashlib.md5()` or `hashlib.sha1()` used for password hashing or signature verification — flag. Use `bcrypt`, `argon2-cffi`, or `passlib`.
- `Crypto.Cipher.AES.new(key, AES.MODE_ECB)` — ECB mode reveals patterns. Use GCM or CBC with random IV.
- Fixed IV: `cipher = AES.new(key, AES.MODE_CBC, b"0000000000000000")`. IV must be random per-encryption.
- JWT verification with `verify=False` or `algorithms=["none"]`. The `python-jose` and `PyJWT` libraries both support this misuse.

### Supply chain (SC5)

- New entry in `requirements.txt` / `pyproject.toml` / `setup.py` / `Pipfile` / `poetry.lock`. Check:
  - Package age (`pip show <pkg>` or pypi.org first-published date) — < 3 months is suspicious.
  - Package downloads per week (`pypistats recent <pkg>`) — very low downloads, recently uploaded, no GitHub link is a typosquat signal.
  - Known CVEs: `pip-audit` output, GitHub Advisory Database.
- `setup.py` with `cmdclass={"install": CustomInstall}` from a third-party package — postinstall code execution.
- New `--index-url` or `--extra-index-url` pointing to a non-PyPI host.

### PII / log leakage (SC6, SC7)

- `logger.info(f"User logged in: {user.email}")` — PII in logs. Replace with user ID or hashed identifier.
- `logger.exception(e)` with a stack trace that contains the original request body — Django's default `request_logger` includes POST data unless filtered. Check `LOGGING` config.
- DRF serializer that includes `password`, `token`, or `secret` fields in `to_representation()`. Verify with `grep -B 5 -A 20 "class.*Serializer" <file>`.

---

## SE — Senior Engineer (Python patterns)

### Breaking changes (SE1)

- Public function in `__init__.py` or `__all__` removed or renamed.
- Required positional argument added to a function that's part of the public API.
- Decorator behavior changed (e.g., `@cached_property` semantics changed from `@property` + caching elsewhere).

### Contract drift (SE2)

- TypedDict / dataclass field made `Optional` where it was required.
- Pydantic model: `Optional[X]` ↔ `X` change, `default` change, `validator` semantics change.
- DRF / FastAPI response model field renamed or removed.
- Django model field's `null=True ↔ null=False`, `blank=True ↔ blank=False` change without a corresponding migration / data backfill.

### Rollout risk (SE3)

- New code path added without a feature flag in a service that has a feature-flag framework (look for `Flagsmith`, `LaunchDarkly`, `Unleash`, or project-internal flag module).
- `if settings.DEBUG:` guarding production-relevant behavior.

### Deprecation missing (SE5)

- Function removed in this PR; `git log` shows no prior commit marking it `@deprecated` (via `warnings.warn(DeprecationWarning)` or `@deprecated` decorator from `typing_extensions` 4.5+).

---

## IN — Senior Infra/SRE (Python patterns)

### Network call hygiene (IN1)

- `requests.get(url)` without `timeout=` — `requests` has no default timeout; hangs forever on a slow upstream. Always pass `timeout=(connect, read)` tuple or single seconds value.
- `httpx.get(url)` defaults to a 5s timeout (httpx ≥ 0.20) but should be explicit.
- `aiohttp.ClientSession()` without `timeout=ClientTimeout(...)`.
- `urllib.request.urlopen(url)` without `timeout=` argument.
- New async client without retry policy. The project's standard helper (often `lib/http.py`, `clients/base.py`) should be used.

### Observability (IN2)

- New endpoint (Django view, FastAPI route, Flask route) with no `logger.info` for state changes and no metric. Look for `prometheus_client.Counter`, `statsd`, `opentelemetry` imports as the project's metric pattern.
- Background task / Celery task without a structured log on start/finish/error.

### Resource limits (IN3)

- `for row in cursor:` or `Model.objects.all()` without `.iterator()` / pagination on a table that might have > 10k rows.
- `requests.get(url).content` on an unbounded response body — no `stream=True` + bounded read.
- New `Pool(processes=N)` without a sensible upper bound on N.

### Idempotency (IN4)

- Celery task that mutates state without an idempotency key or `@idempotent` decorator. Retries are on by default.
- Webhook handler with no replay-protection (timestamp + nonce check, or idempotency key from upstream).

### Migration safety (delegates to DA for correctness; IN owns ops)

- `RunPython` migration that does a full-table scan in a single transaction — locks the table. Use `atomic = False` and chunked updates.
- `AddIndex` without `CONCURRENTLY` on PostgreSQL: Django doesn't add CONCURRENTLY by default. Verify with `--sql` to see the generated DDL.

### Performance hot path (IN7)

- N+1 in a request handler. Patterns to look for: `for user in users: user.profile` (Django without `select_related`), `for obj in qs: obj.related_set.all()` without `prefetch_related`.
- Sync I/O inside an `async def` (`open()`, `requests.get()`, `time.sleep()`, blocking ORM call in async views). Use `aiofiles`, `httpx`, `asyncio.sleep()`, async ORM.

---

## DA — Senior Data Engineer (Python patterns)

### Schema break (DA1, DA2, DA3)

- **Django migration**: `RemoveField` on a field referenced in serializers, admin, signals, or external systems (analytics ETL). Cross-reference via `grep -rn "<field_name>" --include="*.py"`.
- **Alembic migration**: `op.drop_column()` on a column that may be referenced elsewhere. Same grep audit.
- **Reversibility**: every Alembic migration should have a non-trivial `downgrade()`. Empty downgrade is acceptable only for additive changes (CREATE TABLE, ADD COLUMN nullable).
- **NOT NULL + no backfill**: `op.alter_column(nullable=False)` without a backfill `op.execute("UPDATE ...")` step before it.

### Type precision (DA5)

- `models.FloatField()` for currency — use `DecimalField(max_digits=..., decimal_places=...)`.
- `models.DateTimeField()` without `USE_TZ = True` in settings — leads to naive datetime bugs.
- `models.CharField(max_length=N)` where N < typical real-world length for the field (email < 254, URL < 2048 per RFC).

### Event contract (DA6)

- Removing a field from a JSON Schema, Pydantic model, or protobuf message that's published to Kafka / SNS / EventBridge / Pub/Sub.
- Changing the type of a published field (string → int).

### Retention / PII (DA7)

- New `EmailField`, `PhoneField`, names, SSN, DOB column on a model. Check for a corresponding retention-policy entry in `docs/data-retention.md` or equivalent.

---

## TS — Test Reviewer (Python patterns)

### Test file detection

A file is in the `test` bucket if its path matches any of:
- `test_*.py`, `*_test.py`, `tests/`, `test/`, `__tests__/`
- `conftest.py` (pytest fixtures count as "test infrastructure")

### Production file detection

`code` bucket: `.py` files outside test paths, outside `migrations/`, outside `setup.py` / `conftest.py`.

### Coverage gap signal (TS1)

If ≥ 30 net added lines across `code` bucket files AND zero `test` bucket files added or modified, fire TS1.

### Regression test signal (TS2)

If PR description matches `(fixes|closes|resolves) #\d+` (case-insensitive) AND zero `test` bucket files added or modified, fire TS2.

Both findings delegate to `ship-tested-code` for depth.
