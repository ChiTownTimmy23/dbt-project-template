from __future__ import annotations

import json
import re
import tomllib
from pathlib import Path

import pytest
import yaml

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
REQUIRED_DAG_FILES = {
    "seeds/raw_customers.csv",
    "seeds/raw_orders.csv",
    "models/staging/sources.yml",
    "models/staging/stg_customers.sql",
    "models/staging/stg_customers.yml",
    "models/staging/stg_orders.sql",
    "models/staging/stg_orders.yml",
    "models/intermediate/int_customer_order_metrics.sql",
    "models/intermediate/int_customer_order_metrics.yml",
    "models/marts/dim_customers.sql",
    "models/marts/fct_orders.sql",
    "models/marts/marts.yml",
    "models/marts/unit_tests.yml",
    "tests/assert_order_amounts_are_nonnegative.sql",
    "analyses/customer_health_summary.sql",
}
REQUIRED_DOC_FILES = {
    "docs/index.md",
    "docs/getting-started.md",
    "docs/architecture.md",
    "docs/commands.md",
    "docs/client-onboarding.md",
    "docs/adapter-migrations.md",
    "docs/decisions/0001-duckdb-first.md",
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

    project_name = re.search(r"^name:\s*([a-z][a-z0-9_]*)$", project, re.MULTILINE)
    profile_name = re.search(r"^profile:\s*([a-z][a-z0-9_]*)$", project, re.MULTILINE)
    assert project_name is not None
    assert profile_name is not None
    assert project_name.group(1) == profile_name.group(1)
    assert re.search(rf"^{project_name.group(1)}:$", profile, re.MULTILINE)
    if (ROOT / ".template-state.json").exists():
        assert project_name.group(1) == "dbt_project_template"
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
        ".user.yml",
        "profiles.local.yml",
    } <= patterns


def test_sample_dag_has_the_required_layers_and_dependencies() -> None:
    if not (ROOT / ".template-state.json").exists() and not any(
        (ROOT / path).exists() for path in REQUIRED_DAG_FILES
    ):
        pytest.skip("sample DAG was intentionally removed during initialization")
    assert all((ROOT / path).is_file() for path in REQUIRED_DAG_FILES)

    sources = read_text("models/staging/sources.yml")
    assert "name: raw" in sources
    assert "name: raw_customers" in sources
    assert "name: raw_orders" in sources
    assert "source('raw', 'raw_customers')" in read_text("models/staging/stg_customers.sql")
    assert "source('raw', 'raw_orders')" in read_text("models/staging/stg_orders.sql")

    intermediate = read_text("models/intermediate/int_customer_order_metrics.sql")
    assert "ref('stg_customers')" in intermediate
    assert "ref('stg_orders')" in intermediate
    assert "ref('int_customer_order_metrics')" in read_text("models/marts/dim_customers.sql")
    assert "ref('stg_orders')" in read_text("models/marts/fct_orders.sql")


def test_sample_dag_demonstrates_governance_and_testing_features() -> None:
    if not (ROOT / ".template-state.json").exists() and not any(
        (ROOT / path).exists() for path in REQUIRED_DAG_FILES
    ):
        pytest.skip("sample DAG was intentionally removed during initialization")
    marts = read_text("models/marts/marts.yml")
    unit_tests = read_text("models/marts/unit_tests.yml")
    singular_test = read_text("tests/assert_order_amounts_are_nonnegative.sql")

    assert marts.count("enforced: true") == 2
    assert "name: customer_health_dashboard" in marts
    assert "ref('dim_customers')" in marts
    assert "ref('fct_orders')" in marts
    assert "unit_tests:" in unit_tests
    assert "model: int_customer_order_metrics" in unit_tests
    assert "given:" in unit_tests
    assert "expect:" in unit_tests
    assert "ref('fct_orders')" in singular_test
    assert "order_amount < 0" in singular_test


def test_documentation_covers_the_operating_lifecycle() -> None:
    assert (ROOT / "README.md").is_file()
    assert all((ROOT / path).is_file() for path in REQUIRED_DOC_FILES)
    mkdocs = read_text("mkdocs.yml")
    readme = read_text("README.md")

    assert all(Path(path).name in mkdocs for path in REQUIRED_DOC_FILES)
    assert all(
        command in readme
        for command in (
            'just init client_project "Client Project"',
            "just setup",
            "just demo",
            "just check",
        )
    )
    adapter_guide = read_text("docs/adapter-migrations.md")
    assert all(
        adapter in adapter_guide
        for adapter in ("Snowflake", "Databricks", "BigQuery", "Postgres")
    )


def test_automation_uses_the_same_gate_and_immutable_actions() -> None:
    workflow = read_text(".github/workflows/ci.yml")
    precommit = read_text(".pre-commit-config.yaml")
    dependabot = yaml.safe_load(read_text(".github/dependabot.yml"))

    uses_lines = [line.strip() for line in workflow.splitlines() if "uses:" in line]
    assert len(uses_lines) == 4
    assert all(
        re.fullmatch(r"- uses: [^@\s]+@[0-9a-f]{40}(?:\s+# .+)?", line)
        for line in uses_lines
    )
    assert "just setup" in workflow
    assert "just check" in workflow
    assert "permissions:\n  contents: read" in workflow
    assert "repo: local" in precommit
    assert all(
        hook in precommit
        for hook in (
            "uv-lock-check",
            "ruff-check",
            "repository-tests",
            "sqlfluff-lint",
            "mkdocs-strict",
        )
    )
    assert {update["package-ecosystem"] for update in dependabot["updates"]} == {
        "github-actions",
        "uv",
    }


def test_template_marker_rewrites_every_identity_bearing_document() -> None:
    marker_path = ROOT / ".template-state.json"
    if not marker_path.exists():
        pytest.skip("project was already initialized")
    marker = json.loads(marker_path.read_text(encoding="utf-8"))

    assert {
        ".sqlfluff",
        "README.md",
        "dbt_project.yml",
        "docs/index.md",
        "mkdocs.yml",
        "profiles.yml",
        "pyproject.toml",
        "uv.lock",
    } <= set(marker["rewrite_files"])
