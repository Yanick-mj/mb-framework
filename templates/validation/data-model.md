# Data Model Validation Checklist

## Table Design
- [ ] Table name is plural, snake_case
- [ ] Primary key is UUID with gen_random_uuid()
- [ ] created_at and updated_at columns present
- [ ] Foreign keys have ON DELETE policy (CASCADE, SET NULL, or RESTRICT)
- [ ] UNIQUE constraints where needed
- [ ] CHECK constraints for enums/status fields

## RLS
- [ ] RLS enabled on table
- [ ] Policy for each role (driver, dealer, admin)
- [ ] SELECT policy exists
- [ ] INSERT/UPDATE policies use WITH CHECK
- [ ] No policy allows unrestricted access

## Indexes
- [ ] Primary key indexed (automatic)
- [ ] Foreign keys indexed
- [ ] Frequently filtered columns indexed
- [ ] Composite index for multi-column queries
- [ ] No unnecessary indexes (write overhead)

## Data Integrity
- [ ] NOT NULL on required columns
- [ ] DEFAULT values where appropriate
- [ ] No orphan records possible (FK constraints)
- [ ] Soft delete vs hard delete decision documented

## Naming
- [ ] Column names are snake_case
- [ ] Boolean columns prefixed with is_/has_
- [ ] Timestamp columns suffixed with _at
- [ ] Status columns use CHECK constraint with explicit values
