# Clean Code Best Practices - Comprehensive Reference

> Consolidated clean code principles + modern software engineering best practices.
> Organized for code review evaluation and team onboarding.

**Priority Key:**
- **P0** = Always enforce (block merge if violated)
- **P1** = Enforce in code reviews (request changes)
- **P2** = Nice-to-have (suggest but approve)

**Language Key:**
- **All** = Language-agnostic
- **Py** = Python
- **Java** = Java
- **TS/JS** = TypeScript / JavaScript

---

## 1. Naming

| ID | Rule | Priority | Source | Lang |
|----|------|----------|--------|------|
| NAM-01 | Use intention-revealing names. The name should answer why it exists, what it does, and how it is used. | P0 | Core | All |
| NAM-02 | Avoid disinformation. Do not use `accountList` unless it is actually a `List`. Do not use names that vary in small ways (`XYZControllerForHandlingOfStrings` vs `XYZControllerForStorageOfStrings`). | P1 | Core | All |
| NAM-03 | Make meaningful distinctions. Never use number-series naming (`a1, a2, a3`) or noise words (`ProductInfo` vs `ProductData`). | P0 | Core | All |
| NAM-04 | Use pronounceable names. If you cannot pronounce it, you cannot discuss it without sounding foolish. | P1 | Core | All |
| NAM-05 | Use searchable names. Single-letter names and numeric constants are hard to grep. Length of a name should correspond to the size of its scope. | P1 | Core | All |
| NAM-06 | Avoid encodings and Hungarian notation. No `strName`, `m_description`, `IShapeFactory`. Modern IDEs make type prefixes obsolete. | P1 | Core | All |
| NAM-07 | Class names should be nouns or noun phrases (`Customer`, `WikiPage`, `Account`). Never a verb. | P0 | Core | All |
| NAM-08 | Method names should be verbs or verb phrases (`postPayment`, `deletePage`, `save`). Accessors/mutators prefixed with `get`/`set`/`is`. | P0 | Core | All |
| NAM-09 | Use one word per concept consistently. Pick one of `fetch`/`retrieve`/`get` and stick with it across the codebase. | P1 | Core | All |
| NAM-10 | Use solution domain names when a CS term exists (`JobQueue`, `AccountVisitor`). Use problem domain names when no CS term fits. | P2 | Core | All |
| NAM-11 | Add no gratuitous context. In an application named "Gas Station Deluxe", do not prefix every class with `GSD`. Shorter names are better when clear. | P1 | Core | All |
| NAM-12 | N1: Choose descriptive names. Names are 90% of readability. Take time to choose well and rename when better names occur. | P0 | Core | All |
| NAM-13 | N2: Choose names at the appropriate level of abstraction. Do not pick names that communicate implementation; choose names that reflect the level of abstraction of the class or function. | P1 | Core | All |
| NAM-14 | N3: Use standard nomenclature where possible. Use `toString`, `Decorator`, `Factory` when the pattern applies. | P1 | Core | All |
| NAM-15 | N4: Use unambiguous names. Choose names that make the workings of a function or variable unambiguous. | P1 | Core | All |
| NAM-16 | N5: Use long names for long scopes. Short names (`i`, `j`) only for tiny scopes (5 lines). | P1 | Core | All |
| NAM-17 | N6: Avoid encodings. No Hungarian, no member prefixes, no type encodings. | P1 | Core | All |
| NAM-18 | N7: Names should describe side effects. `createOrReturnOos()` not `getOos()` if it creates on miss. | P0 | Core | All |

---

## 2. Functions

