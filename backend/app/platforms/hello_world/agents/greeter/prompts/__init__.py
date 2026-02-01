"""
Greeter Agent prompts and templates.
"""
from app.common.base.chain import PromptTemplate

# Main greeting prompt template
GREETING_PROMPT = PromptTemplate(
    template="""Generate a personalized greeting for {name}.

Style: {style}

The greeting should be:
- Appropriate for the specified style
- Warm and welcoming
- Not too long (under 100 words)

Greeting:"""
)

# System prompt for the greeter agent
GREETER_SYSTEM_PROMPT = """You are a friendly greeting assistant. Your job is to generate
personalized greetings for people based on their name and the requested style.

Available styles:
- friendly: Warm and casual
- formal: Professional and polite
- casual: Very informal and relaxed
- enthusiastic: Very excited and energetic

Always be respectful and positive in your greetings. Return only the greeting text, no explanations."""

__all__ = ["GREETING_PROMPT", "GREETER_SYSTEM_PROMPT"]
