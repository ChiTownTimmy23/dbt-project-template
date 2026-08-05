from __future__ import annotations

import os
import shutil
import subprocess
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path

import yaml

SENSITIVE_FRAGMENTS = ("KEY", "TOKEN", "SECRET", "PASSWORD")


@dataclass(frozen=True, slots=True)
class CheckResult:
    name: str
    ok: bool
    detail: str


def summarize_environment(environ: Mapping[str, str]) -> str:
    visible: list[str] = []
    for name in sorted(environ):
        is_sensitive = any(fragment in name.upper() for fragment in SENSITIVE_FRAGMENTS)
        if not name.startswith("DBT_") and not is_sensitive:
            continue
        if is_sensitive:
            state = "<redacted>"
        else:
            state = "<set>" if environ[name] else "<empty>"
        visible.append(f"{name}={state}")
    return ", ".join(visible) if visible else "no DBT or sensitive variables detected"


def _tool_check(name: str) -> CheckResult:
    path = shutil.which(name)
    if path is None:
        return CheckResult(name, False, f"{name} not found on PATH")
    return CheckResult(name, True, path)


def _profile_check(root: Path) -> CheckResult:
    profile_path = root / "profiles.yml"
    if not profile_path.is_file():
        return CheckResult("profile", False, "profiles.yml is missing")
    try:
        profile = yaml.safe_load(profile_path.read_text(encoding="utf-8"))
    except yaml.YAMLError as error:
        return CheckResult("profile", False, f"invalid YAML: {error}")

    try:
        project_name = next(iter(profile))
        target_name = profile[project_name]["target"]
        adapter = profile[project_name]["outputs"][target_name]["type"]
    except (KeyError, StopIteration, TypeError) as error:
        return CheckResult("profile", False, f"invalid profile structure: {error}")
    if adapter != "duckdb":
        return CheckResult("profile", False, f"expected duckdb adapter, found {adapter!r}")
    return CheckResult("profile", True, f"{project_name}/{target_name} uses duckdb")


def _git_check(root: Path) -> CheckResult:
    if shutil.which("git") is None:
        return CheckResult("git", False, "git not found on PATH")
    result = subprocess.run(
        ["git", "rev-parse", "--show-toplevel"],
        cwd=root,
        check=False,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        return CheckResult("git", False, "project is not inside a Git worktree")
    return CheckResult("git", True, result.stdout.strip())


def collect_checks(root: Path) -> list[CheckResult]:
    root = root.resolve()
    virtualenv = root / ".venv"
    return [
        _tool_check("uv"),
        _tool_check("just"),
        CheckResult(
            "virtualenv",
            virtualenv.is_dir(),
            str(virtualenv) if virtualenv.is_dir() else ".venv is absent; run 'just setup'",
        ),
        _profile_check(root),
        _git_check(root),
        CheckResult("environment", True, summarize_environment(os.environ)),
    ]


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    checks = collect_checks(root)
    for check in checks:
        status = "ok" if check.ok else "fail"
        print(f"[{status}] {check.name}: {check.detail}")
    return 0 if all(check.ok for check in checks) else 1


if __name__ == "__main__":
    raise SystemExit(main())
