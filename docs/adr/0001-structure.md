# 0001 - Modular Feature-First Structure

- Status: Accepted
- Date: 2026-10-21

## Context
We need a maintainable structure that is easy to extend (tenants, users, students, biometrics, attendance). Coming from Spring Boot layered structure, we need Python equivalent that matches our conventions.

## Decision
Use feature-first modules under `app/modules/`:
- Each module contains: `models.py`, `schemas.py`, `repository.py`, `service.py`, `router.py` as needed
- Shared concerns live in `app/core/`, `app/db/`, `app/shared/`
- Flow: Router -> Service -> Repository (same responsibility split as PLD)

## Consequences
- Better cohesion per feature
- Easier to understand and test
- Avoids giant global `services/`/`controllers/` folders
- Imports stay clear
