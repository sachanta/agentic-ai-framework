# End-to-End Testing Plan: Phases 6-7 (Research + Writing)

## Current State

| Component | Backend | Frontend | E2E Ready |
|-----------|---------|----------|-----------|
| Research Agent (Phase 6) | Complete | Complete | Yes |
| Writing Agent (Phase 7) | Complete | Complete | Yes |

---

## Part 1: E2E Testing - Research Agent (Ready Now)

### Prerequisites

```bash
# Terminal 1: Backend
cd backend && source .venv/bin/activate
uvicorn app.main:app --reload --port 8000

# Terminal 2: Frontend
cd frontend && npm run dev

# Required .env
NEWSLETTER_TAVILY_API_KEY=your_key
LLM_PROVIDER=ollama
LLM_DEFAULT_MODEL=llama3
```

### Test Case 1: Platform Health
| Step | Action | Expected |
|------|--------|----------|
| 1 | Navigate to `http://localhost:5173/apps/newsletter` | Page loads |
| 2 | Check sidebar | Shows status: Connected, LLM info |
| 3 | Check agents list | Shows 5 agents, "research" is Active |

### Test Case 2: Topic Research
| Step | Action | Expected |
|------|--------|----------|
| 1 | Type "AI" in Topics, press Enter | Chip appears |
| 2 | Add "machine learning" | Second chip appears |
| 3 | Set Max Results to 5 | Slider moves |
| 4 | Enable "Include AI Summaries" | Toggle is ON |
| 5 | Click "Search for Content" | Loading skeleton appears |
| 6 | Wait 30-60 seconds | Articles appear with scores, summaries |

### Test Case 3: Custom Prompt Research
| Step | Action | Expected |
|------|--------|----------|
| 1 | Clear topics | No chips |
| 2 | Enter custom prompt: "Find quantum computing security news" | Text in textarea |
| 3 | Click "Search for Content" | Returns relevant articles |

### Test Case 4: Cache Verification
| Step | Action | Expected |
|------|--------|----------|
| 1 | Search for ["AI"] | Takes ~30 seconds |
| 2 | Search again for ["AI"] | Instant, shows "Cached: true" |

### Test Case 5: Error Handling
| Scenario | Expected |
|----------|----------|
| Empty topics + empty prompt | Button disabled |
| Invalid Tavily API key | Error alert displayed |
| LLM unavailable | Research works, summaries empty |

---

## Part 2: Missing UI for Phase 7 E2E Testing

To test Writing Agent end-to-end, we need:

| Component | Purpose | Priority |
|-----------|---------|----------|
| Article checkboxes | Select articles for newsletter | P0 |
| SelectedArticles summary | Show selection count | P0 |
| ToneSelector | Choose writing tone | P0 |
| "Generate Newsletter" button | Trigger writing agent | P0 |
| NewsletterPreview | Display generated content | P0 |
| SubjectLinePicker | Select from 5 options | P0 |
| FormatTabs | View HTML/Text/Markdown | P1 |

---

## Part 3: Implementation Plan

### Files to Create

```
frontend/src/components/apps/newsletter/
├── ArticleSelector.tsx      # Checkbox + select all
├── WritingPanel.tsx         # Tone selector + generate button
├── NewsletterPreview.tsx    # Content preview
├── SubjectLinePicker.tsx    # 5 radio options
└── FormatTabs.tsx           # HTML/Text/Markdown tabs

frontend/src/api/apps.ts     # Add writing endpoints
frontend/src/hooks/useNewsletter.ts  # Add writing mutations
frontend/src/types/newsletter.ts     # Add writing types

backend/app/platforms/newsletter/routers/
└── writing.py               # Writing API endpoints
```

### Step 1: Backend - Writing Router

Create `/api/v1/platforms/newsletter/writing/` endpoints:

```python
# backend/app/platforms/newsletter/routers/writing.py
@router.post("/generate")
async def generate_newsletter(request: GenerateRequest):
    """Generate newsletter from selected articles."""
    agent = WritingAgent()
    result = await agent.run({
        "articles": request.articles,
        "tone": request.tone,
        "user_id": request.user_id or "anonymous",
    })
    return result
```

### Step 2: Frontend - Article Selection

Add to ArticleResults.tsx:
- Checkbox on each article card
- "Select All" / "Clear" header buttons
- Selection count badge

### Step 3: Frontend - Writing Panel

Create WritingPanel.tsx:
- Shows when articles selected
- Tone dropdown: Professional | Casual | Formal | Enthusiastic
- "Generate Newsletter" button
- Loading state during generation

### Step 4: Frontend - Newsletter Preview

Create NewsletterPreview.tsx:
- Display generated content
- Subject line radio buttons (5 options)
- Format tabs: HTML | Text | Markdown
- Summary bullets display
- "Download" / "Copy" actions

---

## Part 4: E2E Test Cases After Implementation

