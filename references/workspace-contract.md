# Workspace contract

Read this reference before creating, validating, or changing runtime course
files.

## Runtime layout

```text
.adaptive-teach/
├── .gitignore
├── ONBOARDING.md
├── LEARNER.md
├── ROADMAP.md
├── RESOURCES.md
├── lessons/              # canonical lesson Markdown
├── evidence/             # one evidence record per lesson or assessment
├── modules/              # canonical compiled module Markdown
├── output/
│   ├── lessons/          # derived lesson PDFs
│   └── modules/          # derived module PDFs
└── tmp/                  # render and QA intermediates
```

Initialize it with:

```bash
python3 <skill-dir>/scripts/init_workspace.py <course-root>
```

The initializer fails rather than overwriting an existing workspace.

## Source-of-truth order

1. `ONBOARDING.md` preserves the original questions, answers, constraints, and
   diagnostic interpretations. Keep it after onboarding as historical evidence.
2. `LEARNER.md` is the current, revisable learner hypothesis. Newer evidence can
   supersede onboarding conclusions.
3. `ROADMAP.md` is the current high-level destination and detailed current
   milestone.
4. `lessons/*.md` and `modules/*.md` are canonical teaching content.
5. PDFs are reproducible derived outputs.
6. Chat is transient. Persist only evidence and decisions that change the
   learner model or roadmap.

## Status protocol

Every completable Markdown artifact begins with simple YAML frontmatter:

```yaml
---
schema_version: 1
status: not_done
---
```

Valid status values are `not_done` and `done`.

For a lesson, keep `status: not_done` while explaining, assessing, recording
evidence, updating `LEARNER.md`, generating the PDF, and verifying the PDF. Set
it to `done` only after all have succeeded. If interrupted, redo the same lesson
ID and overwrite its drafts.

Validate the workspace after material state changes:

```bash
python3 <skill-dir>/scripts/validate_workspace.py <course-root>
```

## IDs

- Milestone: `M01`, `M02`, ...
- Module inside a milestone: `M01-U01`, `M01-U02`, ...
- Lesson inside a milestone: `M01-L01`, `M01-L02`, ...

IDs are stable. Replanning may change outcomes and ordering, but never reuse an
existing ID for a different capability.

