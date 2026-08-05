from __future__ import annotations

import importlib
from pathlib import Path


def load_module():
    spec = importlib.util.find_spec("scripts.doctor")
    assert spec is not None, "scripts.doctor must exist"
    return importlib.import_module("scripts.doctor")


def checks_by_name(results):
    return {result.name: result for result in results}


def write_profile(root: Path, content: str | None = None) -> None:
    (root / "profiles.yml").write_text(
        content
        or (
            "dbt_project_template:\n"
            "  target: dev\n"
            "  outputs:\n"
            "    dev:\n"
            "      type: duckdb\n"
            "      path: target/dev.duckdb\n"
        ),
        encoding="utf-8",
    )


def test_collect_checks_reports_missing_host_tools(tmp_path: Path, monkeypatch) -> None:
    module = load_module()
    write_profile(tmp_path)
    (tmp_path / ".venv").mkdir()
    monkeypatch.setattr(module.shutil, "which", lambda _name: None)

    checks = checks_by_name(module.collect_checks(tmp_path))

    assert not checks["uv"].ok
    assert not checks["just"].ok
    assert "not found" in checks["uv"].detail
    assert "not found" in checks["just"].detail


def test_collect_checks_reports_absent_virtual_environment(tmp_path: Path, monkeypatch) -> None:
    module = load_module()
    write_profile(tmp_path)
    monkeypatch.setattr(module.shutil, "which", lambda name: f"/usr/local/bin/{name}")

    checks = checks_by_name(module.collect_checks(tmp_path))

    assert not checks["virtualenv"].ok
    assert ".venv" in checks["virtualenv"].detail


def test_collect_checks_parses_duckdb_profile(tmp_path: Path, monkeypatch) -> None:
    module = load_module()
    write_profile(tmp_path)
    (tmp_path / ".venv").mkdir()
    monkeypatch.setattr(module.shutil, "which", lambda name: f"/usr/local/bin/{name}")

    valid = checks_by_name(module.collect_checks(tmp_path))
    assert valid["profile"].ok
    assert "duckdb" in valid["profile"].detail

    write_profile(tmp_path, "not: [valid")
    invalid = checks_by_name(module.collect_checks(tmp_path))
    assert not invalid["profile"].ok
    assert "invalid YAML" in invalid["profile"].detail


def test_environment_summary_redacts_sensitive_values() -> None:
    module = load_module()
    environment = {
        "DBT_DUCKDB_PATH": "target/custom.duckdb",
        "API_TOKEN": "super-secret-token",
        "WAREHOUSE_PASSWORD": "correct-horse-battery-staple",
        "PUBLIC_SETTING": "visible-value",
    }

    summary = module.summarize_environment(environment)

    assert "DBT_DUCKDB_PATH=<set>" in summary
    assert "API_TOKEN=<redacted>" in summary
    assert "WAREHOUSE_PASSWORD=<redacted>" in summary
    assert "super-secret-token" not in summary
    assert "correct-horse-battery-staple" not in summary
    assert "visible-value" not in summary