### Test Case 6: Full Research → Writing Flow
| Step | Action | Expected |
|------|--------|----------|
| 1 | Search for ["AI", "technology"] | 5+ articles appear |
| 2 | Select 3 articles via checkboxes | "3 selected" shows |
| 3 | Choose tone: "Professional" | Dropdown selection |
| 4 | Click "Generate Newsletter" | Loading spinner |
| 5 | Wait 30-60 seconds | Preview appears |
| 6 | Verify 5 subject lines | Radio buttons visible |
| 7 | Select a subject line | Radio selected |
| 8 | Check HTML tab | Rendered newsletter |
| 9 | Check Text tab | Plain text version |
| 10 | Check Markdown tab | Markdown source |
| 11 | Verify summary bullets | 5-6 bullets shown |

### Test Case 7: Tone Variations
| Tone | Expected Style |
|------|---------------|
| Professional | Formal language, no emojis |
| Casual | Conversational, contractions |
| Formal | Academic tone, structured |
| Enthusiastic | Energetic, exclamation marks |

### Test Case 8: Error Scenarios
| Scenario | Expected |
|----------|----------|
| No articles selected | Button disabled |
| LLM fails mid-generation | Error message + retry option |
| Timeout (>5 min) | Timeout error displayed |

---

## Part 5: API Contracts

### Generate Newsletter
```bash
POST /api/v1/platforms/newsletter/writing/generate
Content-Type: application/json

{
  "articles": [
    {"title": "...", "source": "...", "content": "...", "summary": "..."}
  ],
  "tone": "professional",
  "user_id": "user123"
}
```

### Response
```json
{
  "success": true,
  "newsletter": {
    "content": "# Weekly AI Digest...",
    "word_count": 850
  },
  "subject_lines": [
    {"text": "AI Revolution: What You Need to Know", "style": "curiosity"},
    {"text": "3 AI Breakthroughs Changing Everything", "style": "benefit"},
    {"text": "This Week in AI: Top Stories", "style": "informative"},
    {"text": "Is AI Ready to Transform Your Work?", "style": "question"},
    {"text": "AI Trends Defining 2024", "style": "trend"}
  ],
  "summary": {
    "bullets": [
      "AI is transforming healthcare diagnostics",
      "New models achieve 95% accuracy",
      "Privacy concerns remain a challenge"
    ]
  },
  "formats": {
    "html": "<html>...</html>",
    "text": "Weekly AI Digest...",
    "markdown": "# Weekly AI Digest..."
  },
  "metadata": {
    "article_count": 3,
    "topics": ["AI", "technology"],
    "tone": "professional",
    "generated_at": "2024-01-15T10:30:00Z"
  }
}
```

---

## Implementation Order

| Day | Task | Files |
|-----|------|-------|
| 1 | Backend writing router | `routers/writing.py`, `router.py` |
| 2 | Frontend API + types | `api/apps.ts`, `types/newsletter.ts`, `useNewsletter.ts` |
| 3 | Article selection UI | `ArticleResults.tsx`, `WritingPanel.tsx` |
| 4 | Newsletter preview | `NewsletterPreview.tsx`, `SubjectLinePicker.tsx`, `FormatTabs.tsx` |
| 5 | Integration + testing | E2E manual tests |

---

## Appendix: UI Wireframes

### Article Selection
```
┌─────────────────────────────────────────────────────┐
│ Results: 5 articles  │ ☑ Select All │ [Clear]      │
├─────────────────────────────────────────────────────┤
│ ☑ │ AI Breakthrough in Healthcare     │ Score: 92% │
│ ☐ │ ML Trends 2024                    │ Score: 85% │
│ ☑ │ Deep Learning Advances            │ Score: 88% │
└───┴───────────────────────────────────┴────────────┘
```

### Writing Panel (appears when articles selected)
```
┌─────────────────────────────────────────────────────┐
│ Generate Newsletter                                 │
│                                                     │
│ Selected: 3 articles                                │
│ Tone: [Professional ▼]                              │
│                                                     │
│         [ Generate Newsletter ]                     │
└─────────────────────────────────────────────────────┘
```

### Newsletter Preview
```
┌─────────────────────────────────────────────────────┐
│ Newsletter Generated                   [Regenerate] │
├─────────────────────────────────────────────────────┤
│ Choose Subject Line:                                │
│ ○ "AI Revolution: What You Need to Know"           │
│ ● "3 AI Breakthroughs Changing Everything"         │
│ ○ "This Week in AI: Top Stories"                   │
├─────────────────────────────────────────────────────┤
│ [HTML] [Text] [Markdown]                            │
│ ┌─────────────────────────────────────────────────┐ │
│ │  <Rendered newsletter content>                  │ │
│ └─────────────────────────────────────────────────┘ │
├─────────────────────────────────────────────────────┤
│ Summary:                                            │
│ • AI transforms healthcare diagnostics              │
│ • New models achieve 95% accuracy                   │
│ • Privacy concerns remain                           │
├─────────────────────────────────────────────────────┤
│        [ Copy ]  [ Download ]                       │
└─────────────────────────────────────────────────────┘
```
