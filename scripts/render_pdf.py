#!/usr/bin/env python3
"""Render adaptive-teach Markdown to a stable, source-derived PDF."""

from __future__ import annotations

import argparse
import html
import os
import re
import sys
from pathlib import Path

try:
    from reportlab.lib import colors
    from reportlab.lib.enums import TA_CENTER
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
    from reportlab.lib.units import mm
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    from reportlab.platypus import (
        Image,
        ListFlowable,
        ListItem,
        PageBreak,
        Paragraph,
        Preformatted,
        SimpleDocTemplate,
        Spacer,
        Table,
        TableStyle,
    )
except ImportError as exc:  # pragma: no cover - exercised in dependency-poor hosts
    raise SystemExit(
        "Missing ReportLab. Install it with: python3 -m pip install reportlab"
    ) from exc

from adaptive_common import split_frontmatter

FONT_CANDIDATES = (
    "/System/Library/Fonts/Supplemental/Arial Unicode.ttf",
    "/System/Library/Fonts/Supplemental/AppleGothic.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    "/usr/share/fonts/truetype/noto/NotoSans-Regular.ttf",
    "C:/Windows/Fonts/arial.ttf",
)


def choose_font(explicit: str | None = None) -> tuple[str, str | None]:
    requested = explicit or os.environ.get("ADAPTIVE_TEACH_FONT")
    candidates = (requested,) if requested else FONT_CANDIDATES
    for candidate in candidates:
        if candidate and Path(candidate).is_file():
            try:
                name = "AdaptiveUnicode"
                pdfmetrics.registerFont(TTFont(name, candidate))
                pdfmetrics.registerFontFamily(
                    "AdaptiveFamily", normal=name, bold=name, italic=name, boldItalic=name
                )
                return name, candidate
            except Exception:
                continue
    return "Helvetica", None


def require_font_coverage(text: str, font_name: str, font_path: str | None) -> None:
    """Fail visibly instead of emitting tofu for unsupported teaching text."""
    characters = {character for character in text if ord(character) > 127 and not character.isspace()}
    if not characters:
        return
    if font_path is None:
        unsupported = sorted(character for character in characters if ord(character) > 255)
    else:
        cmap = pdfmetrics.getFont(font_name).face.charToGlyph
        unsupported = sorted(character for character in characters if ord(character) not in cmap)
    if unsupported:
        sample = " ".join(f"{character} (U+{ord(character):04X})" for character in unsupported[:12])
        raise RuntimeError(
            "Selected PDF font lacks required glyphs: "
            f"{sample}. Set ADAPTIVE_TEACH_FONT to a suitable Unicode .ttf file."
        )


def inline_markup(value: str, code_font: str) -> str:
    escaped = html.escape(value, quote=False)
    escaped = re.sub(
        r"`([^`]+)`",
        lambda m: f'<font name="{code_font}">{m.group(1)}</font>',
        escaped,
    )
    escaped = re.sub(r"\*\*([^*]+)\*\*", r"<b>\1</b>", escaped)
    escaped = re.sub(r"(?<!\*)\*([^*]+)\*(?!\*)", r"<i>\1</i>", escaped)
    escaped = re.sub(
        r"\[([^\]]+)\]\((https?://[^)]+)\)",
        r'<link href="\2" color="#285f8f">\1</link>',
        escaped,
    )
    escaped = re.sub(
        r"\$([^$]+)\$",
        lambda m: f'<font name="{code_font}">{m.group(1)}</font>',
        escaped,
    )
    return escaped


