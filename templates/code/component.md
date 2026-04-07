# Component Template

## Structure

```typescript
/**
 * {ComponentName} — {description}
 *
 * {Story/AC reference}
 */

import React from 'react';
import { View, Text, StyleSheet } from 'react-native';
// For web: import from design system

interface {ComponentName}Props {
  // required props first
  // optional props second
}

export function {ComponentName}({ ...props }: {ComponentName}Props) {
  return (
    <View style={styles.container}>
      {/* content */}
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    // use design tokens
  },
});
```

## Conventions

- Named exports (not default)
- Props interface above component
- StyleSheet at bottom of file
- Use design tokens for spacing, colors, typography
- Accessible: proper roles, labels, hit areas
