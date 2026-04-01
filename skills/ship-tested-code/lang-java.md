# Java Testing Idioms

## Test Runner & Conventions

- Use **JUnit 5** (Jupiter) as the test framework
- Use `@Test` for test methods, `@DisplayName("should X when Y")` for readable names
- Use `@Nested` classes to group related tests by scenario or feature
- Use `@BeforeEach` / `@AfterEach` for per-test setup/teardown

```java
class OrderServiceTest {

    @Nested
    @DisplayName("when placing an order")
    class PlaceOrder {

        @Test
        @DisplayName("should save order with calculated total")
        void savesOrderWithTotal() { /* ... */ }

        @Test
        @DisplayName("should reject order with empty cart")
        void rejectsEmptyCart() { /* ... */ }
    }

    @Nested
    @DisplayName("when cancelling an order")
    class CancelOrder {

        @Test
        @DisplayName("should refund payment for paid orders")
        void refundsPayment() { /* ... */ }
    }
}
```

## Parameterized Tests

- Use `@ParameterizedTest` with `@ValueSource`, `@CsvSource`, `@MethodSource`, or `@EnumSource`
- Always add `@DisplayName` or `name` parameter for readable failure messages

```java
@ParameterizedTest(name = "email \"{0}\" should be {1}")
@CsvSource({
    "valid@email.com, true",
    "no-at-sign, false",
    "'', false",
    "a@b.c, true"
})
void testEmailValidation(String email, boolean expected) {
    assertThat(EmailValidator.isValid(email)).isEqualTo(expected);
}

@ParameterizedTest
@MethodSource("invalidOrderInputs")
@DisplayName("should reject invalid order input")
void rejectsInvalidInput(Order input, String expectedError) {
    assertThatThrownBy(() -> service.place(input))
        .isInstanceOf(ValidationException.class)
        .hasMessageContaining(expectedError);
}
```

## Assertions with AssertJ

- **AssertJ** is preferred over JUnit's built-in assertions for fluent, readable assertions
- Use `assertThat()` as the entry point for all assertions
- Chain assertions for clarity; each chain reads as a sentence

```java
// GOOD: AssertJ fluent assertions
assertThat(order.getStatus()).isEqualTo(OrderStatus.CONFIRMED);
assertThat(order.getItems()).hasSize(3).extracting("name").contains("Widget", "Gadget");
assertThat(order.getTotal()).isCloseTo(new BigDecimal("99.99"), within(new BigDecimal("0.01")));

// Exception assertions
assertThatThrownBy(() -> service.withdraw(account, new Amount(1000)))
    .isInstanceOf(InsufficientFundsException.class)
    .hasMessageContaining("balance: 50");

// BAD: JUnit assertions with poor readability
assertEquals(OrderStatus.CONFIRMED, order.getStatus());
assertTrue(order.getItems().size() == 3);
```

## Mocking with Mockito

- Use `@Mock` for mock creation, `@InjectMocks` for the system under test
- Extend with `@ExtendWith(MockitoExtension.class)` (JUnit 5)
- Use `when().thenReturn()` for stubbing, `verify()` only for critical interactions
- **Prefer constructor injection** for testability; avoid `@Autowired` field injection

```java
@ExtendWith(MockitoExtension.class)
class NotificationServiceTest {

    @Mock
    private EmailGateway emailGateway; // External boundary -- mock is appropriate

    private NotificationService service;

    @BeforeEach
    void setUp() {
        service = new NotificationService(emailGateway);
    }

    @Test
    @DisplayName("should send welcome email to new users")
    void sendsWelcomeEmail() {
        var user = UserFactory.active();

        service.welcomeNewUser(user);

        verify(emailGateway).send(argThat(email ->
            email.getTo().equals(user.getEmail()) &&
            email.getSubject().contains("Welcome")
        ));
    }
}
```

## Integration Testing with TestContainers

- Use **TestContainers** for real databases, Kafka, Redis, Elasticsearch in tests
- Prefer `@Testcontainers` + `@Container` annotations for JUnit 5 lifecycle management
- Use `@DynamicPropertySource` in Spring Boot to wire container URLs

