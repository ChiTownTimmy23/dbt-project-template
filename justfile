set dotenv-load := true
set shell := ["bash", "-euo", "pipefail", "-c"]

default: list

# Show the available project commands.
list:
    @just --list

# Verify host prerequisites without installing global software.
_require-host:
    @command -v uv >/dev/null || { echo "uv is required: https://docs.astral.sh/uv/" >&2; exit 1; }
    @command -v just >/dev/null || { echo "just is required: https://just.systems/" >&2; exit 1; }

# Synchronize the exact locked environment and install Git hooks.
setup: _require-host
    uv sync --locked
    @if git rev-parse --git-dir >/dev/null 2>&1; then uv run pre-commit install; fi
    @echo "Environment ready. Run 'just demo', then 'just check'."

# Diagnose host tools, environment, profile, and Git state.
doctor:
    uv run python scripts/doctor.py

# Seed and build the complete sample project.
demo:
    uv run dbt seed --profiles-dir . --full-refresh
    uv run dbt build --profiles-dir .

# Run Python and repository contract tests.
test:
    uv run pytest
    uv run ruff check scripts tests

# Lint all dbt-aware SQL.
lint:
    uv run sqlfluff lint models analyses tests

# Apply safe SQLFluff fixes; review the resulting diff.
format:
    uv run sqlfluff fix models analyses tests

# Parse, seed, build, and retest the dbt project.
dbt-check:
    uv run dbt parse --profiles-dir .
    uv run dbt seed --profiles-dir . --full-refresh
    uv run dbt build --profiles-dir .
    uv run dbt test --profiles-dir .

# Verify the committed uv lockfile is current.
lock-check:
    uv lock --check

# Build the operating handbook with strict link/navigation checks.
docs:
    uv run mkdocs build --strict

# Serve the operating handbook locally.
docs-serve:
    uv run mkdocs serve

# Run the exact quality gate used by CI.
check: lock-check test dbt-check lint docs

# Initialize a client project, passing all user input as shell-safe positional arguments.
[positional-arguments]
init project_name friendly_name *flags:
    uv run python scripts/init_project.py "$@"

# Remove only generated paths declared by dbt_project.yml.
clean:
    uv run dbt clean
