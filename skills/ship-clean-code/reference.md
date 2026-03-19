# Clean Code Reference

Detailed rules organized by concern area, combining established clean code
principles with modern software engineering best practices.

---

## 1. Naming

### Principles

1. **Intention-revealing names.** A name should tell you why something exists, what it does, and how it is used without requiring a comment.
2. **Avoid disinformation.** Do not call something `accountList` unless it is literally a `List`; prefer `accounts` or `accountGroup`.
3. **Make meaningful distinctions.** Never differentiate names with number series (`a1`, `a2`) or noise words (`data` vs `info`, `the` vs `a`).
4. **Use pronounceable names.** If you cannot read a name aloud in conversation, rename it. `generationTimestamp` beats `genymdhms`.
5. **Use searchable names.** Single-letter names and numeric literals are impossible to grep for; reserve short names for tiny scopes.
6. **No encodings or prefixes.** Drop Hungarian notation (`strName`), member prefixes (`m_count`), and interface markers (`IShape`). Modern tooling makes them unnecessary.
7. **Class names are nouns or noun phrases.** `Customer`, `WikiPage`, `AddressParser` -- never a verb.
8. **Method names are verbs or verb phrases.** `postPayment`, `deletePage`, `calculateTax`.
9. **One word per concept.** Pick `fetch`, `retrieve`, or `get` and use it everywhere. Do not mix synonyms across equivalent operations.
10. **Use solution-domain names first, then problem-domain names.** Prefer CS terms (`Queue`, `Visitor`, `Factory`) when the audience is programmers; fall back to domain terms when there is no technical equivalent.
11. **Do not add gratuitous context.** In an app called `GasStationDeluxe`, the class `Address` does not need the prefix `GSD`.
12. **Choose names at the right abstraction level (N1).** A function in a high-level module should not reveal low-level implementation details through its name.
13. **Use standard nomenclature (N2).** Name classes after known patterns: `AccountFactory`, `OrderVisitor`, `PaymentStrategy`.
14. **Names must be unambiguous (N3).** `rename` could mean rename a file, a variable, or a user -- qualify it.
15. **Long names for long scopes, short for short (N4).** A loop index `i` is fine in a 3-line loop; a class-level field needs a full descriptive name.
16. **Names should describe side effects (N6).** A function named `getOos` that creates an output stream if one does not exist should be `createOrReturnOos`.
17. **Do not pun (N7).** If `add` means arithmetic addition in one class, do not reuse `add` to mean inserting into a collection elsewhere; use `insert` or `append`.

### Common Violations

- Variables named `temp`, `data`, `result`, `val`, `item` with no qualifier.
- Boolean variables that do not read as predicates: `flag`, `status` instead of `isValid`, `hasAccess`.
- Abbreviations that only the original author understands: `cntxt`, `mngr`, `svc`.
- Class names that are verbs: `Manage`, `Process`, `Handle`.
- Inconsistent vocabulary: `fetchUser` in one service, `getUser` in another, `retrieveUser` in a third.

### Quick Examples

**Before:**
```java
int d; // elapsed time in days
List<int[]> theList;
for (int[] x : theList)
    if (x[0] == 4) result.add(x);
```

**After:**
```java
int elapsedDays;
List<Cell> board;
for (Cell cell : board)
    if (cell.isFlagged()) flaggedCells.add(cell);
```

---

## 2. Functions & Methods

### Principles

1. **Keep functions small.** Target under 20 lines; treat 50 as a hard ceiling. If a function is long, it is doing too much.
2. **Do one thing.** A function should perform a single task, perform it well, and perform it only.
3. **One level of abstraction per function.** Do not mix high-level policy (`chargeCustomer`) with low-level detail (`socket.write`) in the same body.
4. **Follow the stepdown rule.** Arrange code so high-level functions appear first, calling into successively lower-level helpers.
5. **Limit arguments to three.** Zero is ideal, one is good, two is acceptable, three is the maximum. Beyond that, wrap arguments into a parameter object.
6. **No flag arguments (F3).** A boolean parameter means the function does two things. Split it into `renderForSuite()` and `renderForSingleTest()`.
7. **No side effects.** A function named `checkPassword` must not also initialize a session. If it must, the name should reflect the side effect.
8. **Command-Query Separation.** A function either changes state (command) or returns information (query), never both.
9. **Prefer exceptions over return codes.** Error codes force deeply nested `if` chains and mix happy path with error handling.
10. **Extract try/catch bodies.** The `try` block should call a single function; the `catch` block should call another. Error handling is one thing.
11. **DRY -- Do not Repeat Yourself.** Duplication is the root of many maintenance evils. Extract shared logic.
12. **Eliminate dead functions (F4).** If a function is never called, delete it. Version control remembers.
13. **Avoid output arguments (F2).** Do not modify arguments passed into a function. Return a new value instead.

