#!/usr/bin/env python3
"""Validate that the Skill package is self-contained and publishable."""

from __future__ import annotations

import re
import sys
from pathlib import Path


MARKDOWN_LINK = re.compile(r"\[[^\]]+\]\(([^)]+)\)")
EXTERNAL_PREFIXES = ("http://", "https://", "mailto:", "#")


def validate_package(root: Path) -> list[str]:
    root = root.resolve()
    errors: list[str] = []
    markdown_files = [root / "SKILL.md", *sorted((root / "references").glob("*.md"))]

    for path in markdown_files:
        if not path.exists():
            errors.append(f"missing instruction file: {path.relative_to(root)}")
            continue
        for raw_target in MARKDOWN_LINK.findall(path.read_text(encoding="utf-8")):
            target = raw_target.strip().strip("<>")
            if not target or target.startswith(EXTERNAL_PREFIXES):
                continue
            target = target.split("#", 1)[0]
            resolved = (path.parent / target).resolve()
            try:
                resolved.relative_to(root)
            except ValueError:
                errors.append(
                    f"link escapes package: {path.relative_to(root)} -> {raw_target}"
                )
                continue
            if not resolved.exists():
                errors.append(
                    f"missing local link: {path.relative_to(root)} -> {raw_target}"
                )

    for path in root.rglob("*"):
        if path.name == "__pycache__" or path.suffix == ".pyc":
            errors.append(f"generated cache in package: {path.relative_to(root)}")

    return errors


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    errors = validate_package(root)
    if errors:
        for error in errors:
            print(error)
        raise SystemExit(1)
    print("skill package: OK")


if __name__ == "__main__":
    main()
