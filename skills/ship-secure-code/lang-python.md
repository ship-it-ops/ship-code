# Python Secure-Code Patterns

Per-SEC-category detection patterns for Python, organized by framework. For per-pattern rubric depth (anti-overlap, false-positive notes), see `reference-categories.md`.

Frameworks covered: Django, FastAPI, Flask, Pyramid, Starlette, SQLAlchemy, Pydantic, DRF.

---

## SEC1 — AUTH

### SEC1.1 — Missing AuthN

**Django:**
- New view in `views.py` (function-based or class-based) without `@login_required` decorator (function), `LoginRequiredMixin` (class-based), or `@method_decorator(login_required, name='dispatch')`.
- DRF viewset / generic view without `permission_classes = [IsAuthenticated]` (or stricter). Check the global `DEFAULT_PERMISSION_CLASSES` in settings — if it's `AllowAny`, every view needs explicit override.
- Custom permission class that returns `True` unconditionally.

**FastAPI:**
- New endpoint without a `Depends(get_current_user)` (or equivalent) parameter. Search for `@app.get|post|put|patch|delete` decorators followed by handlers missing the auth dependency.
- `OAuth2PasswordBearer(tokenUrl=..., auto_error=False)` — silently allows unauthenticated; usually wrong.

**Flask:**
- New `@app.route` or blueprint route without `@login_required` (Flask-Login).
- `@app.route` for state-changing methods (POST/PUT/DELETE) without auth check inside the body.

**Pyramid:**
- `config.add_view(view, ...)` without `permission='...'` argument or default permission set.

### SEC1.2 — IDOR / Missing AuthZ

- `Model.objects.get(id=request.GET['id'])` / `Model.objects.get(pk=request.POST['id'])` without `.filter(owner=request.user)` first.
- `Document.objects.get(id=id)` where the user is logged in but ownership is not checked.
- DRF: `queryset = Model.objects.all()` in a viewset instead of `queryset = Model.objects.filter(owner=self.request.user)`.
- SQLAlchemy: `session.query(Document).filter_by(id=id).one()` without tenant/owner filter.
- Tenant-scoped resource fetched without tenant scope: `db.documents.find_one({'id': id})` instead of `{'id': id, 'tenant_id': ctx.tenant_id}`.

### SEC1.3 — Broken session

- Session cookie config missing `SESSION_COOKIE_HTTPONLY = True` / `SESSION_COOKIE_SECURE = True` / `SESSION_COOKIE_SAMESITE = 'Lax'` in Django settings.
- Flask: `app.config['SESSION_COOKIE_HTTPONLY']` not set (defaults to True but worth verifying for custom configs).
- Logout that doesn't actually rotate the session ID (Django's `logout()` does; custom implementations may not).

### SEC1.4 — Over-privileged

- Container running as root: `USER root` or no `USER` directive in Dockerfile, plus Python process started from that user.
- DB connection string using superuser: `postgres://postgres:...` or `mysql://root:...`.
- AWS IAM role with `*` action (check `boto3.client(..., aws_access_key_id=...)` setup paths).

### SEC1.5 — JWT misuse

- `jwt.decode(token, options={'verify_signature': False})` — accepts forged tokens.
- `jwt.decode(token, key, algorithms=None)` — `algorithms` arg required in PyJWT >= 2.0.
- `jwt.decode(token, key, algorithms=['none'])`.
- `python-jose`, `authlib.jose` — same checks.

---

## SEC2 — INPUT-VALIDATION

### SEC2.1 — No schema validation at boundary

**FastAPI:**
- Endpoint handler missing a Pydantic model in its signature: `def handler(request: Request)` with `await request.json()` instead of `def handler(payload: PaymentPayload)`.
- Pydantic v2 model without `model_config = ConfigDict(extra='forbid')` accepting unknown fields.
- Pydantic v1 model without `class Config: extra = 'forbid'`.

**Django / DRF:**
- DRF `Serializer.save()` called without `is_valid(raise_exception=True)`.
- Django view accessing `request.POST['field']` / `request.GET['field']` directly without `forms.Form` validation.

