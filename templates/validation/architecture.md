# Architecture Validation Checklist

## Design Decisions
- [ ] Each decision has a "why" (not just "what")
- [ ] Alternatives considered and documented
- [ ] Trade-offs explicit
- [ ] Reversibility assessed

## Separation of Concerns
- [ ] Clear boundaries between layers (UI, business logic, data)
- [ ] No business logic in UI components
- [ ] No database queries in UI components
- [ ] Shared types in dedicated package

## Security
- [ ] Authentication required for all non-public endpoints
- [ ] Authorization checked (role-based)
- [ ] Input validation at system boundaries
- [ ] No secrets in code or config files
- [ ] RLS enabled on all tables

## Scalability
- [ ] Stateless where possible
- [ ] Database queries optimized (indexes, pagination)
- [ ] No N+1 queries
- [ ] Cache strategy for hot data

## Maintainability
- [ ] Consistent patterns across codebase
- [ ] Dependencies justified
- [ ] No circular dependencies
- [ ] Error handling strategy consistent
