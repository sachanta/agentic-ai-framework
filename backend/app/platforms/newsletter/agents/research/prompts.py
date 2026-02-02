"""
Prompts for the Research Agent.

Contains prompts for:
- Article summarization
- Relevance scoring
- Query enhancement
"""

# System prompt for the Research Agent
RESEARCH_SYSTEM_PROMPT = """You are a research assistant specializing in finding and summarizing relevant content for newsletters.

Your responsibilities:
1. Analyze articles for relevance to given topics
2. Generate concise, informative summaries
3. Score content quality and relevance
4. Identify key insights and takeaways

Always be objective, accurate, and concise in your analysis."""


# Prompt for summarizing a single article
SUMMARIZE_ARTICLE_PROMPT = """Summarize the following article for a newsletter.

Title: {title}
Source: {source}
Content: {content}

Requirements:
- Keep the summary to 2-3 sentences
- Focus on the key insight or news
- Make it engaging for newsletter readers
- Include any notable data points or quotes

Summary:"""


# Prompt for batch summarization
BATCH_SUMMARIZE_PROMPT = """Summarize each of the following articles for a newsletter about {topics}.

{articles}

For each article, provide:
1. A 2-3 sentence summary
2. The key takeaway
3. Why it's relevant to the topics

Format your response as JSON:
```json
[
  {{
    "index": 0,
    "summary": "...",
    "key_takeaway": "...",
    "relevance": "..."
  }}
]
```"""


# Prompt for scoring article relevance
SCORE_RELEVANCE_PROMPT = """Score the relevance of this article to the given topics.

Topics: {topics}
Title: {title}
Content snippet: {content}

Score from 0.0 to 1.0 where:
- 0.0-0.3: Not relevant
- 0.4-0.6: Somewhat relevant
- 0.7-0.8: Relevant
- 0.9-1.0: Highly relevant

Also identify:
- Which topics it matches
- Why it's relevant or not

Respond in JSON format:
```json
{{
  "score": 0.0,
  "matched_topics": [],
  "reasoning": "..."
}}
```"""


# Prompt for enhancing a natural language query
ENHANCE_QUERY_PROMPT = """Convert this natural language request into effective search queries.

User request: {prompt}

Generate 2-3 specific search queries that would find relevant articles.
Consider:
- Key terms and concepts
- Recent events or trends
- Related topics

Respond in JSON format:
```json
{{
  "queries": ["query1", "query2", "query3"],
  "identified_topics": ["topic1", "topic2"],
  "time_relevance": "recent|any"
}}
```"""


# Prompt for analyzing search results quality
ANALYZE_RESULTS_PROMPT = """Analyze these search results for quality and relevance.

Topics requested: {topics}
Number of results: {count}

Results summary:
{results_summary}

Assess:
1. Overall quality of results
2. Topic coverage
3. Source diversity
4. Any gaps or missing angles

Respond in JSON format:
```json
{{
  "quality_score": 0.0,
  "topic_coverage": {{}},
  "source_diversity": "low|medium|high",
  "gaps": [],
  "recommendations": []
}}
```"""


# Prompt for deduplication analysis
DEDUPE_ANALYSIS_PROMPT = """Analyze if these two articles are duplicates or cover the same story.

Article 1:
Title: {title1}
Content: {content1}

Article 2:
Title: {title2}
Content: {content2}

Determine:
1. Are they about the same event/topic?
2. Do they provide unique perspectives?
3. Which one is better quality?

Respond in JSON format:
```json
{{
  "is_duplicate": true/false,
  "similarity": 0.0,
  "unique_angles": [],
  "recommended_keep": 1 or 2,
  "reasoning": "..."
}}
```"""


def format_articles_for_prompt(articles: list, max_chars: int = 500) -> str:
    """
    Format a list of articles for inclusion in a prompt.

    Args:
        articles: List of article dicts with title, content, source
        max_chars: Maximum characters per article content

    Returns:
        Formatted string for prompt
    """
    formatted = []
    for i, article in enumerate(articles):
        content = article.get("content", "")[:max_chars]
        formatted.append(
            f"[Article {i}]\n"
            f"Title: {article.get('title', 'Untitled')}\n"
            f"Source: {article.get('source', 'Unknown')}\n"
            f"Content: {content}...\n"
        )
    return "\n".join(formatted)
