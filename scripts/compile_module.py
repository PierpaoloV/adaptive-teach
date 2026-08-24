#!/usr/bin/env python3
"""Compile canonical lesson Markdown files into one module Markdown and PDF."""

from __future__ import annotations

import argparse
import re
from pathlib import Path

from adaptive_common import split_frontmatter
from render_pdf import render_markdown


def demote_lesson_headings(body: str) -> str:
    """Nest a lesson under the module title without changing canonical sources."""
    return re.sub(r"^(#{1,5})(\s+)", lambda match: f"#{match.group(1)}{match.group(2)}", body, flags=re.MULTILINE)


def compile_sources(title: str, sources: list[Path], output_md: Path) -> None:
    sections = [
        "---",
        "schema_version: 1",
        "status: not_done",
        "---",
        "",
        f"# {title}",
        "",
    ]
    for index, source in enumerate(sources):
        metadata, body = split_frontmatter(source.read_text(encoding="utf-8"))
        if metadata.get("status") != "done":
            raise ValueError(f"lesson source is not done: {source}")
        if index:
            sections.extend(["", "<!-- pagebreak -->", ""])
        sections.append(demote_lesson_headings(body.strip()))
        sections.append("")
    output_md.parent.mkdir(parents=True, exist_ok=True)
    output_md.write_text("\n".join(sections), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("sources", nargs="+", type=Path)
    parser.add_argument("--title", required=True)
    parser.add_argument("--output-md", required=True, type=Path)
    parser.add_argument("--output-pdf", required=True, type=Path)
    parser.add_argument("--font")
    args = parser.parse_args()
    sources = [source.resolve() for source in args.sources]
    missing = [str(source) for source in sources if not source.is_file()]
    if missing:
        parser.error(f"missing sources: {', '.join(missing)}")
    try:
        compile_sources(args.title, sources, args.output_md.resolve())
    except ValueError as exc:
        parser.error(str(exc))
    render_markdown(args.output_md.resolve(), args.output_pdf.resolve(), args.font)
    print(args.output_pdf.resolve())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