### Common Violations

- Functions over 100 lines that mix validation, business logic, persistence, and logging.
- Functions accepting 5+ positional parameters.
- Boolean parameters that toggle behavior: `createUser(data, true)`.
- A "utility" function that mutates one of its arguments.
- Functions named `process`, `handle`, `manage` that do everything.

### Quick Examples

**Before:**
```python
def process(data, flag, output_list):
    if flag:
        for item in data:
            if item.is_valid():
                result = transform(item)
                output_list.append(result)
                log(result)
    else:
        for item in data:
            output_list.append(item)
```

**After:**
```python
def collect_transformed_items(items):
    return [transform(item) for item in items if item.is_valid()]

def log_items(items):
    for item in items:
        log(item)
```

---

## 3. Classes & Modules

### Principles

1. **Classes should be small -- measured by responsibilities, not lines.** If you cannot describe a class in 25 words without using "and", "or", or "but", it has too many responsibilities.
2. **Single Responsibility Principle (SRP).** A class should have one and only one reason to change.
3. **Open/Closed Principle (OCP).** A class should be open for extension but closed for modification. Add behavior through new classes or composition, not by editing existing code.
4. **Liskov Substitution Principle (LSP).** Subtypes must be substitutable for their base types without altering correctness. If `Square` cannot honor `setWidth` and `setHeight` independently, it must not extend `Rectangle`.
5. **Interface Segregation Principle (ISP).** No client should be forced to depend on methods it does not use. Prefer many small interfaces over one large one.
6. **Dependency Inversion Principle (DIP).** High-level modules must not depend on low-level modules; both should depend on abstractions.
7. **High cohesion.** Every method in a class should use most of the class's instance variables. When a subset of methods operates on a subset of fields, extract a new class.
8. **Low coupling.** Minimize the number of other classes each class knows about. Changes to one module should not ripple across the system.
9. **Law of Demeter.** A method should only call methods on: itself, its parameters, objects it creates, and its direct components.
10. **No train wrecks.** `a.getB().getC().doSomething()` violates Demeter and couples you to the entire chain's structure.
11. **Objects vs. data structures.** Objects hide data and expose behavior. Data structures expose data and have no meaningful behavior. Do not create hybrids.
12. **No hybrids.** A class that has public fields and also business methods is the worst of both worlds -- it is hard to extend and hard to use as plain data.

### Common Violations

- God classes with 30+ methods spanning multiple concerns (validation, persistence, formatting).
- Service classes that directly instantiate their dependencies instead of receiving them.
- Deep inheritance hierarchies (more than 2-3 levels) instead of composition.
- Classes with names ending in `Manager`, `Processor`, `Handler` that accumulate unrelated responsibilities.
- Getters chained 3+ levels deep to reach a nested value.

### Quick Examples

**Before:**
```java
class OrderService {
    void createOrder(Order o) { /* validate, save, email, log, audit */ }
    void cancelOrder(int id)  { /* load, validate, refund, email, log */ }
    String formatReceipt(Order o) { /* HTML generation */ }
    boolean isValidAddress(Address a) { /* geocoding */ }
}
```

**After:**
```java
class OrderService {
    OrderValidator validator;
    OrderRepository repo;
    OrderNotifier notifier;

    void create(Order o) {
        validator.validate(o);
        repo.save(o);
        notifier.confirmCreation(o);
    }
}
```

---

## 4. Error Handling

### Principles

1. **Use exceptions, not return codes.** Return codes clutter the caller with `if` checks and are easily ignored.
2. **Write try-catch-finally first.** When writing code that could fail, start by defining the scope of what you expect to catch; this forces you to think about failure before success.
3. **Never return null.** Return `Optional`, an empty collection, or a Null Object. Returning null forces every caller to add a null check.
4. **Never pass null as an argument.** There is almost no clean way to handle a null argument; it leads to `NullPointerException` or defensive checks in every function.
5. **Provide context with exceptions.** Include the operation attempted, the input that caused failure, and why it failed.
6. **Define exceptions by the caller's needs.** The caller usually cares about one thing: "did it work?" Wrap vendor exceptions into a single application exception when the caller does not need to distinguish between failure modes.
7. **Use the Special Case pattern.** Instead of returning null for "not found," return an object that implements the expected interface with default behavior.
8. **Wrap third-party exceptions.** Isolate external API error types behind your own exception hierarchy so vendor changes do not propagate through your codebase.

