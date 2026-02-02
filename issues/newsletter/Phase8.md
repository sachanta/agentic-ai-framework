# Phase 8: Preference & Custom Prompt Agents

## Goal
User preference and NLP processing agents

## Status
- [ ] Not Started

## Files to Create
```
backend/app/platforms/newsletter/agents/preference/
├── agent.py           # PreferenceAgent
├── chain.py
└── prompts/

backend/app/platforms/newsletter/agents/custom_prompt/
├── agent.py           # CustomPromptAgent
├── chain.py
└── prompts/
```

## Preference Agent Tasks
- `update_preferences()`: Store user preferences
- `get_preferences()`: Retrieve with fallback
- `analyze_preferences()`: Behavior pattern analysis
- `recommend_preferences()`: Suggestions based on engagement

## Custom Prompt Agent Tasks
- `process_prompt()`: Full NLP pipeline
- `analyze_prompt()`: Extract intent/parameters
- `enhance_prompt()`: Add user context
- `generate_parameters()`: Research/writing params

## How It Helps The Project

These two agents handle **personalization** at the start of each newsletter generation:

### Preference Agent
Manages user preferences and learns from behavior:
- Stores topic interests, tone preferences, frequency
- Analyzes which preferences lead to high engagement
- Recommends preference changes based on patterns

### Custom Prompt Agent
Processes natural language requests into structured parameters:
```
Input:  "Write about AI in healthcare, keep it short and professional"
Output: {
  topics: ["AI", "healthcare"],
  tone: "professional",
  max_word_count: 500,
  focus_areas: ["medical AI", "diagnostics"]
}
```

### The Flow
1. Preference Agent loads user preferences
2. If custom prompt provided, Custom Prompt Agent extracts parameters
3. Combined parameters go to Research Agent (Phase 6)

## Dependencies
- Phase 5 (Memory Service)
- Framework BaseAgent

## Verification
- [ ] Preference Agent stores/retrieves preferences
- [ ] Custom Prompt Agent extracts parameters correctly
- [ ] NLP handles various prompt styles
- [ ] Tests passing
