#!/usr/bin/env python3
"""Initialize a private adaptive-teach runtime workspace."""

from __future__ import annotations

import argparse
import shutil
from pathlib import Path

from adaptive_common import course_workspace


def initialize(course_root: Path) -> Path:
    workspace = course_workspace(course_root)
    if workspace.exists():
        raise FileExistsError(f"workspace already exists: {workspace}")

    assets = Path(__file__).resolve().parents[1] / "assets" / "workspace"
    workspace.mkdir(parents=True)
    for name in ("ONBOARDING.md", "LEARNER.md", "ROADMAP.md", "RESOURCES.md"):
        shutil.copy2(assets / name, workspace / name)
    shutil.copy2(assets / "gitignore.template", workspace / ".gitignore")

    for directory in (
        "lessons",
        "evidence",
        "modules",
        "output/lessons",
        "output/modules",
        "tmp",
    ):
        (workspace / directory).mkdir(parents=True, exist_ok=True)

    return workspace


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("course_root", nargs="?", default=".")
    args = parser.parse_args()
    try:
        workspace = initialize(Path(args.course_root))
    except FileExistsError as exc:
        parser.error(str(exc))
    print(workspace)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
