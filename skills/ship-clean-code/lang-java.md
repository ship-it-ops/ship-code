# Java Clean Code Idioms

## Naming Conventions

- `PascalCase` for classes, interfaces, enums, annotations
- `camelCase` for methods, variables, parameters
- `UPPER_SNAKE_CASE` for `static final` constants
- Package names all lowercase, dot-separated
- No Hungarian notation, no member prefixes (`m_`, `f_`)

## Type Design

- Use `enum` over `static final int/String` constants
- Use sealed classes/interfaces (Java 17+) for restricted hierarchies
- Prefer composition over inheritance
- Program to interfaces, not implementations
- Use generics — never use raw types (`List` without type parameter)

## Error Handling

- Use checked exceptions ONLY for recoverable conditions the caller can handle
- Use unchecked exceptions (RuntimeException) for programming errors
- Always use try-with-resources for `AutoCloseable` resources
- Never catch `Exception` or `Throwable` broadly — catch specific types
- Include context in exception messages (operation, input, state)
- Wrap third-party exceptions in your own exception types at module boundaries

## Null Safety

- Use `Optional<T>` for return values that may be absent
- Never use `Optional` as a method parameter or field
- Use `Objects.requireNonNull()` for fail-fast on null arguments
- Prefer empty collections (`Collections.emptyList()`) over null returns
- Use `@Nullable`/`@NonNull` annotations

## equals/hashCode Contract

- Always override `hashCode()` when you override `equals()`
- Use `Objects.equals()` and `Objects.hash()` for clean implementations
- Consider using records (Java 16+) for value objects (auto-generates both)

## Modern Java Patterns

- Records for immutable data carriers (Java 16+)
- Pattern matching for `instanceof` (Java 16+)
- Switch expressions (Java 14+) over switch statements
- Text blocks for multi-line strings (Java 15+)
- Stream API for collection transformations (prefer over manual loops when readable)
- `var` for local variables when the type is obvious from context

## Common Traps

- **Mutable static fields**: Static mutable state is global state — avoid or synchronize.
- **String concatenation in loops**: Use `StringBuilder` instead of `+=` in loops.
- **Autoboxing/unboxing NPE**: `Integer` can be null, `int` cannot — unboxing null throws NPE.
- **ConcurrentModificationException**: Don't modify a collection while iterating it. Use `Iterator.remove()` or collect changes separately.
- **Synchronization on wrong object**: Don't synchronize on `this` or `String` literals. Use a private `final Object lock`.
- **equals with inheritance**: Use `getClass()` check, not `instanceof`, in equals (unless using Liskov-safe pattern).

## Dependency Injection

- Constructor injection over field injection
- Make injected dependencies `final`
- Use interfaces for injectable services
- Avoid service locator pattern
- Keep constructors simple — no logic, just assignment

## Collections and Streams

- Return unmodifiable collections from public methods (`List.of()`, `Collections.unmodifiableList()`)
- Use `List.of()`, `Map.of()`, `Set.of()` for immutable collection literals (Java 9+)
- Prefer `Stream` operations over imperative loops for transformations
- Avoid side effects in stream operations — use `forEach` only for terminal actions
- Use `Collectors.toUnmodifiableList()` to collect into immutable lists

## Concurrency

- Prefer `ExecutorService` over manually creating threads
- Use `CompletableFuture` for composable async operations
- Make shared objects immutable or use thread-safe alternatives (`ConcurrentHashMap`, `AtomicInteger`)
- Avoid `synchronized` on public methods — use private lock objects
- Use `volatile` for flags that are read by multiple threads without other synchronization
- **Java 21+**: Use virtual threads (`Executors.newVirtualThreadPerTaskExecutor()`) for I/O-bound concurrent work. Virtual threads are cheap — do not pool them. Traditional thread pool sizing advice does not apply.

## Secrets & Configuration

- Never hardcode credentials, API keys, or tokens in source code
- Load secrets from environment variables or a secrets manager (Vault, AWS Secrets Manager)
- Validate required configuration at startup — fail fast with descriptive errors
- Never log secret values — mask them in `toString`/logging implementations

## Testing Conventions

- Use JUnit 5 with `@DisplayName` for readable test names: `@DisplayName("should reject overdraft when balance is insufficient")`
- Use `@Nested` classes to group tests by scenario
- Use `@ParameterizedTest` with appropriate sources: `@ValueSource`, `@CsvSource`, `@MethodSource`, `@EnumSource`
- Use AssertJ for fluent assertions: `assertThat(result).isEqualTo(expected)`
- Use `assertSoftly` for multiple assertions without short-circuiting
- Use `@ExtendWith(MockitoExtension.class)` for automatic mock injection
- Use argument captors for verifying complex argument structures
- Understand test layering: `@SpringBootTest` (full context) vs `@WebMvcTest` (web only) vs plain JUnit (unit)
- Mock external dependencies with Mockito — never mock value objects or records
