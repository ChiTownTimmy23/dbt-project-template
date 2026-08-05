# dbt Project Template

This handbook explains how to take the repository from a fresh clone to a verified client project while preserving one local/CI quality contract.

## Golden path

```bash
just init client_project "Client Project"
just setup
just demo
just check
```

The uninitialized template is also executable. DuckDB keeps the first run credential-free, and the sample DAG proves the repository before client-specific changes begin.

## Operating principles

- Keep raw-source cleanup in staging, reusable transformations in intermediate, and business-facing entities in marts.
- Represent source money as integer minor units and convert at the contracted mart boundary.
- Add tests and documentation in the same change as a model.
- Treat `just check` as the minimum merge gate.
- Change the dbt adapter, profile, and SQLFluff dialect as one coordinated migration.
- Keep credentials and client data outside Git.

Continue with [getting started](getting-started.md) or the [client onboarding checklist](client-onboarding.md).
