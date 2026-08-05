# Architecture and conventions

## Data flow

```text
CSV seeds → sources → staging views → intermediate ephemeral model → contracted mart tables
```

### Staging

One staging model maps to one source relation. Rename fields, cast types, and perform light source cleanup here. Do not encode business aggregation in staging.

### Intermediate

Intermediate models make reusable transformations legible. The sample customer-order aggregation demonstrates a stable grain, left-join behavior for customers without orders, and completed-order value measured in integer cents.

### Marts

Marts expose business-facing entities and enforce contracts. Every contracted column has a declared warehouse type. Monetary values convert from integer cents to fixed-decimal major units here.

## Model requirements

- Use `source()` for raw relations and `ref()` for all model dependencies.
- Name staging models `stg_<source_entity>` and intermediate models `int_<purpose>`.
- Use `dim_` and `fct_` prefixes for dimensional marts when that semantic model fits.
- Document every model and every contracted column.
- Add `not_null` and `unique` tests for declared grains.
- Use relationship and accepted-value tests where the source contract supports them.
- Add a dbt unit test for transformation logic with meaningful branching.
- Keep singular tests focused on invariants that generic tests cannot express clearly.

## Runtime boundary

The repository profile writes to `target/dev.duckdb`. Generated data, logs, packages, docs output, virtual environments, local profiles, and `.env` files are ignored. CI uses the same profile and requires no external credentials.

The rationale is recorded in [ADR 0001](decisions/0001-duckdb-first.md).
