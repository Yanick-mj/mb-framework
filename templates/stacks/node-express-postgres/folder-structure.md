# Node + Express + PostgreSQL — Folder Structure

```
project/
├── src/
│   ├── routes/              # Express route handlers
│   ├── controllers/         # Business logic
│   ├── services/            # Data access layer
│   ├── middleware/           # Auth, validation, error handling
│   ├── models/              # Database models/types
│   ├── utils/               # Helpers
│   ├── config/              # Environment, DB connection
│   └── app.ts               # Express app setup
├── migrations/              # SQL or ORM migrations
├── tests/
│   ├── unit/
│   ├── integration/
│   └── fixtures/
├── package.json
├── tsconfig.json
└── Dockerfile
```
