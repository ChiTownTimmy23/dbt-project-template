# Contributing

## Development workflow

1. Create a focused branch from `main`.
2. Run `just setup`.
3. Add tests before behavior changes.
4. Keep models within the staging → intermediate → marts boundaries documented in `docs/architecture.md`.
5. Run `just check` before opening a pull request.

Do not commit `target/`, `.venv/`, DuckDB databases, local profiles, `.env` files, or credentials. When changing an adapter, update the Python dependency, dbt profile, and SQLFluff dialect together and describe the validation environment in the pull request.

Commit messages should be concise and explain one coherent change. Pull requests should state what changed, why it changed, user impact, and the exact commands used for validation.
