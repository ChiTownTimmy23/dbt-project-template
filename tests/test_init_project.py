from __future__ import annotations

import importlib
import json
import subprocess
from pathlib import Path

import pytest


def load_module():
    spec = importlib.util.find_spec("scripts.init_project")
    assert spec is not None, "scripts.init_project must exist"
    return importlib.import_module("scripts.init_project")


def run_git(root: Path, *args: str) -> None:
    subprocess.run(["git", *args], cwd=root, check=True, capture_output=True, text=True)


def make_project(tmp_path: Path) -> Path:
    root = tmp_path / "project"
    root.mkdir()
    files = {
        "dbt_project.yml": "name: dbt_project_template\nprofile: dbt_project_template\n",
        "profiles.yml": "dbt_project_template:\n  target: dev\n",
        "pyproject.toml": (
            'name = "dbt-project-template"\n'
            'description = "dbt Project Template"\n'
        ),
        "uv.lock": 'name = "dbt-project-template"\n',
        "README.md": "# dbt Project Template\n\nUse `dbt_project_template`.\n",
        "notes.txt": "dbt_project_template must not change outside the allowlist.\n",
        "seeds/raw_customers.csv": "customer_id\n1\n",
        "models/staging/stg_customers.sql": "select 1 as customer_id\n",
        "tests/assert_example.sql": "select 1 where false\n",
    }
    for relative_path, content in files.items():
        path = root / relative_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")

    marker = {
        "template_project_name": "dbt_project_template",
        "template_display_name": "dbt Project Template",
        "rewrite_files": [
            "dbt_project.yml",
            "profiles.yml",
            "pyproject.toml",
            "uv.lock",
            "README.md",
        ],
        "example_paths": [
            "seeds/raw_customers.csv",
            "models/staging/stg_customers.sql",
            "tests/assert_example.sql",
        ],
    }
    (root / ".template-state.json").write_text(json.dumps(marker), encoding="utf-8")

    run_git(root, "init", "-b", "main")
    run_git(root, "add", ".")
    run_git(
        root,
        "-c",
        "user.name=Template Test",
        "-c",
        "user.email=template@example.com",
        "commit",
        "-m",
        "initial",
    )
    return root


@pytest.mark.parametrize(
    "value",
    ["client_analytics", "a", "project2", "project_2026"],
)
def test_validate_project_name_accepts_dbt_safe_identifiers(value: str) -> None:
    module = load_module()

    assert module.validate_project_name(value) == value


@pytest.mark.parametrize(
    "value",
    ["", "ClientAnalytics", "2project", "client-project", "client project", "_private"],
)
def test_validate_project_name_rejects_unsafe_identifiers(value: str) -> None:
    module = load_module()

    with pytest.raises(ValueError, match="lowercase letter"):
        module.validate_project_name(value)


def test_initialize_rejects_blank_friendly_name(tmp_path: Path) -> None:
    module = load_module()
    root = make_project(tmp_path)

    with pytest.raises(ValueError, match="friendly name"):
        module.initialize(root, "client_analytics", "   ", False, False)


def test_initialize_refuses_dirty_git_state(tmp_path: Path) -> None:
    module = load_module()
    root = make_project(tmp_path)
    (root / "scratch.txt").write_text("dirty\n", encoding="utf-8")

    with pytest.raises(RuntimeError, match="dirty"):
        module.initialize(root, "client_analytics", "Client Analytics", False, False)


def test_initialize_allow_dirty_rewrites_only_allowlisted_files(tmp_path: Path) -> None:
    module = load_module()
    root = make_project(tmp_path)
    (root / "scratch.txt").write_text("dirty\n", encoding="utf-8")

    changed = module.initialize(root, "client_analytics", "Client Analytics", False, True)

    assert {path.relative_to(root).as_posix() for path in changed} == {
        "README.md",
        "dbt_project.yml",
        "profiles.yml",
        "pyproject.toml",
        "uv.lock",
    }
    assert "client_analytics" in (root / "dbt_project.yml").read_text(encoding="utf-8")
    assert "client-analytics" in (root / "pyproject.toml").read_text(encoding="utf-8")
    assert "Client Analytics" in (root / "README.md").read_text(encoding="utf-8")
    assert (root / "notes.txt").read_text(encoding="utf-8").startswith(
        "dbt_project_template"
    )
    assert not (root / ".template-state.json").exists()


def test_initialize_refuses_a_second_run(tmp_path: Path) -> None:
    module = load_module()
    root = make_project(tmp_path)
    module.initialize(root, "client_analytics", "Client Analytics", False, False)

    with pytest.raises(RuntimeError, match="already initialized"):
        module.initialize(root, "another_project", "Another Project", False, True)


def test_initialize_remove_example_deletes_only_declared_paths(tmp_path: Path) -> None:
    module = load_module()
    root = make_project(tmp_path)

    module.initialize(root, "client_analytics", "Client Analytics", True, False)

    assert not (root / "seeds/raw_customers.csv").exists()
    assert not (root / "models/staging/stg_customers.sql").exists()
    assert not (root / "tests/assert_example.sql").exists()
    assert (root / "notes.txt").is_file()

