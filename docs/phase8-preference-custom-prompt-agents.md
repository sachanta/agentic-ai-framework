# Phase 8: Preference & Custom Prompt Agents

## Status: Not Started

## Overview

Phase 8 implements two personalization agents:
1. **Preference Agent** - Manages user preferences and learns from behavior
2. **Custom Prompt Agent** - Processes natural language requests into structured parameters

These agents run at the start of newsletter generation to personalize the experience.

---

## Architecture

```
User Request
    │
    ├─→ Has preferences? ─→ Preference Agent ─→ Load preferences
    │                                              │
    ├─→ Has custom prompt? ─→ Custom Prompt Agent ─→ Extract parameters
    │                                              │
    └───────────────────┬──────────────────────────┘
                        │
                        ▼
              Combined Parameters
                        │
                        ▼
              Research Agent (Phase 6)
                        │
                        ▼
              Writing Agent (Phase 7)
```

---

## Files to Create

```
backend/app/platforms/newsletter/agents/preference/
├── __init__.py           # Exports
├── agent.py              # PreferenceAgent class
├── llm.py                # get_preference_llm()
├── prompts.py            # Preference analysis prompts
└── schemas.py            # UserPreferences, PreferenceUpdate

backend/app/platforms/newsletter/agents/custom_prompt/
├── __init__.py           # Exports
├── agent.py              # CustomPromptAgent class
├── llm.py                # get_custom_prompt_llm()
├── prompts.py            # NLP extraction prompts
└── schemas.py            # PromptAnalysis, ExtractedParameters

backend/app/platforms/newsletter/routers/
└── preferences.py        # Preference API endpoints

backend/app/platforms/newsletter/tests/phase8/
├── test_preference_agent.py
├── test_preference_llm.py
├── test_preference_prompts.py
├── test_custom_prompt_agent.py
├── test_custom_prompt_llm.py
└── test_custom_prompt_prompts.py

frontend/src/components/apps/newsletter/
├── PreferencesPanel.tsx  # User preference settings
└── PromptInput.tsx       # Enhanced prompt input with suggestions
```

---

## Part 1: Preference Agent

### Schemas

```python
# schemas.py
class UserPreferences(BaseModel):
    user_id: str
    topics: List[str] = []                    # Interested topics
    tone: str = "professional"                 # Preferred tone
    frequency: str = "weekly"                  # Newsletter frequency
    max_articles: int = 10                     # Articles per newsletter
    include_summaries: bool = True             # AI summaries
    include_mindmap: bool = True               # Visual mindmap
    sources_blacklist: List[str] = []          # Blocked sources
    sources_whitelist: List[str] = []          # Preferred sources
    language: str = "en"                       # Content language
    created_at: datetime
    updated_at: datetime

class PreferenceUpdate(BaseModel):
    topics: Optional[List[str]] = None
    tone: Optional[str] = None
    frequency: Optional[str] = None
    # ... other optional fields

class EngagementData(BaseModel):
    newsletter_id: str
    opened: bool = False
    clicked_links: List[str] = []
    read_time_seconds: int = 0
    rating: Optional[int] = None  # 1-5
```

### Agent Methods

```python
class PreferenceAgent(BaseAgent):
    async def run(self, input: Dict) -> Dict:
        """Main entry point - routes to appropriate method."""

    async def get_preferences(self, user_id: str) -> UserPreferences:
        """Get user preferences with defaults fallback."""

    async def update_preferences(
        self, user_id: str, updates: PreferenceUpdate
    ) -> UserPreferences:
        """Update specific preference fields."""

    async def analyze_preferences(self, user_id: str) -> Dict:
        """Analyze preference patterns and engagement."""

    async def recommend_preferences(self, user_id: str) -> List[Dict]:
        """Suggest preference changes based on behavior."""

    async def learn_from_engagement(
        self, user_id: str, engagement: EngagementData
    ) -> None:
        """Update preferences based on engagement signals."""
```

### Storage

Uses Memory Service (Phase 5) for persistence:
- Key pattern: `preferences:{user_id}`
- TTL: None (permanent storage)
- Uses MongoDB directly for complex queries

### Prompts

```python
ANALYZE_PREFERENCES_PROMPT = """
Analyze the user's newsletter preferences and engagement history.

User Preferences:
{preferences}

Recent Engagement (last 10 newsletters):
{engagement_history}

Provide insights on:
1. Most engaging topics (by click rate)
2. Optimal newsletter length
3. Best performing tone
4. Recommended schedule
5. Topics to consider adding/removing

Return as JSON:
{
  "insights": [...],
  "recommendations": [...],
  "confidence_score": 0.0-1.0
}
"""
```

