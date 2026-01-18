"""
AI-powered research assistant using Claude.

Provides research Q&A, paper summarization, comparison, and topic suggestions.
"""

import json
import logging
from typing import Any, Dict, Generator, List, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from academic_research_toolkit.intelligence.vector_store import VectorStore


logger = logging.getLogger(__name__)


class ResearchAssistant:
    """AI-powered research assistant using Claude.

    Uses RAG (Retrieval-Augmented Generation) when a vector store is provided
    to ground responses in actual document content.
    """

    # Default model settings
    DEFAULT_MODEL = "claude-sonnet-4-20250514"
    DEFAULT_MAX_TOKENS = 4096
    DEFAULT_TEMPERATURE = 0.7

    # System prompts
    SYSTEM_PROMPT_QA = """You are a research assistant helping with academic research questions.
When answering questions:
1. Be accurate and cite sources when available
2. Acknowledge uncertainty when appropriate
3. Provide structured, well-organized responses
4. Focus on academic rigor and clarity

If context from papers is provided, use it to ground your response and cite the sources."""

    SYSTEM_PROMPT_SUMMARY = """You are a research assistant specialized in synthesizing academic literature.
When summarizing papers:
1. Identify key themes and findings across papers
2. Note areas of agreement and disagreement
3. Highlight methodological approaches
4. Identify gaps and opportunities for future research
5. Be concise but comprehensive"""

    def __init__(
        self,
        vector_store: Optional["VectorStore"] = None,
        model: str = DEFAULT_MODEL,
        max_tokens: int = DEFAULT_MAX_TOKENS,
        temperature: float = DEFAULT_TEMPERATURE,
        dry_run: bool = False,
    ):
        """Initialize the research assistant.

        Args:
            vector_store: Optional vector store for RAG.
            model: Claude model to use.
            max_tokens: Maximum tokens in response.
            temperature: Sampling temperature (0-1).
            dry_run: If True, don't make API calls (for testing/cost awareness).
        """
        self.vector_store = vector_store
        self.model = model
        self.max_tokens = max_tokens
        self.temperature = temperature
        self.dry_run = dry_run

        self._client = None
        self._token_usage: Dict[str, int] = {
            "input_tokens": 0,
            "output_tokens": 0,
        }

    @property
    def client(self):
        """Lazy-load the Anthropic client."""
        if self._client is None:
            try:
                import anthropic
            except ImportError:
                raise ImportError(
                    "anthropic package required for ResearchAssistant. "
                    "Install with: pip install academic-research-toolkit[ai]"
                )
            self._client = anthropic.Anthropic()
        return self._client

    def _format_context(self, context: List[Dict[str, Any]]) -> str:
        """Format context documents for the prompt.

        Args:
            context: List of context documents with text and metadata.

        Returns:
            Formatted context string.
        """
        if not context:
            return ""

        parts = ["Here is relevant context from the research corpus:\n"]

        for i, doc in enumerate(context, 1):
            parts.append(f"--- Source {i} ---")

            # Add metadata if available
            metadata = doc.get("metadata", {})
            if metadata.get("title"):
                parts.append(f"Title: {metadata['title']}")
            if metadata.get("authors"):
                authors = metadata["authors"]
                if isinstance(authors, list):
                    parts.append(f"Authors: {', '.join(authors)}")
                else:
                    parts.append(f"Authors: {authors}")
            if metadata.get("year"):
                parts.append(f"Year: {metadata['year']}")

            # Add relevance score if available
            if "score" in doc:
                parts.append(f"Relevance: {doc['score']:.2f}")

            # Add text content
            parts.append(f"\nContent:\n{doc.get('text', '')}")
            parts.append("")

        return "\n".join(parts)

    def _call_claude(
        self,
        user_message: str,
        system: str,
        context: Optional[List[Dict[str, Any]]] = None,
    ) -> str:
        """Make a call to Claude API.

        Args:
            user_message: The user's message/question.
            system: System prompt.
            context: Optional context documents.

        Returns:
            Claude's response text.
        """
        if self.dry_run:
            return "[DRY RUN] No API call made. Message would have been sent to Claude."

        # Build the message with context if available
        if context:
            context_str = self._format_context(context)
            full_message = f"{context_str}\n\n---\n\nUser Question: {user_message}"
        else:
            full_message = user_message

        response = self.client.messages.create(
            model=self.model,
            max_tokens=self.max_tokens,
            temperature=self.temperature,
            system=system,
            messages=[{"role": "user", "content": full_message}],
        )

        # Track token usage
        if hasattr(response, 'usage'):
            self._token_usage["input_tokens"] += response.usage.input_tokens
            self._token_usage["output_tokens"] += response.usage.output_tokens

        return response.content[0].text

    def _call_claude_streaming(
        self,
        user_message: str,
        system: str,
        context: Optional[List[Dict[str, Any]]] = None,
    ) -> Generator[str, None, None]:
        """Make a streaming call to Claude API.

        Args:
            user_message: The user's message/question.
            system: System prompt.
            context: Optional context documents.

        Yields:
            Text chunks from Claude's response.
        """
        if self.dry_run:
            yield "[DRY RUN] No API call made."
            return

        # Build the message with context if available
        if context:
            context_str = self._format_context(context)
            full_message = f"{context_str}\n\n---\n\nUser Question: {user_message}"
        else:
            full_message = user_message

        with self.client.messages.stream(
            model=self.model,
            max_tokens=self.max_tokens,
            temperature=self.temperature,
            system=system,
            messages=[{"role": "user", "content": full_message}],
        ) as stream:
            for text in stream.text_stream:
                yield text

    def ask(
        self,
        question: str,
        context: Optional[List[Dict[str, Any]]] = None,
        use_rag: bool = True,
        top_k: int = 5,
        stream: bool = False,
    ) -> str | Generator[str, None, None]:
        """Answer a research question using available context.

        Args:
            question: The research question to answer.
            context: Optional pre-provided context documents.
            use_rag: Whether to use RAG if vector store is available.
            top_k: Number of documents to retrieve for RAG.
            stream: Whether to stream the response.

        Returns:
            Answer text or generator for streaming.
        """
        # Use provided context or retrieve from vector store
        if context is None and use_rag and self.vector_store:
            context = self.vector_store.search(question, top_k=top_k)
            logger.info(f"Retrieved {len(context)} documents for RAG")

        if stream:
            return self._call_claude_streaming(
                question, self.SYSTEM_PROMPT_QA, context
            )

        return self._call_claude(question, self.SYSTEM_PROMPT_QA, context)

    def summarize_papers(
        self,
        citations: List[Dict[str, Any]],
        focus: Optional[str] = None,
    ) -> str:
        """Generate a synthesis summary of multiple papers.

        Args:
            citations: List of citation dictionaries.
            focus: Optional focus area for the summary.

        Returns:
            Synthesis summary text.
        """
        # Format citations as context
        context = []
        for citation in citations:
            context.append({
                "text": self._format_citation_for_context(citation),
                "metadata": {
                    "title": citation.get("title"),
                    "authors": citation.get("authors"),
                    "year": citation.get("year"),
                },
            })

        prompt = "Please synthesize the following papers into a comprehensive summary."
        if focus:
            prompt += f" Focus particularly on: {focus}"
        prompt += "\n\nIdentify:\n"
        prompt += "1. Key themes and findings\n"
        prompt += "2. Methodological approaches\n"
        prompt += "3. Areas of agreement and disagreement\n"
        prompt += "4. Gaps in the literature\n"
        prompt += "5. Implications for future research"

        return self._call_claude(prompt, self.SYSTEM_PROMPT_SUMMARY, context)

    def _format_citation_for_context(self, citation: Dict[str, Any]) -> str:
        """Format a citation dictionary for use as context.

        Args:
            citation: Citation dictionary.

        Returns:
            Formatted citation text.
        """
        parts = []

        if citation.get("title"):
            parts.append(f"Title: {citation['title']}")

        if citation.get("authors"):
            authors = citation["authors"]
            if isinstance(authors, list):
                parts.append(f"Authors: {', '.join(authors)}")
            else:
                parts.append(f"Authors: {authors}")

        if citation.get("year"):
            parts.append(f"Year: {citation['year']}")

        if citation.get("source"):
            parts.append(f"Source: {citation['source']}")

        if citation.get("raw_text"):
            parts.append(f"Full citation: {citation['raw_text']}")

        return "\n".join(parts)

    def compare_papers(
        self,
        paper_a: Dict[str, Any],
        paper_b: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Compare methodologies, findings, and contributions of two papers.

        Args:
            paper_a: First paper citation/data.
            paper_b: Second paper citation/data.

        Returns:
            Comparison dictionary with methodology, findings, contributions.
        """
        context = [
            {
                "text": self._format_citation_for_context(paper_a),
                "metadata": {"title": paper_a.get("title"), "source": "Paper A"},
            },
            {
                "text": self._format_citation_for_context(paper_b),
                "metadata": {"title": paper_b.get("title"), "source": "Paper B"},
            },
        ]

        prompt = """Compare the two papers provided and return a structured comparison.
Please analyze:
1. Methodology - How do their approaches differ?
2. Findings - What are the key findings and how do they relate?
3. Contributions - What unique contributions does each make?
4. Limitations - What are the limitations of each?
5. Complementarity - How might they complement each other?

Format your response as JSON with the following structure:
{
    "methodology": {"paper_a": "...", "paper_b": "...", "comparison": "..."},
    "findings": {"paper_a": "...", "paper_b": "...", "comparison": "..."},
    "contributions": {"paper_a": "...", "paper_b": "...", "comparison": "..."},
    "limitations": {"paper_a": "...", "paper_b": "...", "comparison": "..."},
    "complementarity": "...",
    "summary": "..."
}"""

        system = """You are a research assistant specialized in comparing academic papers.
Provide structured, objective comparisons based on the available information.
Always respond with valid JSON."""

        response = self._call_claude(prompt, system, context)

        # Parse JSON response
        try:
            # Find JSON in response (in case of extra text)
            start = response.find("{")
            end = response.rfind("}") + 1
            if start >= 0 and end > start:
                return json.loads(response[start:end])
        except json.JSONDecodeError:
            logger.warning("Failed to parse comparison as JSON")

        # Return raw response if parsing fails
        return {
            "raw_comparison": response,
            "paper_a_title": paper_a.get("title"),
            "paper_b_title": paper_b.get("title"),
        }

    def extract_key_findings(self, text: str) -> List[Dict[str, Any]]:
        """Extract structured key findings from paper text.

        Args:
            text: Paper text or abstract.

        Returns:
            List of finding dictionaries with finding, evidence, confidence.
        """
        prompt = """Extract the key findings from the following text.
For each finding, identify:
1. The main claim or finding
2. Supporting evidence or methodology
3. Confidence level (high/medium/low based on how clearly stated)

Format your response as JSON array:
[
    {
        "finding": "...",
        "evidence": "...",
        "confidence": "high|medium|low",
        "category": "methodology|result|conclusion|implication"
    }
]

Text to analyze:
"""
        prompt += text

        system = """You are a research assistant specialized in extracting key findings from academic texts.
Be thorough and objective. Only include findings that are clearly stated or strongly implied.
Always respond with valid JSON."""

        response = self._call_claude(prompt, system)

        # Parse JSON response
        try:
            start = response.find("[")
            end = response.rfind("]") + 1
            if start >= 0 and end > start:
                return json.loads(response[start:end])
        except json.JSONDecodeError:
            logger.warning("Failed to parse findings as JSON")

        return [{"raw_response": response}]

    def suggest_related_topics(
        self,
        topic: str,
        num_suggestions: int = 5,
    ) -> List[str]:
        """Suggest related research topics to explore.

        Args:
            topic: Main research topic.
            num_suggestions: Number of suggestions to generate.

        Returns:
            List of related topic suggestions.
        """
        prompt = f"""Given the research topic: "{topic}"

Suggest {num_suggestions} related research topics that would be valuable to explore.
Consider:
- Adjacent research areas
- Methodological variations
- Application domains
- Theoretical perspectives
- Emerging trends

Return only the list of topics, one per line, without numbering or explanations."""

        system = """You are a research advisor helping to identify promising research directions.
Suggest topics that are specific, researchable, and academically relevant."""

        response = self._call_claude(prompt, system)

        # Parse response into list
        suggestions = []
        for line in response.strip().split("\n"):
            line = line.strip()
            # Remove common prefixes
            for prefix in ["-", "*", "•", "–"]:
                if line.startswith(prefix):
                    line = line[len(prefix):].strip()
            if line:
                suggestions.append(line)

        return suggestions[:num_suggestions]

    def get_token_usage(self) -> Dict[str, int]:
        """Get total token usage.

        Returns:
            Dictionary with input and output token counts.
        """
        return self._token_usage.copy()

    def reset_token_usage(self) -> None:
        """Reset token usage counters."""
        self._token_usage = {"input_tokens": 0, "output_tokens": 0}
