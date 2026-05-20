# Java Secure-Code Patterns

Per-SEC-category detection patterns for Java, organized by framework. For per-pattern rubric depth (anti-overlap, false-positive notes), see `reference-categories.md`.

Frameworks covered: Spring Boot, Spring Security, JPA/Hibernate, JAX-RS, Servlet API, Apache Shiro, OWASP ESAPI, Jackson.

---

## SEC1 — AUTH

### SEC1.1 — Missing AuthN

**Spring:**
- New `@GetMapping`/`@PostMapping`/`@PutMapping`/`@DeleteMapping`/`@PatchMapping`/`@RequestMapping` on a controller method without a `@PreAuthorize` / `@Secured` annotation, AND the `SecurityFilterChain` doesn't explicitly cover the path. Both checks are needed.
- Spring Security config with `.permitAll()` on a sensitive path matcher.
- Method-level: `@PreAuthorize("permitAll()")` or `@PreAuthorize("isAnonymous()")` on a state-changing operation.

**JAX-RS:**
- `@Path` resource method with `@PermitAll` annotation, or missing `@RolesAllowed`/`@DenyAll`.

**Servlet:**
- New `@WebServlet` / `@WebFilter` without `<security-constraint>` in `web.xml` or programmatic config.

### SEC1.2 — IDOR / Missing AuthZ

- Spring Data: `repository.findById(id)` returning a resource without ownership filter. Should be `repository.findByIdAndOwnerId(id, currentUser.getId())`.
- JPA: `entityManager.find(Document.class, id)` without tenant scope.
- `@PreAuthorize("isAuthenticated()")` instead of `@PreAuthorize("hasRole('ADMIN')")` on an admin endpoint.
- Custom permission expressions that don't check resource ownership.
- Spring Data REST: exposing repositories without `@RepositoryRestResource(exported = false)` on internal repositories.

### SEC1.3 — Broken session

- Servlet `HttpSession.getAttribute("user")` without freshness check.
- Cookies set without `httpOnly=true` and `secure=true`: `Cookie c = new Cookie("session", value); response.addCookie(c);` — should set both flags.
- Spring Session config not setting `HttpOnly`/`Secure`/`SameSite`.

### SEC1.4 — Over-privileged

- DataSource connecting as `root`/`postgres`/`admin` user.
- `@PreAuthorize("permitAll()")` on actuator endpoints.
- Container running as root.

### SEC1.5 — JWT misuse

- `Jwts.parser().setSigningKey(key).parseClaimsJws(jwt)` (jjwt 0.10 or earlier) without algorithm check — vulnerable to algorithm confusion.
- jjwt 0.11+: `Jwts.parserBuilder().setSigningKey(key).build().parseClaimsJws(jwt)` — verify the key matches the alg.
- Spring Security OAuth2 resource server: missing `jwtDecoder` config or accepting `none` alg.
- `jwt.io`-style decode without verification: `Jwts.parser().parse(jwt)` (no `parseClaimsJws`).

---

## SEC2 — INPUT-VALIDATION

### SEC2.1 — No schema validation at boundary

**Spring:**
- Controller signature: `@RequestParam String x` without `@Pattern` / `@Size` / `@Valid` constraints.
- `@RequestBody Map<String, Object> payload` (untyped) instead of `@Valid @RequestBody PaymentDto payload`.
- DTO class without JSR-380 constraints (`@NotNull`, `@Pattern`, `@Email`, `@Size`, `@Min`, `@Max`).
- Missing `@Validated` on the controller class or method.
- Spring Boot `application.properties`: `spring.mvc.problemdetails.enabled=false` and no global exception handler — validation errors leak stack traces.

**JAX-RS:**
- Missing `@Valid` on `@RequestBody`-equivalent parameter.

### SEC2.2 — Denylist patterns

- `if (input.contains("..")) reject();` — denylist; use allowlist regex `Pattern.matches("[a-zA-Z0-9_]+", input)`.
- `input.replaceAll("<script>", "")` — naive HTML stripping; use OWASP Java HTML Sanitizer.

### SEC2.3 — Partial validation

- DTO has JSR-380 constraints on some fields but the controller reads unvalidated fields via the request directly.

### SEC2.4 — Number parsing without try/catch

- `Integer.parseInt(request.getParameter("n"))` without `try { } catch (NumberFormatException e)` — unhandled exception, may leak stack trace.

