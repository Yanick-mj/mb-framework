# Migration Template

## Naming

`{NNN}_{description_snake_case}.sql`

Number must be sequential (check existing migrations).

## Structure

```sql
-- {NNN}: {Description}
-- {Why this migration exists}

-- 1. New tables
CREATE TABLE IF NOT EXISTS public.{table_name} (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  -- columns
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- 2. Indexes
CREATE INDEX IF NOT EXISTS idx_{table}_{column} ON public.{table_name}({column});

-- 3. RLS
ALTER TABLE public.{table_name} ENABLE ROW LEVEL SECURITY;

CREATE POLICY "{description}" ON public.{table_name}
  FOR {ALL|SELECT|INSERT|UPDATE|DELETE}
  USING ({condition});

-- 4. Triggers (if needed)
CREATE OR REPLACE FUNCTION public.{function_name}()
RETURNS TRIGGER AS $$
BEGIN
  -- logic
  RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

CREATE TRIGGER trg_{name}
  {BEFORE|AFTER} {INSERT|UPDATE|DELETE} ON public.{table_name}
  FOR EACH ROW
  EXECUTE FUNCTION public.{function_name}();
```

## Conventions

- Always enable RLS on new tables
- Use `SECURITY DEFINER` for triggers that need elevated access
- Use `FOR UPDATE SKIP LOCKED` for concurrent operations
- Add indexes for frequently queried columns
- Comment the "why", not the "what"
