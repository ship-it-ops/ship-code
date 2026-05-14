# Java PR-Review Idioms

PR-review-specific patterns for Java. For file-level Java idioms (records, virtual threads, JUnit), defer to `ship-clean-code/lang-java.md`. This file covers what each persona looks for in a *PR* context.

---

## SC — Senior Security Engineer (Java patterns)

### Auth/Authz (SC1)

- **Spring Security**: new controller method without `@PreAuthorize`, `@Secured`, or coverage by a `SecurityFilterChain` config. Check `SecurityConfig.java` for the URL pattern.
- **Spring MVC**: new `@GetMapping`/`@PostMapping` outside of an `@PreAuthorize`-annotated class without method-level annotation.
- **JAX-RS**: new `@Path` resource without `@RolesAllowed` or `@PermitAll` (explicit on every endpoint is best).
- **Method-security check missing**: `@PreAuthorize("hasRole('USER')")` on a method that should be `hasRole('ADMIN')` — flag any role change in a PR.
- **Bypass pattern**: `SecurityContextHolder.getContext().getAuthentication()` used without checking `isAuthenticated()`.

### Injection (SC2)

- **JDBC**: `Statement.executeQuery("SELECT ... " + var)` — injection. Use `PreparedStatement` with `?` placeholders.
- **JPA**: `entityManager.createQuery("FROM User WHERE name = '" + name + "'")` — JPQL injection. Use named/positional parameters.
- **Spring JdbcTemplate**: `jdbcTemplate.queryForObject("SELECT ... " + var, ...)` — same issue. Use parameterized version.
- **Hibernate native query**: same as JPA. Always parameterize.
- **OGNL / SpEL injection**: Spring's `@Value("#{...}")` with user input, Struts OGNL evaluation.
- **XML external entities (XXE)**: `DocumentBuilderFactory.newInstance()` without `setFeature("http://apache.org/xml/features/disallow-doctype-decl", true)` and similar XXE protections.
- **Deserialization**: `ObjectInputStream.readObject()` on untrusted input — classic Java deserialization vulnerability.
- **Command injection**: `Runtime.exec(String)` (string form, shell-parsed). Use the `String[]` argv form.
- **Path traversal**: `new File(baseDir, userInput)` where userInput is unsanitized. Validate against canonical path.

### Secrets (SC3)

- Hardcoded credentials in `application.yml` / `application.properties` — should be `${ENV_VAR}` or Vault references.
- `application-local.yml` committed (project convention should `.gitignore` it).
- Build-time secrets in `pom.xml` / `build.gradle`: repository credentials in plaintext.

### Crypto misuse (SC4)

- `MessageDigest.getInstance("MD5")` / `"SHA1"` for security. Use `SHA-256` minimum; for passwords use BCrypt / Argon2 / PBKDF2.
- `Cipher.getInstance("AES")` defaults to `AES/ECB/PKCS5Padding` — ECB. Always specify a mode: `AES/GCM/NoPadding` or `AES/CBC/PKCS5Padding`.
- `Cipher.getInstance("DES")`, `"DESede"` — weak ciphers.
- Fixed IV in CBC mode: `new IvParameterSpec(new byte[16])`. IV must be random per-encryption.
- `new Random()` for security tokens. Use `SecureRandom`.
- JWT verification accepting `alg=none`: check the `jjwt`/`nimbus-jose-jwt` configuration for explicit algorithm allowlist.

### Supply chain (SC5)

- New `<dependency>` in `pom.xml` or `implementation 'X'` in `build.gradle`:
  - Check for known CVEs via OWASP Dependency-Check report.
  - Check the version against `mvnrepository.com` — `0.x` or very new versions are suspicious.
  - Verify the groupId is the canonical one (typosquats like `com.googlle.guava` exist).
- New `<repository>` in `pom.xml` pointing to a non-Maven-Central host.

### PII / log leakage (SC6, SC7)

- `log.info("User: {}", user)` where `user.toString()` includes PII. Override `toString()` or use a redacted form.
- Spring Cloud Sleuth / Micrometer trace tags with user IDs (low risk) vs. emails (high risk).
- HTTP request logging via `OncePerRequestFilter` that doesn't redact `Authorization` header.

---

## SE — Senior Engineer (Java patterns)

### Breaking changes (SE1)

- A `public` method in a package marked as the library's public API (typically `*.api.*` or per project convention) was removed, renamed, or its parameters changed.
- An interface gained a non-default method — all implementers break.
- An enum value removed — switch statements without `default` break.

### Contract drift (SE2)

- `@NonNull` ↔ `@Nullable` change on a public method parameter or return type.
- A field on a JSON-serialized DTO (Jackson `@JsonProperty`) renamed or removed.
- A Spring `@RequestMapping` URL path changed.
- A Kafka `@KafkaListener` topic name changed.
- An exception type in a public method's `throws` clause removed (callers may not catch the new replacement).

### Rollout risk (SE3)

