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
        ".user.yml",
        "profiles.local.yml",
    } <= patterns


def test_sample_dag_has_the_required_layers_and_dependencies() -> None:
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
