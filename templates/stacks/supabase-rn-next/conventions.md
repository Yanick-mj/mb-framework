# Supabase + React Native + Next.js — Conventions

## Naming
- Files: camelCase for hooks/utils, PascalCase for components
- Hooks: `use{Action}{Entity}` (e.g. `usePlaceBid`)
- Components: `{Entity}{Action}` (e.g. `BidStatusBadge`)
- Migrations: `{NNN}_{description_snake_case}.sql`
- Edge functions: `kebab-case/index.ts`

## Imports
- Absolute imports with `@/` alias in web
- Relative imports in mobile
- Shared types: `import type { X } from '@project/types'`

## State Management
- Server state: Supabase realtime subscriptions
- Client state: React useState/useReducer
- No global state library unless needed

## API Pattern
- Mobile: Supabase client direct (hooks call supabase.from/rpc)
- Web: Service layer (lib/services/) wraps Supabase calls
- Shared: RPC functions for atomic operations

## Error Handling
- User-facing: French messages
- Logs: English
- Pattern: try/catch → map to user message → return {success, error}

## Testing
- Unit: Jest + React Testing Library
- Integration: Real Supabase (test project)
- E2E: Playwright (web) / Detox (mobile, if needed)
