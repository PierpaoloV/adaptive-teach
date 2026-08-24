#!/usr/bin/env python3
"""Validate adaptive-teach workspace schemas and completion invariants."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

from adaptive_common import SCHEMA_VERSION, VALID_STATUSES, course_workspace, read_frontmatter

REQUIRED_FILES = ("ONBOARDING.md", "LEARNER.md", "ROADMAP.md", "RESOURCES.md")
LESSON_ID = re.compile(r"^M\d{2}-L\d{2}$")
MODULE_ID = re.compile(r"^M\d{2}-U\d{2}$")


def roadmap_lesson_statuses(text: str) -> dict[str, str]:
    statuses: dict[str, str] = {}
    for line in text.splitlines():
        if not line.lstrip().startswith("|"):
            continue
        cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
        if len(cells) >= 5 and LESSON_ID.fullmatch(cells[0]):
            statuses[cells[0]] = cells[-1]
    return statuses


def validate(course_root: Path) -> dict[str, object]:
    workspace = course_workspace(course_root)
    errors: list[str] = []
    warnings: list[str] = []

    if not workspace.is_dir():
        return {"ok": False, "errors": [f"missing workspace: {workspace}"], "warnings": []}

    required_metadata: dict[str, dict[str, str]] = {}
    for name in REQUIRED_FILES:
        path = workspace / name
        if not path.is_file():
            errors.append(f"missing required file: {name}")
            continue
        try:
            meta = read_frontmatter(path)
        except ValueError as exc:
            errors.append(f"{name}: {exc}")
            continue
        required_metadata[name] = meta
        if meta.get("schema_version") != SCHEMA_VERSION:
            errors.append(f"{name}: schema_version must be {SCHEMA_VERSION}")

    onboarding_status = required_metadata.get("ONBOARDING.md", {}).get("status")
    if "ONBOARDING.md" in required_metadata:
        status = onboarding_status
        if status not in VALID_STATUSES:
            errors.append("ONBOARDING.md: status must be not_done or done")

    roadmap_path = workspace / "ROADMAP.md"
    roadmap_text = roadmap_path.read_text(encoding="utf-8") if roadmap_path.is_file() else ""
    roadmap_statuses = roadmap_lesson_statuses(roadmap_text)
    if "ROADMAP.md" in required_metadata:
        mission_status = required_metadata["ROADMAP.md"].get("mission_status")
        if mission_status not in VALID_STATUSES:
            errors.append("ROADMAP.md: mission_status must be not_done or done")

    learner_text = (
        (workspace / "LEARNER.md").read_text(encoding="utf-8")
        if "LEARNER.md" in required_metadata
        else ""
    )

    lesson_files = sorted((workspace / "lessons").glob("*.md")) if (workspace / "lessons").exists() else []
    lesson_ids: set[str] = set()
    seen_not_done = False
    lesson_summary: list[dict[str, str]] = []

    for path in lesson_files:
        try:
            meta = read_frontmatter(path)
        except ValueError as exc:
            errors.append(f"{path.name}: {exc}")
            continue
        lesson_id = meta.get("lesson_id", "")
        module_id = meta.get("module_id", "")
        status = meta.get("status", "")
        capability = meta.get("capability", "")
        if meta.get("schema_version") != SCHEMA_VERSION:
            errors.append(f"{path.name}: schema_version must be {SCHEMA_VERSION}")
        if not LESSON_ID.fullmatch(lesson_id):
            errors.append(f"{path.name}: invalid lesson_id {lesson_id!r}")
        elif lesson_id in lesson_ids:
            errors.append(f"duplicate lesson_id: {lesson_id}")
        lesson_ids.add(lesson_id)
        if not MODULE_ID.fullmatch(module_id):
            errors.append(f"{path.name}: invalid module_id {module_id!r}")
        if status not in VALID_STATUSES:
            errors.append(f"{path.name}: invalid status {status!r}")
        if not capability or capability.startswith("Replace with"):
            errors.append(f"{path.name}: capability must be observable and populated")

        if status == "not_done":
            seen_not_done = True
        elif status == "done" and seen_not_done:
            errors.append(f"{lesson_id}: done lesson follows a not_done lesson")

        if lesson_id and lesson_id not in roadmap_statuses:
            errors.append(f"{lesson_id}: missing from ROADMAP.md")
        elif lesson_id and roadmap_statuses[lesson_id] != status:
            errors.append(
                f"{lesson_id}: lesson status {status!r} does not match roadmap status "
                f"{roadmap_statuses[lesson_id]!r}"
            )

        if status == "done":
            evidence = workspace / "evidence" / f"{lesson_id}.md"
            if not evidence.is_file():
                errors.append(f"{lesson_id}: done without evidence/{lesson_id}.md")
            else:
                try:
                    evidence_meta = read_frontmatter(evidence)
                except ValueError as exc:
                    errors.append(f"{lesson_id}: invalid evidence frontmatter: {exc}")
                else:
                    if evidence_meta.get("status") != "done":
                        errors.append(f"{lesson_id}: evidence status is not done")
                    if evidence_meta.get("lesson_id") != lesson_id:
                        errors.append(f"{lesson_id}: evidence lesson_id mismatch")
            pdf_matches = list((workspace / "output" / "lessons").glob(f"{lesson_id}*.pdf"))
            if not pdf_matches:
                errors.append(f"{lesson_id}: done without a lesson PDF")
            else:
                verification = pdf_matches[0].with_suffix(".verify.json")
                if not verification.is_file():
                    errors.append(f"{lesson_id}: done without a PDF verification report")
                else:
                    try:
                        verification_data = json.loads(verification.read_text(encoding="utf-8"))
                    except (json.JSONDecodeError, OSError) as exc:
                        errors.append(f"{lesson_id}: invalid PDF verification report: {exc}")
                    else:
                        if verification_data.get("ok") is not True:
                            errors.append(f"{lesson_id}: PDF verification did not pass")
            if lesson_id not in learner_text:
                errors.append(f"{lesson_id}: done without learner-model evidence reference")

        lesson_summary.append({"id": lesson_id, "status": status, "file": path.name})

    if not lesson_files and onboarding_status == "done":
        warnings.append("onboarding is done but no lessons are planned as source files")

    return {
        "ok": not errors,
        "workspace": str(workspace),
        "lessons": lesson_summary,
        "errors": errors,
        "warnings": warnings,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("course_root", nargs="?", default=".")
    parser.add_argument("--json", action="store_true", dest="as_json")
    args = parser.parse_args()
    report = validate(Path(args.course_root))
    if args.as_json:
        print(json.dumps(report, indent=2, ensure_ascii=False))
    else:
        for warning in report["warnings"]:
            print(f"WARNING: {warning}")
        for error in report["errors"]:
            print(f"ERROR: {error}")
        print("OK" if report["ok"] else "INVALID")
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
