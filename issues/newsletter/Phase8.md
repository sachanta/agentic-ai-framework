# Phase 8: Preference & Custom Prompt Agents

## Goal
User preference and NLP processing agents for personalization

## Status
- [ ] Not Started

## Files to Create
```
backend/app/platforms/newsletter/agents/preference/
├── __init__.py
├── agent.py           # PreferenceAgent
├── llm.py             # get_preference_llm()
├── prompts.py         # Preference analysis prompts
└── schemas.py         # UserPreferences, PreferenceUpdate

backend/app/platforms/newsletter/agents/custom_prompt/
├── __init__.py
├── agent.py           # CustomPromptAgent
├── llm.py             # get_custom_prompt_llm()
├── prompts.py         # NLP extraction prompts
└── schemas.py         # PromptAnalysis, ExtractedParameters

backend/app/platforms/newsletter/routers/
└── preferences.py     # Preference API endpoints

backend/app/platforms/newsletter/tests/phase8/
├── test_preference_agent.py
├── test_preference_llm.py
├── test_preference_prompts.py
├── test_custom_prompt_agent.py
├── test_custom_prompt_llm.py
└── test_custom_prompt_prompts.py
```

## Preference Agent Tasks
- `get_preferences()`: Retrieve user preferences with defaults
- `update_preferences()`: Update specific preference fields
- `analyze_preferences()`: Behavior pattern analysis
- `recommend_preferences()`: Suggestions based on engagement
- `learn_from_engagement()`: Update based on signals

## Custom Prompt Agent Tasks
- `analyze_prompt()`: Extract intent and parameters from NL
- `enhance_prompt()`: Add user context to prompt
- `generate_parameters()`: Convert to research/writing params
- `validate_parameters()`: Validate extracted parameters

## Example Transformation
```
Input:  "Write about AI in healthcare, keep it short and professional"
Output: {
  topics: ["AI", "healthcare"],
  tone: "professional",
  max_word_count: 500,
  focus_areas: ["medical AI", "diagnostics"]
}
```

## How It Helps The Project

These agents handle **personalization** at the start of each newsletter generation:

### The Flow
```
User Request
    │
    ├─→ Preference Agent → Load user preferences
    │                          │
    ├─→ Custom Prompt Agent → Extract parameters (if prompt provided)
    │                          │
    └──────────┬───────────────┘
               ▼
       Combined Parameters
               │
               ▼
       Research Agent (Phase 6)
               │
               ▼
       Writing Agent (Phase 7)
```

### Key Features

| Agent | Feature | Description |
|-------|---------|-------------|
| Preference | Storage | MongoDB-backed preference persistence |
| Preference | Learning | Updates preferences from engagement |
| Preference | Recommendations | AI-powered preference suggestions |
| Custom Prompt | NLP | Extracts topics, tone, constraints |
| Custom Prompt | Context | Merges with user preferences |
| Custom Prompt | Validation | Ensures valid parameters |

## Dependencies
- Phase 5 (Memory Service)
- Phase 6 (Research Agent)
- Phase 7 (Writing Agent)
- Framework BaseAgent

## Verification
- [ ] Preference Agent stores/retrieves preferences
- [ ] Preference Agent recommends based on engagement
- [ ] Custom Prompt Agent extracts topics correctly
- [ ] Custom Prompt Agent detects tone
- [ ] Parameters merge with user preferences
- [ ] API endpoints work
- [ ] Tests passing (~64 tests)
