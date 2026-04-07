# Hook Template

## Structure

```typescript
/**
 * {hookName} — {description}
 *
 * {Story/AC reference}
 */

import { useState, useEffect, useCallback } from 'react';
import { supabase } from '../../lib/supabase';

interface {HookName}Return {
  // State
  data: {DataType} | null;
  isLoading: boolean;
  error: string | null;
  // Actions
  execute: (params: {Params}) => Promise<{ success: boolean; error?: string }>;
  refetch: () => void;
}

export function {hookName}(): {HookName}Return {
  const [data, setData] = useState<{DataType} | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Fetch on mount
  useEffect(() => {
    let cancelled = false;
    async function fetch() {
      // auth check + query
    }
    fetch();
    return () => { cancelled = true; };
  }, []);

  // Realtime subscription (if needed)
  useEffect(() => {
    const channel = supabase
      .channel('{channel-name}')
      .on('postgres_changes', { event: '*', schema: 'public', table: '{table}' }, () => {
        refetch();
      })
      .subscribe();
    return () => { supabase.removeChannel(channel); };
  }, []);

  const execute = useCallback(async (params: {Params}) => {
    // mutation logic
  }, []);

  const refetch = useCallback(() => {
    // re-fetch logic
  }, []);

  return { data, isLoading, error, execute, refetch };
}
```

## Conventions

- Name: `use{Action}{Entity}` (e.g. `usePlaceBid`, `useRespondToCounterOffer`)
- Auth check at start of every mutation
- Error messages in user's language
- Cleanup subscriptions on unmount
- Use `useCallback` for all exposed functions