---

## Part 2: Custom Prompt Agent

### Schemas

```python
# schemas.py
class PromptAnalysis(BaseModel):
    original_prompt: str
    intent: str                    # research, summarize, analyze, compare
    topics: List[str]              # Extracted topics
    tone: Optional[str]            # Detected tone preference
    constraints: Dict[str, Any]    # Length, format, etc.
    focus_areas: List[str]         # Specific aspects to focus on
    exclusions: List[str]          # Things to avoid
    confidence: float              # 0.0-1.0

class ExtractedParameters(BaseModel):
    topics: List[str]
    tone: str = "professional"
    max_articles: int = 10
    max_word_count: Optional[int] = None
    focus_areas: List[str] = []
    time_range_days: int = 7
    source_preferences: List[str] = []
```

### Agent Methods

```python
class CustomPromptAgent(BaseAgent):
    async def run(self, input: Dict) -> Dict:
        """Main entry point - full NLP pipeline."""

    async def analyze_prompt(self, prompt: str) -> PromptAnalysis:
        """Extract intent and parameters from natural language."""

    async def enhance_prompt(
        self, prompt: str, user_preferences: UserPreferences
    ) -> str:
        """Enhance prompt with user context."""

    async def generate_parameters(
        self, analysis: PromptAnalysis
    ) -> ExtractedParameters:
        """Convert analysis to research/writing parameters."""

    async def validate_parameters(
        self, params: ExtractedParameters
    ) -> Tuple[bool, List[str]]:
        """Validate extracted parameters, return errors if any."""
```

### NLP Pipeline

```
User Prompt
    │
    ▼
1. Analyze Intent
   - What does the user want? (research, summarize, compare)
   - Extract key entities (topics, sources, constraints)
    │
    ▼
2. Extract Parameters
   - Topics: ["AI", "healthcare"]
   - Tone: "professional" (detected or default)
   - Constraints: {max_words: 500}
    │
    ▼
3. Enhance with Context
   - Add user's preferred sources
   - Apply user's topic preferences
   - Merge with default parameters
    │
    ▼
4. Validate
   - Check topics are researchable
   - Validate parameter ranges
   - Return errors if invalid
    │
    ▼
ExtractedParameters
```

### Prompts

```python
ANALYZE_PROMPT_PROMPT = """
Analyze this user request for newsletter content:

"{prompt}"

Extract the following information:
1. Intent: What does the user want? (research, summarize, analyze, compare, generate)
2. Topics: What subjects should be covered?
3. Tone: What writing style is requested? (professional, casual, formal, enthusiastic)
4. Constraints: Any length, format, or time requirements?
5. Focus areas: Specific aspects to emphasize?
6. Exclusions: What should be avoided?

Examples:
- "Write about AI in healthcare, keep it professional"
  → topics: ["AI", "healthcare"], tone: "professional"

- "Quick summary of this week's tech news, casual style"
  → topics: ["technology"], tone: "casual", time_range: 7 days

Return as JSON:
{
  "intent": "research|summarize|analyze|compare|generate",
  "topics": ["topic1", "topic2"],
  "tone": "professional|casual|formal|enthusiastic|null",
  "constraints": {"max_words": null, "format": null},
  "focus_areas": [],
  "exclusions": [],
  "confidence": 0.0-1.0
}
"""
```

---

## Part 3: API Endpoints

### Preference Router

```python
# routers/preferences.py

@router.get("/preferences/{user_id}")
async def get_preferences(user_id: str) -> UserPreferences:
    """Get user preferences."""

@router.put("/preferences/{user_id}")
async def update_preferences(
    user_id: str, updates: PreferenceUpdate
) -> UserPreferences:
    """Update user preferences."""

@router.get("/preferences/{user_id}/recommendations")
async def get_recommendations(user_id: str) -> List[Dict]:
    """Get preference recommendations."""

@router.post("/preferences/{user_id}/engagement")
async def track_engagement(
    user_id: str, engagement: EngagementData
) -> Dict:
    """Track newsletter engagement."""
```

### Custom Prompt Router

```python
# Add to existing research router or create new

@router.post("/prompt/analyze")
async def analyze_prompt(prompt: str) -> PromptAnalysis:
    """Analyze a natural language prompt."""

@router.post("/prompt/generate-params")
async def generate_params(prompt: str) -> ExtractedParameters:
    """Convert prompt to research parameters."""
```

