# 0003 - Alembic as Single Source of Schema

- Status: Accepted
- Date: 2026-10-21

## Context
Schema must be version controlled and reproducible across environments.

## Decision
Use Alembic for all schema changes. No manual DDL outside migrations. Enable pgvector extension via migration if needed.

## Consequences
- Consistent schema
- Easy rollback/upgrade
- Reviewable schema changes
