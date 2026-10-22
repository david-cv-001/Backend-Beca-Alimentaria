# 0002 - Multitenant Isolation by Discriminator

- Status: Accepted
- Date: 2026-10-21

## Context
Data leakage between cafeterias/tenants is a critical security issue. Same principle as PLD: isolation must be automatic, not manual in every query.

## Decision
Row-level discriminator `tenant_id` on tenant-scoped tables, applied automatically:
1. `TenantContext` (contextvars) holds current tenant from JWT claim `organization`
2. SQLAlchemy session uses loader criteria to filter all tenant-scoped queries
3. All inserts must set `tenant_id`
4. Fail-closed: if no tenant in context, return nothing
5. Uniqueness constraints must be scoped by `tenant_id` where appropriate
6. Native queries MUST filter by `tenant_id` explicitly

SUPER_ADMIN may operate across tenants (no organization claim) but must be handled explicitly.

## Consequences
- Isolation is a property of data access, not discipline
- Native queries are the exception and must be reviewed carefully
- Async work must propagate context