**Flask:**
- `request.get_json()` followed by direct `data['field']` access without a Pydantic / marshmallow / cerberus schema.

### SEC2.2 — Denylist patterns

- `if 'javascript:' in url.lower():` — denylist; use allowlist `if not url.startswith(('http://', 'https://')):`.
- `re.sub(r'<script>', '', input, flags=re.I)` — naive HTML stripping; use `bleach.clean` or `nh3.clean`.
- `if filename.endswith('.exe'): reject()` — denylist of extensions; allowlist is correct.

### SEC2.3 — Partial validation

- Pydantic schema validates some fields, handler reads more via `request.body`. Pydantic catches this only with `extra='forbid'`.
- DRF serializer fields don't cover all `request.data` keys accessed in `perform_create`/`perform_update`.

---

## SEC3 — INJECTION

### SEC3.1 — SQL injection

- f-string SQL: `cursor.execute(f"SELECT * FROM users WHERE id = {id}")`.
- `%` formatting: `cursor.execute("SELECT * FROM users WHERE id = %s" % id)` (string formatting BEFORE the driver sees it — wrong; use parameterized `(id,)` as second arg).
- `.format()` on SQL: `cursor.execute("SELECT * FROM x WHERE y = {}".format(y))`.
- SQLAlchemy raw: `session.execute(text(f"... {user_input}"))` — use `text(":id").bindparams(id=user_input)` or `bindparam`.
- SQLAlchemy ORM `.filter()` with f-string: `Model.query.filter(text(f"x = {y}"))`.
- Django ORM raw: `Model.objects.raw(f"... {x}")`, `Model.objects.extra(where=[f"... {x}"])`, `Model.objects.extra(select={'x': f"... {y}"})`.

### SEC3.2 — NoSQL injection (MongoDB)

- PyMongo: `db.users.find({'email': request.json['email']})` where the JSON value can be a dict like `{'$ne': None}`. Coerce: `db.users.find({'email': str(request.json['email'])})`.
- Mongoengine: same risk.

### SEC3.3 — OS command injection

- `subprocess.run(f"ls {user_input}", shell=True)`.
- `subprocess.call(f"convert {file_in} {file_out}", shell=True)`.
- `os.system(user_input)`, `os.popen(user_input)`.
- `commands.getoutput(...)` (Python 2 legacy, sometimes still seen).

Use `subprocess.run(['ls', user_input], shell=False)` — args as list, `shell=False`.

### SEC3.4 — LDAP injection

- `ldap.search_s(base, scope, f"(uid={user_input})")` — escape with `ldap.dn.escape_dn_chars` or `ldap3.utils.conv.escape_filter_chars`.

### SEC3.5 — XPath injection

- `tree.xpath(f"//user[@name='{name}']")` — use lxml's parameterized XPath via `xpath(..., name=value)` form.

### SEC3.6 — Log injection (CRLF)

- `logger.info(f"User logged in: {user_input}")` — `user_input` containing `\n` injects fake log lines. Strip CRLF: `logger.info("user.login", extra={'user_id': user_input.replace('\\n', '').replace('\\r', '')})`.
- Better: log structured fields, not interpolated strings, so untrusted values are never part of the format string.

### SEC3.7 — Header injection (CRLF)

- Django: `response['X-Foo'] = user_input` — modern Django raises on newlines, but custom WSGI middleware may not.
- Flask: `response.headers['X-Foo'] = user_input` — same.

### SEC3.8 — Template injection / SSTI

- Jinja2: `Template(user_input).render()` — RCE via `{{config.__class__.__init__.__globals__['os'].popen('id').read()}}`.
- Mako: `Template(user_input).render()` — Python expression evaluation.
- Django: `Template(user_input).render(Context())` — less powerful than Jinja2 but still risky.

**Fix:** never accept template strings from users. If users provide content, they provide data, not templates.

### SEC3.9 — Prototype-pollution analog

- `dict.update(untrusted_dict)` where `untrusted_dict` has special keys (`__class__`, `__init_subclass__`) — affects Pydantic v1 (`Model(**untrusted)` blocks `_`-prefixed but not all).
- `setattr(obj, user_attr_name, user_value)` — gadget for type confusion.

