from __future__ import annotations

import re
import tomllib
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

EXPECTED_DEPENDENCIES = {
    "dbt-core==1.12.0",
    "dbt-duckdb==1.10.1",
}
EXPECTED_DEV_DEPENDENCIES = {
    "mkdocs==1.6.1",
    "mkdocs-material==9.7.7",
    "pre-commit==4.6.1",
    "pytest==9.1.1",
    "ruff==0.16.1",
    "sqlfluff==4.2.2",
    "sqlfluff-templater-dbt==4.2.2",
}
REQUIRED_RECIPES = {
    "setup",
    "doctor",
    "demo",
    "check",
    "docs",
    "docs-serve",
    "lint",
    "format",
    "test",
    "init",
    "clean",
}


def read_text(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_python_and_dependency_versions_are_exactly_pinned() -> None:
    pyproject = tomllib.loads(read_text("pyproject.toml"))

    assert pyproject["project"]["requires-python"] == ">=3.12,<3.15"
    assert set(pyproject["project"]["dependencies"]) == EXPECTED_DEPENDENCIES
    assert set(pyproject["dependency-groups"]["dev"]) == EXPECTED_DEV_DEPENDENCIES
    assert read_text(".python-version").strip() == "3.12"


def test_dbt_uses_repository_local_duckdb_profile() -> None:
    project = read_text("dbt_project.yml")
    profile = read_text("profiles.yml")

    assert re.search(r"^name:\s*dbt_project_template$", project, re.MULTILINE)
    assert re.search(r"^profile:\s*dbt_project_template$", project, re.MULTILINE)
    assert re.search(r"^dbt_project_template:$", profile, re.MULTILINE)
    assert "type: duckdb" in profile
    assert "env_var('DBT_DUCKDB_PATH', 'target/dev.duckdb')" in profile


def test_sqlfluff_uses_dbt_templating_and_duckdb_dialect() -> None:
    sqlfluff = read_text(".sqlfluff")

    assert re.search(r"^dialect\s*=\s*duckdb$", sqlfluff, re.MULTILINE)
    assert re.search(r"^templater\s*=\s*dbt$", sqlfluff, re.MULTILINE)
    assert re.search(r"^project_dir\s*=\s*\.$", sqlfluff, re.MULTILINE)
    assert re.search(r"^profiles_dir\s*=\s*\.$", sqlfluff, re.MULTILINE)


def test_justfile_exposes_the_stable_command_contract() -> None:
    justfile = read_text("justfile")
    recipes = set(re.findall(r"^([a-z][a-z0-9-]*)(?:\s+[^:]*)?:", justfile, re.MULTILINE))

    assert REQUIRED_RECIPES <= recipes
    assert "uv lock --check" in justfile
    assert "dbt parse --profiles-dir ." in justfile
    assert "dbt build --profiles-dir ." in justfile
    assert "sqlfluff lint models analyses tests" in justfile
    assert "mkdocs build --strict" in justfile


def test_generated_and_local_secret_paths_are_ignored() -> None:
    patterns = set(read_text(".gitignore").splitlines())

    assert {
        ".venv/",
        "target/",
        "dbt_packages/",
        "logs/",
        "site/",
        "*.duckdb",
        "*.duckdb.wal",
        ".env",
        ".env.*",
        "profiles.local.yml",
    } <= patterns