def build_styles(font_name: str):
    base = getSampleStyleSheet()
    body = ParagraphStyle(
        "AdaptiveBody",
        parent=base["BodyText"],
        fontName=font_name,
        fontSize=10,
        leading=14,
        textColor=colors.HexColor("#20262e"),
        spaceAfter=6,
    )
    return {
        "body": body,
        "title": ParagraphStyle(
            "AdaptiveTitle",
            parent=body,
            fontSize=23,
            leading=28,
            alignment=TA_CENTER,
            textColor=colors.HexColor("#17324d"),
            spaceAfter=16,
        ),
        "h2": ParagraphStyle(
            "AdaptiveH2",
            parent=body,
            fontSize=16,
            leading=20,
            textColor=colors.HexColor("#17324d"),
            spaceBefore=8,
            spaceAfter=6,
            keepWithNext=True,
        ),
        "h3": ParagraphStyle(
            "AdaptiveH3",
            parent=body,
            fontSize=12.5,
            leading=16,
            textColor=colors.HexColor("#285f8f"),
            spaceBefore=7,
            spaceAfter=5,
            keepWithNext=True,
        ),
        "quote": ParagraphStyle(
            "AdaptiveQuote",
            parent=body,
            leftIndent=10 * mm,
            borderColor=colors.HexColor("#9db3c8"),
            borderWidth=1,
            borderPadding=6,
            backColor=colors.HexColor("#f2f6f9"),
        ),
        "code": ParagraphStyle(
            "AdaptiveCode",
            parent=body,
            fontName=font_name,
            fontSize=8.5,
            leading=11,
            leftIndent=5 * mm,
            rightIndent=5 * mm,
            borderPadding=7,
            backColor=colors.HexColor("#f3f4f6"),
            spaceBefore=4,
            spaceAfter=8,
        ),
        "small": ParagraphStyle(
            "AdaptiveSmall", parent=body, fontSize=8, leading=10, textColor=colors.HexColor("#52606d")
        ),
    }


def table_from_lines(lines: list[str], styles, font_name: str):
    rows = []
    for index, line in enumerate(lines):
        cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
        if index == 1 and all(re.fullmatch(r":?-{3,}:?", cell) for cell in cells):
            continue
        rows.append([Paragraph(inline_markup(cell, font_name), styles["small"]) for cell in cells])
    if not rows:
        return Spacer(1, 1)
    page_width = A4[0] - 38 * mm
    widths = [page_width / len(rows[0])] * len(rows[0])
    table = Table(rows, colWidths=widths, repeatRows=1, hAlign="LEFT")
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#e6eef5")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.HexColor("#17324d")),
                ("GRID", (0, 0), (-1, -1), 0.35, colors.HexColor("#bac7d3")),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 5),
                ("RIGHTPADDING", (0, 0), (-1, -1), 5),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ]
        )
    )
    return table


