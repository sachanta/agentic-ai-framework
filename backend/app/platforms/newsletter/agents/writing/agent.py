"""
Writing Agent for Newsletter Platform.

Transforms researched articles into polished newsletter content with:
- RAG-enhanced writing using past successful newsletters
- Multiple output formats (HTML, email, text, markdown)
- Subject line generation
- Summary/bullet point generation
"""
import json
import logging
from typing import Any, Dict, List, Optional

from app.common.base.agent import BaseAgent
from app.platforms.newsletter.services.rag import get_rag_service, NewsletterRAGService
from app.platforms.newsletter.agents.writing.llm import (
    get_writing_llm,
    get_writing_config,
    get_creative_config,
)
from app.platforms.newsletter.agents.writing.prompts import (
    WRITING_SYSTEM_PROMPT,
    GENERATE_NEWSLETTER_PROMPT,
    GENERATE_SUBJECT_LINES_PROMPT,
    GENERATE_SUMMARY_PROMPT,
    format_articles_for_newsletter,
    format_rag_examples,
    extract_topics_from_articles,
)
from app.platforms.newsletter.agents.writing.formatters import format_all

logger = logging.getLogger(__name__)


class WritingAgent(BaseAgent):
    """
    Writing Agent for newsletter content generation.

    Transforms researched articles into polished newsletters with:
    - RAG enhancement from past successful newsletters
    - Multiple tone options (professional, casual, formal, enthusiastic)
    - Multi-format output (HTML, email HTML, plain text, markdown)
    - Subject line generation (5 options)
    - Bullet-point summary generation
    """

    VALID_TONES = ["professional", "casual", "formal", "enthusiastic"]

    def __init__(
        self,
        rag_service: Optional[NewsletterRAGService] = None,
        use_rag: bool = True,
    ):
        """
        Initialize the Writing Agent.

        Args:
            rag_service: Optional RAG service (uses singleton if not provided)
            use_rag: Whether to use RAG for style enhancement
        """
        llm = get_writing_llm()
        llm_config = get_writing_config()

        super().__init__(
            name="writing",
            description="Newsletter content generation agent",
            llm=llm,
            system_prompt=WRITING_SYSTEM_PROMPT,
            model=llm_config.get("model"),
            temperature=llm_config.get("temperature", 0.7),
            max_tokens=llm_config.get("max_tokens", 2000),
        )

        self.rag_service = rag_service or get_rag_service()
        self.use_rag = use_rag

    async def run(self, input: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute the writing pipeline.

        Args:
            input: Dict containing:
                - articles: List of article dicts from Research Agent
                - user_id: User ID for RAG personalization
                - tone: Writing tone (professional, casual, formal, enthusiastic)
                - title: Optional newsletter title
                - include_subject_lines: Whether to generate subject lines (default True)
                - include_summary: Whether to generate summary (default True)
                - include_rag: Whether to use RAG enhancement (default True)

        Returns:
            Dict with:
                - success: Whether writing completed
                - newsletter: Dict with content and all formats
                - subject_lines: List of 5 subject line options
                - summary: Bullet-point summary
                - metadata: Writing metadata
        """
        await self.initialize()

        articles = input.get("articles", [])
        user_id = input.get("user_id", "anonymous")
        tone = input.get("tone", "professional")
        title = input.get("title", "Newsletter")
        include_subject_lines = input.get("include_subject_lines", True)
        include_summary = input.get("include_summary", True)
        include_rag = input.get("include_rag", self.use_rag)

        # Validate tone
        if tone not in self.VALID_TONES:
            tone = "professional"
            logger.warning(f"Invalid tone, defaulting to: {tone}")

        if not articles:
            return {
                "success": False,
                "error": "No articles provided for newsletter generation",
                "newsletter": None,
            }

        try:
            # Extract topics from articles
            topics = extract_topics_from_articles(articles)

            # Get RAG examples if enabled
            rag_examples = []
            if include_rag and self.rag_service.is_available():
                rag_examples = await self._get_rag_examples(user_id, topics)

            # Generate main newsletter content
            logger.info(f"Generating newsletter with {len(articles)} articles, tone: {tone}")
            content = await self._generate_newsletter(articles, tone, topics, rag_examples)

            if not content:
                return {
                    "success": False,
                    "error": "Failed to generate newsletter content",
                    "newsletter": None,
                }

            # Generate all format versions
            formats = format_all(
                content=content,
                title=title,
                subtitle=f"Curated insights on {', '.join(topics[:3])}",
            )

            # Build result
            result = {
                "success": True,
                "newsletter": {
                    "title": title,
                    "content": content,
                    "tone": tone,
                    "topics": topics,
                    **formats,
                },
                "metadata": {
                    "article_count": len(articles),
                    "tone": tone,
                    "rag_examples_used": len(rag_examples),
                    "topics": topics,
                },
            }

            # Generate subject lines
            if include_subject_lines:
                logger.info("Generating subject lines")
                subject_lines = await self.create_subject_lines(content, tone)
                result["subject_lines"] = subject_lines

            # Generate summary
            if include_summary:
                logger.info("Generating summary")
                summary = await self.generate_summary(content)
                result["summary"] = summary

            return result

        except Exception as e:
            logger.error(f"Writing failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "newsletter": None,
            }

    async def generate_newsletter(
        self,
        articles: List[Dict[str, Any]],
        tone: str = "professional",
        user_id: str = "anonymous",
    ) -> Optional[str]:
        """
        Generate newsletter content from articles.

        Args:
            articles: List of article dicts
            tone: Writing tone
            user_id: User ID for RAG

        Returns:
            Newsletter content string or None if failed
        """
        topics = extract_topics_from_articles(articles)
        rag_examples = []

        if self.use_rag and self.rag_service.is_available():
            rag_examples = await self._get_rag_examples(user_id, topics)

        return await self._generate_newsletter(articles, tone, topics, rag_examples)

    async def _generate_newsletter(
        self,
        articles: List[Dict[str, Any]],
        tone: str,
        topics: List[str],
        rag_examples: List[Dict[str, Any]],
    ) -> Optional[str]:
        """
        Internal newsletter generation.

        Args:
            articles: Articles to include
            tone: Writing tone
            topics: Extracted topics
            rag_examples: RAG examples for style

        Returns:
            Newsletter content or None
        """
        # Format articles for prompt
        formatted_articles = format_articles_for_newsletter(articles)

        # Format RAG context
        rag_context = format_rag_examples(rag_examples) if rag_examples else ""

        # Build prompt
        prompt = GENERATE_NEWSLETTER_PROMPT.format(
            tone=tone,
            topics=", ".join(topics) if topics else "general news",
            articles=formatted_articles,
            rag_context=rag_context,
        )

        try:
            response = await self.llm.generate(
                prompt=prompt,
                system=self.system_prompt,
                temperature=0.7,
                max_tokens=2000,
            )

            content = response.content.strip()

            # Clean up any markdown code blocks if the model wrapped the output
            if content.startswith("```"):
                lines = content.split("\n")
                # Remove first and last lines if they're code block markers
                if lines[0].startswith("```"):
                    lines = lines[1:]
                if lines and lines[-1].strip() == "```":
                    lines = lines[:-1]
                content = "\n".join(lines)

            return content

        except Exception as e:
            logger.error(f"Newsletter generation failed: {e}")
            return None

    async def create_subject_lines(
        self,
        content: str,
        tone: str = "professional",
    ) -> List[Dict[str, str]]:
        """
        Generate subject line options for the newsletter.

        Args:
            content: Newsletter content
            tone: Writing tone for consistency

        Returns:
            List of 5 subject line dicts with 'text' and 'angle'
        """
        # Use first 500 chars of content for subject line generation
        content_preview = content[:500] if len(content) > 500 else content

        prompt = GENERATE_SUBJECT_LINES_PROMPT.format(
            content=content_preview,
            tone=tone,
        )

        try:
            config = get_creative_config()
            response = await self.llm.generate(
                prompt=prompt,
                system=self.system_prompt,
                temperature=config.get("temperature", 0.8),
                max_tokens=config.get("max_tokens", 500),
            )

            # Parse JSON response
            result = self._parse_json_response(response.content)

            if result and "subject_lines" in result:
                return result["subject_lines"]

            # Fallback if parsing fails
            return self._generate_fallback_subject_lines(content)

        except Exception as e:
            logger.warning(f"Subject line generation failed: {e}")
            return self._generate_fallback_subject_lines(content)

    async def generate_summary(self, content: str) -> Dict[str, Any]:
        """
        Generate a bullet-point summary of the newsletter.

        Args:
            content: Newsletter content

        Returns:
            Dict with 'summary' (list of bullets) and 'one_liner'
        """
        prompt = GENERATE_SUMMARY_PROMPT.format(content=content)

        try:
            response = await self.llm.generate(
                prompt=prompt,
                system=self.system_prompt,
                temperature=0.5,
                max_tokens=500,
            )

            result = self._parse_json_response(response.content)

            if result and "summary" in result:
                return result

            # Fallback
            return self._generate_fallback_summary(content)

        except Exception as e:
            logger.warning(f"Summary generation failed: {e}")
            return self._generate_fallback_summary(content)

    async def format_for_email(
        self,
        content: str,
        title: str = "Newsletter",
    ) -> Dict[str, str]:
        """
        Format content for email delivery.

        Args:
            content: Newsletter content
            title: Newsletter title

        Returns:
            Dict with html, email_html, text, markdown
        """
        return format_all(content, title)

    async def _get_rag_examples(
        self,
        user_id: str,
        topics: List[str],
    ) -> List[Dict[str, Any]]:
        """
        Get similar successful newsletters from RAG.

        Args:
            user_id: User ID for personalization
            topics: Topics to search for

        Returns:
            List of similar newsletters
        """
        try:
            if not topics:
                return []

            # Search for similar newsletters
            query = " ".join(topics)
            results = await self.rag_service.search_similar(
                query=query,
                user_id=user_id,
                limit=3,
                min_score=0.5,
            )

            # Sort by engagement score and return top 2
            results.sort(key=lambda x: x.get("engagement_score", 0), reverse=True)
            return results[:2]

        except Exception as e:
            logger.warning(f"RAG query failed: {e}")
            return []

    def _parse_json_response(self, content: str) -> Optional[Dict[str, Any]]:
        """
        Parse JSON from LLM response.

        Args:
            content: Raw LLM response

        Returns:
            Parsed dict or None
        """
        try:
            # Extract JSON from markdown code blocks if present
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0]
            elif "```" in content:
                content = content.split("```")[1].split("```")[0]

            return json.loads(content.strip())

        except (json.JSONDecodeError, IndexError) as e:
            logger.warning(f"Failed to parse JSON response: {e}")
            return None

    def _generate_fallback_subject_lines(self, content: str) -> List[Dict[str, str]]:
        """
        Generate fallback subject lines without LLM.

        Args:
            content: Newsletter content

        Returns:
            List of basic subject lines
        """
        # Extract first header or use generic
        lines = content.split("\n")
        first_header = "This Week's Highlights"
        for line in lines:
            if line.startswith("##"):
                first_header = line.replace("#", "").strip()
                break

        return [
            {"text": first_header, "angle": "direct"},
            {"text": f"Your Weekly Update: {first_header[:30]}...", "angle": "news"},
            {"text": "Don't Miss These Key Insights", "angle": "curiosity"},
            {"text": "Quick Read: Top Stories This Week", "angle": "benefit"},
            {"text": "What You Need to Know Today", "angle": "urgency"},
        ]

    def _generate_fallback_summary(self, content: str) -> Dict[str, Any]:
        """
        Generate fallback summary without LLM.

        Args:
            content: Newsletter content

        Returns:
            Basic summary structure
        """
        # Extract headers as bullet points
        lines = content.split("\n")
        bullets = []

        for line in lines:
            if line.startswith("##") and not line.startswith("###"):
                bullet = line.replace("#", "").strip()
                if bullet and len(bullets) < 6:
                    bullets.append(bullet)

        if not bullets:
            bullets = ["Key insights from this week's top stories"]

        return {
            "summary": bullets,
            "one_liner": bullets[0] if bullets else "Your weekly newsletter digest",
        }
