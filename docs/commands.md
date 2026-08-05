# Command reference

`just` is the public interface. CI and developer laptops call the same recipes.

| Recipe | Executes | Mutates |
|---|---|---|
| `just setup` | Host checks, `uv sync --locked`, hook installation | `.venv/`, Git hook |
| `just doctor` | Structured diagnostics with value redaction | Nothing |
| `just demo` | `dbt seed --full-refresh`, then `dbt build` | `target/`, `logs/` |
| `just test` | pytest and Ruff | Test caches only |
| `just dbt-check` | dbt parse, seed, build, and test | DuckDB and dbt artifacts |
| `just lint` | SQLFluff with the dbt templater | dbt/SQLFluff caches only |
| `just format` | SQLFluff fix | SQL files; review the diff |
| `just docs` | strict MkDocs build | `site/` |
| `just docs-serve` | local documentation server | Runtime process |
| `just check` | lock + Python + dbt + SQLFluff + docs | Generated artifacts only |
| `just clean` | dbt clean targets | Only declared generated paths |

## Initialization

```bash
just init project_name "Friendly Name" [--remove-example] [--allow-dirty]
```

The operation is one-time and rewrites only paths listed in `.template-state.json`. It does not delete Git history, install dependencies, or contact a warehouse.

## Direct commands

When diagnosing a failing stage, run its exact underlying command from the `justfile`; for example:

```bash
uv run dbt parse --profiles-dir .
uv run pytest -v
uv run sqlfluff lint models analyses tests
uv run mkdocs build --strict
```

Return to `just check` after the focused issue is corrected.
