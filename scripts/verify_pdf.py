#!/usr/bin/env python3
"""Reopen, inspect, and render an adaptive-teach PDF for visual QA."""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
from pathlib import Path

try:
    from pypdf import PdfReader
except ImportError as exc:  # pragma: no cover
    raise SystemExit("Missing pypdf. Install it with: python3 -m pip install pypdf") from exc

from adaptive_common import split_frontmatter


def render_pages(pdf: Path, render_dir: Path) -> tuple[list[str], str]:
    render_dir.mkdir(parents=True, exist_ok=True)
    pdftoppm = shutil.which("pdftoppm")
    if pdftoppm:
        prefix = render_dir / "page"
        completed = subprocess.run(
            [pdftoppm, "-png", "-r", "120", str(pdf), str(prefix)],
            check=False,
            capture_output=True,
            text=True,
        )
        if completed.returncode != 0:
            raise RuntimeError(completed.stderr.strip() or "pdftoppm failed")
        files = sorted(str(path) for path in render_dir.glob("page-*.png"))
        return files, "pdftoppm"

    try:
        import fitz  # type: ignore
    except ImportError as exc:
        raise RuntimeError(
            "No page renderer. Install Poppler or PyMuPDF: python3 -m pip install pymupdf"
        ) from exc
    document = fitz.open(pdf)
    files = []
    for index, page in enumerate(document):
        output = render_dir / f"page-{index + 1}.png"
        page.get_pixmap(matrix=fitz.Matrix(1.5, 1.5), alpha=False).save(output)
        files.append(str(output))
    return files, "pymupdf"


def verify(pdf: Path, source: Path | None, render_dir: Path, report_path: Path) -> dict[str, object]:
    errors: list[str] = []
    warnings: list[str] = []
    if not pdf.is_file() or pdf.stat().st_size < 1024:
        errors.append("PDF is missing or implausibly small")
        report = {"ok": False, "errors": errors, "warnings": warnings}
        report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
        return report

    try:
        reader = PdfReader(str(pdf))
    except Exception as exc:
        errors.append(f"PDF cannot be reopened: {exc}")
        reader = None

    extracted_pages: list[str] = []
    if reader is not None:
        if not reader.pages:
            errors.append("PDF has no pages")
        for index, page in enumerate(reader.pages, start=1):
            text = (page.extract_text() or "").strip()
            extracted_pages.append(text)
            if len(text) < 10:
                errors.append(f"page {index} has too little extractable text")
            if "□" in text or "�" in text:
                errors.append(f"page {index} contains a missing-glyph marker")
        if len(extracted_pages) > 1:
            largest_page = max((len(text) for text in extracted_pages), default=0)
            for index, text in enumerate(extracted_pages, start=1):
                if len(text) < 300 and len(text) < largest_page * 0.15:
                    warnings.append(
                        f"page {index} is unusually sparse; inspect for an orphaned block"
                    )

    if source and source.is_file() and extracted_pages:
        _, body = split_frontmatter(source.read_text(encoding="utf-8"))
        heading = next((line[2:].strip() for line in body.splitlines() if line.startswith("# ")), "")
        if heading and heading.casefold() not in "\n".join(extracted_pages).casefold():
            errors.append("source title is not extractable from the PDF")

    rendered_files: list[str] = []
    renderer = "none"
    try:
        rendered_files, renderer = render_pages(pdf, render_dir)
        if not rendered_files:
            errors.append("page renderer produced no images")
        for rendered in rendered_files:
            if Path(rendered).stat().st_size < 1024:
                errors.append(f"rendered page is implausibly small: {rendered}")
    except Exception as exc:
        errors.append(f"page rendering failed: {exc}")

    report = {
        "ok": not errors,
        "pdf": str(pdf),
        "pages": len(extracted_pages),
        "renderer": renderer,
        "rendered_files": rendered_files,
        "errors": errors,
        "warnings": warnings,
    }
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("pdf", type=Path)
    parser.add_argument("--source", type=Path)
    parser.add_argument("--render-dir", type=Path)
    parser.add_argument("--report", type=Path)
    args = parser.parse_args()
    pdf = args.pdf.resolve()
    render_dir = (args.render_dir or pdf.with_suffix(".rendered")).resolve()
    report_path = (args.report or pdf.with_suffix(".verify.json")).resolve()
    report = verify(pdf, args.source.resolve() if args.source else None, render_dir, report_path)
    for warning in report["warnings"]:
        print(f"WARNING: {warning}")
    for error in report["errors"]:
        print(f"ERROR: {error}")
    print(report_path)
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
