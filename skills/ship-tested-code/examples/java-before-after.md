# Java Test Transformations

## Example 1: Over-Mocked → Focused with Fakes

### Before
```java
@ExtendWith(MockitoExtension.class)
class OrderServiceTest {

    @Mock private OrderRepository orderRepo;
    @Mock private PaymentGateway paymentGateway;
    @Mock private InventoryService inventoryService;
    @Mock private NotificationService notificationService;
    @Mock private AuditLogger auditLogger;

    @InjectMocks private OrderService service;

    @Test
    void testPlaceOrder() {
        Order order = new Order(1L, List.of(
            new LineItem("Widget", 2, new BigDecimal("25.00"))
        ), "USD");

        when(inventoryService.checkAvailability(any())).thenReturn(true);
        when(paymentGateway.charge(any())).thenReturn(new PaymentResult("tx-123", "SUCCESS"));
        when(orderRepo.save(any())).thenAnswer(inv -> inv.getArgument(0));

        Order result = service.placeOrder(order);

        assertNotNull(result);
        verify(inventoryService).checkAvailability(any());
        verify(paymentGateway).charge(any());
        verify(orderRepo).save(any());
        verify(notificationService).sendConfirmation(any());
        verify(auditLogger).log(any());
    }
}
```

**Problems:**
- 5 mocks for one test — testing wiring, not behavior (M1, D6)
- `assertNotNull` is the weakest possible assertion (A1)
- `verify(any())` — does not check what was actually passed (A4)
- One giant test covering everything (D2)
- `testPlaceOrder` — vague name (N3)

### After
```java
class OrderServiceTest {

    private final FakeOrderRepository orderRepo = new FakeOrderRepository();
    private final FakePaymentGateway paymentGateway = new FakePaymentGateway();
    private final FakeInventoryService inventory = new FakeInventoryService();
    private final SpyNotificationService notifications = new SpyNotificationService();
    private final OrderService service = new OrderService(
        orderRepo, paymentGateway, inventory, notifications
    );

    @Nested
    @DisplayName("when placing a valid order")
    class ValidOrder {

        @Test
        @DisplayName("should save order with calculated total")
        void savesWithTotal() {
            var order = OrderFactory.withItems(
                item("Widget", 2, "25.00"),
                item("Gadget", 1, "50.00")
            );

            var result = service.placeOrder(order);

            var saved = orderRepo.findById(result.getId());
            assertThat(saved).isPresent();
            assertThat(saved.get().getTotal()).isEqualByComparingTo("100.00");
            assertThat(saved.get().getStatus()).isEqualTo(OrderStatus.CONFIRMED);
        }

        @Test
        @DisplayName("should charge payment with correct amount")
        void chargesPayment() {
            var order = OrderFactory.withTotal("75.00");

            service.placeOrder(order);

            assertThat(paymentGateway.getCharges()).hasSize(1);
            assertThat(paymentGateway.getCharges().get(0).getAmount())
                .isEqualByComparingTo("75.00");
        }

        @Test
        @DisplayName("should send confirmation email")
        void sendsConfirmation() {
            var order = OrderFactory.standard();

            service.placeOrder(order);

            assertThat(notifications.getSentEmails()).hasSize(1);
            assertThat(notifications.getSentEmails().get(0).getSubject())
                .containsIgnoringCase("confirmation");
        }
    }

    @Nested
    @DisplayName("when inventory is insufficient")
    class InsufficientInventory {

        @Test
        @DisplayName("should reject order with clear error")
        void rejectsOrder() {
            inventory.setAvailable(false);
            var order = OrderFactory.standard();

            assertThatThrownBy(() -> service.placeOrder(order))
                .isInstanceOf(InsufficientInventoryException.class)
                .hasMessageContaining("Widget");
        }

        @Test
        @DisplayName("should not charge payment")
        void doesNotCharge() {
            inventory.setAvailable(false);
            var order = OrderFactory.standard();

            catchThrowable(() -> service.placeOrder(order));

            assertThat(paymentGateway.getCharges()).isEmpty();
        }
    }
}
```

**Improvements:**
- Fakes expose state for assertion — no `verify()` on mocks
- Each test verifies one specific behavior
- `@Nested` groups organize by scenario
- `@DisplayName` makes test output read like a spec
- Factory pattern for test data
- Error paths tested explicitly

