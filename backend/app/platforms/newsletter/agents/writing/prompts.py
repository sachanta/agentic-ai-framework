"""
Prompts for the Writing Agent.

Contains prompts for:
- Newsletter generation
- Subject line creation
- Summary generation
- RAG enhancement
"""
from typing import List, Dict, Any

# System prompt for the Writing Agent
WRITING_SYSTEM_PROMPT = """You are an expert newsletter writer who creates engaging, informative content.

Your responsibilities:
1. Transform research articles into cohesive newsletter content
2. Write in the specified tone (professional, casual, formal, enthusiastic)
3. Create compelling subject lines that drive opens
4. Generate concise summaries with key takeaways

Guidelines:
- Keep paragraphs short and scannable
- Use headers to organize content
- Include relevant quotes or data points
- End with a clear call-to-action or takeaway
- Match the tone consistently throughout"""


# Main newsletter generation prompt
GENERATE_NEWSLETTER_PROMPT = """Write a newsletter based on the following curated articles.

**Tone:** {tone}
**Topic Focus:** {topics}

**Articles to include:**
{articles}

{rag_context}

**Requirements:**
1. Write an engaging introduction that hooks the reader
2. Cover each article with 2-3 paragraphs, highlighting key insights
3. Add smooth transitions between sections
4. Include a brief conclusion with key takeaways
5. Keep the total length around 800-1200 words

**Format:**
- Use ## for section headers
- Use **bold** for emphasis
- Use > for notable quotes
- Use bullet points for lists

Write the newsletter now:"""


# RAG context template
RAG_CONTEXT_TEMPLATE = """**Style Reference (from your previous successful newsletters):**
{examples}

Use a similar style, structure, and tone as these successful examples."""


# Subject line generation prompt
GENERATE_SUBJECT_LINES_PROMPT = """Generate 5 compelling email subject lines for this newsletter.

**Newsletter Content:**
{content}

**Tone:** {tone}

**Requirements:**
- Each subject line should be 40-60 characters
- Use different angles: curiosity, urgency, benefit, question, news
- Avoid spam trigger words
- Make them specific to the content

Respond with exactly 5 subject lines in JSON format:
```json
{{
  "subject_lines": [
    {{"text": "...", "angle": "curiosity"}},
    {{"text": "...", "angle": "benefit"}},
    {{"text": "...", "angle": "question"}},
    {{"text": "...", "angle": "news"}},
    {{"text": "...", "angle": "urgency"}}
  ]
}}
```"""


# Summary generation prompt
GENERATE_SUMMARY_PROMPT = """Create a bullet-point summary of this newsletter for quick scanning.

**Newsletter Content:**
{content}

**Requirements:**
- Generate 5-6 bullet points
- Each bullet should be one key insight or takeaway
- Keep each bullet to 1-2 sentences max
- Start each with an action verb or key topic

Respond in JSON format:
```json
{{
  "summary": [
    "First key point...",
    "Second key point...",
    "Third key point...",
    "Fourth key point...",
    "Fifth key point..."
  ],
  "one_liner": "A single sentence summary of the entire newsletter"
}}
```"""


# Tone adjustment prompt
ADJUST_TONE_PROMPT = """Rewrite this newsletter content to match the {target_tone} tone.

**Current Content:**
{content}

**Target Tone:** {target_tone}

**Tone Guidelines:**
- Professional: Clear, authoritative, data-driven, formal language
- Casual: Friendly, conversational, uses contractions, relatable
- Formal: Academic, precise, structured, no colloquialisms
- Enthusiastic: Energetic, exclamation points, positive, motivating

Rewrite the content maintaining all the information but adjusting the tone:"""


# Section generation prompts for structured output
GENERATE_INTRO_PROMPT = """Write an engaging introduction for a newsletter about: {topics}

**Tone:** {tone}
**Key themes from articles:** {themes}

Requirements:
- 2-3 sentences max
- Hook the reader immediately
- Hint at the value they'll get from reading

Introduction:"""


GENERATE_SECTION_PROMPT = """Write a newsletter section about this article.

**Article:**
Title: {title}
Source: {source}
Content: {content}

**Tone:** {tone}
**Section number:** {section_num} of {total_sections}

Requirements:
- 2-3 paragraphs
- Highlight the key insight
- Add context or analysis
- Keep it engaging and informative

Section:"""


GENERATE_CONCLUSION_PROMPT = """Write a conclusion for this newsletter.

**Topics covered:** {topics}
**Key takeaways:** {takeaways}
**Tone:** {tone}

Requirements:
- 2-3 sentences
- Summarize the main theme
- End with a forward-looking statement or call-to-action

Conclusion:"""


def format_articles_for_newsletter(articles: List[Dict[str, Any]], max_chars: int = 600) -> str:
    """
    Format articles for inclusion in the newsletter generation prompt.

    Args:
        articles: List of article dicts with title, content, source, summary
        max_chars: Maximum characters per article content

    Returns:
        Formatted string for prompt
    """
    formatted = []
    for i, article in enumerate(articles, 1):
        content = article.get("summary") or article.get("content", "")
        if len(content) > max_chars:
            content = content[:max_chars] + "..."

        formatted.append(
            f"### Article {i}: {article.get('title', 'Untitled')}\n"
            f"**Source:** {article.get('source', 'Unknown')}\n"
            f"**Key Points:** {content}\n"
        )
    return "\n".join(formatted)


def format_rag_examples(examples: List[Dict[str, Any]], max_examples: int = 2) -> str:
    """
    Format RAG examples for the context prompt.

    Args:
        examples: List of similar newsletters from RAG
        max_examples: Maximum examples to include

    Returns:
        Formatted context string or empty string if no examples
    """
    if not examples:
        return ""

    formatted = []
    for i, example in enumerate(examples[:max_examples], 1):
        content = example.get("content", "")[:500]
        formatted.append(
            f"**Example {i}** (Engagement: {example.get('engagement_score', 0):.0%}):\n"
            f"{content}...\n"
        )

    examples_text = "\n".join(formatted)
    return RAG_CONTEXT_TEMPLATE.format(examples=examples_text)


def extract_topics_from_articles(articles: List[Dict[str, Any]]) -> List[str]:
    """
    Extract unique topics from a list of articles.

    Args:
        articles: List of article dicts

    Returns:
        List of unique topic strings
    """
    topics = set()
    for article in articles:
        # From article topics field
        if "topics" in article:
            topics.update(article["topics"])
        # From matched_topics in scoring
        if "matched_topics" in article:
            topics.update(article["matched_topics"])

    return list(topics)[:5]  # Limit to top 5
