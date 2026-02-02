"""
Newsletter Platform agents.

Agents:
- ResearchAgent: Content discovery via Tavily (Phase 6)
- WritingAgent: Newsletter content generation (Phase 7)
- PreferenceAgent: User personalization (Phase 8)
- CustomPromptAgent: NLP processing (Phase 8)
- MindmapAgent: Visual knowledge maps (Phase 9)
"""
from app.platforms.newsletter.agents.research import ResearchAgent

__all__ = [
    "ResearchAgent",
]
