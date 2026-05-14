# Java Debugging Idioms

## IDE Debuggers

- IntelliJ IDEA and Eclipse both provide full-featured JDB-based debuggers; prefer the IDE over command-line `jdb`
- **Conditional breakpoints**: right-click a breakpoint → set condition (e.g., `order.getId() == 4711`). Pauses only on matching iterations
- **Exception breakpoints**: pause on any throw of a given exception type, even if caught downstream. Critical for finding the origin of a wrapped exception
- **Field watchpoints**: pause on read or write of a specific field. Finds the mysterious mutator
- **Evaluate expression** while paused: run arbitrary Java in the current frame's context (`order.calculateTax()` etc.). Inspect derived values without modifying code
- **Drop frame / Reset frame** (IntelliJ): step back up the stack and re-execute. Useful when you stepped past the interesting point

## Remote Debugging

- Run target JVM with: `-agentlib:jdwp=transport=dt_socket,server=y,suspend=n,address=*:5005`
- Use `suspend=y` to pause on startup until the debugger attaches — useful for debugging initialization issues
- Attach from IntelliJ via "Remote JVM Debug" run config
- Never leave the JDWP port open on production-accessible network — it allows arbitrary code execution

## Stack Traces

- **Read the bottom of the stack first** for the entry point, then trace up to where it failed — Java stacks print deepest-first
- `Throwable.getCause()` and `Throwable.getSuppressed()` reveal wrapped and suppressed exceptions; print with `e.printStackTrace()` which handles both
- For better stack traces in production, use a logger that emits **JSON** with the stack as a structured field
- Avoid `printStackTrace()` in production code — use `logger.error("context", e)` instead so the trace is properly captured

## Logging for Debugging

- Use **SLF4J** as the facade; **Logback** or **Log4j 2** as the backend. Never use `System.out.println` in production code
- Parameterized messages: `logger.debug("Got user {}", user)` — the toString runs only if DEBUG is enabled. Avoid string concatenation (`"Got user " + user`) which runs every time
- `logger.error("Failed to process {}", order.getId(), e)` — last argument that is a Throwable is treated as the exception, not a format param
- For structured logging, use **MDC** (Mapped Diagnostic Context): `MDC.put("requestId", id); ... MDC.clear()`. Logs include the MDC keys automatically. Critical for distributed debugging
- Adjust log levels at runtime via JMX or Spring Boot Actuator's `/loggers` endpoint without restarting

## Inspecting State

- **Heap dumps**: `jmap -dump:format=b,file=heap.hprof <pid>` (Java 8) or `jcmd <pid> GC.heap_dump heap.hprof` (modern). Analyze with **Eclipse MAT** or **VisualVM**
- **Thread dumps**: `jstack <pid>` or `jcmd <pid> Thread.print`. Critical for diagnosing deadlocks and stuck threads
- **JFR (Java Flight Recorder)**: `jcmd <pid> JFR.start duration=60s filename=profile.jfr`. Low-overhead profiling and event recording, suitable for production
- **`Object.toString()` matters**: implement it (or use `@ToString` from Lombok / records) so logs and debuggers show meaningful state. Default `Object.toString` is useless: `com.example.Order@7d4f81b3`

## Common Java Bug Patterns

- **NullPointerException with chained calls**: `a.getB().getC()` — which one was null? Java 14+ Helpful NullPointerExceptions tell you: enable with `-XX:+ShowCodeDetailsInExceptionMessages` (default on in Java 15+). Always upgrade for this feature
- **Concurrent modification**: `for (X x : list) list.remove(x)` throws `ConcurrentModificationException`. Use `Iterator.remove()` or `list.removeIf(predicate)`
- **`equals`/`hashCode` contract violation**: object stored in a `HashMap` then "lost" after mutation — because hashCode changed. Make value objects immutable, or use records
- **Autoboxing NullPointerException**: `Integer i = null; int x = i;` throws NPE on unbox. Common in `Optional.orElse(null).intValue()` patterns
- **`String.split` edge cases**: `",a,b".split(",")` returns `["", "a", "b"]`; `"a,b,".split(",")` returns `["a", "b"]` (trailing empty dropped). Use `split(regex, -1)` to keep trailing
- **`SimpleDateFormat` is not thread-safe**: shared across threads silently corrupts state. Use `DateTimeFormatter` (from `java.time`) which is immutable
- **`==` for String comparison**: works for interned literals, fails for runtime-created strings. Always use `.equals()` or `Objects.equals()`
- **Static initializer order**: cycles between static fields in different classes lead to nulls. Avoid by deferring computation or using lazy initialization
- **Default methods + diamond inheritance**: compile-time ambiguity. Java forces you to override and pick. Be explicit about which super to call
- **Resource leak without try-with-resources**: connections, streams, file handles. Always wrap `AutoCloseable` in try-with-resources

## Concurrency Debugging

- **Deadlock detection**: `jstack <pid>` reports "Found one Java-level deadlock" if present. Make a habit of running this when threads "freeze"
- **Race conditions**: enable `-ea` (assertions) and add `assert` invariants inside synchronized blocks during testing
- **Thread-stress tests**: use `ExecutorService` + `CountDownLatch` to force concurrent execution. Run many times to catch races
- **`-XX:+PrintConcurrentLocks` (Java 8) / `jcmd Thread.print -l`**: shows lock ownership in thread dumps. Essential for diagnosing contention
- **AtomicLong / ConcurrentHashMap / LongAdder**: use these instead of synchronized blocks when possible — fewer bugs, better performance

## Profiling

- **JFR + JMC (Java Mission Control)**: production-grade profiling, low overhead, ships with the JDK
- **async-profiler**: sampling profiler with flame graph output. Lower overhead than JFR for CPU sampling
- **VisualVM**: free, attaches to a running JVM via JMX, shows CPU/memory/threads
- **YourKit / JProfiler**: commercial, more polished, deeper analysis

## Spring Boot-Specific

- `spring-boot-actuator` exposes `/actuator/health`, `/actuator/loggers`, `/actuator/heapdump`, `/actuator/threaddump`. Restrict access in production
- For debugging dependency injection issues: `--debug` flag prints the autoconfiguration report at startup
- `@SpringBootTest(webEnvironment=RANDOM_PORT)` + `@Autowired TestRestTemplate` for full-context integration debugging
- Spring's `BeanCreationException` usually wraps the real cause — read the `Caused by:` chain to the bottom

## Bisection

- `git bisect run mvn test -Dtest=LoginIntegrationTest` — bisect over commits, fail when the test fails
- For Gradle: `git bisect run ./gradlew test --tests "LoginIntegrationTest"`
- Ensure the test exits non-zero on failure (default for both)

## Common Traps

- **Logback / Log4j configuration not picked up**: classpath order matters, multiple binding warnings. Run with `-Dlogback.debug=true` to see what's loaded
- **`@Async` methods called from the same class don't actually run async**: Spring proxies only intercept external calls. Call across class boundaries
- **`@Transactional` self-invocation**: same issue — the proxy is bypassed
- **`equals` without `hashCode`**: silently breaks `HashMap`/`HashSet`. IDE warnings and Lombok's `@EqualsAndHashCode` prevent this
- **`Files.list(path)` without try-with-resources**: leaks file descriptors. Always close the stream
