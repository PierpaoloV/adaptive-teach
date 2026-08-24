#!/usr/bin/env python3
"""Shared helpers for adaptive-teach runtime scripts."""

from __future__ import annotations

import re
from pathlib import Path

SCHEMA_VERSION = "1"
VALID_STATUSES = {"not_done", "done"}


def split_frontmatter(text: str) -> tuple[dict[str, str], str]:
    """Parse the skill's intentionally simple scalar YAML frontmatter."""
    if not text.startswith("---\n"):
        return {}, text
    end = text.find("\n---\n", 4)
    if end < 0:
        raise ValueError("unterminated frontmatter")
    metadata: dict[str, str] = {}
    for raw_line in text[4:end].splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if ":" not in line:
            raise ValueError(f"invalid frontmatter line: {raw_line!r}")
        key, value = line.split(":", 1)
        metadata[key.strip()] = value.strip().strip('"').strip("'")
    return metadata, text[end + 5 :]


def read_frontmatter(path: Path) -> dict[str, str]:
    metadata, _ = split_frontmatter(path.read_text(encoding="utf-8"))
    return metadata


def replace_frontmatter_value(path: Path, key: str, value: str) -> None:
    text = path.read_text(encoding="utf-8")
    metadata, _ = split_frontmatter(text)
    if key not in metadata:
        raise ValueError(f"{path}: missing frontmatter key {key!r}")
    pattern = re.compile(rf"^({re.escape(key)}\s*:\s*).*$", re.MULTILINE)
    updated, count = pattern.subn(rf"\g<1>{value}", text, count=1)
    if count != 1:
        raise ValueError(f"{path}: could not update {key!r}")
    path.write_text(updated, encoding="utf-8")


def course_workspace(course_root: str | Path) -> Path:
    root = Path(course_root).expanduser().resolve()
    return root if root.name == ".adaptive-teach" else root / ".adaptive-teach"


def slugify(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return slug or "lesson"

