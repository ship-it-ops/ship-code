# Code Smells and Heuristics Quick Reference

A comprehensive checklist of common code smells and how to fix them.

## Comments

| ID | Smell | How to Detect | How to Fix |
|----|-------|---------------|------------|
| C1 | Inappropriate Information | Comments contain metadata (author, date, changelog) | Move to version control metadata |
| C2 | Obsolete Comment | Comment describes code that has changed | Delete or update the comment |
| C3 | Redundant Comment | Comment restates what the code clearly says | Delete the comment |
| C4 | Poorly Written Comment | Grammar errors, rambling, unclear | Rewrite concisely or delete |
| C5 | Commented-Out Code | Lines of code in comments | Delete — VCS has the history |

## Environment

| ID | Smell | How to Detect | How to Fix |
|----|-------|---------------|------------|
| E1 | Build Requires More Than One Step | Multi-command build process | Create single-command build script |
| E2 | Tests Require More Than One Step | Multi-command test execution | Create single-command test runner |

## Functions

| ID | Smell | How to Detect | How to Fix |
|----|-------|---------------|------------|
| F1 | Too Many Arguments | Function takes >3 parameters | Group into parameter object |
| F2 | Output Arguments | Function modifies its arguments | Return the result instead |
| F3 | Flag Arguments | Boolean parameter selecting behavior | Split into two functions |
| F4 | Dead Function | Function never called | Delete it |

## General

| ID | Smell | How to Detect | How to Fix |
|----|-------|---------------|------------|
| G1 | Multiple Languages in One Source File | File contains mixed languages (HTML+JS+CSS, SQL in Java) | Separate into distinct files or layers |
| G2 | Obvious Behavior Is Unimplemented | Function doesn't do what its name promises | Implement the expected behavior or rename |
| G3 | Incorrect Behavior at the Boundaries | Edge cases and boundary conditions fail | Write boundary tests, handle all edge cases explicitly |
| G4 | Overridden Safeties | Compiler warnings suppressed, tests skipped | Remove suppressions, fix the underlying issue |
| G5 | Duplication | Same code/logic appears in multiple places | Extract into shared function, apply DRY |
| G6 | Code at Wrong Level of Abstraction | High-level concepts mixed with low-level details | Separate into distinct abstraction layers |
| G7 | Base Classes Depending on Their Derivatives | Base class references or imports a subclass | Invert the dependency, use abstractions |
| G8 | Too Much Information | Class/module exposes too many methods or details | Minimize public API, hide internals |
| G9 | Dead Code | Unreachable code, unused branches, impossible conditions | Delete it |
| G10 | Vertical Separation | Variable declared far from where it is used | Declare variables close to their first use |
| G11 | Inconsistency | Similar things done in different ways | Pick one convention, apply it everywhere |
| G12 | Clutter | Default constructors, unused variables, unneeded comments | Remove anything that adds no information |
| G13 | Artificial Coupling | Two unrelated modules depend on each other | Move shared element to where it truly belongs |
| G14 | Feature Envy | Method uses another class's data more than its own | Move the method to the class whose data it uses |
| G15 | Selector Arguments | Boolean/enum arg selects internal behavior | Split into separate functions |
| G16 | Obscured Intent | Clever tricks, dense expressions, poor formatting | Rewrite for clarity over brevity |
| G17 | Misplaced Responsibility | Function is in the wrong class or module | Move to the class that owns the relevant data |
| G18 | Inappropriate Static | Static method that should be polymorphic | Convert to instance method on the right class |
| G19 | Use Explanatory Variables | Complex expression with no intermediate names | Break into named intermediate variables |
| G20 | Function Names Should Say What They Do | Name is vague (`process`, `handle`, `doWork`) | Rename to describe the specific action |
| G21 | Understand the Algorithm | Code works by trial and error, not understanding | Rewrite once you fully understand the logic |
| G22 | Make Logical Dependencies Physical | Module assumes something about another without explicit contract | Pass the dependency explicitly via parameter or interface |
| G23 | Prefer Polymorphism to If/Else or Switch/Case | Repeated switch/if on type codes | Replace with polymorphic dispatch |
| G24 | Follow Standard Conventions | Code violates team/language coding standards | Apply agreed-upon conventions consistently |
| G25 | Replace Magic Numbers with Named Constants | Literal numbers scattered through code | Extract to well-named constants |
| G26 | Be Precise | Ambiguous code (e.g., using float for currency) | Use exact types, handle all cases explicitly |
| G27 | Structure Over Convention | Relying on naming conventions instead of language enforcement | Use compiler-enforced structures (enums, types, interfaces) |
| G28 | Encapsulate Conditionals | Raw boolean expressions in if statements | Extract to a well-named boolean method |
| G29 | Avoid Negative Conditionals | `if (!isNotReady)` double negatives | Rephrase as positive: `if (isReady)` |
| G30 | Functions Should Do One Thing | Function has multiple sections or responsibilities | Split into focused single-purpose functions |
| G31 | Hidden Temporal Couplings | Functions must be called in a specific order but nothing enforces it | Make the ordering explicit via return values or parameters |
| G32 | Don't Be Arbitrary | Code structure seems random with no rationale | Restructure with clear intent, document the why |
| G33 | Encapsulate Boundary Conditions | `level + 1` or `length - 1` appears in multiple places | Extract to a named variable like `nextLevel` |
| G34 | Functions Should Descend Only One Level of Abstraction | High-level and low-level operations mixed in one function | Extract lower-level details into helper functions |
| G35 | Keep Configurable Data at High Levels | Config values buried deep in low-level code | Move constants/config to top-level or config files |
| G36 | Avoid Transitive Navigation | `a.getB().getC().doThing()` Law of Demeter violation | Apply "tell, don't ask" — let A delegate to B |

