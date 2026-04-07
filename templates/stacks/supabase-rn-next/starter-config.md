# Supabase + React Native + Next.js — Starter Config

## Monorepo
- Package manager: Yarn workspaces or pnpm
- Build orchestrator: Turborepo
- TypeScript: Strict mode, shared tsconfig base

## Mobile (Expo)
- SDK: Latest stable
- Navigation: React Navigation v6+
- Build: EAS Build
- OTA: EAS Update

## Web (Next.js)
- App Router (not Pages)
- Server Components by default
- TailwindCSS for styling
- Shadcn/ui for component library

## Supabase
- Auth: Supabase Auth (email + social)
- Database: Postgres with RLS
- Storage: Supabase Storage
- Functions: Deno edge functions
- Realtime: Postgres changes subscriptions

## CI/CD
- GitHub Actions
- Lint + typecheck + test on PR
- Deploy web on merge to main
- EAS Build on tag