### Common Violations

- Catching generic `Exception` or `Throwable` and swallowing it silently.
- Returning `null` from a function that could return an empty list.
- Logging an exception and then re-throwing it (double-logging).
- Throwing exceptions with no message or a generic message like `"Error"`.
- Leaking library-specific exceptions (e.g., `SqlException`) through all layers.

### Quick Examples

**Before:**
```java
User user = userRepo.findById(id);
if (user == null) {
    return null;
}
Plan plan = user.getPlan();
if (plan == null) {
    return null;
}
return plan.getRate();
```

**After:**
```java
User user = userRepo.findById(id)
    .orElseThrow(() -> new UserNotFoundException(id));
return user.getPlan().getRate();

// Where getPlan() returns a NullObject (FreePlan) instead of null
```

---

## 5. Testing

### Principles

1. **F.I.R.S.T.** Tests must be Fast, Independent (no ordering dependencies), Repeatable (in any environment), Self-validating (boolean pass/fail, no manual inspection), and Timely (written alongside production code).
2. **One concept per test.** Each test verifies a single behavior. Multiple assertions are fine if they all verify the same concept.
3. **Arrange-Act-Assert (AAA).** Structure every test in three distinct phases: set up the scenario, perform the action, verify the result.
4. **Tests should read like specs.** A non-programmer should be able to read a test name and its body and understand what the system does.
5. **Build-Operate-Check for integration tests.** Build the test data, operate on the system, check results -- keep these phases visually distinct.
6. **Create a domain-specific testing language.** Write helper methods that read like domain operations: `givenACustomerWith(balance: 100)`, `whenWithdrawing(50)`, `thenBalanceIs(50)`.
7. **Test everything that could break (T1).** If a line of code can fail in production, it deserves a test.
8. **Use a coverage tool (T2).** Coverage highlights untested branches; treat gaps as questions, not just metrics.
9. **Do not skip trivial tests (T3).** They serve as documentation and catch regressions.
10. **An ignored test is a question about ambiguity (T4).** Do not `@Ignore` a test without a comment explaining the open question.
11. **Test boundary conditions (T5).** Off-by-one, empty inputs, nulls, maximums, unicode, concurrency edges.
12. **Exhaustively test near bugs (T6).** Bugs cluster. When you find one, write tests for adjacent logic.
13. **Patterns of failure reveal root causes (T7).** When multiple tests fail, look at what they share.
14. **Tests should be fast (T9).** Slow tests get skipped. Keep unit tests under 100ms each.
15. **Choose test doubles by purpose.** Fake: replace a slow/external collaborator with a fast in-memory equivalent when you only care about state outcomes (repositories, caches, queues). Mock: verify interaction protocols — use when the assertion IS whether a call was made (e.g., "email sent exactly once"). Stub: provide canned responses. Prefer fakes for state-based tests; use mocks only for interaction-based tests. Never mock value objects.
16. **Property-based testing for transformations.** When a function has a clear invariant (encode/decode roundtrip, sort order), generate random inputs. Libraries: `hypothesis` (Python), `fast-check` (TS), `jqwik` (Java).
17. **Integration tests at boundaries, unit tests for logic.** Test I/O and external systems at the edges; test business rules with fast isolated unit tests.
18. **Test names describe behavior, not implementation.** Use `should_X_when_Y` (Python/TS) or `@DisplayName("should X when Y")` (Java). A failing test name should tell you exactly what broke. Never use `test1`, `testProcess`, or `testHappyPath`.
19. **Test behavior contracts, not implementation details.** Do not test: private methods, auto-generated code (records, dataclasses), third-party library behavior, or framework wiring. Test observable outputs for given inputs.

### Common Violations

- Tests that depend on execution order or shared mutable state.
- Tests that call real external services (network, database) without isolation.
- Test methods named `test1`, `test2` with no indication of what they verify.
- Assertions buried inside helper methods with no clear failure message.
- Mock setups longer than the actual test logic.
- Time-coupled tests: `assert result.timestamp == datetime.now()` fails on slow machines. Inject a clock and freeze time.
- Sleep-based synchronization: `time.sleep(0.1)` or `Thread.sleep(500)` to wait for async operations. Use proper async test patterns.
- Tests that leave filesystem/database state behind. Use setup/teardown, transaction rollback, or temp directories.

### Quick Examples

**Before:**
```python
def test_account():
    a = Account()
    a.deposit(100)
    a.withdraw(50)
    assert a.balance == 50
    a.withdraw(100)
    assert a.balance == 50  # overdraft blocked
```

