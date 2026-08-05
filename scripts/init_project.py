from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import tempfile
from collections.abc import Iterable
from pathlib import Path

PROJECT_NAME_PATTERN = re.compile(r"^[a-z][a-z0-9_]*$")
MARKER_NAME = ".template-state.json"


def validate_project_name(value: str) -> str:
    if not PROJECT_NAME_PATTERN.fullmatch(value):
        raise ValueError(
            "project name must start with a lowercase letter and contain only "
            "lowercase letters, numbers, and underscores"
        )
    return value


def _validated_relative_paths(root: Path, values: Iterable[str]) -> list[Path]:
    root = root.resolve()
    paths: list[Path] = []
    for value in values:
        relative = Path(value)
        if relative.is_absolute() or ".." in relative.parts:
            raise RuntimeError(f"unsafe path in {MARKER_NAME}: {value}")
        path = root / relative
        if not path.resolve(strict=False).is_relative_to(root):
            raise RuntimeError(f"path escapes project root in {MARKER_NAME}: {value}")
        if path.is_symlink():
            raise RuntimeError(f"refusing symlink in {MARKER_NAME}: {value}")
        paths.append(path)
    return paths


def _is_dirty(root: Path) -> bool:
    result = subprocess.run(
        ["git", "status", "--porcelain"],
        cwd=root,
        check=False,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        raise RuntimeError("project root is not a Git worktree")
    return bool(result.stdout.strip())


def _atomic_write(path: Path, content: str) -> None:
    temporary_name: str | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            dir=path.parent,
            prefix=f".{path.name}.",
            delete=False,
        ) as temporary:
            temporary.write(content)
            temporary.flush()
            os.fsync(temporary.fileno())
            temporary_name = temporary.name
        Path(temporary_name).replace(path)
    finally:
        if temporary_name is not None:
            Path(temporary_name).unlink(missing_ok=True)


def initialize(
    root: Path,
    project_name: str,
    friendly_name: str,
    remove_example: bool,
    allow_dirty: bool,
) -> list[Path]:
    root = root.resolve()
    project_name = validate_project_name(project_name)
    friendly_name = friendly_name.strip()
    if not friendly_name:
        raise ValueError("friendly name must not be blank")

    marker_path = root / MARKER_NAME
    if not marker_path.is_file():
        raise RuntimeError("project is already initialized; template marker is absent")
    if not allow_dirty and _is_dirty(root):
        raise RuntimeError("Git worktree is dirty; commit changes or pass --allow-dirty")

    state = json.loads(marker_path.read_text(encoding="utf-8"))
    rewrite_paths = _validated_relative_paths(root, state["rewrite_files"])
    example_paths = _validated_relative_paths(root, state["example_paths"])
    missing = [path.relative_to(root).as_posix() for path in rewrite_paths if not path.is_file()]
    if missing:
        raise RuntimeError(f"rewrite allowlist contains missing files: {', '.join(missing)}")
    if remove_example:
        invalid_examples = [
            path.relative_to(root).as_posix()
            for path in example_paths
            if path.exists() and not path.is_file()
        ]
        if invalid_examples:
            raise RuntimeError(
                "example allowlist must contain files, not directories: "
                + ", ".join(invalid_examples)
            )

    template_project_name = state["template_project_name"]
    template_slug = template_project_name.replace("_", "-")
    replacements = (
        (state["template_display_name"], friendly_name),
        (template_project_name.upper(), project_name.upper()),
        (template_project_name, project_name),
        (template_slug, project_name.replace("_", "-")),
    )

    pending: list[tuple[Path, str]] = []
    for path in rewrite_paths:
        original = path.read_text(encoding="utf-8")
        updated = original
        for old, new in replacements:
            updated = updated.replace(old, new)
        if updated != original:
            pending.append((path, updated))

    for path, content in pending:
        _atomic_write(path, content)

    if remove_example:
        for path in example_paths:
            path.unlink(missing_ok=True)

    marker_path.unlink()
    return [path for path, _ in pending]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Safely initialize a new project from dbt-project-template."
    )
    parser.add_argument("project_name", help="dbt-safe identifier such as client_analytics")
    parser.add_argument("friendly_name", help="human-readable project name")
    parser.add_argument(
        "--remove-example",
        action="store_true",
        help="remove the allowlisted sample DAG files",
    )
    parser.add_argument(
        "--allow-dirty",
        action="store_true",
        help="allow initialization when Git reports local changes",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    root = Path(__file__).resolve().parents[1]
    try:
        changed = initialize(
            root,
            args.project_name,
            args.friendly_name,
            args.remove_example,
            args.allow_dirty,
        )
    except (KeyError, OSError, ValueError, RuntimeError, json.JSONDecodeError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 2

    print(f"Initialized {args.friendly_name.strip()} ({args.project_name}).")
    print(f"Rewrote {len(changed)} allowlisted files.")
    if args.remove_example:
        print("Removed the allowlisted sample DAG files.")
    print("Next: just setup && just demo && just check")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