---

## SEC3 — INJECTION

### SEC3.1 — SQL injection

- String concat: `String sql = "SELECT * FROM users WHERE id = " + id; stmt.executeQuery(sql);` — use `PreparedStatement` with `?` placeholders.
- JPQL string concat: `em.createQuery("SELECT u FROM User u WHERE u.email = '" + email + "'")` — use `setParameter`.
- Native query string concat: `em.createNativeQuery("SELECT * FROM ... WHERE x = '" + x + "'")` — same.
- Spring Data `@Query("SELECT u FROM User u WHERE u.name = '" + ... + "'")` — concat in annotation value (unusual but seen).
- Dynamic ORDER BY: `String sql = "SELECT * FROM x ORDER BY " + sortColumn;` — column names can't be parameterized; allowlist.
- Hibernate `Criteria` builder: `cb.like(root.get("name"), userInput)` — needs escaping of `%` and `_` to prevent over-match (not injection but related).

### SEC3.2 — NoSQL injection

- MongoDB Java driver: `collection.find(new Document("email", userInput))` where userInput could be a Document (`{$ne: null}`). Coerce to String.

### SEC3.3 — OS command injection

- `Runtime.getRuntime().exec("ls " + userInput)` — string command. Use ProcessBuilder with separate args.
- `Runtime.getRuntime().exec(new String[]{"sh", "-c", userCommand})` — same risk.
- `ProcessBuilder("sh", "-c", userInput)` — should pass args separately: `ProcessBuilder("ls", userInput)`.

### SEC3.4 — LDAP injection

- `DirContext.search(base, "(uid=" + userInput + ")", controls)` — use `Filter.escape` or build with `LdapName`.

### SEC3.5 — XPath injection

- `xpath.compile("//user[@name='" + name + "']")` — use parameterized XPath via Apache JXPath or escape with `XmlEscapers`.

### SEC3.6 — Log injection (CRLF)

- SLF4J: `logger.info("user: " + userInput)` — `userInput` containing `\n` injects log lines.
- Better: `logger.info("user.login", kv("user_id", userInput))` (structured).
- For unstructured loggers, sanitize: `userInput.replaceAll("[\\r\\n]", "_")`.

### SEC3.7 — Header injection (CRLF)

- `response.setHeader("X-Foo", userInput)` — Servlet API may or may not sanitize depending on version. Strip CRLF defensively.

### SEC3.8 — Template injection (SSTI) / Expression injection

- Velocity: `Velocity.evaluate(context, writer, "tag", userTemplate)`.
- Freemarker: `Template t = new Template("name", new StringReader(userTemplate), cfg);`.
- Spring SpEL: `ExpressionParser.parseExpression(userInput).getValue()` — full RCE.
- Spring SpEL in annotations: `@Value("#{${user.config}}")` where the config value is user-influenceable.
- OGNL (Struts): `OgnlContext` with user-controlled expressions — historical Struts RCE class.

### SEC3.9 — Other

- Hibernate `@Query(value = "...")` with `nativeQuery = true` and string concat.
- iBatis/MyBatis `${variable}` (string substitution) vs `#{variable}` (parameter binding) — `${...}` is unsafe with user input.

---

## SEC4 — XSS / OUTPUT-ENCODING

### SEC4.1 — Unsafe HTML rendering

**JSP:**
- `<%= userInput %>` — JSP expression, unescaped by default. Use `<c:out value="${userInput}"/>` (escaped) or `fn:escapeXml(userInput)`.
- `<jsp:expression>${userInput}</jsp:expression>` — same risk.

**Thymeleaf:**
- `th:utext="${userInput}"` (utext = unescaped text). Use `th:text` (escaped) instead.
- `[(${userInput})]` (utext inline). Use `[[${userInput}]]` (escaped).

**JSF:**
- `<h:outputText escape="false" value="#{user.bio}" />` — explicit escape disable.

**Velocity:**
- `$user.bio` (auto-references) — if Velocity context has escape tool, this is escaped; without, it's raw. Verify with `$esc.html($user.bio)`.

**Spring MVC:**
- Returning raw HTML strings from `@ResponseBody` without sanitization.

### SEC4.2 — DOM XSS in server-side response

- Generating HTML via `StringBuilder` and `setContentType("text/html")` without escaping.
- `PrintWriter.println("<div>" + userInput + "</div>")`.