**After:**
```python
def test_withdraw_reduces_balance():
    account = Account(balance=100)
    account.withdraw(50)
    assert account.balance == 50

def test_withdraw_exceeding_balance_is_rejected():
    account = Account(balance=50)
    account.withdraw(100)
    assert account.balance == 50
```

---

## 6. Comments & Documentation

### Principles

1. **Good code is self-documenting.** The best comment is a well-named function or variable that eliminates the need for one.
2. **Comments are for "why," not "what."** Explain intent, constraints, or non-obvious trade-offs -- never restate what the code already says.
3. **Acceptable comments:** legal headers, intent clarification, warnings of consequences, `TODO` with a ticket reference, amplification of something easily overlooked.
4. **Delete mumbling comments.** If a comment does not add clarity, it adds noise.
5. **Delete redundant comments (C3).** A comment that restates the function signature or the obvious logic is worse than no comment.
6. **Delete misleading comments.** A comment that disagrees with the code is a trap for the next developer.
7. **Delete journal comments.** Source control tracks history; do not maintain a changelog inside the file.
8. **Delete commented-out code (C5).** It rots, confuses readers, and version control preserves anything you might need later.
9. **Delete closing-brace comments and banner markers.** If you need them, your function is too long -- shorten it instead.
10. **No nonlocal information.** A comment must describe the code it appears next to, not some distant part of the system.
11. **Keep comments current (C2).** An obsolete comment is worse than none. If you change code, update or remove the adjacent comment.
12. **Comments must have an obvious connection to the code (C4).** If a reader cannot understand the comment without reading other files, rewrite it.

### Common Violations

- `// increment i` above `i++`.
- Javadoc on every private method with no added insight.
- `// TODO: fix this` with no ticket, no context, dated 2018.
- Large blocks of commented-out code "just in case."
- Attribution comments: `// Added by John, March 2024` -- that is what `git blame` is for.

### Quick Examples

**Before:**
```java
// Check if the employee is eligible for benefits
if (employee.flags & HOURLY_FLAG && employee.age > 65) {
    // ...
}
```

**After:**
```java
if (employee.isEligibleForBenefits()) {
    // ...
}

// Inside Employee:
boolean isEligibleForBenefits() {
    return isHourly() && isRetirementAge();
}
```

---

## 7. Formatting & Organization

### Principles

1. **Target files under 500 lines.** Most files should be around 200 lines. Files over 500 lines almost certainly contain multiple responsibilities.
2. **Newspaper metaphor.** The file name should be a headline. The top of the file shows high-level abstractions; details increase as you read down.
3. **Vertical openness between concepts.** Separate functions, class declarations, and logical sections with blank lines.
4. **Vertical density for related code.** Lines that are tightly related should appear close together without intervening blank lines or comments.
5. **Caller above callee.** A function should be defined above the functions it calls, so reading flows top-down.
6. **Conceptual affinity.** Group related functions together even if one does not call the other -- shared concept is reason enough.
7. **Line length under 120 characters.** Horizontal scrolling kills readability. If a line is too long, the expression is too complex -- extract a variable or break the chain.
8. **Use horizontal whitespace to show relationships.** Tight binding has no space (`a*b`); loose binding uses spaces (`a + b`). Follow language conventions consistently.
9. **Consistent indentation -- always.** Never collapse a short `if` onto one line to save space. Consistency aids scanning.
10. **Team rules override personal preference.** Agree on a style, configure the formatter, and enforce it in CI. Debates end once the rule is set.

### Common Violations

- 1000+ line files mixing constants, DTOs, business logic, and utility functions.
- Random function ordering with no discernible narrative flow.
- Inconsistent blank-line usage: some functions separated by 3 blank lines, others by none.
- Deeply nested code (4+ levels of indentation) instead of early returns or extracted functions.
- Mixed tabs and spaces, or inconsistent brace placement within the same project.

### Quick Examples

**Before:**
```python
class ReportService:
    def _format_header(self, data): ...
    def generate(self, request):
        # 200 lines mixing validation, data fetching,
        # transformation, formatting, and sending
        ...
    def _validate(self, request): ...
    def _fetch_data(self, query): ...
    def _send_email(self, report): ...
```

**After:**
```python
class ReportService:
    def generate(self, request):
        self._validate(request)
        data = self._fetch_data(request.query)
        report = self._format(data)
        self._deliver(report, request.recipient)

    def _validate(self, request): ...
    def _fetch_data(self, query): ...
    def _format(self, data): ...
    def _deliver(self, report, recipient): ...
```

