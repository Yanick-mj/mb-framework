---
name: 'mb-skill-ux-design'
description: 'UX design principles, patterns, and accessibility guidelines'
when_to_use: 'When implementing UI components, screens, or user-facing features'
---

# UX Design Knowledge

Injectable skill for fe-dev and architect agents.

## Core Principles

1. **Consistency** — Same action = same result everywhere
2. **Feedback** — Every action gets immediate visual feedback
3. **Forgiveness** — Allow undo, confirm destructive actions
4. **Discoverability** — Key actions visible, secondary actions accessible
5. **Accessibility** — WCAG 2.1 AA minimum

## Mobile Patterns

- Bottom sheets for contextual actions (not modals)
- Pull-to-refresh for list views
- Skeleton loaders instead of spinners
- Haptic feedback on important actions
- Safe area insets respected

## Web Patterns

- Responsive breakpoints: mobile (<768), tablet (768-1024), desktop (>1024)
- Loading states on every async action
- Error states with retry option
- Empty states with call-to-action
- Breadcrumbs for navigation depth >2

## Form Design

- Inline validation (on blur, not on change)
- Clear error messages in user's language
- Required fields marked, optional noted
- Smart defaults when possible
- Disable submit during processing

## Color & Contrast

- Text contrast ratio >= 4.5:1 (AA)
- Large text contrast ratio >= 3:1
- Don't rely on color alone (add icons/text)
- Status colors: green=success, red=error, orange=warning, blue=info

## Typography

- Max 2 font families
- Body text: 16px minimum on mobile
- Line height: 1.5 for body, 1.2 for headings
- Max line length: 65-75 characters

$ARGUMENTS