```java
@Testcontainers
@SpringBootTest
class OrderRepositoryIntegrationTest {

    @Container
    static PostgreSQLContainer<?> postgres = new PostgreSQLContainer<>("postgres:16")
        .withDatabaseName("testdb");

    @DynamicPropertySource
    static void configureProperties(DynamicPropertyRegistry registry) {
        registry.add("spring.datasource.url", postgres::getJdbcUrl);
        registry.add("spring.datasource.username", postgres::getUsername);
        registry.add("spring.datasource.password", postgres::getPassword);
    }

    @Autowired
    private OrderRepository repository;

    @Test
    @DisplayName("should find orders by customer and date range")
    void findsByCustomerAndDateRange() {
        // Arrange: seed test data
        var customer = CustomerFactory.standard();
        repository.saveAll(List.of(
            OrderFactory.forCustomer(customer).createdAt(LocalDate.of(2025, 1, 15)),
            OrderFactory.forCustomer(customer).createdAt(LocalDate.of(2025, 3, 20)),
            OrderFactory.forCustomer(customer).createdAt(LocalDate.of(2025, 6, 1))
        ));

        // Act
        var results = repository.findByCustomerAndDateRange(
            customer.getId(),
            LocalDate.of(2025, 1, 1),
            LocalDate.of(2025, 3, 31)
        );

        // Assert
        assertThat(results).hasSize(2);
    }
}
```

## Database Test Isolation

- Use `@Transactional` + `@Rollback` for automatic rollback after each test
- For tests that require committed transactions (e.g., testing constraints), use `@Sql` cleanup scripts
- Never rely on auto-increment IDs for test ordering -- use explicit values or assertions on properties

## Spring Boot Test Slices

- Use the **narrowest test slice** available to keep tests fast:
  - `@WebMvcTest` for controller layer (no database, no service beans)
  - `@DataJpaTest` for repository layer (embedded DB, no web layer)
  - `@SpringBootTest` only when you need the full context
- Use `@MockBean` to replace beans in slice tests

```java
@WebMvcTest(OrderController.class)
class OrderControllerTest {

    @Autowired
    private MockMvc mockMvc;

    @MockBean
    private OrderService orderService;

    @Test
    @DisplayName("should return 404 for unknown order")
    void returnsNotFound() throws Exception {
        when(orderService.findById(999L)).thenReturn(Optional.empty());

        mockMvc.perform(get("/api/orders/999"))
            .andExpect(status().isNotFound())
            .andExpect(jsonPath("$.error").value("Order not found"));
    }
}
```

## Contract Testing with Pact

- Use **Pact** for consumer-driven contract testing between microservices
- Consumer writes the contract (what it expects from the provider)
- Provider verifies it can fulfill the contract
- Publish contracts to a Pact Broker for cross-team visibility

## Architecture Testing with ArchUnit

- Use **ArchUnit** to enforce dependency rules, layer boundaries, and naming conventions
- Run as regular JUnit tests -- no special infrastructure needed

```java
@Test
@DisplayName("domain layer should not depend on infrastructure")
void domainDoesNotDependOnInfra() {
    noClasses()
        .that().resideInAPackage("..domain..")
        .should().dependOnClassesThat().resideInAPackage("..infrastructure..")
        .check(importedClasses);
}
```

## Property-Based Testing with jqwik

- Use **jqwik** for property-based testing in Java
- Define properties with `@Property`, generate data with `@ForAll`

```java
@Property
void sortedListPreservesLength(@ForAll List<Integer> list) {
    var sorted = new ArrayList<>(list);
    Collections.sort(sorted);
    assertThat(sorted).hasSameSizeAs(list);
}
```

## Mutation Testing with Pitest

- Use **Pitest** for mutation testing. Integrate in CI periodically (not every commit -- too slow)
- Target business logic modules: `mutationThreshold = 70`
- Maven: `pitest-maven`, Gradle: `info.solidsoft.pitest`

## HTTP Service Stubbing with WireMock

- Use **WireMock** for stubbing external HTTP services in integration tests
- Prefer `WireMockExtension` (JUnit 5) for automatic lifecycle management

```java
@WireMockTest(httpPort = 8089)
class PaymentGatewayClientTest {

    @Test
    @DisplayName("should handle gateway timeout gracefully")
    void handlesTimeout() {
        stubFor(post("/charge")
            .willReturn(aResponse().withFixedDelay(5000)));

        assertThatThrownBy(() -> client.charge(payment))
            .isInstanceOf(GatewayTimeoutException.class);
    }
}
```

## Common Traps

- **Field injection makes testing hard**: `@Autowired private Service service` cannot be set in a unit test. Use constructor injection.
- **`@SpringBootTest` everywhere**: Full context startup is slow (5-30 seconds). Use test slices for focused tests.
- **Testing with H2 when production uses Postgres**: Behavioral differences in SQL dialects, locking, JSON. Use TestContainers.
- **`@Transactional` in tests hides bugs**: If your production code manages transactions explicitly, `@Transactional` in tests may hide missing transaction boundaries. Test with and without.
- **Static method mocking**: If you need `Mockito.mockStatic()`, the production code probably needs refactoring to inject the dependency.