### SEC4.3 — Unsafe URL contexts

- `response.sendRedirect(userUrl)` without scheme/host allowlist — open redirect (SEC12.4) AND `javascript:` URL risk.
- `href="${userUrl}"` in JSP/Thymeleaf without scheme validation.

### SEC4.4 — CSS injection

- `<div style="background: ${userBg}">` without escape — user can break out of style scope.

---

## SEC5 — CSRF / ORIGIN

### SEC5.1 — Missing CSRF token

- Spring Security: `.csrf().disable()` without justification.
- Spring Security custom config not enabling CSRF for state-changing methods.
- Servlet: missing CSRF token check on form POSTs.
- JSF: missing `protected-views` configuration.

### SEC5.5 — CORS misconfiguration

- `@CrossOrigin(origins = "*", allowCredentials = "true")` — invalid combo, indicates confusion.
- `corsConfiguration.setAllowedOrigins(List.of("*"))` AND `setAllowCredentials(true)`.
- Reflected origin: `corsConfiguration.setAllowedOriginPatterns(List.of("*"))` — should be specific.

---

## SEC6 — CRYPTO

### SEC6.1 — Weak password hash

- `MessageDigest.getInstance("MD5")` / `"SHA-1"` / `"SHA-256"` / `"SHA-512"` for passwords.
- Custom: `MessageDigest md = MessageDigest.getInstance("SHA-256"); md.update((pw + salt).getBytes());`.
- Spring Security: `NoOpPasswordEncoder.getInstance()` — passwords stored plaintext (sometimes seen in demos that escape to prod).

**Fix:** `BCryptPasswordEncoder`, `Argon2PasswordEncoder`, `Pbkdf2PasswordEncoder` (with high iterations).

### SEC6.2 — Weak RNG for security

- `new Random()` for session tokens, password-reset tokens, CSRF tokens.
- `Math.random()` (which delegates to `Random` internally).

**Fix:** `SecureRandom secureRandom = new SecureRandom(); byte[] bytes = new byte[32]; secureRandom.nextBytes(bytes);`.

### SEC6.3 — Deprecated / weak ciphers

- `Cipher.getInstance("AES")` — defaults to ECB. Specify `"AES/GCM/NoPadding"` for new code.
- `Cipher.getInstance("AES/ECB/PKCS5Padding")` — ECB.
- `Cipher.getInstance("DES")`, `"DESede"`, `"RC4"` — deprecated.
- `KeyGenerator.getInstance("DES")`.

### SEC6.4 — Hardcoded IV / salt / key

- `new IvParameterSpec("1234567812345678".getBytes())` — literal IV.
- `Cipher.init(mode, key, new IvParameterSpec(STATIC_BYTES))`.
- Hardcoded SecretKey: `SecretKeySpec key = new SecretKeySpec("hardcoded-key-bytes".getBytes(), "AES");`.

### SEC6.5 — JWT misuse

- See SEC1.5.

### SEC6.6 — TLS misconfiguration

- `SSLContext.getInstance("TLSv1")` — TLS 1.0 deprecated.
- `SSLContext.getInstance("SSL")` — SSLv3 deprecated.
- `TrustManager` returning `null` from `getAcceptedIssuers()` and empty `checkServerTrusted` — disables validation entirely.
- `HostnameVerifier` returning `true` always — disables hostname check.
- `HttpsURLConnection.setDefaultHostnameVerifier((hostname, session) -> true)`.

---

## SEC7 — SECRETS

### SEC7.1 — Hardcoded secret literal

- `private static final String API_KEY = "sk_live_...";`.
- `String DB_PASSWORD = "realpassword";`.
- `application.properties` / `application.yml` with literal values: `spring.datasource.password=hardcoded` instead of `${DB_PASSWORD}`.
- AWS keys: literals matching `AKIA[A-Z0-9]{16}`.
- Private keys inline: `-----BEGIN RSA PRIVATE KEY-----`.

### SEC7.2 — Committed config with secrets

- `application-prod.properties` tracked with production credentials.
- `secrets.yml` in repo.

### SEC7.3 — Token in URL

- `restTemplate.getForObject("https://api.example.com/?token=" + TOKEN, ...)` — tokens in URLs leak.

### SEC7.4 — CI YAML literal secret

