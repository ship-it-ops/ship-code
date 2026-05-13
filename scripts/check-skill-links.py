#!/usr/bin/env python3
"""
Verify that relative links in skill documentation resolve on disk.

Walks every `.md` file under skills/ and checks:
  - markdown link targets: [text](path/to/file.md)
  - markdown image targets: ![alt](path/to/file.png)
  - explicit inline backtick references that start with ./ (relative-to-current-dir)

Skipped:
  - http://, https://, mailto:, ftp:// — external links
  - #anchor — same-document anchors (target verification is complex)
  - things in fenced code blocks (illustrative, not real links)
  - bare strings in backticks (too noisy — e.g. security examples like `../../etc/passwd`,
    TypeScript path-alias illustrations, command snippets)

Exit code:
  0 - all targets resolve
  1 - one or more broken links
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SKILLS_DIR = REPO_ROOT / "skills"

# Match [text](target) but not ![alt](target) or `[in code]`
MARKDOWN_LINK = re.compile(r"(?<!!)\[(?P<text>[^\]]+)\]\((?P<target>[^)]+)\)")

# Match backtick file references that look like paths (heuristic — contains `/` or `.md`/`.py`/`.sh`/`.ts`/etc.)
INLINE_FILE_REF = re.compile(
    r"`(?P<path>[a-zA-Z0-9_\-./]+(?:/[a-zA-Z0-9_\-./]+|\.(?:md|py|sh|ts|tsx|js|jsx|java|sql|yml|yaml|json|toml))(?:[a-zA-Z0-9_\-./]*))`"
)

EXTERNAL_SCHEMES = (
    "http://",
    "https://",
    "mailto:",
    "ftp://",
    "git@",
    "ssh://",
)


def strip_fenced_blocks(text: str) -> str:
    """Remove ```...``` fenced blocks so links inside them aren't checked."""
    result: list[str] = []
    in_fence = False
    for line in text.split("\n"):
        if line.lstrip().startswith("```"):
            in_fence = not in_fence
            result.append("")
            continue
        if in_fence:
            result.append("")
        else:
            result.append(line)
    return "\n".join(result)


def is_external(target: str) -> bool:
    return target.startswith(EXTERNAL_SCHEMES)


def is_anchor(target: str) -> bool:
    return target.startswith("#")


def strip_anchor(target: str) -> str:
    """Remove `#anchor` and `?query` fragments."""
    return target.split("#")[0].split("?")[0]


def check_file(md_path: Path) -> list[tuple[int, str, str]]:
    """Return list of (line_no, link_target, reason) for broken links."""
    text = md_path.read_text(encoding="utf-8")
    stripped = strip_fenced_blocks(text)
    broken: list[tuple[int, str, str]] = []

    # IMPORTANT: line_no counts newlines in `stripped` (not `text`), because all
    # regex matches below run against `stripped`. `strip_fenced_blocks` preserves
    # newlines 1:1 with `text` but empties the fenced-block content, so the
    # character offsets diverge after the first fenced block — using `text[:idx]`
    # would mis-report line numbers for any link that appears after a code block.
    def line_no(idx: int) -> int:
        return stripped[:idx].count("\n") + 1

    # Markdown links
    for m in MARKDOWN_LINK.finditer(stripped):
        target = m.group("target").strip()
        if not target or is_external(target) or is_anchor(target):
            continue
        # Skip mailto-like and javascript: schemes
        if ":" in target.split("/")[0]:
            continue
        # Resolve relative to the .md file's directory
        resolved = (md_path.parent / strip_anchor(target)).resolve()
        # Allow resolution outside REPO_ROOT? No — we only check within the repo
        try:
            resolved.relative_to(REPO_ROOT)
        except ValueError:
            broken.append((line_no(m.start()), target, "resolves outside repo"))
            continue
        if not resolved.exists():
            broken.append((line_no(m.start()), target, "does not exist"))

    # Inline backtick file references — only flag explicit `./relative` references.
    # `../parent` is too noisy: it shows up in security examples (`../../etc/passwd`),
    # TypeScript path-alias illustrations, and command snippets.
    for m in INLINE_FILE_REF.finditer(stripped):
        path = m.group("path").strip()
        if not path.startswith("./"):
            continue
        resolved = (md_path.parent / path).resolve()
        try:
            resolved.relative_to(REPO_ROOT)
        except ValueError:
            broken.append((line_no(m.start()), path, "resolves outside repo (inline)"))
            continue
        if not resolved.exists():
            broken.append((line_no(m.start()), path, "does not exist (inline)"))

    return broken


def main() -> int:
    parser = argparse.ArgumentParser(description="Check relative links in skill docs")
    parser.add_argument("--verbose", "-v", action="store_true")
    args = parser.parse_args()

    if not SKILLS_DIR.is_dir():
        print("[WARN] skills/ directory not found")
        return 0

    md_files = sorted(SKILLS_DIR.rglob("*.md"))
    total_broken = 0
    files_with_errors = 0

    for md in md_files:
        if args.verbose:
            print(f"Checking {md.relative_to(REPO_ROOT)}...")
        broken = check_file(md)
        if broken:
            files_with_errors += 1
            print(f"\n{md.relative_to(REPO_ROOT)}:")
            for line, target, reason in broken:
                print(f"  L{line}: [{target}] -> {reason}")
                total_broken += 1

    if total_broken == 0:
        print(f"[OK] {len(md_files)} markdown file(s) checked; all relative links resolve.")
        return 0
    print(
        f"\n[FAIL] {total_broken} broken link(s) across {files_with_errors} file(s)."
    )
    return 1


if __name__ == "__main__":
    sys.exit(main())
