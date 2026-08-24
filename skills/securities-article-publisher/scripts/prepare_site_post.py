#!/usr/bin/env python3
"""Create a site-ready post directory from the temporary master article."""

from __future__ import annotations

import argparse
import json
import re
import shutil
import tempfile
from datetime import date
from pathlib import Path


SLUG_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")


def strip_frontmatter(text: str) -> str:
    lines = text.splitlines(keepends=True)
    if not lines or lines[0].strip() != "---":
        return text.lstrip()
    for index in range(1, len(lines)):
        if lines[index].strip() == "---":
            return "".join(lines[index + 1 :]).lstrip()
    raise ValueError("Source starts with frontmatter but has no closing delimiter")


def yaml_string(value: str) -> str:
    return json.dumps(value, ensure_ascii=False)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path, help="Master article.md")
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument("--date", required=True, dest="publish_date")
    parser.add_argument("--slug", required=True)
    parser.add_argument("--title", required=True)
    parser.add_argument("--summary")
    parser.add_argument("--tag", action="append", default=[])
    parser.add_argument("--source-wechat", action="store_true")
    parser.add_argument("--draft", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    source = args.source.resolve()
    if not source.is_file():
        raise SystemExit(f"Source file not found: {source}")
    try:
        date.fromisoformat(args.publish_date)
    except ValueError as exc:
        raise SystemExit(f"Invalid date: {args.publish_date}") from exc
    if not SLUG_RE.fullmatch(args.slug):
        raise SystemExit("Slug must contain lowercase letters, digits, and single hyphens only")
    if not args.title.strip():
        raise SystemExit("Title must not be empty")
    output_root = args.output_root.resolve()
    destination = output_root / f"{args.publish_date}-{args.slug}"
    if destination.exists():
        raise SystemExit(f"Destination already exists: {destination}")

    try:
        body = strip_frontmatter(source.read_text(encoding="utf-8"))
    except ValueError as exc:
        raise SystemExit(str(exc)) from exc
    if not body.strip():
        raise SystemExit("Article body is empty")

    image_dir = source.parent / "imgs"
    if image_dir.exists() and not image_dir.is_dir():
        raise SystemExit(f"Expected an image directory: {image_dir}")

    fields = [
        "---",
        f"title: {yaml_string(args.title.strip())}",
        f"date: {args.publish_date}",
    ]
    if args.summary:
        fields.append(f"summary: {yaml_string(args.summary.strip())}")
    fields.append(f"tags: {json.dumps(args.tag, ensure_ascii=False)}")
    if args.source_wechat:
        fields.append("source: wechat")
    if args.draft:
        fields.append("draft: true")
    fields.extend(["---", ""])

    output_root.mkdir(parents=True, exist_ok=True)
    staging = Path(tempfile.mkdtemp(prefix=".prepare-site-post-", dir=output_root))
    try:
        (staging / "index.md").write_text("\n".join(fields) + body, encoding="utf-8")
        if image_dir.exists():
            shutil.copytree(image_dir, staging / "imgs")
        staging.rename(destination)
    except Exception:
        shutil.rmtree(staging, ignore_errors=True)
        raise

    print(destination)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
