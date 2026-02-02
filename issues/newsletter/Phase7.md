# Phase 7: Writing Agent Implementation

## Goal
Newsletter content generation agent

## Status
- [ ] Not Started

## Files to Create
```
backend/app/platforms/newsletter/agents/writing/
├── __init__.py
├── agent.py           # WritingAgent extends BaseAgent
├── chain.py           # WritingChain with RAG enhancement
├── llm.py
├── prompts/
│   └── __init__.py    # Writing prompts (intro, body, conclusion)
└── tools/
    └── __init__.py    # FormatHTMLTool, SubjectLineTool
```

## Agent Tasks
- `generate_newsletter()`: Full newsletter with RAG enhancement
- `create_subject_lines()`: 5 subject line options
- `format_for_email()`: HTML/text/markdown versions
- `generate_summary()`: 5-6 bullet point summary

## Output Formats
- Blog-style HTML with gradient headers
- Responsive email template
- Plain text version
- Markdown version

## How It Helps The Project

The Writing Agent is the **core content generator**. It takes researched articles and transforms them into a polished newsletter:

### The Flow
1. Receives approved articles from Research Agent
2. Queries RAG (Phase 4) for similar successful newsletters
3. Generates newsletter content in user's preferred tone
4. Creates multiple subject line options
5. Formats output for email delivery
6. Output goes to **HITL Checkpoint 2** for content review

### Key Capabilities

| Capability | Description |
|------------|-------------|
| RAG-enhanced writing | Uses past successful newsletters as examples |
| Tone matching | Adapts to professional, casual, formal, enthusiastic |
| Multi-format output | HTML, plain text, markdown versions |
| Subject line generation | Creates 5 options with different angles |

## Dependencies
- Phase 4 (RAG System for examples)
- Phase 6 (Research Agent output)
- Framework BaseAgent

## Verification
- [ ] Agent extends BaseAgent correctly
- [ ] Generates coherent newsletter content
- [ ] Creates 5 subject line options
- [ ] HTML/text/markdown outputs are valid
- [ ] RAG integration works
- [ ] Tests passing
