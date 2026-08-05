# Adapter migrations

DuckDB is the default development and CI adapter. Moving to a client warehouse is a coordinated change across the Python dependency, `profiles.yml`, and `.sqlfluff`; changing only one creates a misleading local gate.

The versions below were verified from official package metadata on 2026-08-04 and all admit `dbt-core==1.12.0`. Regenerate and review `uv.lock` after every change.

## Common sequence

1. Create a branch dedicated to the adapter migration.
2. Remove DuckDB and add the pinned client adapter.
3. Replace the `dev` output in `profiles.yml` with environment-backed fields from the adapter’s official documentation.
4. Change `.sqlfluff` `dialect` while retaining `templater = dbt` and `profiles_dir = .`.
5. Run `uv lock`, `just doctor`, and `uv run dbt parse --profiles-dir .`.
6. Test against an approved non-production target.
7. Run `just check`; document any credential-backed integration validation separately.

## Snowflake

```bash
uv remove dbt-duckdb
uv add "dbt-snowflake==1.12.0"
```

Set `type: snowflake` in the profile and `dialect = snowflake` in `.sqlfluff`. Supply account, user/authenticator, role, warehouse, database, and schema through the client’s approved environment and secret manager.

## Databricks

```bash
uv remove dbt-duckdb
uv add "dbt-databricks==1.12.3"
```

Set `type: databricks` and `dialect = databricks`. The published adapter constraint is currently the tightest of the documented set (`dbt-core>=1.11.2,<1.12.1`), so keep Core and the adapter locked together. Use environment-backed host, HTTP path, catalog, schema, and approved authentication.

## BigQuery

```bash
uv remove dbt-duckdb
uv add "dbt-bigquery==1.12.0"
```

Set `type: bigquery` and `dialect = bigquery`. Configure project, dataset, location, and an approved authentication method. Do not commit service-account JSON.

## Postgres

```bash
uv remove dbt-duckdb
uv add "dbt-postgres==1.11.0"
```

Set `type: postgres` and `dialect = postgres`. Supply hostname, port, user, password, database, schema, and TLS settings through approved configuration.

## Reverting to credential-free development

If the client adapter cannot run in untrusted pull-request CI, retain a separate DuckDB-compatible check only when project SQL semantics remain comparable. Otherwise state the coverage gap and require an approved credential-backed job; do not imply that a DuckDB pass proves warehouse-specific behavior.