---

## 8. Boundaries & Dependencies

### Principles

1. **Wrap third-party APIs.** Put external libraries behind your own interfaces so you can swap, mock, or evolve them independently.
2. **Write learning tests.** When adopting a third-party library, write small tests that document how it behaves. These break early when you upgrade.
3. **Define the interface you wish existed, then adapt.** Do not let an awkward vendor API dictate the shape of your domain layer.
4. **Separate construction from use.** The code that creates objects should be distinct from the code that uses them. Main or a factory wires things together; business logic receives ready-made collaborators.
5. **Dependency injection.** Pass dependencies in through constructors or method parameters. Do not reach into global state or instantiate collaborators internally.
6. **Use factories when callers need control over timing.** If the business logic decides when to create an object but should not know the concrete class, inject a factory.
7. **Scale incrementally.** Start with the simplest architecture that works. Add layers, queues, caches, and abstractions only when a real need emerges.
8. **Use the simplest thing that can possibly work.** Premature abstraction is as harmful as premature optimization.
9. **Avoid Big Design Up Front (BDUF).** Design emerges from iteration. Plan enough to start, then refactor as you learn.
10. **Consider Domain-Specific Languages.** When a problem domain has clear vocabulary and rules, a small DSL can make the code dramatically more readable.

### Common Violations

- Business logic classes directly importing and calling AWS SDK, Stripe API, or database driver methods.
- Constructors that create their own dependencies: `this.repo = new PostgresRepo()`.
- No interface between your code and the ORM -- switching databases requires rewriting half the application.
- Over-engineering: introducing microservices, message brokers, or CQRS in a 3-person project with simple CRUD needs.
- Test files that require a running database or network connection because nothing is abstracted.

### Quick Examples

**Before:**
```python
class OrderService:
    def place_order(self, order):
        stripe.Charge.create(
            amount=order.total,
            currency="usd",
            source=order.payment_token,
        )
        ses_client = boto3.client("ses")
        ses_client.send_email(
            Source="noreply@shop.com",
            Destination={"ToAddresses": [order.email]},
            Message={"Subject": {"Data": "Confirmation"}, ...},
        )
```

**After:**
```python
class OrderService:
    def __init__(self, payment_gateway, notifier):
        self.payment_gateway = payment_gateway
        self.notifier = notifier

    def place_order(self, order):
        self.payment_gateway.charge(order.total, order.payment_token)
        self.notifier.send_confirmation(order.email, order)
```

---

## 9. Logging & Observability

### Principles

1. **Use structured logging, not print statements.** Use the language's logging framework (`logging` in Python, `winston`/`pino` in Node, `SLF4J` in Java). Log as structured key-value pairs or JSON, not interpolated strings.
2. **Log at the right level.** DEBUG for trace detail, INFO for state changes and request lifecycle, WARN for recoverable problems, ERROR for failures needing attention. Never log at ERROR for expected conditions.
3. **Never log secrets, PII, tokens, or passwords.** Not even partially. Mask or omit sensitive fields.
4. **Don't log-and-rethrow.** Either handle the error (log it) or propagate it (throw it). Doing both creates duplicate log entries that obscure root cause.
5. **Include correlation IDs.** In distributed systems, every log entry should carry a request/trace ID for cross-service debugging.

### Common Violations

- `print()` / `console.log()` / `System.out.println()` in production code
- Logging entire request/response bodies (may contain PII or secrets)
- Catching an exception, logging it, then re-throwing the same exception
- ERROR level for expected business conditions (e.g., "user not found" during lookup)
- Missing context in log messages ("Error occurred" with no details)

---

## 10. Quality Gates

### Recommended Minimums

- Track **branch coverage**, not just line coverage. New code should not decrease existing coverage.
- 100% line coverage with no assertions is worthless — coverage measures execution, not verification.
- Zero lint errors enforced in CI. Style warnings optional; correctness rules mandatory.
- Consider mutation testing (pitest/stryker) — 70%+ mutation score indicates tests verify behavior.

---

## Quick-Reference Checklist

Use this for rapid code review scanning:

| Area | Key Question |
|---|---|
| Naming | Can I understand this name without reading the implementation? |
| Functions | Does this function do exactly one thing? |
| Classes | Can I describe this class's purpose in one sentence? |
| Errors | Is every failure path handled without returning null? |
| Tests | Does each test verify one behavior with a clear name? |
| Comments | Does this comment explain *why*, not *what*? |
| Formatting | Does this file read top-down like a newspaper article? |
| Boundaries | Is every external dependency behind an interface I control? |
