# dbt Project Template

A clone-and-go, DuckDB-first dbt repository for starting client analytics projects with a reproducible local environment, a documented sample DAG, and one quality gate shared by developers and CI.

## Why this template

- Runs locally and in CI without warehouse credentials.
- Pins dbt Core, dbt-duckdb, SQLFluff, and documentation tooling in `uv.lock`.
- Demonstrates staging → intermediate → marts with tests, contracts, a unit test, and an exposure.
- Uses `just` as the stable command interface.
- Includes a safe, one-time initializer for client project naming.
- Documents coordinated migrations to Snowflake, Databricks, BigQuery, and Postgres.

## Prerequisites

- [Git](https://git-scm.com/)
- [uv](https://docs.astral.sh/uv/getting-started/installation/)
- [just](https://just.systems/man/en/chapter_4.html)

Python is installed and managed by uv from `.python-version`; a separate global Python setup is not required.

## Start a client project

```bash
git clone https://github.com/ChiTownTimmy23/dbt-project-template.git client-project
cd client-project
just init client_project "Client Project"
just setup
just demo
just check
```

Use a lowercase dbt identifier with letters, numbers, and underscores. Add `--remove-example` to `just init` when you want the operating framework without the sample DAG:

```bash
just init client_project "Client Project" --remove-example
```

Initialization refuses a dirty worktree and refuses to run twice. `--allow-dirty` is available for an intentional exception; inspect and commit the resulting diff immediately.

## Daily commands

| Command | Purpose |
|---|---|
| `just doctor` | Check host tools, environment, local profile, and Git state without printing secret values. |
| `just setup` | Synchronize `uv.lock` and install repository pre-commit hooks. |
| `just demo` | Seed and build the complete sample DAG in `target/dev.duckdb`. |
| `just check` | Run the exact lock, Python, dbt, SQLFluff, and MkDocs gate used by CI. |
| `just format` | Apply SQLFluff fixes for review. |
| `just docs` | Build the handbook strictly into `site/`. |
| `just docs-serve` | Serve the handbook locally. |
| `just clean` | Remove only paths declared in `dbt_project.yml` under `clean-targets`. |

Run `just --list` for the complete recipe index.

## Repository shape

```text
seeds/raw_*                  deterministic source fixtures
models/staging/              source-conformed views
models/intermediate/         reusable transformations
models/marts/                contracted business-facing tables
tests/                       singular dbt and Python contract tests
scripts/                     initialization and diagnostics
docs/                        operating handbook and decisions
.github/workflows/ci.yml     credential-free quality gate
```

The repository-local `profiles.yml` defaults to DuckDB at `target/dev.duckdb`. Override the path without editing tracked configuration:

```bash
DBT_DUCKDB_PATH=/absolute/path/development.duckdb just demo
```

Do not commit warehouse credentials or a client-specific `profiles.yml`. See the [client onboarding checklist](docs/client-onboarding.md) and [adapter migration guide](docs/adapter-migrations.md).

## Documentation

The complete operating handbook lives in [`docs/`](docs/index.md). Start with:

- [Getting started](docs/getting-started.md)
- [Architecture and conventions](docs/architecture.md)
- [Command reference](docs/commands.md)
- [Client onboarding](docs/client-onboarding.md)
- [Adapter migrations](docs/adapter-migrations.md)

## License

MIT. See [LICENSE](LICENSE).

