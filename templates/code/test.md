# Test Template

## Structure

```typescript
import { renderHook, act } from '@testing-library/react-hooks';
// or for components:
// import { render, screen, fireEvent } from '@testing-library/react-native';

// Mock dependencies
jest.mock('../../lib/supabase', () => ({
  supabase: {
    from: jest.fn(),
    rpc: jest.fn(),
    auth: { getUser: jest.fn() },
    channel: jest.fn(() => ({ on: jest.fn().mockReturnThis(), subscribe: jest.fn() })),
    removeChannel: jest.fn(),
  },
}));

describe('{ModuleName}', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('should {expected behavior}', async () => {
    // Arrange
    // Act
    // Assert
  });

  it('should handle errors gracefully', async () => {
    // Arrange: mock error
    // Act
    // Assert: error state correct
  });
});
```

## Conventions

- Test file next to source: `__tests__/{module}.test.ts`
- Describe block = module name
- Each `it` = one behavior
- Arrange / Act / Assert pattern
- Mock external dependencies (supabase, APIs)
- Test error paths, not just happy paths
