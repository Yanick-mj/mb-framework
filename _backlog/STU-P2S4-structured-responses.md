---
story_id: STU-P2S4.4
title: Structured chat responses
priority: medium
status: todo
created: 2026-05-05
assignee: be-dev
sprint: phase2-sprint4
parent_story: STU-P2S4.3
---

# Structured chat responses

## Why

Raw LLM text is fine for open questions, but status queries should return formatted, scannable output — not paragraphs.

## Scope

**In:**
- Prompt engineering: instruct Claude to use markdown formatting
- Status queries → bullet lists with emoji indicators
- Metrics queries → inline numbers/percentages
- Frontend: render markdown in chat bubbles (lightweight parser)

**Out:**
- Charts or visualizations in chat (text only)
- Interactive elements in responses (buttons come in Sprint 5)

## Acceptance criteria

- [ ] "État du sprint" → bulleted list with story counts + emojis
- [ ] "Qu'est-ce qui bloque ?" → numbered list of blockers with story IDs
- [ ] Markdown rendered in assistant bubbles (bold, lists, code)
- [ ] Responses are concise (< 200 words for status queries)
- [ ] French and English questions both work

## Tech requirements

- **Prompt tuning:** system prompt instructs format (bullets, concise, emoji)
- **Markdown render:** `marked.js` (CDN, 8kb) or server-side `mistune`
- **Sanitization:** strip HTML from LLM output (prevent XSS)
- **Language:** system prompt in French (project language)

## Designer requirements

- Markdown in bubbles: consistent font, proper list indentation
- Code blocks in bubbles: dark background, monospace
- Emoji: used as status indicators (✅ 🟡 🔴 🚧)
- Bubble max-width: 85% of panel width (readable line length)

## TDD

```python
# tests/dashboard/test_structured_responses.py

def test_status_query_returns_formatted():
    """'État du sprint' → response has bullet points"""

def test_blocker_query_lists_stories():
    """'Qu'est-ce qui bloque' → response mentions blocked story IDs"""

def test_response_under_200_words():
    """Status query response word count < 200"""

def test_markdown_rendered_in_ui(page):
    """Bold text in response → <strong> in DOM"""

def test_xss_stripped():
    """If LLM returns <script> → stripped from rendered output"""
```
