# Security Policy

## Credentials and client data

This repository is designed to run without credentials. Never commit client data, passwords, tokens, private keys, service-account material, populated `.env` files, or client-specific profiles.

Use environment variables or an approved secret manager for warehouse credentials. Keep local overrides in ignored files. `just doctor` reports whether relevant variables are set but redacts sensitive values.

## Reporting a vulnerability

Use GitHub private vulnerability reporting for the repository. Do not open a public issue containing an exploit, credential, or client detail. Rotate any exposed credential before continuing investigation.
