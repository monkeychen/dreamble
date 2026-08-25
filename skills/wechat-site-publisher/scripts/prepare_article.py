#!/usr/bin/env python3
"""Prepare a channel-ready Markdown file without rewriting research content."""

from __future__ import annotations

import argparse
import hashlib
import json
import tempfile
from pathlib import Path


def split_frontmatter(text: str) -> tuple[list[str], str]:
    lines = text.splitlines(keepends=True)
    if not lines or lines[0].strip() != "---":
        raise ValueError("Source Markdown must start with YAML frontmatter")
    for index in range(1, len(lines)):
        if lines[index].strip() == "---":
            fields = [line.rstrip("\r\n") for line in lines[1:index]]
            return fields, "".join(lines[index + 1 :])
    raise ValueError("Source Markdown frontmatter has no closing delimiter")


def has_nonempty_field(fields: list[str], name: str) -> bool:
    prefix = f"{name}:"
    return any(line.startswith(prefix) and line[len(prefix) :].strip() for line in fields)


def prepare_article_text(text: str, cover_path: str = "./imgs/cover.png") -> tuple[str, str]:
    fields, source_body = split_frontmatter(text)
    for required in ("title", "summary"):
        if not has_nonempty_field(fields, required):
            raise ValueError(f"Source Markdown frontmatter requires non-empty {required}")

    publishing_fields = [line for line in fields if not line.startswith("coverImage:")]
    publishing_fields.append(f"coverImage: {json.dumps(cover_path, ensure_ascii=False)}")
    frontmatter = "\n".join(["---", *publishing_fields, "---"])

    if cover_path in source_body:
        article = frontmatter + "\n" + source_body
    else:
        article = frontmatter + f"\n\n![文章封面]({cover_path})\n" + source_body

    if not article.endswith(source_body):
        raise AssertionError("Source body was not preserved")
    return article, source_body


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path, help="Immutable finalized Markdown source")
    parser.add_argument("destination", type=Path, help="Channel-ready article.md")
    parser.add_argument("--cover", default="./imgs/cover.png")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    source = args.source.resolve()
    destination = args.destination.resolve()
    if not source.is_file():
        raise SystemExit(f"Source Markdown not found: {source}")
    if source == destination:
        raise SystemExit("Source and destination must be different files")

    try:
        article, source_body = prepare_article_text(
            source.read_text(encoding="utf-8"), args.cover
        )
    except ValueError as exc:
        raise SystemExit(str(exc)) from exc

    destination.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        mode="w",
        encoding="utf-8",
        dir=destination.parent,
        prefix=f".{destination.name}.",
        delete=False,
    ) as handle:
        handle.write(article)
        staging = Path(handle.name)
    staging.replace(destination)

    digest = hashlib.sha256(source_body.encode("utf-8")).hexdigest()
    print(
        json.dumps(
            {
                "source": str(source),
                "destination": str(destination),
                "source_body_sha256": digest,
                "source_body_preserved": article.endswith(source_body),
            },
            ensure_ascii=False,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