## Java-Specific

| ID | Smell | How to Detect | How to Fix |
|----|-------|---------------|------------|
| J1 | Avoid Long Import Lists | Dozens of individual imports from the same package | Use explicit imports; configure your IDE/formatter to manage them. Wildcards (`import java.util.*`) obscure dependencies and cause ambiguity conflicts |
| J2 | Don't Inherit Constants | Implementing an interface just to access its constants | Use static imports instead |
| J3 | Constants vs. Enums | `static final int` used as enumerated values | Replace with `enum` types |

## Names

| ID | Smell | How to Detect | How to Fix |
|----|-------|---------------|------------|
| N1 | Choose Descriptive Names | Names are vague (`d`, `temp`, `data`, `info`) | Rename to reveal intent |
| N2 | Choose Names at the Appropriate Level of Abstraction | Name is too implementation-specific for its abstraction level | Rename to reflect the concept, not the implementation |
| N3 | Use Standard Nomenclature Where Possible | Custom names for well-known patterns | Use established names (Factory, Visitor, Iterator) |
| N4 | Unambiguous Names | Name could mean multiple things | Rename to eliminate ambiguity |
| N5 | Use Long Names for Long Scopes | Short name used in a broad scope | Lengthen name proportional to scope size |
| N6 | Avoid Encodings | Hungarian notation, type prefixes (`strName`, `iCount`) | Remove encoding, use the plain concept name |
| N7 | Names Should Describe Side-Effects | Name hides what the function really does (e.g., `getX` also creates X) | Rename to expose full behavior (`getOrCreateX`) |

## Tests

| ID | Smell | How to Detect | How to Fix |
|----|-------|---------------|------------|
| T1 | Insufficient Tests | Code paths, edge cases, or branches untested | Add tests for every condition and boundary |
| T2 | Use a Coverage Tool | No visibility into what is tested | Run coverage analysis, target gaps |
| T3 | Don't Skip Trivial Tests | Simple tests omitted as "too obvious" | Write them — they document expected behavior |
| T4 | An Ignored Test Is a Question About an Ambiguity | Tests marked `@Ignore` or `skip` | Resolve the ambiguity, then enable or delete the test |
| T5 | Test Boundary Conditions | Only happy path tested | Add tests for boundaries, nulls, empties, overflow |
| T6 | Exhaustively Test Near Bugs | Bug found but nearby code not re-examined | Test surrounding code thoroughly — bugs cluster |
| T7 | Patterns of Failure Are Revealing | Failures in tests seem random | Analyze failure patterns — they hint at root cause |
| T8 | Test Coverage Patterns Can Be Revealing | Uncovered code lines form a pattern | Investigate why those paths are uncovered |
| T9 | Tests Should Be Fast | Tests take too long to run frequently | Optimize setup, mock I/O, parallelize |
