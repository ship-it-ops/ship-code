# Expected Review Output — fixture-3-java-srp

---

## Code Review: input.java

### Critical (must fix before merge)

- **[P2-SEC] Line 8**: Database credentials hardcoded: `"root", "password"`. → Load from environment variables or a secrets manager. Never commit credentials.

- **[P2-SEC] Lines 11, 14**: SQL injection via string concatenation in `executeUpdate`. → Use `PreparedStatement` with parameterized queries.

- **[P1-BUG] Lines 7-29**: Resources (Connection, Statement) are not closed. On any exception, they leak. → Use try-with-resources: `try (Connection conn = ...; Statement stmt = ...) { ... }`.

### Important (should fix)

- **[P5-MAINT] Class `OrderManager`**: Violates Single Responsibility — opens database connection, persists order, persists items, formats HTML, configures SMTP, sends email, logs. Six reasons to change in one method. → Split into `OrderRepository`, `OrderConfirmationFormatter`, `EmailNotifier`, with `OrderManager` coordinating injected collaborators.

- **[P3-ERR] Lines 28-30**: `catch (Exception e)` is too broad and `e.printStackTrace()` writes to stderr instead of using a logger. Swallows all failures including SQL constraint violations, network errors, and class-loader issues. → Catch specific exceptions (`SQLException`, `MessagingException`), log with context via SLF4J, and either propagate or wrap in a domain exception.

- **[P4-TEST] Line 6**: `createOrder` instantiates Connection and javax.mail.Session internally — impossible to unit-test without a real database and SMTP server. → Inject `DataSource`, `MailSender` (or equivalents) via the constructor.

- **[P5-MAINT] Line 6**: Method takes 4 positional parameters including a boolean flag (`isPremium`) that the body does not use. → Wrap in a request object; remove the unused parameter.

### Suggestions (improve when convenient)

- **[P6-READ] Line 26**: `System.out.println` for logging. → Use SLF4J: `logger.info("Order created for customer {}", customerId)`.

- **[P6-READ] Line 17**: HTML built via string concatenation is fragile and not localized. → Use a template engine (Thymeleaf, Mustache, or Freemarker).

### What's Good

- The method's positional flow (persist → notify) is the right sequence — the structure is fine; the responsibilities just need to be separated into collaborators.
- Use of `LAST_INSERT_ID()` to link order_items to orders is sound (assuming a single-statement session). When split into a repository, this becomes a cleaner explicit ID return.
