#!/usr/bin/env python3
"""
Validate the structure, frontmatter, and plugin wiring of every skill in this repo.

Run locally: `python3 scripts/validate-skills.py` (or `--verbose` for more detail).
Exits non-zero on any violation. CI runs this on every PR; treat failures as blocking.

Checks performed:

  STRUCTURE
    - Each skills/<name>/ contains SKILL.md
    - SKILL.md has parseable YAML frontmatter
    - Frontmatter `name` matches directory name
    - Frontmatter has non-empty `description` (50-2000 chars recommended)
    - SKILL.md is under 500 lines (per docs/writing-skills.md)
    - allowed-tools (if present) parses as a string or list
    - disable-model-invocation (if present) is a boolean
    - context (if present) is "fork"
    - agent (if present, requires context: fork) is one of the documented types
    - argument-hint (if present) is a string

  PLUGIN LAYOUT
    - For each skills/<name>/, plugins/<name>/skills/<name>/SKILL.md MUST exist (not at plugins/<name>/skills/SKILL.md - the layout-regression we fixed previously)
    - plugins/<name>/.claude-plugin/plugin.json exists and is valid JSON
    - plugin.json.name matches directory name
    - plugin.json.version is a valid semver string (X.Y.Z)
    - Per-file symlinks resolve to the source files

  MARKETPLACE CONSISTENCY
    - .claude-plugin/marketplace.json is valid JSON
    - Every skill in skills/ has an entry in marketplace.json (and vice-versa)
    - marketplace.json plugin version matches the corresponding plugins/<name>/.claude-plugin/plugin.json version
    - .claude-plugin/plugin.json (root) lists every skill

  CONTENT HYGIENE
    - No ${SKILL_DIR} references in any skills/**/*.md (we use relative paths or ${CLAUDE_SKILL_DIR})

  FIXTURE PARITY
    - If tests/fixture-N/ exists, it contains both input.* and expected-output.md

Error categories are printed at the end, with file paths. Exit code:
  0 - all checks pass
  1 - structural violations
  2 - usage error (script invocation)
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SKILLS_DIR = REPO_ROOT / "skills"
PLUGINS_DIR = REPO_ROOT / "plugins"
MARKETPLACE_JSON = REPO_ROOT / ".claude-plugin" / "marketplace.json"
ROOT_PLUGIN_JSON = REPO_ROOT / ".claude-plugin" / "plugin.json"

SKILL_MD_MAX_LINES = 500
DESCRIPTION_MIN_CHARS = 50
DESCRIPTION_MAX_CHARS = 2000
SEMVER_PATTERN = re.compile(r"^\d+\.\d+\.\d+(?:[-+][\w.]+)?$")
SKILL_NAME_PATTERN = re.compile(r"^[a-z][a-z0-9-]*$")
VALID_AGENT_TYPES = {"Explore", "Plan", "general-purpose"}
VALID_FRONTMATTER_KEYS = {
    "name",
    "description",
    "allowed-tools",
    "disable-model-invocation",
    "user-invocable",
    "context",
    "agent",
    "model",
    "argument-hint",
}


class Errors:
    """Accumulates errors keyed by category."""

    def __init__(self) -> None:
        self._bucket: dict[str, list[str]] = {}

    def add(self, category: str, message: str) -> None:
        self._bucket.setdefault(category, []).append(message)

    def any(self) -> bool:
        return any(self._bucket.values())

    def report(self) -> None:
        if not self.any():
            print("[OK] All validation checks passed.")
            return
        total = sum(len(v) for v in self._bucket.values())
        print(f"\n[FAIL] {total} validation error(s) across {len(self._bucket)} categor(ies):\n")
        for category, messages in self._bucket.items():
            print(f"### {category} ({len(messages)})")
            for m in messages:
                print(f"  - {m}")
            print()


# ---------------------------------------------------------------------------
# Minimal YAML frontmatter parser (no external deps)
# ---------------------------------------------------------------------------


def parse_frontmatter(text: str) -> tuple[dict | None, str | None]:
    """Parse a YAML frontmatter block at the start of `text`.

    Returns (frontmatter_dict, error_message). frontmatter_dict is None on error.

    Supports only the subset used in this repo:
      key: value
      key: >
        multi-line folded scalar
      key: |
        multi-line literal scalar
      # comments

    Values are returned as strings; bool conversion happens at use site.
    """
    if not text.startswith("---\n"):
        return None, "missing opening `---` line"

    end = text.find("\n---\n", 4)
    if end < 0:
        # Allow `---` at end of file without trailing newline
        end_alt = text.find("\n---", 4)
        if end_alt < 0:
            return None, "missing closing `---` delimiter"
        end = end_alt

    body = text[4:end]
    out: dict[str, str | bool] = {}
    lines = body.split("\n")
    i = 0
    while i < len(lines):
        line = lines[i]
        if not line.strip() or line.lstrip().startswith("#"):
            i += 1
            continue
        # Top-level key (no leading whitespace)
        if line[0] in (" ", "\t"):
            return None, f"unexpected indented line at frontmatter top level: {line!r}"
        if ":" not in line:
            return None, f"malformed frontmatter line: {line!r}"
        key, _, value = line.partition(":")
        key = key.strip()
        value = value.strip()
        if value in (">", "|"):
            # Folded or literal scalar — collect indented continuation
            collected: list[str] = []
            i += 1
            while i < len(lines):
                cont = lines[i]
                if cont and not cont[0].isspace() and cont.strip():
                    break
                if cont.strip():
                    collected.append(cont.strip())
                else:
                    collected.append("")
                i += 1
            joined = (" " if value == ">" else "\n").join(c for c in collected if c)
            out[key] = joined.strip()
            continue
        # Strip quotes if scalar is quoted
        if (value.startswith('"') and value.endswith('"')) or (
            value.startswith("'") and value.endswith("'")
        ):
            value = value[1:-1]
        out[key] = value
        i += 1
    return out, None


def to_bool(value: str | bool) -> bool | None:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        if value.lower() in ("true", "yes", "on"):
            return True
        if value.lower() in ("false", "no", "off"):
            return False
    return None


# ---------------------------------------------------------------------------
# Checks
# ---------------------------------------------------------------------------


def discover_skills() -> list[Path]:
    if not SKILLS_DIR.is_dir():
        return []
    return sorted(
        p for p in SKILLS_DIR.iterdir() if p.is_dir() and (p / "SKILL.md").exists()
    )


def validate_skill_structure(errors: Errors, skill_dir: Path) -> dict | None:
    skill_name = skill_dir.name
    skill_md = skill_dir / "SKILL.md"

    if not SKILL_NAME_PATTERN.match(skill_name):
        errors.add(
            "Skill naming",
            f"{skill_name!r}: directory name must match {SKILL_NAME_PATTERN.pattern}",
        )

    if not skill_md.exists():
        errors.add("Missing SKILL.md", f"skills/{skill_name}/SKILL.md does not exist")
        return None

    text = skill_md.read_text(encoding="utf-8")
    line_count = text.count("\n") + (0 if text.endswith("\n") else 1)
    if line_count > SKILL_MD_MAX_LINES:
        errors.add(
            "SKILL.md too long",
            f"skills/{skill_name}/SKILL.md is {line_count} lines (max {SKILL_MD_MAX_LINES}; "
            f"move detail into reference.md per docs/writing-skills.md)",
        )

    fm, parse_err = parse_frontmatter(text)
    if fm is None:
        errors.add(
            "Frontmatter parse error",
            f"skills/{skill_name}/SKILL.md: {parse_err}",
        )
        return None

    # Required fields
    if "name" not in fm:
        errors.add(
            "Frontmatter missing name",
            f"skills/{skill_name}/SKILL.md: `name` is required",
        )
    elif fm["name"] != skill_name:
        errors.add(
            "Frontmatter name mismatch",
            f"skills/{skill_name}/SKILL.md: frontmatter name {fm['name']!r} != directory name "
            f"{skill_name!r} (skill discovery requires these to match)",
        )

    if "description" not in fm:
        errors.add(
            "Frontmatter missing description",
            f"skills/{skill_name}/SKILL.md: `description` is required",
        )
    else:
        desc = str(fm["description"])
        if len(desc) < DESCRIPTION_MIN_CHARS:
            errors.add(
                "Description too short",
                f"skills/{skill_name}/SKILL.md: description is {len(desc)} chars "
                f"(min {DESCRIPTION_MIN_CHARS}). Auto-invocation matching needs enough context to "
                f"distinguish this skill from others.",
            )
        elif len(desc) > DESCRIPTION_MAX_CHARS:
            errors.add(
                "Description too long",
                f"skills/{skill_name}/SKILL.md: description is {len(desc)} chars "
                f"(max {DESCRIPTION_MAX_CHARS}). Move detail to the Purpose section of SKILL.md.",
            )

    # Type / value checks on optional fields
    if "disable-model-invocation" in fm:
        if to_bool(fm["disable-model-invocation"]) is None:
            errors.add(
                "Invalid disable-model-invocation",
                f"skills/{skill_name}/SKILL.md: disable-model-invocation must be a boolean, "
                f"got {fm['disable-model-invocation']!r}",
            )

    if "user-invocable" in fm:
        if to_bool(fm["user-invocable"]) is None:
            errors.add(
                "Invalid user-invocable",
                f"skills/{skill_name}/SKILL.md: user-invocable must be a boolean, "
                f"got {fm['user-invocable']!r}",
            )

    if "context" in fm and fm["context"] != "fork":
        errors.add(
            "Invalid context",
            f"skills/{skill_name}/SKILL.md: context must be 'fork' if present, "
            f"got {fm['context']!r}",
        )

    if "agent" in fm:
        if "context" not in fm:
            errors.add(
                "agent without context: fork",
                f"skills/{skill_name}/SKILL.md: agent field requires context: fork",
            )
        if fm["agent"] not in VALID_AGENT_TYPES:
            errors.add(
                "Invalid agent type",
                f"skills/{skill_name}/SKILL.md: agent must be one of "
                f"{sorted(VALID_AGENT_TYPES)}, got {fm['agent']!r}",
            )

    # Unknown keys
    unknown = set(fm.keys()) - VALID_FRONTMATTER_KEYS
    if unknown:
        errors.add(
            "Unknown frontmatter keys",
            f"skills/{skill_name}/SKILL.md: unknown keys {sorted(unknown)} "
            f"(allowed: {sorted(VALID_FRONTMATTER_KEYS)})",
        )

    return fm


def validate_plugin_layout(errors: Errors, skill_name: str) -> dict | None:
    """Validate the plugin wrapper at plugins/<name>/. Returns the parsed plugin.json."""
    plugin_dir = PLUGINS_DIR / skill_name
    if not plugin_dir.is_dir():
        errors.add(
            "Missing plugin wrapper",
            f"plugins/{skill_name}/ does not exist (every skill must have a plugin wrapper)",
        )
        return None

    # CRITICAL: the nested skills/<name>/SKILL.md must resolve. We learned this
    # the hard way when ship-tested-code shipped with a single-directory symlink
    # that collapsed plugins/<name>/skills/<name>/ to plugins/<name>/skills/.
    expected_skill_md = plugin_dir / "skills" / skill_name / "SKILL.md"
    if not expected_skill_md.exists():
        errors.add(
            "Plugin layout broken",
            f"plugins/{skill_name}/skills/{skill_name}/SKILL.md does not resolve. "
            f"Use per-file symlinks under plugins/{skill_name}/skills/{skill_name}/ that "
            f"point to ../../../../skills/{skill_name}/<file>, NOT a single directory "
            f"symlink at plugins/{skill_name}/skills/.",
        )

    # plugin.json
    plugin_manifest = plugin_dir / ".claude-plugin" / "plugin.json"
    if not plugin_manifest.exists():
        errors.add(
            "Missing plugin.json",
            f"plugins/{skill_name}/.claude-plugin/plugin.json does not exist",
        )
        return None
    try:
        manifest = json.loads(plugin_manifest.read_text())
    except json.JSONDecodeError as e:
        errors.add(
            "Invalid plugin.json",
            f"plugins/{skill_name}/.claude-plugin/plugin.json: {e}",
        )
        return None

    if manifest.get("name") != skill_name:
        errors.add(
            "Plugin name mismatch",
            f"plugins/{skill_name}/.claude-plugin/plugin.json: name "
            f"{manifest.get('name')!r} != directory name {skill_name!r}",
        )

    version = manifest.get("version", "")
    if not SEMVER_PATTERN.match(str(version)):
        errors.add(
            "Plugin version invalid",
            f"plugins/{skill_name}/.claude-plugin/plugin.json: version {version!r} "
            f"is not a valid semver (X.Y.Z)",
        )

    if "description" not in manifest:
        errors.add(
            "Plugin missing description",
            f"plugins/{skill_name}/.claude-plugin/plugin.json: description is required",
        )

    return manifest


def validate_marketplace(errors: Errors, skill_dirs: list[Path]) -> None:
    if not MARKETPLACE_JSON.exists():
        errors.add(
            "Missing marketplace.json",
            ".claude-plugin/marketplace.json does not exist",
        )
        return
    try:
        marketplace = json.loads(MARKETPLACE_JSON.read_text())
    except json.JSONDecodeError as e:
        errors.add("Invalid marketplace.json", f".claude-plugin/marketplace.json: {e}")
        return

    if "plugins" not in marketplace:
        errors.add(
            "Marketplace missing plugins",
            ".claude-plugin/marketplace.json: top-level `plugins` array required",
        )
        return

    listed_plugins = {p.get("name"): p for p in marketplace["plugins"]}
    skill_names = {s.name for s in skill_dirs}

    # Every skill must be in marketplace
    for name in skill_names - set(listed_plugins.keys()):
        errors.add(
            "Skill not in marketplace",
            f"skills/{name}/ has no entry in .claude-plugin/marketplace.json plugins array",
        )

    # Every marketplace entry must have a skill
    for name in set(listed_plugins.keys()) - skill_names:
        errors.add(
            "Marketplace lists missing skill",
            f".claude-plugin/marketplace.json lists plugin {name!r} but skills/{name}/ "
            f"does not exist",
        )

    # Version cross-check: marketplace.json plugin version == plugins/<name>/plugin.json version
    for name, entry in listed_plugins.items():
        if name not in skill_names:
            continue
        manifest_path = PLUGINS_DIR / name / ".claude-plugin" / "plugin.json"
        if not manifest_path.exists():
            continue
        try:
            manifest = json.loads(manifest_path.read_text())
        except json.JSONDecodeError:
            continue
        mv = entry.get("version")
        pv = manifest.get("version")
        if mv != pv:
            errors.add(
                "Version mismatch",
                f"marketplace.json says {name} v{mv}, but plugins/{name}/.claude-plugin/"
                f"plugin.json says v{pv}",
            )
        # Required marketplace fields
        for field in ("description", "source", "version", "category"):
            if field not in entry:
                errors.add(
                    "Marketplace entry missing field",
                    f".claude-plugin/marketplace.json plugin {name!r}: `{field}` is required",
                )


def validate_root_plugin_json(errors: Errors, skill_dirs: list[Path]) -> None:
    if not ROOT_PLUGIN_JSON.exists():
        errors.add(
            "Missing root plugin.json",
            ".claude-plugin/plugin.json does not exist",
        )
        return
    try:
        root = json.loads(ROOT_PLUGIN_JSON.read_text())
    except json.JSONDecodeError as e:
        errors.add("Invalid root plugin.json", f".claude-plugin/plugin.json: {e}")
        return

    listed = set(root.get("skills", []))
    expected = {f"./skills/{s.name}" for s in skill_dirs}

    for missing in expected - listed:
        errors.add(
            "Skill not in root plugin.json",
            f".claude-plugin/plugin.json `skills` array does not include {missing!r}",
        )
    for extra in listed - expected:
        errors.add(
            "Root plugin.json lists missing skill",
            f".claude-plugin/plugin.json `skills` lists {extra!r} but skill does not exist",
        )

    if "version" in root and not SEMVER_PATTERN.match(str(root["version"])):
        errors.add(
            "Root plugin.json version invalid",
            f".claude-plugin/plugin.json: version {root['version']!r} is not valid semver",
        )


def validate_no_skill_dir_leakage(errors: Errors) -> None:
    """The bare ${SKILL_DIR} variable is not the documented form. Use ${CLAUDE_SKILL_DIR} or relative paths."""
    if not SKILLS_DIR.is_dir():
        return
    for md in SKILLS_DIR.rglob("*.md"):
        try:
            text = md.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        # ${SKILL_DIR} bad, ${CLAUDE_SKILL_DIR} good
        bad_pattern = re.compile(r"\$\{SKILL_DIR\}")
        for match in bad_pattern.finditer(text):
            line_no = text[: match.start()].count("\n") + 1
            errors.add(
                "${SKILL_DIR} leakage",
                f"{md.relative_to(REPO_ROOT)}:{line_no}: use ${{CLAUDE_SKILL_DIR}} or a "
                f"relative path; bare ${{SKILL_DIR}} is not the documented variable",
            )


def validate_fixture_parity(errors: Errors, skill_dirs: list[Path]) -> None:
    for skill_dir in skill_dirs:
        tests_dir = skill_dir / "tests"
        if not tests_dir.is_dir():
            continue
        for fixture in sorted(tests_dir.iterdir()):
            if not fixture.is_dir():
                continue
            if not fixture.name.startswith("fixture-"):
                continue
            input_files = [
                p
                for p in fixture.iterdir()
                if p.is_file() and (p.stem == "input" or p.name.startswith("input."))
            ]
            expected = fixture / "expected-output.md"
            if not input_files:
                errors.add(
                    "Fixture missing input",
                    f"{fixture.relative_to(REPO_ROOT)}: no `input.*` file found",
                )
            if not expected.exists():
                errors.add(
                    "Fixture missing expected-output",
                    f"{fixture.relative_to(REPO_ROOT)}: no `expected-output.md` file found",
                )


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate ship-code skills")
    parser.add_argument(
        "--verbose", "-v", action="store_true", help="print each skill as it's checked"
    )
    args = parser.parse_args()

    errors = Errors()
    skill_dirs = discover_skills()

    if not skill_dirs:
        print("[WARN] No skills found at skills/*/SKILL.md")
        return 0

    if args.verbose:
        print(f"Found {len(skill_dirs)} skill(s):")
        for s in skill_dirs:
            print(f"  - {s.name}")
        print()

    for skill_dir in skill_dirs:
        if args.verbose:
            print(f"Checking {skill_dir.name}...")
        validate_skill_structure(errors, skill_dir)
        validate_plugin_layout(errors, skill_dir.name)

    validate_marketplace(errors, skill_dirs)
    validate_root_plugin_json(errors, skill_dirs)
    validate_no_skill_dir_leakage(errors)
    validate_fixture_parity(errors, skill_dirs)

    errors.report()
    return 1 if errors.any() else 0


if __name__ == "__main__":
    sys.exit(main())