| ID | Rule | Priority | Source | Lang |
|----|------|----------|--------|------|
| FUN-01 | Functions should be small. Ideally under 20 lines, rarely over 30. | P1 | Core | All |
| FUN-02 | Do one thing. If a function does only steps one level below its name, it does one thing. | P0 | Core | All |
| FUN-03 | One level of abstraction per function. Do not mix `getHtml()` with `.append("\n")`. | P1 | Core | All |
| FUN-04 | The Stepdown Rule. Code should read top-to-bottom. Each function should be followed by functions at the next level of abstraction. | P2 | Core | All |
| FUN-05 | Limit arguments. Zero (niladic) is best, then one (monadic), then two (dyadic). Three (triadic) requires very special justification. More than three: use an argument object. | P1 | Core | All |
| FUN-06 | No flag arguments. Passing a boolean into a function is a terrible practice. It proclaims the function does two things. Split into two functions. | P1 | Core | All |
| FUN-07 | No side effects. A function named `checkPassword` should not initialize a session. Side effects are hidden lies. | P0 | Core | All |
| FUN-08 | Command-Query Separation. A function should either do something (command) or answer something (query), not both. `if (set("username", "bob"))` is confusing. | P1 | Core | All |
| FUN-09 | Prefer exceptions to returning error codes. Error codes force deeply nested `if` structures. | P1 | Core | All |
| FUN-10 | Extract try/catch bodies. The bodies of `try` and `catch` blocks should be extracted into their own functions. Error handling is one thing. | P2 | Core | All |
| FUN-11 | DRY (Don't Repeat Yourself). Duplication is the root of all evil in software. | P0 | Core | All |
| FUN-12 | F1: Too many arguments. Functions should have a small number of arguments. No argument is best, followed by one, two, and three. | P1 | Core | All |
| FUN-13 | F2: Output arguments. If your function must change state, have it change the state of its owning object. | P1 | Core | All |
| FUN-14 | F3: Flag arguments. Boolean arguments loudly declare the function does more than one thing. Eliminate them. | P1 | Core | All |
| FUN-15 | F4: Dead functions. Methods that are never called should be discarded. Version control remembers. | P1 | Core | All |

---

## 3. Comments

### Good Comments

| ID | Rule | Priority | Source | Lang |
|----|------|----------|--------|------|
| COM-01 | Legal comments. Copyright and license headers when required. | P2 | Core | All |
| COM-02 | Informative comments. Explain what a regex matches or what a return value represents when it cannot be expressed in the name. | P2 | Core | All |
| COM-03 | Explanation of intent. Why a decision was made, not what the code does. | P1 | Core | All |
| COM-04 | TODO comments. Acceptable for work that should be done but cannot be done right now. Must be cleaned up regularly. | P2 | Core | All |
| COM-05 | Warning comments. Warn other programmers about consequences (e.g., "this test takes a long time to run"). | P2 | Core | All |
| COM-06 | Amplification. A comment to amplify the importance of something that may otherwise seem inconsequential. | P2 | Core | All |

### Bad Comments (avoid or remove)

| ID | Rule | Priority | Source | Lang |
|----|------|----------|--------|------|
| COM-07 | No redundant comments. A comment that takes longer to read than the code is a failure. | P1 | Core | All |
| COM-08 | No misleading comments. Comments that are slightly inaccurate are worse than no comment. | P0 | Core | All |
| COM-09 | No mandated comments. Javadoc for every function or variable is clutter, not help. | P1 | Core | All |
| COM-10 | No journal comments. Remove changelogs from source files; that is what version control is for. | P1 | Core | All |
| COM-11 | No commented-out code. Delete it. Version control keeps the history. | P0 | Core | All |
| COM-12 | C1: Inappropriate information. Comments should not hold info better kept in other systems (issue trackers, VCS). | P1 | Core | All |
| COM-13 | C2: Obsolete comment. A comment that has gotten old, irrelevant, or incorrect. Update or delete. | P1 | Core | All |
| COM-14 | C3: Redundant comment. A comment that describes something already self-evident. | P1 | Core | All |
| COM-15 | C4: Poorly written comment. If you write a comment, take time to write it well. Use correct grammar. Be brief. | P2 | Core | All |
| COM-16 | C5: Commented-out code. Delete it. It rots. Others will be afraid to remove it. | P0 | Core | All |

---

## 4. Formatting

| ID | Rule | Priority | Source | Lang |
|----|------|----------|--------|------|
| FMT-01 | File size: target ~200 lines, hard limit 500 lines. Smaller files are easier to understand. | P1 | Core | All |
| FMT-02 | Newspaper metaphor. Name at the top, high-level summary next, details increase as we move down. | P1 | Core | All |
| FMT-03 | Vertical openness. Blank lines between distinct concepts (imports, each function, logical sections). | P1 | Core | All |
| FMT-04 | Vertical density. Lines that are tightly related should appear close together. No random blank lines between related statements. | P1 | Core | All |
| FMT-05 | Vertical distance. Variables declared close to their usage. Instance variables at the top of the class. Dependent functions close together. | P1 | Core | All |
| FMT-06 | Caller above callee. If function A calls function B, A should be above B (stepdown rule). | P2 | Core | All |
| FMT-07 | Line length under 120 characters. Prefer 80-100. Never force horizontal scrolling. | P1 | Core | All |
| FMT-08 | Horizontal alignment of assignments is not useful. Let indentation and short statements do the work. | P2 | Core | All |
| FMT-09 | Indentation. Never break the indentation structure. Even for short `if` or `while` bodies. | P1 | Core | All |
| FMT-10 | Team rules. A team should agree on a single formatting style. Consistency trumps personal preference. Use autoformatters. | P0 | Core | All |

---

## 5. Objects & Data Structures

| ID | Rule | Priority | Source | Lang |
|----|------|----------|--------|------|
| OBJ-01 | Hide implementation behind abstractions. Exposing implementation couples callers to details. | P0 | Core | All |
| OBJ-02 | Objects expose behavior, hide data. You tell an object to do something; you do not ask for its internals. | P1 | Core | All |
| OBJ-03 | Data structures expose data, have no meaningful behavior. DTOs, records, dataclasses. | P1 | Core | All |
| OBJ-04 | Law of Demeter. A method `f` of class `C` should only call methods on: `C` itself, objects created by `f`, objects passed as arguments to `f`, objects held as instance variables of `C`. | P1 | Core | All |
| OBJ-05 | No train wrecks. `a.getB().getC().doSomething()` violates Law of Demeter. Break the chain. | P1 | Core | All |
| OBJ-06 | No hybrids. A class that is half object and half data structure is the worst of both worlds. Decide which it is. | P1 | Core | All |
| OBJ-07 | Data Transfer Objects (DTOs) should be simple. No business logic. Public fields or simple accessors only. | P1 | Core | All |

---

## 6. Error Handling

| ID | Rule | Priority | Source | Lang |
|----|------|----------|--------|------|
| ERR-01 | Use exceptions, not return codes. Exceptions separate error handling from the happy path. | P1 | Core | All |
| ERR-02 | Write your try-catch-finally first. Define the scope and transaction behavior early. | P2 | Core | All |
| ERR-03 | Use unchecked exceptions. Checked exceptions violate OCP; a low-level change forces signature changes up the call chain. | P1 | Core | Java |
| ERR-04 | Provide context with exceptions. Include the operation that failed and the type of failure. Stack traces alone are not enough. | P0 | Core | All |
| ERR-05 | Define exception classes in terms of the caller's needs. Wrap third-party exceptions to unify the interface. | P1 | Core | All |
| ERR-06 | Use the Special Case pattern. Instead of checking for null, return a special case object that encapsulates the behavior. | P1 | Core | All |
| ERR-07 | Do not return null. Returning null creates work for callers and invites NullPointerExceptions. Return empty collections, Optional, or throw. | P0 | Core | All |
| ERR-08 | Do not pass null. Passing null to a method is worse than returning it. Unless an API expects null, forbid it. | P0 | Core | All |

---

## 7. Boundaries

| ID | Rule | Priority | Source | Lang |
|----|------|----------|--------|------|
| BND-01 | Wrap third-party APIs. Create your own interface around external code. Protects against API changes and simplifies testing. | P1 | Core | All |
| BND-02 | Write learning tests. When integrating a third-party library, write tests to verify your understanding. They also serve as an early warning when the library updates. | P2 | Core | All |
| BND-03 | Use code that does not yet exist. Define the interface you wish you had and write an adapter later. | P2 | Core | All |
| BND-04 | Clean boundaries. Keep third-party types from leaking into your domain. Map at the boundary. | P1 | Core | All |

---

## 8. Unit Tests

| ID | Rule | Priority | Source | Lang |
|----|------|----------|--------|------|
| TST-01 | TDD First Law: Do not write production code until you have a failing test. | P1 | Core | All |
| TST-02 | TDD Second Law: Write only enough of a test to demonstrate a failure. | P1 | Core | All |
| TST-03 | TDD Third Law: Write only enough production code to pass the currently failing test. | P1 | Core | All |
| TST-04 | Clean tests are readable tests. Clarity, simplicity, density of expression. Build a test DSL if needed. | P1 | Core | All |
| TST-05 | One concept per test. Do not test multiple concerns in a single test function. | P1 | Core | All |
| TST-06 | **F**ast. Tests should run quickly. Slow tests do not get run. | P0 | Core | All |
| TST-07 | **I**ndependent. Tests should not depend on each other. Any test should run alone or in any order. | P0 | Core | All |
| TST-08 | **R**epeatable. Tests should be repeatable in any environment (dev, CI, airplane mode). | P0 | Core | All |
| TST-09 | **S**elf-validating. Tests should have a boolean output: pass or fail. No manual log inspection. | P0 | Core | All |
| TST-10 | **T**imely. Write tests just before the production code that makes them pass. | P1 | Core | All |
| TST-11 | T1: Insufficient tests. A test suite should test everything that could break. Use coverage tools as a guide, not a goal. | P1 | Core | All |
| TST-12 | T2: Use a coverage tool. They highlight untested modules, classes, and functions. | P1 | Core | All |
| TST-13 | T3: Do not skip trivial tests. They are easy to write and their documentary value is high. | P2 | Core | All |
| TST-14 | T4: An ignored test is a question about an ambiguity. Use `@Ignore`/`skip` with a comment explaining why. | P1 | Core | All |
| TST-15 | T5: Test boundary conditions. The boundaries are where bugs cluster. | P0 | Core | All |
| TST-16 | T6: Exhaustively test near bugs. Bugs tend to congregate. When you find a bug, test the neighboring code thoroughly. | P1 | Core | All |
| TST-17 | T7: Patterns of failure are revealing. If tests fail in a pattern, diagnose the pattern not just the test. | P2 | Core | All |
| TST-18 | T8: Test coverage patterns can be revealing. Look at the code that is or is not executed by passing tests. | P2 | Core | All |
| TST-19 | T9: Tests should be fast. A slow test is a test that will not get run. | P0 | Core | All |

---

## 9. Classes

| ID | Rule | Priority | Source | Lang |
|----|------|----------|--------|------|
| CLS-01 | Classes should be small. Measured by responsibilities, not lines. A class name should describe its single responsibility. | P0 | Core | All |
| CLS-02 | Single Responsibility Principle (SRP). A class should have one, and only one, reason to change. | P0 | Core | All |
| CLS-03 | High cohesion. Methods should manipulate one or more instance variables. More variables each method uses means higher cohesion. | P1 | Core | All |
| CLS-04 | When classes lose cohesion, split them. If a subset of variables is used by a subset of methods, those form a new class. | P1 | Core | All |
| CLS-05 | Open-Closed Principle (OCP). Classes should be open for extension, closed for modification. Use interfaces and abstract classes. | P1 | Core | All |
| CLS-06 | Dependency Inversion Principle (DIP). Depend on abstractions, not on concretions. High-level modules must not depend on low-level modules. | P1 | Core | All |
| CLS-07 | Organize for change. Structure classes so that adding new functionality does not require modifying existing code. | P1 | Core | All |

---

## 10. Systems

| ID | Rule | Priority | Source | Lang |
|----|------|----------|--------|------|
| SYS-01 | Separate construction from use. The startup process (building object graph) is a concern separate from runtime logic. | P1 | Core | All |
| SYS-02 | Use dependency injection. Let a framework or main() build and wire the object graph. Objects should not know how to construct their dependencies. | P1 | Core | All |
| SYS-03 | Scale incrementally. Do not build a grand architecture up front. Start simple and evolve with tests. YAGNI. | P1 | Core | All |
| SYS-04 | Use the simplest thing that could possibly work. Do not over-engineer. Add complexity only when tests and requirements demand it. | P1 | Core | All |
| SYS-05 | Separate cross-cutting concerns (logging, security, transactions) from business logic. Use aspects, middleware, or decorators. | P1 | Core | All |
| SYS-06 | Use standards wisely. Standards only help when they genuinely serve the project, not when they are resume-driven. | P2 | Core | All |

---

## 11. Emergence

| ID | Rule | Priority | Source | Lang |
|----|------|----------|--------|------|
| EMR-01 | Rule 1 (most important): Runs all the tests. A system that cannot be verified should not be deployed. Tests drive design toward small, single-purpose classes. | P0 | Core | All |
| EMR-02 | Rule 2: No duplication. Duplication is the primary enemy of a well-designed system. Extract common code rigorously. | P0 | Core | All |
| EMR-03 | Rule 3: Expresses the intent of the programmer. Good names, small functions, standard patterns, well-written tests. | P0 | Core | All |
| EMR-04 | Rule 4: Minimizes the number of classes and methods. Keep the system small. This rule has the lowest priority of the four. Do not create classes and interfaces just to follow dogma. | P2 | Core | All |

---

## 12. Concurrency

| ID | Rule | Priority | Source | Lang |
|----|------|----------|--------|------|
| CON-01 | Concurrency is hard. Even simple-looking concurrent code can behave in surprising ways. Treat with respect. | P0 | Core | All |
| CON-02 | Keep concurrent code separate. Concurrency-related code has its own lifecycle and challenges. Isolate it from other code. | P1 | Core | All |
| CON-03 | Limit the scope of shared data. Fewer places that share mutable data means fewer sources of bugs. Use encapsulation rigorously. | P0 | Core | All |
| CON-04 | Use copies of data. If possible, avoid sharing data entirely. Give each thread its own copy and merge results. | P1 | Core | All |
| CON-05 | Threads should be as independent as possible. Each thread should process its own data with no sharing. | P1 | Core | All |
| CON-06 | Keep synchronized sections small. Locks are expensive and invite deadlocks. Minimize the code between lock and unlock. | P0 | Core | All |
| CON-07 | Know your execution models. Understand Producer-Consumer, Readers-Writers, and Dining Philosophers. Know which one applies to your problem. | P1 | Core | All |
| CON-08 | Beware dependencies between synchronized methods. If a class has more than one synchronized method, consider the coupling. | P1 | Core | All |
| CON-09 | Write tests that expose concurrency problems. Run with more threads than processors, on different platforms, with random instrumentation. | P1 | Core | All |
| CON-10 | Do not ignore one-off failures. Threading bugs masquerade as one-time flukes. Never dismiss a failure as "cosmic ray". | P0 | Core | All |

---

## 13. Code Smells Quick Reference

All 66 cataloged code smells, organized by category.

### Comments (C1-C5)

| Smell | Description |
|-------|-------------|
| C1 | Inappropriate Information -- comments holding info better held in VCS, issue tracker, etc. |
| C2 | Obsolete Comment -- old, irrelevant, or incorrect comment. |
| C3 | Redundant Comment -- describes something self-evident. |
| C4 | Poorly Written Comment -- worth writing well or not at all. |
| C5 | Commented-Out Code -- dead code. Delete it. |

### Environment (E1-E2)

| Smell | Description |
|-------|-------------|
| E1 | Build Requires More Than One Step -- build should be a single trivial command. |
| E2 | Tests Require More Than One Step -- running all tests should be a single trivial command. |

### Functions (F1-F4)

| Smell | Description |
|-------|-------------|
| F1 | Too Many Arguments -- fewer is better, more than three is very questionable. |
| F2 | Output Arguments -- readers expect arguments to be inputs, not outputs. |
| F3 | Flag Arguments -- boolean arguments indicate the function does more than one thing. |
| F4 | Dead Function -- never called. Delete it. |

### General (G1-G36)

| Smell | Description |
|-------|-------------|
| G1 | Multiple Languages in One Source File -- minimize the number of languages in a single file. |
| G2 | Obvious Behavior Is Unimplemented -- function does not do what its name promises. |
| G3 | Incorrect Behavior at the Boundaries -- do not rely on intuition; test every boundary. |
| G4 | Insufficient Safety -- disabled compiler warnings, failed tests, turned-off checks. |
| G5 | Duplication -- DRY. Every duplicate is a missed abstraction. Consider Template Method or Strategy. |
| G6 | Code at Wrong Level of Abstraction -- separate higher-level concepts from lower-level details. |
| G7 | Base Classes Depending on Their Derivatives -- base classes should know nothing of their derivatives. |
| G8 | Too Much Information -- well-defined modules have small, tight interfaces. |
| G9 | Dead Code -- code that is not executed. Find it and remove it. |
| G10 | Vertical Separation -- variables and functions should be defined close to where they are used. |
| G11 | Inconsistency -- if you do something a certain way, do all similar things in the same way. |
| G12 | Clutter -- unused variables, uncalled functions, meaningless comments. Remove them. |
| G13 | Artificial Coupling -- things that do not depend on each other should not be coupled. Do not put general utilities inside specific classes. |
| G14 | Feature Envy -- a method that uses accessors of another object more than its own. Move the method. |
| G15 | Selector Arguments -- boolean or enum arguments that select behavior. Use polymorphism instead. |
| G16 | Obscured Intent -- code that is unnecessarily hard to read (Hungarian, magic numbers, dense expressions). |
| G17 | Misplaced Responsibility -- code should be where the reader expects it. Use the Principle of Least Surprise. |
| G18 | Inappropriate Static -- if there is any chance a function needs to be polymorphic, make it non-static. |
| G19 | Use Explanatory Variables -- break complex calculations into intermediate variables with meaningful names. |
| G20 | Function Names Should Say What They Do -- if you need to read the body to know, rename. |
| G21 | Understand the Algorithm -- do not just make it work by tinkering. Understand it first, then make it clean. |
| G22 | Make Logical Dependencies Physical -- if a module depends on another, the dependency should be explicit, not assumed. |
| G23 | Prefer Polymorphism to If/Else or Switch/Case -- use polymorphism for most conditional behavior. ONE switch is tolerable in a factory; repeated switches are not. |
| G24 | Follow Standard Conventions -- follow team/community coding standards. Every member should follow them. |
| G25 | Replace Magic Numbers with Named Constants -- `SECONDS_PER_DAY = 86400` not `86400`. |
| G26 | Be Precise -- do not be lazy about decisions. Know why you are calling `float` vs `double`, `List` vs `Set`. |
| G27 | Structure over Convention -- enforce design decisions with structure (types, interfaces) not just convention (comments, wiki pages). |
| G28 | Encapsulate Conditionals -- extract boolean logic into well-named functions: `if (shouldBeDeleted(timer))` not `if (timer.hasExpired() && !timer.isRecurrent())`. |
| G29 | Avoid Negative Conditionals -- `if (buffer.shouldCompact())` not `if (!buffer.shouldNotCompact())`. |
| G30 | Functions Should Do One Thing -- see FUN-02. |
| G31 | Hidden Temporal Couplings -- if functions must be called in order, make the ordering explicit with return values that feed into arguments. |
| G32 | Don't Be Arbitrary -- have a reason for the structure of your code. If the structure appears arbitrary, others will feel empowered to change it. |
| G33 | Encapsulate Boundary Conditions -- put processing for boundary conditions in one place. `level + 1` should appear once, assigned to `nextLevel`. |
| G34 | Functions Should Descend Only One Level of Abstraction -- statements within a function should be at the same level of abstraction. |
| G35 | Keep Configurable Data at High Levels -- constants and defaults should be declared at high levels and passed down, not buried in low-level functions. |
| G36 | Avoid Transitive Navigation -- (Law of Demeter) `a.getB().getC()` is fragile. Write `a.getC()` or redesign. |

### Java-Specific (J1-J3)

| Smell | Description |
|-------|-------------|
| J1 | Avoid Long Import Lists by Using Wildcards -- (debated in modern Java; teams should decide). |
| J2 | Don't Inherit Constants -- use static imports, not interface inheritance for constants. |
| J3 | Use Enums, Not Constants -- `enum Color { RED, GREEN }` not `static final int COLOR_RED = 1`. |

### Names (N1-N7)

| Smell | Description |
|-------|-------------|
| N1 | Choose Descriptive Names -- invest time. Names account for 90% of readability. |
| N2 | Choose Names at the Appropriate Level of Abstraction -- reflect the abstraction, not the implementation. |
| N3 | Use Standard Nomenclature Where Possible -- leverage well-known patterns and conventions. |
| N4 | Unambiguous Names -- choose names that make the function/variable unambiguous. |
| N5 | Use Long Names for Long Scopes -- name length proportional to scope size. |
| N6 | Avoid Encodings -- no type or scope prefixes. |
| N7 | Names Should Describe Side Effects -- the name must reflect everything the function does. |

### Tests (T1-T9)

| Smell | Description |
|-------|-------------|
| T1 | Insufficient Tests -- test everything that could possibly break. |
| T2 | Use a Coverage Tool -- coverage highlights missed tests. |
| T3 | Don't Skip Trivial Tests -- easy to write, high documentary value. |
| T4 | An Ignored Test Is a Question About an Ambiguity -- use it to mark unclear requirements. |
| T5 | Test Boundary Conditions -- bugs hide at boundaries. |
| T6 | Exhaustively Test Near Bugs -- bugs cluster; find one, test the neighborhood. |
| T7 | Patterns of Failure Are Revealing -- analyze patterns, not just individual failures. |
| T8 | Test Coverage Patterns Can Be Revealing -- what is not tested hints at what may be broken. |
| T9 | Tests Should Be Fast -- slow tests will not get run. |

---

## 14. Modern Additions

These practices extend established principles with lessons from modern software engineering.

### 14.1 Functional Programming

| ID | Rule | Priority | Source | Lang |
|----|------|----------|--------|------|
| MOD-01 | Prefer immutability. Use `const`, `final`, `readonly`, frozen dataclasses. Mutable state is the root of most concurrency and reasoning bugs. | P0 | Modern | All |
| MOD-02 | Write pure functions. Given the same inputs, always return the same output. No side effects. Dramatically improves testability. | P1 | Modern | All |
| MOD-03 | Favor composition over inheritance. Small, composable functions/modules are more flexible than deep class hierarchies. | P1 | Modern | All |
| MOD-04 | Use higher-order functions (`map`, `filter`, `reduce`) instead of manual loops when they improve clarity. Do not force them when a loop is clearer. | P2 | Modern | All |
| MOD-05 | Keep data transformations as pipelines. Each step is a pure function, making the flow easy to trace and test. | P2 | Modern | All |

### 14.2 Type Systems

| ID | Rule | Priority | Source | Lang |
|----|------|----------|--------|------|
| MOD-06 | Use types as documentation. A well-typed function signature tells you what it does without reading the body. | P1 | Modern | TS/JS, Py, Java |
| MOD-07 | Use discriminated unions / tagged unions for state modeling. `type Result = Success | Failure` is clearer and safer than status codes. | P1 | Modern | TS/JS, Py |
| MOD-08 | Avoid `any` (TS), `Object` (Java), bare `dict` (Py). Be specific. These types defeat the purpose of a type system. | P0 | Modern | All |
| MOD-09 | Encode business rules in types. `type PositiveInt` or `type EmailAddress` makes invalid states unrepresentable. | P2 | Modern | All |

### 14.3 Async/Await

| ID | Rule | Priority | Source | Lang |
|----|------|----------|--------|------|
| MOD-10 | Prefer async/await over callbacks or raw promises. Reads like synchronous code, easier to follow and debug. | P1 | Modern | TS/JS, Py |
| MOD-11 | Handle errors explicitly in async code. Unhandled promise rejections crash servers. Always `try/catch` or `.catch()`. | P0 | Modern | TS/JS, Py |
| MOD-12 | Keep async functions small. Long async functions with many awaits are hard to reason about and debug. | P1 | Modern | TS/JS, Py |
| MOD-13 | Use `Promise.all` / `asyncio.gather` for independent concurrent work. Sequential awaits for independent operations waste time. | P1 | Modern | TS/JS, Py |
| MOD-14 | Avoid mixing async and sync paradigms. Do not call sync I/O in an async context or vice versa. | P1 | Modern | All |

### 14.4 Modern Testing

| ID | Rule | Priority | Source | Lang |
|----|------|----------|--------|------|
| MOD-15 | Arrange-Act-Assert (AAA). Every test has three clear sections: setup, execute, verify. Also known as Given-When-Then. | P1 | Modern | All |
| MOD-16 | Prefer fakes over mocks. In-memory implementations are more realistic than mock frameworks. Mocks couple tests to implementation. | P1 | Modern | All |
| MOD-17 | Property-based testing. When a function has a property that should hold for all inputs, test it with randomized inputs (Hypothesis, fast-check, jqwik). | P2 | Modern | All |
| MOD-18 | Test behavior, not implementation. Tests should verify what the code does, not how it does it. Refactoring should not break tests. | P0 | Modern | All |
| MOD-19 | Snapshot tests are fragile. Use sparingly. Prefer explicit assertions on specific fields. | P2 | Modern | TS/JS |

### 14.5 Dependency Injection Without Frameworks

| ID | Rule | Priority | Source | Lang |
|----|------|----------|--------|------|
| MOD-20 | Constructor injection. Pass dependencies through the constructor. Simple, explicit, no magic. | P1 | Modern | All |
| MOD-21 | Default parameters for convenience. `def make_service(db=None): db = db or RealDb()` makes testing easy without a DI container. | P2 | Modern | Py, TS/JS |
| MOD-22 | Avoid service locator pattern. Global registries hide dependencies. Prefer explicit wiring. | P1 | Modern | All |

---

## 15. Language-Specific Patterns

### 15.1 Python

| ID | Rule | Priority | Source | Lang |
|----|------|----------|--------|------|
| PY-01 | Use `snake_case` for functions/variables, `PascalCase` for classes. Follow PEP 8. | P0 | PEP 8 | Py |
| PY-02 | Use type hints everywhere. `def get_user(user_id: int) -> User:` -- enables IDE support, documentation, and mypy. | P1 | Modern | Py |
| PY-03 | Use `dataclasses` or `pydantic` for data containers. Avoid plain dicts for structured data; you lose autocomplete and validation. | P1 | Modern | Py |
| PY-04 | Never use mutable default arguments. `def f(items=[])` shares the list across calls. Use `def f(items=None): items = items or []`. | P0 | Py Gotcha | Py |
| PY-05 | Never use bare `except:`. Catches `SystemExit` and `KeyboardInterrupt`. At minimum `except Exception:`. | P0 | PEP 8 | Py |
| PY-06 | Use context managers (`with`) for resource management. Files, locks, DB connections. Guarantees cleanup. | P0 | Pythonic | Py |
| PY-07 | EAFP over LBYL. "Easier to Ask Forgiveness than Permission." Use `try/except` rather than `if key in dict` when access is the common case. | P2 | Pythonic | Py |
| PY-08 | Use list comprehensions over `map`/`filter` when clearer. But do not nest more than two levels. Extract a function instead. | P1 | Pythonic | Py |
| PY-09 | Use `pathlib.Path` over `os.path`. Cleaner API, object-oriented, cross-platform. | P2 | Modern | Py |
| PY-10 | Use `__slots__` for classes with many instances if memory is a concern. Prevents dynamic attribute creation. | P2 | Modern | Py |
| PY-11 | Prefer `Enum` over string literals for fixed sets of values. Avoids typos, enables IDE support. | P1 | Modern | Py |
| PY-12 | Use `logging` module, not `print()`. Structured logging with levels. Never log sensitive data. | P1 | Modern | Py |

### 15.2 TypeScript / JavaScript

| ID | Rule | Priority | Source | Lang |
|----|------|----------|--------|------|
| TS-01 | Use `camelCase` for variables/functions, `PascalCase` for classes/types/interfaces. | P0 | Convention | TS/JS |
| TS-02 | Always use `===` and `!==`. Never `==` or `!=`. JavaScript type coercion is a source of subtle bugs. | P0 | Best Practice | TS/JS |
| TS-03 | Use `const` by default, `let` when reassignment is needed. Never use `var`. | P0 | ES6+ | TS/JS |
| TS-04 | Use `unknown` over `any`. `unknown` forces you to narrow the type before use; `any` disables type checking. | P0 | Modern TS | TS/JS |
| TS-05 | Use discriminated unions for state machines. `type State = { kind: 'loading' } \| { kind: 'done'; data: T } \| { kind: 'error'; error: Error }`. | P1 | Modern TS | TS/JS |
| TS-06 | Use optional chaining (`?.`) and nullish coalescing (`??`). Cleaner than manual null checks. But do not chain more than 3 levels deep. | P1 | ES2020 | TS/JS |
| TS-07 | Always handle Promise rejections. Unhandled rejections crash Node processes. Use `try/catch` in `async` functions, `.catch()` on raw promises. | P0 | Best Practice | TS/JS |
| TS-08 | Clean up event listeners and subscriptions. Memory leaks from forgotten listeners are a top production bug. Use `AbortController` where possible. | P1 | Modern | TS/JS |
| TS-09 | Prefer `interface` over `type` for object shapes that may be extended. Use `type` for unions and intersections. | P2 | Convention | TS/JS |
| TS-10 | Use `readonly` modifier for properties that should not change after construction. | P1 | Modern TS | TS/JS |
| TS-11 | Avoid `enum` in TypeScript. Prefer `as const` objects or union types. TS enums have surprising runtime behavior. | P2 | Modern TS | TS/JS |
| TS-12 | Use `Array.isArray()` instead of `instanceof Array`. Works across realms (iframes, worker threads). | P2 | Best Practice | TS/JS |

### 15.3 Java

| ID | Rule | Priority | Source | Lang |
|----|------|----------|--------|------|
| JV-01 | Use enums over `public static final int` constants. Type-safe, iterable, can hold behavior. | P0 | Effective Java | Java |
| JV-02 | Use try-with-resources for all `AutoCloseable` objects. `try (var stream = ...)` prevents resource leaks. | P0 | Java 7+ | Java |
| JV-03 | Override `equals` and `hashCode` together. Violating the contract breaks `HashMap`, `HashSet`, and any collection relying on hashing. | P0 | Effective Java | Java |
| JV-04 | Use generics. Avoid raw types. `List<String>` not `List`. Raw types lose type safety at compile time. | P0 | Effective Java | Java |
| JV-05 | Use checked exceptions only for recoverable conditions. Use runtime exceptions for programming errors (`IllegalArgumentException`, `NullPointerException`). | P1 | Effective Java | Java |
| JV-06 | Use the Builder pattern for constructors with many parameters. `new User.Builder("Alice").age(30).build()` is clearer than a 6-parameter constructor. | P1 | Effective Java | Java |
| JV-07 | Use Stream API for collection transformations. `list.stream().filter(...).map(...).collect(...)` is often cleaner than loops. But do not over-chain; extract intermediate variables for clarity. | P1 | Java 8+ | Java |
| JV-08 | Use `Optional` instead of returning null. `Optional.ofNullable(value)` makes the possibility of absence explicit. Never use `Optional` for fields or parameters -- only return types. | P1 | Java 8+ | Java |
| JV-09 | Favor composition over inheritance. Extend only when there is a genuine "is-a" relationship. Use delegation otherwise. | P1 | Effective Java | Java |
| JV-10 | Make classes and members as inaccessible as possible. Default to `private`. Expose only what is necessary. | P1 | Effective Java | Java |
| JV-11 | Use records for simple data carriers (Java 16+). `record Point(int x, int y) {}` eliminates boilerplate. | P1 | Modern Java | Java |
| JV-12 | Prefer `List.of()`, `Map.of()` for immutable collections. Mutable collections should be explicit choices, not defaults. | P1 | Java 9+ | Java |

---

## 16. Anti-Pattern Recognition Guide

Common anti-patterns that violate clean code principles, with the corresponding rule ID.

### 16.1 Naming Anti-Patterns

| Anti-Pattern | Example | Fix | Rule |
|---|---|---|---|
| Single-letter variables in large scope | `d = get_duration()` | `elapsed_days = get_duration()` | NAM-05 |
| Type-encoded names | `strFirstName`, `iCount` | `first_name`, `count` | NAM-06 |
| Generic names | `data`, `info`, `temp`, `result`, `value` | Name the specific thing it holds | NAM-01 |
| Misleading abbreviations | `hp` (hitpoints? horsepower? Hewlett-Packard?) | Spell it out: `hit_points` | NAM-02 |
| Inconsistent vocabulary | `fetchUser()`, `retrieveAccount()`, `getOrder()` | Pick one verb: `get_user()`, `get_account()`, `get_order()` | NAM-09 |
| Class named with verb | `MakePayment`, `RunReport` | `PaymentProcessor`, `ReportGenerator` | NAM-07 |
| Method named with noun | `user.transaction()` | `user.execute_transaction()` | NAM-08 |
| Boolean without question form | `valid`, `disabled` | `is_valid`, `is_disabled` | NAM-15 |

### 16.2 Function Anti-Patterns

| Anti-Pattern | Example | Fix | Rule |
|---|---|---|---|
| God function | 200-line `processOrder()` | Extract into `validate_order()`, `calculate_total()`, `apply_discount()`, `submit_order()` | FUN-01, FUN-02 |
| Flag argument | `render(data, is_pdf=True)` | `render_pdf(data)` and `render_html(data)` | FUN-06 |
| Side effect in getter | `get_user()` also logs analytics | Separate `get_user()` and `track_user_access()` | FUN-07 |
| Output argument | `append_footer(report)` modifies report | `report.append_footer()` or `new_report = with_footer(report)` | FUN-13 |
| Deep nesting (arrow code) | 5+ levels of if/for/try | Extract methods, use early returns, use guard clauses | FUN-01 |
| Returning error code | `return -1` on failure | Raise/throw an exception | FUN-09 |

### 16.3 Class Anti-Patterns

| Anti-Pattern | Example | Fix | Rule |
|---|---|---|---|
| God class | `ApplicationManager` with 50 methods | Split by responsibility into focused classes | CLS-01, CLS-02 |
| Data class with logic | DTO with `validate()`, `save()`, `notify()` | Move logic to service classes; keep DTO pure | OBJ-06 |
| Utility class explosion | `StringUtils`, `DateUtils`, `MathUtils` each with 50 methods | Group by domain concept, not by type | CLS-02 |
| Inheritance for code reuse | `class Dog extends DatabaseEntity` | Use composition: `class Dog { db: DatabaseEntity }` | MOD-03 |
| Anemic domain model | All logic in services, entities are just data | Move behavior to entities where it belongs | OBJ-02 |

### 16.4 Testing Anti-Patterns

| Anti-Pattern | Example | Fix | Rule |
|---|---|---|---|
| Test with no assertion | Test calls function but never asserts | Always assert expected outcomes | TST-09 |
| Test that tests everything | Single test with 15 assertions on different behaviors | One concept per test | TST-05 |
| Test coupled to implementation | Asserting mock was called 3 times with exact args | Assert on observable behavior | MOD-18 |
| Flaky test | Passes 9/10 times due to timing | Remove time dependency, use deterministic fakes | TST-08 |
| Shared mutable state between tests | Tests modify a class-level variable | Each test sets up its own state | TST-07 |
| Testing private methods | Reaching into internals via reflection | Test through the public API | MOD-18 |
| Copy-paste test code | 20 tests with identical setup blocks | Extract setup into helper/fixture | FUN-11 |

---

## 17. Decision Trees

### When to Write a Comment

```
Is the code unclear?
  -> Can you rename to make it clear? -> YES -> Rename, no comment needed.
  -> NO (e.g., regex, algorithm, business rule) -> Write an INTENT comment (COM-03).
Is there a non-obvious consequence? -> Write a WARNING comment (COM-05).
Is there a known issue to fix later? -> Write a TODO comment (COM-04).
Is it a legal requirement? -> Write a LEGAL comment (COM-01).
Otherwise -> Do not write a comment.
```

### When to Create a New Class

```
Does the existing class have more than one reason to change? -> YES -> Extract (CLS-02).
Are a subset of methods using a subset of fields? -> YES -> Extract (CLS-04).
Is the class over 200 lines? -> Consider splitting if cohesion is low (CLS-01).
Are you adding a new responsibility? -> New class, not a new method on existing (CLS-02).
```

### When to Refactor vs. Rewrite

```
Do tests exist for the code?
  -> YES -> Refactor incrementally. Change one thing, run tests, repeat.
  -> NO -> Write characterization tests first, then refactor.
Is the code < 100 lines? -> Rewrite may be faster than understanding it.
Is the code > 500 lines with no tests? -> Write tests for the boundaries, then refactor section by section.
```

### Error Handling Strategy

```
Is the error recoverable by the caller?
  -> YES -> Throw a specific exception with context (ERR-04, ERR-05).
  -> NO -> Let it propagate to a top-level handler.
Could the value legitimately be absent?
  -> YES -> Return Optional / Maybe / None with type annotation (ERR-07).
  -> NO -> Throw; do not return null (ERR-07).
Is this a third-party exception?
  -> YES -> Wrap it in your own exception type (ERR-05, BND-01).
```

---

## 18. Code Review Checklist (Quick Scan)

Use this ordered checklist for efficient reviews. Stop at the first P0 violation, request changes, then proceed.

### Pass 1: P0 Violations (block merge)

- [ ] No commented-out code (COM-16)
- [ ] No returning or passing null without justification (ERR-07, ERR-08)
- [ ] Intention-revealing names (NAM-01)
- [ ] Functions do one thing (FUN-02)
- [ ] No side effects hidden in function names (FUN-07, NAM-18)
- [ ] Classes have single responsibility (CLS-02)
- [ ] Error handling provides context (ERR-04)
- [ ] Tests exist and pass (EMR-01)
- [ ] Tests are independent and repeatable (TST-07, TST-08)
- [ ] Shared mutable state is properly synchronized (CON-03, CON-06)
- [ ] Team formatting rules followed (FMT-10)
- [ ] No `any`/untyped code without justification (MOD-08)
- [ ] Async errors handled explicitly (MOD-11)
- [ ] Immutability used where possible (MOD-01)

### Pass 2: P1 Violations (request changes)

- [ ] Functions under 20 lines (FUN-01)
- [ ] Max 3 function arguments (FUN-05)
- [ ] No redundant comments (COM-07)
- [ ] No train wrecks / Law of Demeter violations (OBJ-05)
- [ ] Third-party APIs wrapped at boundary (BND-01)
- [ ] One concept per test (TST-05)
- [ ] Consistent naming conventions (NAM-09, G11)
- [ ] No flag arguments (FUN-06)
- [ ] DRY -- no copy-paste duplication (FUN-11, EMR-02)
- [ ] Build and tests each require one command (E1, E2)
- [ ] High cohesion within classes (CLS-03)

### Pass 3: P2 Suggestions (approve with comment)

- [ ] Stepdown rule followed (FUN-04)
- [ ] File size under 200 lines target (FMT-01)
- [ ] Learning tests for new third-party integrations (BND-02)
- [ ] Property-based tests for pure functions (MOD-17)
- [ ] Explanatory variables for complex expressions (G19)

---

## Quick Reference: Priority Distribution

| Priority | Count | Description |
|----------|-------|-------------|
| **P0** | ~35 | Always enforce. Block merge on violation. |
| **P1** | ~70 | Enforce in reviews. Request changes. |
| **P2** | ~25 | Nice-to-have. Suggest, but approve. |

## How to Use This Document

1. **New team member onboarding**: Read sections 1-6 first, then 8.
2. **Code review checklist**: Start with P0 rules, then P1.
3. **Tech debt audit**: Use Section 13 (Code Smells) as a scanning checklist.
4. **Language-specific review**: Jump to Section 15 for the relevant language.
5. **Architecture review**: Sections 9-11.
6. **Concurrency review**: Section 12 is mandatory reading.

---

*Sources: Established clean code principles, modern refactoring practices, language-specific style guides (PEP 8, TypeScript Handbook, Effective Java patterns), and test-driven development methodology.*