- `.github/workflows/*.yml` containing literal secret values.
- Jenkins pipeline with literal credentials instead of `withCredentials` binding.

### SEC7.5 — Logging secrets

- `logger.info("Connecting with token " + token);`.
- `System.out.println("Auth header: " + authHeader);`.
- Spring Boot actuator `/env` endpoint exposed without auth (also SEC9.5).

---

## SEC8 — SUPPLY-CHAIN

### SEC8.1 — Suspicious new dep

When `pom.xml` / `build.gradle` adds a dep:

- Check Maven Central for first-published date, total downloads.
- Name typosquats: `log4j-cor` vs `log4j-core`, `commons-lang` vs `commons-lang3` (legitimate but version-sensitive).
- Group ID from unknown publisher.

### SEC8.2 — Non-registry dependency source

- Maven repository declared with `http://` URL (no TLS):
  ```xml
  <repository><url>http://repo.example.com/maven</url></repository>
  ```
  Same for Gradle `maven { url "http://..." }`.
- `repositories { maven { url uri('https://random.host/') } }` — unknown repository.

### SEC8.3 — Lockfile drift

- Gradle: `gradle.lockfile` change introducing a dep from a non-standard source.
- Maven: no lockfile by default (Maven 3.x); use `mvn versions:lock-snapshots` or `mvn dependency:lock`.

### SEC8.4 — Known CVE

- `mvn dependency-check:check` (OWASP Dependency-Check) or `gradle dependencyCheckAnalyze` reports high/critical.
- Transitive deps with known CVEs (Log4j, Spring4Shell, etc.).

---

## SEC9 — PII / LOGGING

### SEC9.1 — PII in logs

- SLF4J: `logger.info("user: {}", user)` where `user.toString()` includes PII.
- Lombok `@ToString` on a User entity without `exclude = {"email", "phoneNumber", "ssn"}`.
- Jackson serializing model to log with all fields.

### SEC9.2 — Unredacted request logging

- Spring Boot `logging.level.org.springframework.web=DEBUG` in production.
- Custom Servlet filter logging full request without redacting `Authorization`/`Cookie`.
- Apache HttpClient request/response logging at DEBUG.

### SEC9.3 — Analytics with PII

- Library calls passing email/phone as identifier.

### SEC9.4 — Error responses leaking PII / internals

- Spring `@RestControllerAdvice` not configured — default error response includes stack trace + bound values.
- `server.error.include-stacktrace=ALWAYS` in `application.properties`.

### SEC9.5 — Spring Actuator over-exposure

- `management.endpoints.web.exposure.include=*` without auth — exposes `/env`, `/heapdump`, `/threaddump`.
- `/actuator/env` accessible without auth — leaks env-var values including secrets.

---

## SEC10 — RESOURCE-EXHAUSTION

### SEC10.1 — ReDoS

- `Pattern.compile("^(a+)+$")` against user input.
- `String.matches(userRegex, userInput)` — both arguments user-controlled.
- Use `RE2/J` (`com.google.re2j`) for untrusted regex.

### SEC10.2 — Unbounded thread pool / queue

- `Executors.newCachedThreadPool()` — unbounded thread count. Use bounded `ThreadPoolExecutor`.
- `Executors.newFixedThreadPool(Integer.MAX_VALUE)` — same effect.
- `LinkedBlockingQueue<>()` (no capacity).
- Spring `@Async` without `taskExecutor` config (uses unbounded default).

### SEC10.3 — Missing request size cap

- Spring: missing `spring.servlet.multipart.max-file-size` and `spring.servlet.multipart.max-request-size` properties.
- `server.tomcat.max-http-form-post-size` not set.
- `spring.codec.max-in-memory-size` not set (WebFlux).

### SEC10.4 — Missing rate limit

- Auth endpoints without `bucket4j-spring-boot-starter` / `resilience4j-ratelimiter` / custom rate-limiter filter.

### SEC10.5 — Large file / JSON / image processing

- Jackson `ObjectMapper` without `StreamReadConstraints` set (Jackson 2.15+):
  ```java
  mapper.getFactory().setStreamReadConstraints(
      StreamReadConstraints.builder().maxStringLength(100_000).maxNumberLength(1000).build()
  );
  ```
- XML parser with entity expansion not limited (XXE-adjacent; see SEC12.2).
- `ImageIO.read(stream)` without max-dimension check.

