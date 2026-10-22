# Conventions

## Golden rule
> A layer earns the right to exist by solving a problem you already have. Not because it appears in a diagram.

Bias towards removing, not adding. Ask: "What problem does this layer solve today?" If answer is "good practice", it is probably unnecessary.

## What we do NOT do
| Pattern | Why not |
| --- | --- |
| `XService` + `XServiceImpl` | Interface with single implementation is extra indirection. Add interface only when second implementation exists |
| `domain/`, aggregates, value objects as folders | Business vocabulary goes in class/method names, not in rigid hierarchies |
| Hexagonal/ports-adapters | Indirection paid on every read. No need to swap DB |
| Own exception hierarchy | Use shared base exceptions; keep single handler |
| Separate `validation/` layer | If model validates with annotations, separate layer drifts |
| Overloaded methods "for flexibility" | More signatures = more paths to test |

## Non-negotiable rules
- **Constructor injection** with `Depends()` in FastAPI or explicit deps. No field injection.
- **Pydantic models** for DTOs/requests/responses. Keep input models mutable where appropriate, output models can be frozen.
- **Never use `@Data` equivalent** - be explicit. Never put `equals/hashCode` logic on ORM entities.
- **Never concatenate in logs**. Use structured logging with key-value pairs.
- **No wildcard imports**.
- **No magic numbers/strings** outside named constants.
- **Javadoc/docstring for contract, not the obvious**.

## Naming
| Type | Pattern | Example |
| --- | --- | --- |
| Router | `<Resource>Router` or just router in module | `tenants/router.py` |
| Service | `<Resource>Service` | `TenantService` |
| ORM Model | `<Name>Model` or `<Name>` | `Tenant` |
| Schema/DTO (out) | `<Name>Response` or `<Name>Dto` | `TenantResponse` |
| Schema/Request (in) | `<Action><Name>Request` | `CreateTenantRequest` |
| Repository | `<Resource>Repository` | `TenantRepository` |
| Exception | `<Situation>Exception` | `DuplicateTenantException` |

## Method verbs
| Verb | Contract |
| --- | --- |
| `find_*` | May not find → `None` or empty list |
| `get_*` | Exists or raises |
| `find_all_*` | Collection, possibly empty, never `None` |
| `exists_*` / `is_*` | `bool` |
| `create_*` / `update_*` | Mutates state |
| `validate_*` | Raises if invalid, does not return `bool` |
| `calculate_*` | Pure computation |

## Responsibility split
```
HTTP (Router/Depends)
  └→ Service (business rules, transactions)
      └→ Repository (data access)
```

- **Router**: validate input, build filters/pagination, call service, return response. No business rules.
- **Service**: business rules, orchestration. Must not build HTTP responses.
- **Repository**: queries only.
- **Service raises exceptions; error handlers translate to status codes.**

## Adding a new resource
1. **Migration (Alembic)** - schema only via migrations
2. **ORM model** - extend audit mixin if needed, add `tenant_id` with tenant scoping for tenant-scoped data
3. **Schemas** (Pydantic) - request/response/dto
4. **Repository**
5. **Service**
6. **Router**
7. **Exceptions** if needed
8. **Tests** - unit + integration

## Testing requirements
- All business rules with `if` must be tested
- All tenant isolation must be tested against real Postgres
- All calculations must be tested
- Every error code the frontend will handle (400,401,403,404,409) must be covered

## Logging
- Message in prose + key-value pairs: `log.info("Tenant created tenant_id=%s code=%s", tenant_id, code)`
- Never log tokens, passwords, keys, Authorization headers
- Never log PII (rfc, curp, full names, emails, phones, addresses). Log internal IDs only
- Never log full request/response bodies
- `info`: matters to someone not actively debugging. `debug`: for debugging. `error`: with exception attached
- In `except`: either log or re-raise, never both

## Git
- Conventional commits: `feat(tenants): ...`, `fix(auth): ...`, `docs(adr): ...`
- One commit, one change
- Explain *why*, not *what* (diff shows what)
- No AI attribution in commits/PRs