---

## Part 4: Frontend Updates

### PreferencesPanel Component

```typescript
interface PreferencesPanelProps {
  userId: string;
  onSave: (preferences: UserPreferences) => void;
}

// Features:
// - Topic chips (add/remove)
// - Tone selector dropdown
// - Frequency selector
// - Source whitelist/blacklist
// - Toggle switches for features
```

### Enhanced PromptInput

```typescript
interface PromptInputProps {
  value: string;
  onChange: (value: string) => void;
  suggestions?: string[];  // AI-generated suggestions
  onAnalyze?: (analysis: PromptAnalysis) => void;
}

// Features:
// - Real-time prompt analysis preview
// - Detected topics badges
// - Tone indicator
// - Suggestions dropdown
```

---

## Part 5: Integration with Existing Flow

### Updated NewsletterApp Flow

```typescript
// Before research:
1. Load user preferences (PreferenceAgent)
2. If custom prompt provided:
   a. Analyze prompt (CustomPromptAgent)
   b. Merge with user preferences
3. Research with combined parameters (ResearchAgent)
4. Generate newsletter (WritingAgent)
```

### Backend Integration

```python
# In orchestrator or research router

async def prepare_research_params(
    user_id: str,
    custom_prompt: Optional[str] = None,
    topic_overrides: Optional[List[str]] = None,
) -> Dict:
    """Prepare research parameters from preferences and prompt."""

    # Load preferences
    pref_agent = PreferenceAgent()
    preferences = await pref_agent.get_preferences(user_id)

    # Process custom prompt if provided
    if custom_prompt:
        prompt_agent = CustomPromptAgent()
        params = await prompt_agent.run({"prompt": custom_prompt})
        # Merge with preferences
        return merge_params(preferences, params)

    # Use topic overrides or preferences
    return {
        "topics": topic_overrides or preferences.topics,
        "tone": preferences.tone,
        "max_results": preferences.max_articles,
        "include_summaries": preferences.include_summaries,
    }
```

---

## Part 6: Tests

### Test Categories

| Category | Tests |
|----------|-------|
| Preference Agent Init | 4 tests |
| Preference Get/Update | 6 tests |
| Preference Analysis | 4 tests |
| Preference Recommendations | 4 tests |
| Custom Prompt Init | 4 tests |
| Prompt Analysis | 8 tests |
| Parameter Generation | 6 tests |
| Parameter Validation | 4 tests |
| LLM Factories | 6 tests |
| Prompts | 8 tests |
| API Endpoints | 10 tests |
| **Total** | **~64 tests** |

### Key Test Cases

```python
# Preference Agent
def test_get_preferences_returns_defaults_for_new_user()
def test_update_preferences_merges_partial_updates()
def test_analyze_preferences_identifies_top_topics()
def test_recommend_preferences_suggests_based_on_engagement()

# Custom Prompt Agent
def test_analyze_prompt_extracts_topics()
def test_analyze_prompt_detects_tone()
def test_analyze_prompt_handles_constraints()
def test_generate_parameters_from_complex_prompt()
def test_validate_parameters_rejects_empty_topics()
def test_enhance_prompt_adds_user_context()
```

---

## Dependencies

- Phase 5: Memory Service (for preference storage)
- Phase 6: Research Agent (receives parameters)
- Phase 7: Writing Agent (receives tone)
- Framework: BaseAgent

---

## Implementation Order

| Day | Task |
|-----|------|
| 1 | Preference Agent: schemas, llm.py, prompts.py |
| 2 | Preference Agent: agent.py, basic methods |
| 3 | Preference Agent: analysis, recommendations |
| 4 | Preference Agent: tests |
| 5 | Custom Prompt Agent: schemas, llm.py, prompts.py |
| 6 | Custom Prompt Agent: agent.py, NLP pipeline |
| 7 | Custom Prompt Agent: tests |
| 8 | API endpoints (preferences router) |
| 9 | Frontend: PreferencesPanel, PromptInput |
| 10 | Integration + E2E testing |

---

## Acceptance Criteria

- [ ] PreferenceAgent stores/retrieves preferences correctly
- [ ] PreferenceAgent provides recommendations based on engagement
- [ ] CustomPromptAgent extracts topics from natural language
- [ ] CustomPromptAgent detects tone and constraints
- [ ] Parameters merge correctly with user preferences
- [ ] API endpoints work for all operations
- [ ] Frontend preference panel saves settings
- [ ] All tests passing (~64 tests)
