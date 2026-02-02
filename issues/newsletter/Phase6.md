# Phase 6: Research Agent Implementation

## Goal
Content discovery agent using framework's BaseAgent

## Status
- [ ] Not Started

## Files to Create
```
backend/app/platforms/newsletter/agents/research/
├── __init__.py
├── agent.py           # ResearchAgent extends BaseAgent
├── chain.py           # ResearchChain
├── llm.py             # LLM configuration
├── prompts/
│   └── __init__.py    # Research prompts
└── tools/
    └── __init__.py    # TavilySearchTool, ContentFilterTool
```

## Agent Tasks
- `search_by_topics()`: Multi-topic parallel search
- `search_custom_prompt()`: Custom query search
- `get_trending_content()`: 24-hour trending
- `filter_and_deduplicate()`: Quality filtering
- `generate_summaries()`: AI summarization

## How It Helps The Project

The Research Agent is the **first agent in the newsletter generation pipeline**. It wraps the Tavily Search Service (Phase 3) with AI capabilities:

### The Flow
1. User provides topics or custom prompt
2. Research Agent searches via Tavily
3. AI analyzes and summarizes each article
4. Results are filtered, deduplicated, and scored
5. Output goes to **HITL Checkpoint 1** for human review

### Key Capabilities

| Capability | Description |
|------------|-------------|
| Smart search | Converts natural language to effective search queries |
| Quality assessment | Uses LLM to score article relevance |
| Summarization | Generates concise summaries for review |
| Deduplication | Identifies semantically similar articles |

## Dependencies
- Phase 3 (Tavily Search Service)
- Phase 5 (Memory Service for caching)
- Framework BaseAgent

## Verification
- [ ] Agent extends BaseAgent correctly
- [ ] Can search multiple topics
- [ ] Generates article summaries
- [ ] Quality filtering works
- [ ] Tests passing
