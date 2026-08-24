from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

SKILL_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SKILL_ROOT / "scripts"))

from init_workspace import initialize  # noqa: E402
from compile_module import compile_sources  # noqa: E402
from render_pdf import render_markdown  # noqa: E402
from validate_workspace import validate  # noqa: E402
from verify_pdf import verify  # noqa: E402


def replace_once(path: Path, old: str, new: str) -> None:
    text = path.read_text(encoding="utf-8")
    if old not in text:
        raise AssertionError(f"missing text in {path}: {old!r}")
    path.write_text(text.replace(old, new, 1), encoding="utf-8")


class AdaptiveTeachTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.course_root = Path(self.temp.name)
        self.workspace = initialize(self.course_root)

    def tearDown(self) -> None:
        self.temp.cleanup()

    def test_initialized_workspace_is_valid_and_private(self) -> None:
        report = validate(self.course_root)
        self.assertTrue(report["ok"], report["errors"])
        self.assertEqual((self.workspace / ".gitignore").read_text(), "*\n!.gitignore\n")

    def test_validator_reports_malformed_required_file_without_crashing(self) -> None:
        (self.workspace / "ONBOARDING.md").write_text("# Missing frontmatter\n", encoding="utf-8")
        report = validate(self.course_root)
        self.assertFalse(report["ok"])
        self.assertTrue(
            any(error.startswith("ONBOARDING.md:") for error in report["errors"]),
            report["errors"],
        )

    def test_done_lesson_cannot_follow_interrupted_lesson(self) -> None:
        roadmap = self.workspace / "ROADMAP.md"
        replace_once(
            roadmap,
            "| ID | Module | Observable capability | Prerequisites | Status |\n"
            "|---|---|---|---|---|\n",
            "| ID | Module | Observable capability | Prerequisites | Status |\n"
            "|---|---|---|---|---|\n"
            "| M01-L01 | M01-U01 | Explain swaps | none | not_done |\n"
            "| M01-L02 | M01-U01 | Implement a pass | M01-L01 | done |\n",
        )
        lessons = self.workspace / "lessons"
        lessons.joinpath("M01-L01-swaps.md").write_text(
            LESSON_SOURCE.replace("M01-LXX", "M01-L01").replace("CAPABILITY", "Explain swaps"),
            encoding="utf-8",
        )
        lessons.joinpath("M01-L02-pass.md").write_text(
            LESSON_SOURCE.replace("M01-LXX", "M01-L02")
            .replace("CAPABILITY", "Implement a pass")
            .replace("status: not_done", "status: done", 1),
            encoding="utf-8",
        )
        report = validate(self.course_root)
        self.assertFalse(report["ok"])
        self.assertIn("M01-L02: done lesson follows a not_done lesson", report["errors"])

    def test_pdf_pipeline_and_done_invariants(self) -> None:
        replace_once(self.workspace / "ONBOARDING.md", "status: not_done", "status: done")
        roadmap = self.workspace / "ROADMAP.md"
        replace_once(
            roadmap,
            "| ID | Module | Observable capability | Prerequisites | Status |\n"
            "|---|---|---|---|---|\n",
            "| ID | Module | Observable capability | Prerequisites | Status |\n"
            "|---|---|---|---|---|\n"
            "| M01-L01 | M01-U01 | Explain one bubble-sort pass | none | done |\n",
        )
        source = self.workspace / "lessons" / "M01-L01-bubble-sort-pass.md"
        source.write_text(
            LESSON_SOURCE.replace("M01-LXX", "M01-L01")
            .replace("CAPABILITY", "Explain one bubble-sort pass")
            .replace("status: not_done", "status: done", 1),
            encoding="utf-8",
        )
        evidence = self.workspace / "evidence" / "M01-L01.md"
        evidence.write_text(
            "---\nschema_version: 1\nlesson_id: M01-L01\nstatus: done\n---\n\n"
            "# Evidence\n\nOperational explanation without assistance.\n",
            encoding="utf-8",
        )
        with (self.workspace / "LEARNER.md").open("a", encoding="utf-8") as stream:
            stream.write("\n| Explain one pass | operational | none | high | M01-L01 | now | later |\n")

        pdf = self.workspace / "output" / "lessons" / "M01-L01-bubble-sort-pass.pdf"
        render_markdown(source, pdf)
        verification = verify(
            pdf,
            source,
            self.workspace / "tmp" / "M01-L01",
            pdf.with_suffix(".verify.json"),
        )
        self.assertTrue(verification["ok"], verification["errors"])
        report = validate(self.course_root)
        self.assertTrue(report["ok"], report["errors"])

    def test_module_compilation_preserves_sources_and_nests_lessons(self) -> None:
        first = self.workspace / "lessons" / "M01-L01-first.md"
        second = self.workspace / "lessons" / "M01-L02-second.md"
        done_source = LESSON_SOURCE.replace("status: not_done", "status: done", 1)
        first.write_text(done_source.replace("M01-LXX", "M01-L01"), encoding="utf-8")
        second.write_text(
            done_source.replace("M01-LXX", "M01-L02").replace(
                "# One bubble-sort pass", "# Reconstructing the full algorithm", 1
            ),
            encoding="utf-8",
        )
        first_before = first.read_text(encoding="utf-8")
        second_before = second.read_text(encoding="utf-8")
        module_md = self.workspace / "modules" / "M01-U01.md"
        module_pdf = self.workspace / "output" / "modules" / "M01-U01.pdf"

        compile_sources("Module: Bubble sort", [first, second], module_md)
        rendered = module_md.read_text(encoding="utf-8")
        self.assertIn("# Module: Bubble sort", rendered)
        self.assertIn("## One bubble-sort pass", rendered)
        self.assertIn("## Reconstructing the full algorithm", rendered)
        self.assertIn("<!-- pagebreak -->", rendered)
        self.assertEqual(first.read_text(encoding="utf-8"), first_before)
        self.assertEqual(second.read_text(encoding="utf-8"), second_before)

        result = render_markdown(module_md, module_pdf)
        self.assertEqual(result["title"], "Module: Bubble sort")
        verification = verify(
            module_pdf,
            module_md,
            self.workspace / "tmp" / "M01-U01",
            module_pdf.with_suffix(".verify.json"),
        )
        self.assertTrue(verification["ok"], verification["errors"])


LESSON_SOURCE = """---
schema_version: 1
lesson_id: M01-LXX
module_id: M01-U01
status: not_done
domain: computing
capability: CAPABILITY
---

# One bubble-sort pass

## Outcome

Explain why adjacent swaps move the largest remaining value to the right.

## Theory

Compare adjacent values. Swap them when the left value is larger. The invariant
is that after one complete pass, the suffix contains its largest value.

La forza netta in meccanica si può scrivere come `$F = ma$`.

한국어 예시: 인접한 두 값을 비교합니다.

## Worked example

| Input | After one pass |
|---|---|
| 3, 1, 2 | 1, 2, 3 |

```python
for index in range(len(values) - 1):
    if values[index] > values[index + 1]:
        values[index], values[index + 1] = values[index + 1], values[index]
```

## Sources

- External Algorithms, *Sorting Fundamentals*.
"""


if __name__ == "__main__":
    unittest.main()
