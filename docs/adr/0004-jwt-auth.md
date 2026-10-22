# 0004 - JWT Authentication in App

- Status: Accepted
- Date: 2026-10-21

## Context
Requirements specify JWT authentication with roles. PLD uses Keycloak, but for this project we start with app-managed JWT for simplicity and direct mapping to `users` table.

## Decision
Use PyJWT + pwdlib (argon2) for password hashing and token creation/validation. Users stored in DB with role and tenant_id. Token must include tenant context where applicable.

## Consequences
- Full control over auth model
- Direct integration with tenant isolation
- Can migrate to Keycloak later if needed
