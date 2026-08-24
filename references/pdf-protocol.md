# PDF protocol

Read this reference only when creating or verifying lesson or module PDFs.

Markdown under `.adaptive-teach/lessons/` and `.adaptive-teach/modules/` is
canonical. PDFs under `.adaptive-teach/output/` are derived.

## Lesson PDF

Render with the bundled deterministic script:

```bash
python3 <skill-dir>/scripts/render_pdf.py \
  <course-root>/.adaptive-teach/lessons/M01-L01-example.md \
  <course-root>/.adaptive-teach/output/lessons/M01-L01-example.pdf
```

Verify and render pages:

```bash
python3 <skill-dir>/scripts/verify_pdf.py \
  <pdf> --source <markdown> --render-dir <course-root>/.adaptive-teach/tmp/M01-L01
```

Inspect every rendered page when the agent has image-viewing capability. Check
typography, margins, page breaks, code, tables, equations, Unicode glyphs,
citations, and empty or clipped content. Keep the lesson `not_done` until the
latest verification succeeds.

## Module PDF

Compile canonical lesson sources, then render and verify:

```bash
python3 <skill-dir>/scripts/compile_module.py \
  --title "Module title" --output-md <module.md> --output-pdf <module.pdf> \
  <lesson-1.md> <lesson-2.md>
python3 <skill-dir>/scripts/verify_pdf.py <module.pdf> \
  --source <module.md> --render-dir <render-dir>
```

## Dependencies and fallback

The renderer requires Python and ReportLab. Verification requires pypdf and a
page renderer: Poppler's `pdftoppm` or PyMuPDF. The scripts report exact missing
dependencies and installation commands. An environment-native PDF capability
may replace the renderer only if it preserves the Markdown source and performs
equivalent reopen, render, and visual checks.

Use `ADAPTIVE_TEACH_FONT` to select a Unicode TrueType font. The renderer probes
common Noto, DejaVu, Arial Unicode, and Apple Gothic locations. Treat missing
glyphs as a failed lesson, especially for language courses.

