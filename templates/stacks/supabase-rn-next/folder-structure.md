# Supabase + React Native + Next.js — Folder Structure

```
project/
├── apps/
│   ├── mobile/              # React Native (Expo)
│   │   ├── src/
│   │   │   ├── components/  # UI components by domain
│   │   │   ├── hooks/       # Custom hooks by domain
│   │   │   ├── screens/     # Screen components
│   │   │   ├── navigation/  # React Navigation config
│   │   │   ├── lib/         # Utilities, services, constants
│   │   │   └── __tests__/   # Tests mirror src structure
│   │   └── app.json         # Expo config
│   └── web/                 # Next.js
│       ├── src/
│       │   ├── app/         # App Router pages
│       │   ├── components/  # UI components
│       │   ├── hooks/       # Custom hooks
│       │   ├── lib/         # Services, utilities
│       │   ├── types/       # Web-specific types
│       │   └── __tests__/   # Tests
│       └── next.config.js
├── packages/
│   └── types/               # Shared TypeScript types
│       └── src/index.ts
├── supabase/
│   ├── migrations/          # SQL migrations (numbered)
│   ├── functions/           # Edge functions
│   └── seed.sql             # Dev seed data
├── package.json             # Monorepo root (workspaces)
└── turbo.json               # Turborepo config
```
