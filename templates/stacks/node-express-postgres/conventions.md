# Node + Express + PostgreSQL — Conventions

## Naming
- Files: camelCase
- Routes: kebab-case URLs
- Controllers: `{entity}Controller.ts`
- Services: `{entity}Service.ts`

## API Design
- RESTful routes: GET/POST/PUT/DELETE
- Versioned: /api/v1/
- Consistent error format: { error: { code, message } }
- Pagination: ?limit=&offset= or ?cursor=

## Middleware Stack
1. CORS
2. Rate limiting
3. Auth (JWT or session)
4. Input validation (zod)
5. Route handler
6. Error handler

## Database
- Migrations for schema changes (never manual DDL)
- Prepared statements (prevent SQL injection)
- Connection pooling
- Transactions for multi-step operations

## Error Handling
- Custom error classes (NotFoundError, ValidationError, etc.)
- Global error handler middleware
- Never expose stack traces in production

## Testing
- Unit: Jest (mock DB)
- Integration: Supertest + test DB
- Fixtures for test data