---

## Example 2: H2 Integration Test → TestContainers

### Before
```java
@SpringBootTest
@ActiveProfiles("test") // Uses H2 in-memory
class UserRepositoryTest {

    @Autowired
    private UserRepository repository;

    @Test
    void testFindByEmail() {
        User user = new User("John", "john@test.com", "hashed_pw",
            LocalDateTime.now(), true, null, 0, "USD");
        repository.save(user);

        Optional<User> found = repository.findByEmail("john@test.com");

        assertTrue(found.isPresent());
        assertEquals("John", found.get().getName());
    }
}
```

**Problems:**
- H2 has different SQL behavior than Postgres (JSON, locking, arrays)
- Raw constructor call breaks when fields are added (TD7)
- `assertTrue`/`assertEquals` — less readable than AssertJ (A1)
- Tests only the happy path (C1)
- `@ActiveProfiles("test")` hides the H2 configuration

### After
```java
@Testcontainers
@DataJpaTest
@AutoConfigureTestDatabase(replace = Replace.NONE)
class UserRepositoryTest {

    @Container
    static PostgreSQLContainer<?> postgres = new PostgreSQLContainer<>("postgres:16");

    @DynamicPropertySource
    static void configure(DynamicPropertyRegistry registry) {
        registry.add("spring.datasource.url", postgres::getJdbcUrl);
        registry.add("spring.datasource.username", postgres::getUsername);
        registry.add("spring.datasource.password", postgres::getPassword);
    }

    @Autowired
    private UserRepository repository;

    @Test
    @DisplayName("should find user by email (case-insensitive)")
    void findsByEmail() {
        repository.save(UserFactory.active(email -> "Jane@Example.com"));

        var found = repository.findByEmail("jane@example.com");

        assertThat(found).isPresent();
        assertThat(found.get().getName()).isEqualTo("Jane");
    }

    @Test
    @DisplayName("should return empty for unknown email")
    void returnsEmptyForUnknownEmail() {
        assertThat(repository.findByEmail("nobody@example.com")).isEmpty();
    }

    @Test
    @DisplayName("should enforce unique email constraint")
    void rejectsDuplicateEmail() {
        repository.save(UserFactory.active(email -> "dupe@test.com"));

        assertThatThrownBy(() ->
            repository.save(UserFactory.active(email -> "dupe@test.com"))
        ).isInstanceOf(DataIntegrityViolationException.class);
    }
}
```

**Improvements:**
- Real Postgres via TestContainers — tests actual SQL behavior
- `@DataJpaTest` — narrower slice, faster than `@SpringBootTest`
- AssertJ fluent assertions
- Factory pattern for test data
- Tests: happy path, not-found, and constraint violation
- `@DisplayName` for readable test output

---

## Example 3: Parameterized for Edge Cases

### Before
```java
@Test
void testValidateEmail() {
    assertTrue(EmailValidator.isValid("test@example.com"));
    assertFalse(EmailValidator.isValid("invalid"));
    assertFalse(EmailValidator.isValid(""));
    assertFalse(EmailValidator.isValid(null));
}
```

**Problems:**
- Multiple concepts in one test (D2)
- If the first assertion fails, remaining cases are not tested
- No test names to identify which case failed (N1)

### After
```java
@ParameterizedTest(name = "\"{0}\" -> valid={1}")
@CsvSource({
    "user@example.com, true",
    "user+tag@example.com, true",
    "user@sub.domain.com, true",
    "invalid, false",
    "'', false",
    "missing-domain@, false",
    "@missing-local.com, false",
    "spaces in@email.com, false",
})
@DisplayName("email validation")
void validatesEmails(String input, boolean expected) {
    assertThat(EmailValidator.isValid(input)).isEqualTo(expected);
}

@Test
@DisplayName("should reject null email")
void rejectsNullEmail() {
    assertThatThrownBy(() -> EmailValidator.isValid(null))
        .isInstanceOf(NullPointerException.class);
}
```

**Improvements:**
- Each case runs independently — one failure doesn't block others
- Test output shows which specific email failed
- Edge cases are visible and comprehensive
- Null case separated (different expected behavior — exception vs boolean)