- New feature in a service with FF4j / Togglz / LaunchDarkly without a flag.
- `@Profile("prod")` guarding behavior that should be flag-controlled.

### Deprecation missing (SE5)

- Public symbol removed; no prior commit adds `@Deprecated`. Mark for one release before removal.

---

## IN — Senior Infra/SRE (Java patterns)

### Network call hygiene (IN1)

- `RestTemplate` without `setConnectTimeout` and `setReadTimeout` configured. Better: use `RestClient` (Spring 6.1+) or `WebClient`.
- `HttpClient.newHttpClient()` without `connectTimeout`. Builder pattern: `.connectTimeout(Duration.ofSeconds(5))`.
- `OkHttpClient` without timeouts configured. Default is 10s connect, 0 (infinite) read.
- `WebClient` without `.responseTimeout(Duration.ofSeconds(N))`.
- New HTTP client without retry policy (Spring Retry, Resilience4j) on a transient-failure-prone upstream.

### Observability (IN2)

- New `@RestController` method without a `log.info("...", ...)` at entry and without a Micrometer metric.
- New `@Async` method or `@Scheduled` task without start/finish/error logs.
- New external integration without a circuit breaker (Resilience4j `@CircuitBreaker`) in a service that uses them elsewhere.

### Resource limits (IN3)

- `findAll()` on a JPA repository without pagination in a request handler — unbounded result set.
- `Stream<T>` from a JPA query that's not closed properly (Hibernate keeps the connection open).
- `HikariCP` pool size unset or unreasonably high.
- `application.yml` raising `server.tomcat.max-threads` significantly — check the downstream connection-pool sizing too.

### Idempotency (IN4)

- Kafka consumer (`@KafkaListener`) with `enable.auto.commit: true` AND mutating downstream state — retries cause duplicates. Use manual commit with at-least-once + idempotency key.
- Webhook receiver without signature verification.

### CI/CD (IN5)

- GitHub Actions `uses: docker/setup-buildx-action@v3` (tag) vs `@<sha>`. Same issue as TS.
- Jenkinsfile with a new credential reference (`withCredentials([...])`).
- `pom.xml` `<distributionManagement>` change — affects publish targets.

### Performance hot path (IN7)

- N+1 in JPA: `for (User u : users) u.getOrders()` without `JOIN FETCH` or `@EntityGraph`.
- Repeated regex compilation: `string.matches("...")` in a loop — hoist `Pattern.compile(...)` to a static field.
- `synchronized` on a public method when a finer-grained lock (private `Object`, or `ReentrantLock`) would do.
- Reflection in a hot path without caching the `Method`/`Field` object.

---

## DA — Senior Data Engineer (Java patterns)

### Schema break (DA1, DA2, DA3)

- **Flyway migration** (`V123__description.sql`): `DROP COLUMN`, `DROP TABLE`. Verify references via:
  - JPA `@Column` annotations across the codebase
  - Native queries containing the column name
  - Downstream consumers (out-of-band data lineage)
- **Liquibase changeset**: same; `<dropColumn>`, `<dropTable>`. Check the changeset has a `<rollback>` block.
- **NOT NULL + no backfill**: `ALTER TABLE ... MODIFY column ... NOT NULL` (MySQL) / `ALTER COLUMN ... SET NOT NULL` (Postgres) without a preceding UPDATE.
- **Liquibase / Flyway reversibility**: a changeset that's `<sql>` without a `<rollback>` block — flag unless the operation is inherently additive (CREATE TABLE, CREATE INDEX).

### Type precision (DA5)

- `Float`/`Double` for money in a JPA entity — use `BigDecimal` with precision/scale annotations.
- `java.util.Date` instead of `java.time.Instant` / `LocalDateTime` / `ZonedDateTime` — legacy date handling.
- `Long` for IDs is fine; `Integer` for high-cardinality IDs is a future-proofing concern.

### Event contract (DA6)

- Avro schema (`.avsc`) field removed without a default — breaks readers expecting the field.
- Protobuf field removed without reserving its number — future re-use of the number breaks compatibility.
- Kafka topic schema change (Confluent Schema Registry) without a compatibility check.

### Retention / PII (DA7)

- New JPA entity with email/phone/name columns without documenting retention.

---

## TS — Test Reviewer (Java patterns)

### Test file detection

A file is in the `test` bucket if its path matches:
- `src/test/java/...` (Maven/Gradle standard)
- `src/test/kotlin/...`
- `*Test.java`, `*Tests.java`, `*IT.java` (integration test naming)
- `*Spec.java` (Spock convention)

### Production file detection

`code` bucket: `.java` files under `src/main/java/` (and `src/main/kotlin/` for Kotlin in mixed projects).

### Coverage gap signal (TS1)

If ≥ 30 net added lines across `code` bucket files AND zero `test` bucket files added or modified, fire TS1.

### Regression test signal (TS2)

If PR description matches `(fixes|closes|resolves) #\d+` AND zero `test` bucket files added or modified, fire TS2.

Both findings delegate to `ship-tested-code` for depth.
