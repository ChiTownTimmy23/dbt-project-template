# ADR 0001: DuckDB-first local and CI execution

## Status

Accepted.

## Context

The repository must work immediately after cloning across client environments. A warehouse-specific default would require credentials before the template itself could be proven, while a fully adapter-agnostic SQLFluff configuration is not possible because SQLFluff requires a dialect.

## Decision

Use DuckDB as the default dbt adapter, local database, and CI execution target. Keep the profile in the repository, write generated data under `target/`, and document client adapters as coordinated dependency/profile/dialect migrations.

## Consequences

- A fresh clone can seed, build, test, and lint without external services.
- Local and CI commands remain identical.
- DuckDB results do not prove warehouse-specific SQL, permissions, performance, or incremental behavior.
- Client migrations require an additional approved integration environment and explicit comparability caveats.
