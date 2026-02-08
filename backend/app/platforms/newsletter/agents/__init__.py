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
from app.platforms.newsletter.agents.writing import WritingAgent
from app.platforms.newsletter.agents.preference import PreferenceAgent
from app.platforms.newsletter.agents.custom_prompt import CustomPromptAgent

__all__ = [
    "ResearchAgent",
    "WritingAgent",
    "PreferenceAgent",
    "CustomPromptAgent",
]