---

## SEC4 — XSS / OUTPUT-ENCODING

### SEC4.1 — Unsafe HTML rendering

**Django templates:**
- `{% autoescape off %}` block surrounding user-rendered content.
- `{{ user_input|safe }}` — marks as safe-HTML.
- `mark_safe(user_input)` in Python code.
- `format_html("{}", user_input)` is safe; `format_html(user_input)` without `{}` placeholders is not.

**Jinja2:**
- `Environment(autoescape=False)` — should be `autoescape=select_autoescape(['html', 'xml'])`.
- `{{ user_input|safe }}` filter.
- `Markup(user_input)` in Python code wrapping raw HTML.

**Mako:**
- `${user_input | n}` — `n` filter disables autoescape.

**Flask:**
- `flask.Markup(user_input)` returned to template.
- `render_template_string(f"... {user_input} ...")` — combined SSTI + XSS risk.

**FastAPI / Starlette:**
- `HTMLResponse(user_html)` directly without sanitization.

### SEC4.2 — Markdown without sanitization

- `markdown.markdown(user_md)` (Python `markdown` lib) — doesn't sanitize by default; use `markdown.markdown(user_md, extensions=['markdown.extensions.sane_lists'])` plus `bleach.clean` post-process.
- `mistune.html(user_md)` — same.

### SEC4.3 — Unsafe URL contexts

- Django: `{% url ... %}` with user-controlled name argument.
- Direct insertion into template `href`: `<a href="{{ user_url }}">` without scheme allowlist.
- `redirect(user_url)` — open redirect risk (also SEC12.4).

### SEC4.4 — CSS injection

- `style="{{ user_style }}"` in templates without escaping.

---

## SEC5 — CSRF / ORIGIN

### SEC5.1 — Missing CSRF token

