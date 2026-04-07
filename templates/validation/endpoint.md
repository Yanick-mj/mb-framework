# Endpoint Validation Checklist

## Structure
- [ ] RESTful convention (GET /resources, POST /resources, etc.)
- [ ] Consistent with existing endpoints
- [ ] Versioned if public API

## Security
- [ ] Auth required (RLS or middleware)
- [ ] Input validated (zod schema or equivalent)
- [ ] Rate limiting if public
- [ ] No sensitive data in URL params

## Typing
- [ ] Request body typed
- [ ] Response body typed
- [ ] Error responses typed
- [ ] Shared types if cross-app

## Performance
- [ ] Pagination for lists
- [ ] DB indexes on filtered columns
- [ ] Cache headers if appropriate

## Testing
- [ ] Unit test for handler
- [ ] Integration test with DB
- [ ] Error case tests (401, 403, 404, 422)