---

## SEC11 — PATH-TRAVERSAL / FILE-OPS

### SEC11.1 — Path traversal

- `new File(uploadDir, userFilename)` without `Path.normalize()` + boundary check.
- `Paths.get(uploadDir).resolve(userFilename)` then `Files.read*` — same.
- `Files.copy(src, Paths.get(uploadDir, userName))`.

**Canonical fix:**
```java
Path base = Paths.get(uploadDir).toAbsolutePath().normalize();
Path target = base.resolve(userFilename).normalize();
if (!target.startsWith(base)) {
    throw new SecurityException("path escapes upload dir");
}
```

### SEC11.2 — Archive extraction (zip slip)

- `ZipInputStream` extraction loop without checking entry name doesn't contain `..` or absolute paths.
- `org.apache.commons.compress` archive extraction without validation.

### SEC11.3 — Unsafe file ops

- `Files.move(src, dst, StandardCopyOption.REPLACE_EXISTING)` with user-controlled `dst`.
- `Files.createSymbolicLink(link, target)` with user-controlled target.

### SEC11.4 — Filename sanitization

- Storing uploaded `MultipartFile` with its original name: `file.transferTo(new File(dir, file.getOriginalFilename()))`. Use UUID-based names.

---

## SEC12 — DESERIALIZATION / SSRF

### SEC12.1 — Unsafe deserialization

- `ObjectInputStream.readObject()` on untrusted input — RCE via gadget chains (Spring4Shell, Log4Shell-adjacent classes).
- `XMLDecoder` for untrusted XML — RCE via constructor-injection gadgets.
- Jackson polymorphic deserialization: `@JsonTypeInfo(use = Id.CLASS)` or `enableDefaultTyping()` without an allowlist. Use `activateDefaultTyping(BasicPolymorphicTypeValidator.builder()...)` with explicit allowlist.
- XStream: `XStream.fromXML(untrusted)` without `XStream.setupDefaultSecurity` + `allowTypes(...)` allowlist.
- Apache Commons Collections `InvokerTransformer` — gadget chain enabler.

### SEC12.2 — XXE (XML External Entity)

- `DocumentBuilderFactory.newInstance()` without:
  ```java
  factory.setFeature("http://apache.org/xml/features/disallow-doctype-decl", true);
  factory.setFeature("http://xml.org/sax/features/external-general-entities", false);
  factory.setFeature("http://xml.org/sax/features/external-parameter-entities", false);
  factory.setXIncludeAware(false);
  factory.setExpandEntityReferences(false);
  ```
- `SAXParserFactory`, `XMLInputFactory`, `TransformerFactory` — same set of features must be disabled.
- `SchemaFactory` — same.

### SEC12.3 — SSRF

- `URL url = new URL(userUrl); url.openConnection().getInputStream();` — no scheme + host validation.
- Apache HttpClient: `HttpGet(userUrl)` without allowlist.
- OkHttp: `client.newCall(new Request.Builder().url(userUrl).build())`.
- Spring `RestTemplate.getForObject(userUrl, ...)`.

**Fix:** validate scheme is `http`/`https`, resolve host, check it's not in private/loopback/link-local ranges (use Apache Commons `InetAddressUtils` or Guava `InetAddresses`).

### SEC12.4 — Open redirect

- `response.sendRedirect(request.getParameter("next"))` without validating the destination.
- Spring: `return "redirect:" + userUrl;` without validation.

---

## Quick triage for diff reviews

1. **Boundary first** — every `@Controller`/`@RestController`/`@WebServlet`/`@Path` method. AuthN (SEC1.1) and `@Valid @RequestBody` (SEC2.1).
2. **Sinks second** — for each `Statement.executeQuery`, `Runtime.exec`/`ProcessBuilder`, `Files.read*`, `ObjectInputStream.readObject`, `URL.openConnection`, look back to source.
3. **Output third** — for each `th:utext`, `<c:out escape="false">`, `escape="false"`, confirm sanitization.
4. **Layer fourth** — CSRF disable, CORS misconfig, missing rate limit, request size, actuator exposure.
5. **Crypto/secrets fifth** — `MessageDigest.getInstance`, `new Random()` (vs `SecureRandom`), `Cipher.getInstance("AES")` (defaults to ECB), hardcoded keys/IVs.
