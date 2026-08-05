# Client onboarding checklist

This is a technical starter checklist, not a substitute for client security, legal, or data-governance approval.

## Repository identity

- [ ] Clone from the template into the approved client repository location.
- [ ] Run `just init <project_name> "<Friendly Name>"` once.
- [ ] Inspect the rename diff and commit it before adding client-specific work.
- [ ] Decide whether to retain or remove the sample DAG.

## Access and security

- [ ] Confirm the approved identity provider, service-account owner, and least-privilege roles.
- [ ] Put credentials in the approved secret manager or CI environment, never in Git.
- [ ] Confirm that `.env`, local profiles, generated databases, and client extracts remain ignored.
- [ ] Record data classification, retention, and deletion requirements.

## Warehouse migration

- [ ] Follow the [adapter migration guide](adapter-migrations.md).
- [ ] Pin the adapter version and regenerate `uv.lock`.
- [ ] Replace the DuckDB output with environment-backed connection fields.
- [ ] Change the SQLFluff dialect in the same commit.
- [ ] Add a credential-backed integration job only in the client-controlled CI environment.

## Modeling

- [ ] Inventory sources, owners, freshness expectations, grains, keys, and units.
- [ ] Replace sample sources with source declarations for approved data.
- [ ] Preserve staging → intermediate → marts boundaries unless an architecture decision records an exception.
- [ ] Add model/column documentation, grain tests, relationships, and business invariants.
- [ ] Distinguish source facts from modeling assumptions in documentation.

## Release gate

- [ ] Run `just doctor`.
- [ ] Run `just check` locally.
- [ ] Verify CI runs `just check` on the exact commit under review.
- [ ] Record any warehouse-specific validation that credential-free CI cannot reproduce.
