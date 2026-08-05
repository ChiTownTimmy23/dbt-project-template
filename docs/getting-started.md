# Getting started

## 1. Install host tools

Install [uv](https://docs.astral.sh/uv/getting-started/installation/) and [just](https://just.systems/man/en/chapter_4.html). Git is required. uv installs the Python version declared in `.python-version` when needed.

## 2. Clone and initialize

```bash
git clone https://github.com/ChiTownTimmy23/dbt-project-template.git client-project
cd client-project
just init client_project "Client Project"
```

The dbt identifier must match `^[a-z][a-z0-9_]*$`. Initialization rewrites only the allowlist in `.template-state.json`, then removes that marker so the operation cannot be repeated accidentally.

Use `--remove-example` to remove the listed sample DAG files. Initialization refuses a dirty Git worktree unless `--allow-dirty` is passed deliberately.

## 3. Bootstrap

```bash
just setup
just doctor
```

`just setup` runs `uv sync --locked` and installs the repository hooks. `just doctor` checks tools, `.venv`, the DuckDB profile, Git, and relevant environment state without displaying secret values.

## 4. Prove the project

```bash
just demo
just check
```

`just demo` seeds and builds into the ignored `target/dev.duckdb`. `just check` repeats the full contract used by GitHub Actions.

## Troubleshooting

| Symptom | Action |
|---|---|
| `uv` or `just` is missing | Install the tool linked above, then rerun `just doctor`. |
| Lockfile is stale | Review dependency changes, run `uv lock`, and commit `pyproject.toml` with `uv.lock`. |
| DuckDB file is locked | Stop other processes using the file or set `DBT_DUCKDB_PATH` to a separate path. |
| SQLFluff cannot compile | Run `uv run dbt parse --profiles-dir .` first; fix dbt/profile errors before linting. |
| Initializer reports a dirty tree | Commit or stash intended changes; use `--allow-dirty` only when you want them included in the rename diff. |