def markdown_story(source: Path, font_name: str):
    metadata, body = split_frontmatter(source.read_text(encoding="utf-8"))
    styles = build_styles(font_name)
    lines = body.splitlines()
    story = []
    title = source.stem
    i = 0
    paragraph: list[str] = []

    def flush_paragraph() -> None:
        if paragraph:
            text = " ".join(part.strip() for part in paragraph).strip()
            if text:
                story.append(Paragraph(inline_markup(text, font_name), styles["body"]))
            paragraph.clear()

    while i < len(lines):
        line = lines[i]
        stripped = line.strip()
        if stripped == "<!-- pagebreak -->":
            flush_paragraph()
            story.append(PageBreak())
            i += 1
            continue
        if stripped.startswith("```"):
            flush_paragraph()
            fence = stripped[:3]
            code: list[str] = []
            i += 1
            while i < len(lines) and not lines[i].strip().startswith(fence):
                code.append(lines[i])
                i += 1
            story.append(Preformatted("\n".join(code), styles["code"], maxLineLength=100))
            i += 1
            continue
        if stripped.startswith("# "):
            flush_paragraph()
            title = stripped[2:].strip()
            story.append(Paragraph(inline_markup(title, font_name), styles["title"]))
            i += 1
            continue
        if stripped.startswith("## "):
            flush_paragraph()
            story.append(Paragraph(inline_markup(stripped[3:], font_name), styles["h2"]))
            i += 1
            continue
        if stripped.startswith("### "):
            flush_paragraph()
            story.append(Paragraph(inline_markup(stripped[4:], font_name), styles["h3"]))
            i += 1
            continue
        if stripped.startswith("> "):
            flush_paragraph()
            quote = []
            while i < len(lines) and lines[i].strip().startswith(">"):
                quote.append(lines[i].strip().lstrip(">").strip())
                i += 1
            story.append(Paragraph(inline_markup(" ".join(quote), font_name), styles["quote"]))
            continue
        if stripped.startswith("|") and i + 1 < len(lines) and re.match(r"^\s*\|?\s*:?-{3,}", lines[i + 1]):
            flush_paragraph()
            table_lines = []
            while i < len(lines) and lines[i].strip().startswith("|"):
                table_lines.append(lines[i])
                i += 1
            story.append(table_from_lines(table_lines, styles, font_name))
            story.append(Spacer(1, 7))
            continue
        image_match = re.fullmatch(r"!\[([^]]*)\]\(([^)]+)\)", stripped)
        if image_match:
            flush_paragraph()
            image_path = (source.parent / image_match.group(2)).resolve()
            if image_path.is_file():
                image = Image(str(image_path))
                max_width, max_height = 160 * mm, 105 * mm
                scale = min(max_width / image.imageWidth, max_height / image.imageHeight, 1)
                image.drawWidth *= scale
                image.drawHeight *= scale
                story.append(image)
                if image_match.group(1):
                    story.append(Paragraph(html.escape(image_match.group(1)), styles["small"]))
            else:
                story.append(Paragraph(f"[Missing image: {html.escape(str(image_path))}]", styles["body"]))
            i += 1
            continue
        bullet_match = re.match(r"^[-*]\s+(.+)$", stripped)
        number_match = re.match(r"^\d+[.)]\s+(.+)$", stripped)
        if bullet_match or number_match:
            flush_paragraph()
            items = []
            ordered = bool(number_match)
            matcher = r"^\d+[.)]\s+(.+)$" if ordered else r"^[-*]\s+(.+)$"
            while i < len(lines):
                match = re.match(matcher, lines[i].strip())
                if not match:
                    break
                items.append(ListItem(Paragraph(inline_markup(match.group(1), font_name), styles["body"])))
                i += 1
            story.append(ListFlowable(items, bulletType="1" if ordered else "bullet", leftIndent=16))
            story.append(Spacer(1, 4))
            continue
        if not stripped:
            flush_paragraph()
            i += 1
            continue
        paragraph.append(line)
        i += 1

    flush_paragraph()
    if not story:
        story.append(Paragraph("Empty lesson", styles["body"]))
    return metadata, title, story, styles


def render_markdown(source: Path, output: Path, font: str | None = None) -> dict[str, str | None]:
    font_name, font_path = choose_font(font)
    require_font_coverage(source.read_text(encoding="utf-8"), font_name, font_path)
    _, title, story, styles = markdown_story(source, font_name)
    output.parent.mkdir(parents=True, exist_ok=True)

    def decorate(canvas, document):
        canvas.saveState()
        canvas.setFont(font_name, 8)
        canvas.setFillColor(colors.HexColor("#657786"))
        canvas.drawString(19 * mm, 12 * mm, title[:75])
        canvas.drawRightString(A4[0] - 19 * mm, 12 * mm, f"{document.page}")
        canvas.restoreState()

    document = SimpleDocTemplate(
        str(output),
        pagesize=A4,
        rightMargin=19 * mm,
        leftMargin=19 * mm,
        topMargin=17 * mm,
        bottomMargin=18 * mm,
        title=title,
        author="Adaptive Teach",
        subject="Source-derived adaptive learning material",
    )
    document.build(story, onFirstPage=decorate, onLaterPages=decorate)
    return {"title": title, "font": font_path, "output": str(output)}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--font")
    args = parser.parse_args()
    if not args.source.is_file():
        parser.error(f"source not found: {args.source}")
    result = render_markdown(args.source.resolve(), args.output.resolve(), args.font)
    print(f"Created {result['output']}")
    print(f"Font: {result['font'] or 'Helvetica fallback'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