- Django: `@csrf_exempt` decorator without justification.
- Django: `CSRF_TRUSTED_ORIGINS` includes wildcard `*` or `http://` (not https).
- DRF: `SessionAuthentication` used without CSRF protection (DRF enforces CSRF only for SessionAuthentication; verify it's not bypassed).
- Flask: missing `CSRFProtect()` from Flask-WTF on the app.
- Flask: `@csrf.exempt` decorator without justification.

### SEC5.2 — postMessage origin verification

(Browser-side, not Python-specific — see `lang-typescript.md` SEC5.2.)

### SEC5.5 — CORS misconfiguration

- FastAPI: `CORSMiddleware(allow_origins=['*'], allow_credentials=True)` — invalid combo, misconfig.
- Django: `django-cors-headers` with `CORS_ALLOW_ALL_ORIGINS = True` AND `CORS_ALLOW_CREDENTIALS = True`.
- Reflected origin: `CORS_ALLOWED_ORIGIN_REGEXES = [r'.*']`.

---

## SEC6 — CRYPTO

### SEC6.1 — Weak password hash

- `hashlib.md5(password.encode()).hexdigest()` for passwords.
- `hashlib.sha1`, `hashlib.sha256`, `hashlib.sha512` for password storage.
- Django: `make_password(password, hasher='unsalted_md5')` — explicit weak hasher.
- Custom: `def hash_password(pw): return hashlib.sha256((pw + SALT).encode()).hexdigest()`.

**Fix:** `bcrypt` (`bcrypt.hashpw(pw.encode(), bcrypt.gensalt())`), `argon2-cffi` (`PasswordHasher().hash(pw)`), or Django's default password hasher (`Argon2PasswordHasher`).

### SEC6.2 — Weak RNG for security

- `random.random()`, `random.randint()`, `random.choice()`, `random.choices()` for security tokens (session IDs, password reset, API keys).
- `uuid.uuid1()` — based on MAC address + time, semi-predictable; use `uuid.uuid4()` (random) or `secrets.token_urlsafe()`.

**Fix:** `secrets.token_urlsafe(32)`, `secrets.token_hex(16)`, `secrets.token_bytes(32)`, `secrets.choice(allowlist)`.

### SEC6.3 — Deprecated / weak ciphers

- `Crypto.Cipher.AES.new(key, AES.MODE_ECB)` — ECB mode leaks plaintext patterns.
- `Crypto.Cipher.DES`, `Crypto.Cipher.DES3` — deprecated.
- `Crypto.PublicKey.RSA.generate(1024)` — 1024-bit RSA broken; use 2048 minimum, 3072 preferred.
- `cryptography.hazmat.primitives.ciphers.algorithms.ARC4` — deprecated.

### SEC6.4 — Hardcoded IV / salt / key

- `cipher = AES.new(key, AES.MODE_CBC, iv=b'1234567812345678')` — literal IV.
- `bcrypt.hashpw(pw, salt=b'constant_salt')` — defeats salting.
- Hardcoded key as literal: `KEY = b'...'`.

### SEC6.5 — JWT misuse

- See SEC1.5.

### SEC6.6 — TLS misconfiguration

- `ssl.SSLContext(ssl.PROTOCOL_TLSv1)` — TLS 1.0 deprecated.
- `ssl.SSLContext(ssl.PROTOCOL_SSLv23)` (often actually negotiates TLS but the name is misleading; use `PROTOCOL_TLS_CLIENT`/`PROTOCOL_TLS_SERVER`).
- `requests.get(url, verify=False)` — disables cert validation.
- `urllib3.disable_warnings(InsecureRequestWarning)` paired with `verify=False`.

---

## SEC7 — SECRETS

### SEC7.1 — Hardcoded secret literal

- `STRIPE_SECRET = 'sk_live_...'`, `AWS_ACCESS_KEY_ID = 'AKIA...'`.
- Django: `SECRET_KEY = '...'` literal in `settings.py` (should be `SECRET_KEY = os.environ['DJANGO_SECRET_KEY']`).
- Database URL with embedded password: `DATABASE_URL = 'postgresql://user:realpass@host/db'`.
- `requirements.txt` with index URL containing credentials: `--index-url https://user:pass@private.pypi.org/simple/`.

### SEC7.2 — Committed `.env`

- `.env`, `.env.local`, `.env.production` tracked.

### SEC7.3 — Token in URL

- `requests.get(f'https://api.example.com/?token={TOKEN}')` — tokens in URLs leak via referrer / proxy logs.

### SEC7.4 — CI YAML literal secret

- `.github/workflows/*.yml` containing `KEY: sk_live_...` instead of `KEY: ${{ secrets.KEY }}`.
- `Jenkinsfile` with `withCredentials(...)` argument pattern containing literal value.

### SEC7.5 — Runtime artifacts

- `*.pyc` committed (unusual; usually in `.gitignore`).
- `__pycache__/` committed.
- `.python-version` for sensitive prod vs `.tool-versions` — fine.

### SEC7.6 — Secrets in code comments

- `# api key from staging: sk_test_...` — old debug comment.
- Old `print(token)` statements left in code.

---

## SEC8 — SUPPLY-CHAIN

### SEC8.1 — Suspicious new dep

When `requirements.txt` / `pyproject.toml` / `Pipfile` adds a new dep:

- Run `pip-audit` and check the package's first-published date and download count on PyPI (`pip show <pkg>`, or check `pypi.org`).
- Name typosquats: `request` (popular) vs `requests` (the typo would be the one with the trailing 's' missing); `python-dateutils` (typo of `python-dateutil`); `urllib` vs `urllib3`; `colors` vs `colored`.
- `setup.py` with a `cmdclass` that runs arbitrary code at install — read the file.

### SEC8.2 — Non-registry dependency source

- `pip install` from a git URL without commit pinning: `git+https://github.com/x/y.git` (no `@<commit>`).
- `requirements.txt` with `-e <path>` editable install referencing a path outside the repo.
- PyPI mirror configured to a non-trusted host.

### SEC8.3 — Lockfile drift

- `Pipfile.lock` / `poetry.lock` change introducing a package from a non-pypi source.
- Lockfile change without a corresponding `Pipfile`/`pyproject.toml` change.

### SEC8.4 — Known CVE

- `pip-audit` / `safety check` reports a high/critical CVE in a direct or transitive dep added by this PR.

---

## SEC9 — PII / LOGGING

### SEC9.1 — PII in logs

- `logger.info(f"User: {user}")` where `user` is a model instance whose `__repr__` exposes `email`, `phone`, `ssn`, etc.
- `print(user.dict())` (Pydantic) including PII fields.
- Django: `logger.info("User: %s", user)` — model `__str__` may include email.

### SEC9.2 — Unredacted request/response logging

- Django: `LOGGING` config without filtering `Authorization` / `Cookie` / `Set-Cookie` headers.
- DRF: logging request body via custom middleware without redacting `password`, `token` fields.
- FastAPI: middleware logging `await request.body()` without redaction.

### SEC9.3 — Analytics with PII

- `analytics.track('event', properties={'email': user.email})`.
- Mixpanel/Segment with email/phone as identifying property.

### SEC9.4 — Error responses leaking PII

- Django: `DEBUG = True` in production — error pages reveal stack traces + locals (which include user data).
- DRF: validation error response echoing the user's submitted value verbatim.
- FastAPI: default 422 response includes the input that failed validation, which may include PII.

### SEC9.5 — Sentry / Bugsnag init

- `sentry_sdk.init(dsn=..., send_default_pii=True)` — defaults to True in some configs; should be False.
- `sentry_sdk.init(...)` without a `before_send` scrubber.
- Bugsnag init without `params_filters` for sensitive fields.

---

## SEC10 — RESOURCE-EXHAUSTION

### SEC10.1 — ReDoS

- `re.compile(r'^(a+)+$')`, `re.compile(r'^(\w+)*$')` — nested quantifiers.
- `re.match` / `re.search` on user input with potentially-catastrophic patterns.
- Python's `re` module doesn't have a timeout option; for untrusted input use the `re2` package (Google RE2 binding) or `regex` with `regex.DEFAULT_VERSION = regex.VERSION1` (still no timeout).

### SEC10.2 — Unbounded concurrency

- `asyncio.gather(*[fetch(u) for u in untrusted_list])` — unbounded concurrency. Use `asyncio.Semaphore(N)`.
- `ThreadPoolExecutor(max_workers=None)` — defaults to `min(32, os.cpu_count() + 4)`, fine for trusted lists but not for user-driven fanout.
- `multiprocessing.Pool()` without explicit size.

### SEC10.3 — Missing request size cap

- Django: `DATA_UPLOAD_MAX_NUMBER_FIELDS = None` (default 1000, but `None` disables) or `DATA_UPLOAD_MAX_MEMORY_SIZE = None` (default 2.5MB).
- FastAPI: no `Body(..., max_length=...)` on string body fields.
- Flask: `MAX_CONTENT_LENGTH` not set.

### SEC10.4 — Missing rate limit

- Auth endpoints without `django-ratelimit` / `django-axes` / `fastapi-limiter`.
- Search endpoints with expensive queries and no rate limit.

### SEC10.5 — Large file / JSON / image processing

- `json.loads(huge_str)` without size pre-check.
- Pillow `Image.open(buf)` without max-dimension check (decompression bomb).
- XML parsing with entity expansion not limited (`xml.etree.ElementTree` is vulnerable; use `defusedxml`).
- `pandas.read_csv(user_file)` without `nrows` or chunk processing.

---

## SEC11 — PATH-TRAVERSAL / FILE-OPS

### SEC11.1 — Path traversal

- `open(os.path.join(uploads_dir, request.GET['file']))` without normalize + boundary check.
- `pathlib.Path(uploads) / filename` where filename is user-controlled.
- Django: `os.path.join(settings.MEDIA_ROOT, user_path)` then `open()` — same risk.

**Canonical fix:**
```python
from pathlib import Path
def safe_path(uploads_dir: str, user_filename: str) -> Path:
    base = Path(uploads_dir).resolve()
    candidate = (base / user_filename).resolve()
    if not candidate.is_relative_to(base):
        raise ValueError("path escapes upload dir")
    return candidate
```

### SEC11.2 — Archive extraction

- `zipfile.ZipFile.extractall(path)` — vulnerable to zip slip via `..` in entry names. Iterate entries and validate each path is inside the target.
- `tarfile.TarFile.extractall(path)` — vulnerable to tar slip AND symlink attacks. On Python 3.12+, use `extractall(path, filter='data')`. On earlier versions, manually validate each entry.
- `shutil.unpack_archive` — wraps both; same risk.

### SEC11.3 — Unsafe file ops

- `shutil.move(src, dst)` with user-controlled `dst`.
- `os.symlink(target, user_path)` where target is sensitive.
- `os.chmod(user_path, mode)`.

### SEC11.4 — Filename sanitization

- Storing uploaded file with user-provided name: `with open(os.path.join(dir, file.filename), 'wb') as f:`. Use UUID-based names.
- Filenames with null bytes (`upload.pdf\x00.jpg`) — older code may treat as `.pdf`.

---

## SEC12 — DESERIALIZATION / SSRF

### SEC12.1 — Unsafe deserialization

- `pickle.loads(bytes_from_user)` — RCE.
- `pickle.load(file_from_user)` — same.
- `cPickle.loads()` — same (Py2 legacy).
- `yaml.load(yaml_str)` without `Loader=SafeLoader` — RCE via Python tags. PyYAML 6+ requires explicit Loader, but older versions don't.
- `marshal.loads()`, `shelve.open(user_path)`, `dill.loads()`.

**Fix:** use JSON for cross-trust-boundary data. For YAML, `yaml.safe_load()`. For Python-specific serialization where the source is fully trusted, document the trust assumption.

### SEC12.2 — XXE (XML External Entity)

- `xml.etree.ElementTree.parse(user_xml)` — vulnerable to XXE.
- `xml.dom.minidom.parseString(user_xml)` — vulnerable.
- `lxml.etree.parse(user_xml)` with default parser — vulnerable; use `lxml.etree.XMLParser(resolve_entities=False, no_network=True)`.

**Fix:** `defusedxml.ElementTree`, `defusedxml.lxml`. Always for untrusted XML.

### SEC12.3 — SSRF

- `requests.get(user_url)` server-side without scheme + host allowlist + private-IP block.
- `urllib.request.urlopen(user_url)`.
- `httpx.get(user_url)`, `aiohttp.ClientSession().get(user_url)`.
- `requests.get(user_url, allow_redirects=True)` — redirect-follow can hop to internal addresses.

**Fix:**
```python
from urllib.parse import urlparse
import ipaddress, socket

def is_safe_url(url: str) -> bool:
    parsed = urlparse(url)
    if parsed.scheme not in ('http', 'https'):
        return False
    if not parsed.hostname:
        return False
    try:
        for family, _, _, _, addr in socket.getaddrinfo(parsed.hostname, None):
            ip = ipaddress.ip_address(addr[0])
            if ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_reserved:
                return False
    except socket.gaierror:
        return False
    return True
```

### SEC12.4 — Open redirect

- Django: `return redirect(request.GET['next'])` — Django's `redirect` only validates if the value is a model/URL pattern; raw URLs go through. Use `is_safe_url(url, allowed_hosts={request.get_host()})`.
- Flask: `return redirect(request.args.get('next'))` — same risk; use `is_safe_url` from werkzeug's old helper or implement an allowlist.

---

## Quick triage for diff reviews

1. **Boundary first** — every view/handler/dependency. AuthN (SEC1.1) and schema validation (SEC2.1).
2. **Sinks second** — for each `cursor.execute`, `subprocess.run`, `open`, `pickle.loads`, `requests.get`, look back to source.
3. **Output third** — for each `|safe`, `mark_safe`, `Markup`, `HTMLResponse`, confirm sanitization.
4. **Layer fourth** — CSRF, CSP, CORS, rate limit, request size cap.
5. **Crypto/secrets fifth** — `hashlib.md5`, `random.random()`, hardcoded keys.
