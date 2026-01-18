"""
Research gap detection and analysis.

Identifies gaps in research coverage, temporal patterns, methodologies,
and geographic distribution. Works with rule-based analysis by default,
with optional AI-powered enhancement.
"""

import logging
import re
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from academic_research_toolkit.intelligence.assistant import ResearchAssistant


logger = logging.getLogger(__name__)


@dataclass
class Gap:
    """Represents a detected research gap."""

    gap_type: str  # 'temporal', 'methodological', 'geographic', 'topical'
    description: str
    severity: str  # 'high', 'medium', 'low'
    evidence: List[str] = field(default_factory=list)
    suggestions: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "gap_type": self.gap_type,
            "description": self.description,
            "severity": self.severity,
            "evidence": self.evidence,
            "suggestions": self.suggestions,
        }


class GapDetector:
    """Detect research gaps and opportunities.

    Uses rule-based analysis by default, with optional AI-powered
    enhancement when a ResearchAssistant is provided.
    """

    # Known research methodologies to detect
    METHODOLOGIES = {
        "quantitative": [
            "survey", "experiment", "statistical", "regression",
            "anova", "correlation", "quantitative", "measurement",
            "questionnaire", "scale", "sample", "hypothesis test",
        ],
        "qualitative": [
            "interview", "ethnography", "case study", "grounded theory",
            "qualitative", "thematic", "narrative", "phenomenology",
            "observation", "focus group", "discourse analysis",
        ],
        "mixed_methods": [
            "mixed method", "mixed-method", "triangulation",
            "convergent design", "sequential design", "embedded design",
        ],
        "computational": [
            "machine learning", "deep learning", "neural network",
            "nlp", "natural language processing", "algorithm",
            "simulation", "computational", "data mining", "ai", "artificial intelligence",
        ],
        "meta_analysis": [
            "meta-analysis", "systematic review", "literature review",
            "meta analysis", "scoping review", "bibliometric",
        ],
        "theoretical": [
            "theoretical", "conceptual", "framework", "model",
            "theory building", "taxonomy", "typology",
        ],
    }

    # Geographic regions and countries for detection
    REGIONS = {
        "north_america": [
            "united states", "usa", "canada", "mexico", "american",
            "canadian", "north america", "north american",
        ],
        "europe": [
            "europe", "european", "uk", "united kingdom", "germany",
            "france", "italy", "spain", "netherlands", "belgium",
            "sweden", "norway", "finland", "denmark", "austria",
            "switzerland", "poland", "britain", "british", "german",
            "french", "italian", "spanish", "dutch", "eu", "european union",
        ],
        "asia_pacific": [
            "china", "chinese", "japan", "japanese", "korea", "korean",
            "india", "indian", "australia", "australian", "singapore",
            "taiwan", "hong kong", "asia", "asian", "pacific",
            "thailand", "vietnam", "indonesia", "malaysia", "philippines",
        ],
        "latin_america": [
            "brazil", "brazilian", "argentina", "chile", "colombia",
            "peru", "latin america", "south america", "central america",
            "mexican", "caribbean",
        ],
        "middle_east_africa": [
            "africa", "african", "middle east", "israel", "turkey",
            "iran", "saudi", "egypt", "south africa", "nigeria",
            "kenya", "morocco", "uae", "emirates", "arab",
        ],
    }

    def __init__(
        self,
        assistant: Optional["ResearchAssistant"] = None,
        use_ai: bool = True,
    ):
        """Initialize the gap detector.

        Args:
            assistant: Optional AI assistant for enhanced analysis.
            use_ai: Whether to use AI when assistant is available.
        """
        self.assistant = assistant
        self.use_ai = use_ai and assistant is not None

    def _extract_year(self, citation: Dict[str, Any]) -> Optional[int]:
        """Extract year from citation."""
        year = citation.get("year")
        if year:
            if isinstance(year, int):
                return year
            try:
                # Extract 4-digit year from string
                match = re.search(r'\b(19|20)\d{2}\b', str(year))
                if match:
                    return int(match.group())
            except (ValueError, TypeError):
                # If the year string is malformed, ignore it and fall back to None
                pass
        return None

    def _get_citation_text(self, citation: Dict[str, Any]) -> str:
        """Get searchable text from citation."""
        parts = []
        for field in ["title", "raw_text", "source", "notes"]:
            if citation.get(field):
                parts.append(str(citation[field]).lower())
        return " ".join(parts)

    def analyze_coverage(
        self,
        citations: List[Dict[str, Any]],
        themes: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Analyze topic coverage across citations.

        Args:
            citations: List of citation dictionaries.
            themes: Optional theme analysis results.

        Returns:
            Coverage analysis results.
        """
        if not citations:
            return {
                "total_citations": 0,
                "theme_coverage": {},
                "coverage_gaps": [],
            }

        # Extract themes from citations if not provided
        if themes is None:
            themes = self._extract_themes_from_citations(citations)

        # Count theme occurrences
        theme_counts: Counter = Counter()
        for citation in citations:
            text = self._get_citation_text(citation)
            for theme in themes.get("dominant_themes", []):
                term = theme.get("term", "").lower()
                if term and term in text:
                    theme_counts[term] += 1

        # Calculate coverage percentages
        total = len(citations)
        coverage = {
            term: count / total for term, count in theme_counts.items()
        }

        # Identify gaps (themes with low coverage)
        coverage_gaps = []
        for theme in themes.get("dominant_themes", []):
            term = theme.get("term", "")
            cov = coverage.get(term.lower(), 0)
            if cov < 0.1:  # Less than 10% coverage
                coverage_gaps.append({
                    "theme": term,
                    "coverage": cov,
                    "expected_based_on_frequency": theme.get("frequency", 0),
                })

        return {
            "total_citations": total,
            "theme_coverage": coverage,
            "coverage_gaps": coverage_gaps,
            "well_covered_themes": [
                t for t, c in coverage.items() if c >= 0.3
            ],
        }

    def _extract_themes_from_citations(
        self,
        citations: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """Extract basic themes from citations when no theme analysis is provided."""
        word_counts: Counter = Counter()

        # Common stop words to skip
        stop_words = {
            "the", "a", "an", "and", "or", "but", "in", "on", "at", "to",
            "for", "of", "with", "by", "from", "as", "is", "was", "are",
            "were", "been", "be", "have", "has", "had", "do", "does", "did",
            "will", "would", "could", "should", "may", "might", "must",
            "that", "which", "who", "whom", "this", "these", "those",
            "it", "its", "their", "there", "here", "where", "when", "what",
            "how", "why", "all", "each", "every", "both", "few", "more",
            "most", "other", "some", "such", "no", "not", "only", "own",
            "same", "so", "than", "too", "very", "can", "just", "into",
        }

        for citation in citations:
            text = self._get_citation_text(citation)
            words = re.findall(r'\b[a-z]{3,}\b', text)
            for word in words:
                if word not in stop_words:
                    word_counts[word] += 1

        # Get top themes
        dominant_themes = [
            {"term": term, "frequency": count}
            for term, count in word_counts.most_common(20)
        ]

        return {"dominant_themes": dominant_themes}

    def find_temporal_gaps(
        self,
        citations: List[Dict[str, Any]],
        min_year: Optional[int] = None,
        max_year: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """Find time periods with sparse research.

        Args:
            citations: List of citation dictionaries.
            min_year: Minimum year to consider.
            max_year: Maximum year to consider.

        Returns:
            List of temporal gaps with year ranges and descriptions.
        """
        # Extract years
        years = []
        for citation in citations:
            year = self._extract_year(citation)
            if year:
                years.append(year)

        if not years:
            return []

        # Set range
        if min_year is None:
            min_year = min(years)
        if max_year is None:
            max_year = max(years)

        # Count publications per year
        year_counts = Counter(years)

        # Calculate average publications per year
        total_years = max_year - min_year + 1
        if total_years <= 0:
            return []

        avg_per_year = len(years) / total_years

        # Find gaps (years with significantly fewer publications)
        gaps = []
        current_gap_start = None
        current_gap_years = []

        for year in range(min_year, max_year + 1):
            count = year_counts.get(year, 0)

            if count < avg_per_year * 0.5:  # Less than 50% of average
                if current_gap_start is None:
                    current_gap_start = year
                current_gap_years.append(year)
            else:
                if current_gap_start is not None and len(current_gap_years) >= 2:
                    gaps.append({
                        "start_year": current_gap_start,
                        "end_year": current_gap_years[-1],
                        "duration": len(current_gap_years),
                        "total_publications": sum(
                            year_counts.get(y, 0) for y in current_gap_years
                        ),
                        "expected_publications": round(
                            avg_per_year * len(current_gap_years)
                        ),
                        "severity": "high" if len(current_gap_years) >= 5 else "medium",
                    })
                current_gap_start = None
                current_gap_years = []

        # Check final gap
        if current_gap_start is not None and len(current_gap_years) >= 2:
            gaps.append({
                "start_year": current_gap_start,
                "end_year": current_gap_years[-1],
                "duration": len(current_gap_years),
                "total_publications": sum(
                    year_counts.get(y, 0) for y in current_gap_years
                ),
                "expected_publications": round(
                    avg_per_year * len(current_gap_years)
                ),
                "severity": "high" if len(current_gap_years) >= 5 else "medium",
            })

        return gaps

    def find_methodological_gaps(
        self,
        citations: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        """Identify underused methodologies.

        Args:
            citations: List of citation dictionaries.

        Returns:
            List of methodological gaps with descriptions.
        """
        # Detect methodologies in citations
        methodology_counts: Dict[str, int] = defaultdict(int)
        methodology_citations: Dict[str, List[str]] = defaultdict(list)

        for citation in citations:
            text = self._get_citation_text(citation)
            title = citation.get("title", "Unknown")

            for method_type, keywords in self.METHODOLOGIES.items():
                for keyword in keywords:
                    if keyword in text:
                        methodology_counts[method_type] += 1
                        if title not in methodology_citations[method_type]:
                            methodology_citations[method_type].append(title)
                        break  # Count each citation once per methodology

        # Calculate percentages
        total = len(citations) if citations else 1
        methodology_percentages = {
            method: count / total
            for method, count in methodology_counts.items()
        }

        # Identify gaps
        gaps = []
        for method_type in self.METHODOLOGIES:
            percentage = methodology_percentages.get(method_type, 0)

            if percentage < 0.05:  # Less than 5%
                severity = "high"
            elif percentage < 0.15:  # Less than 15%
                severity = "medium"
            else:
                continue  # Not a gap

            gaps.append({
                "methodology": method_type,
                "current_usage": percentage,
                "citation_count": methodology_counts.get(method_type, 0),
                "severity": severity,
                "example_keywords": self.METHODOLOGIES[method_type][:3],
                "suggestion": f"Consider incorporating {method_type.replace('_', ' ')} approaches",
            })

        # Sort by severity
        severity_order = {"high": 0, "medium": 1, "low": 2}
        gaps.sort(key=lambda x: severity_order.get(x["severity"], 3))

        return gaps

    def find_geographic_gaps(
        self,
        citations: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        """Identify geographic regions with limited research.

        Args:
            citations: List of citation dictionaries.

        Returns:
            List of geographic gaps with descriptions.
        """
        # Detect regions in citations
        region_counts: Dict[str, int] = defaultdict(int)
        region_citations: Dict[str, List[str]] = defaultdict(list)

        for citation in citations:
            text = self._get_citation_text(citation)
            title = citation.get("title", "Unknown")

            for region, keywords in self.REGIONS.items():
                for keyword in keywords:
                    if keyword in text:
                        region_counts[region] += 1
                        if title not in region_citations[region]:
                            region_citations[region].append(title)
                        break  # Count each citation once per region

        # Calculate percentages
        total = len(citations) if citations else 1
        region_percentages = {
            region: count / total
            for region, count in region_counts.items()
        }

        # Identify gaps
        gaps = []
        for region in self.REGIONS:
            percentage = region_percentages.get(region, 0)

            if percentage < 0.02:  # Less than 2%
                severity = "high"
            elif percentage < 0.1:  # Less than 10%
                severity = "medium"
            else:
                continue  # Not a gap

            gaps.append({
                "region": region.replace("_", " ").title(),
                "current_coverage": percentage,
                "citation_count": region_counts.get(region, 0),
                "severity": severity,
                "suggestion": f"Consider research focusing on {region.replace('_', ' ').title()}",
            })

        # Sort by severity
        severity_order = {"high": 0, "medium": 1, "low": 2}
        gaps.sort(key=lambda x: severity_order.get(x["severity"], 3))

        return gaps

    def suggest_research_questions(
        self,
        citations: List[Dict[str, Any]],
        themes: Optional[Dict[str, Any]] = None,
        num_questions: int = 5,
    ) -> List[Dict[str, Any]]:
        """Generate potential research questions based on gaps.

        Args:
            citations: List of citation dictionaries.
            themes: Optional theme analysis results.
            num_questions: Number of questions to generate.

        Returns:
            List of suggested research questions with context.
        """
        # Run gap analyses
        temporal_gaps = self.find_temporal_gaps(citations)
        methodological_gaps = self.find_methodological_gaps(citations)
        geographic_gaps = self.find_geographic_gaps(citations)

        questions = []

        # Generate questions from temporal gaps
        for gap in temporal_gaps[:2]:
            questions.append({
                "question": f"What developments occurred in the field between {gap['start_year']} and {gap['end_year']}?",
                "gap_type": "temporal",
                "rationale": f"Limited research found for this {gap['duration']}-year period",
                "severity": gap["severity"],
            })

        # Generate questions from methodological gaps
        for gap in methodological_gaps[:2]:
            method = gap["methodology"].replace("_", " ")
            questions.append({
                "question": f"How can {method} approaches contribute to understanding this topic?",
                "gap_type": "methodological",
                "rationale": f"Only {gap['current_usage']:.1%} of papers use {method} methods",
                "severity": gap["severity"],
            })

        # Generate questions from geographic gaps
        for gap in geographic_gaps[:2]:
            region = gap["region"]
            questions.append({
                "question": f"What unique perspectives might research from {region} contribute?",
                "gap_type": "geographic",
                "rationale": f"Only {gap['current_coverage']:.1%} of papers focus on {region}",
                "severity": gap["severity"],
            })

        # Use AI for additional questions if available
        if self.use_ai and self.assistant and len(questions) < num_questions:
            ai_questions = self._generate_ai_questions(
                citations, themes, num_questions - len(questions)
            )
            questions.extend(ai_questions)

        return questions[:num_questions]

    def _generate_ai_questions(
        self,
        citations: List[Dict[str, Any]],
        themes: Optional[Dict[str, Any]],
        num_questions: int,
    ) -> List[Dict[str, Any]]:
        """Generate research questions using AI assistant."""
        if not self.assistant:
            return []

        # Build context from citations
        citation_summaries = []
        for citation in citations[:10]:  # Limit context size
            parts = []
            if citation.get("title"):
                parts.append(citation["title"])
            if citation.get("year"):
                parts.append(f"({citation['year']})")
            if parts:
                citation_summaries.append(" ".join(parts))

        context = "\n".join(f"- {s}" for s in citation_summaries)

        prompt = f"""Based on the following research corpus, suggest {num_questions} novel research questions that address gaps in the literature.

Research papers in the corpus:
{context}

For each question, identify:
1. The research question
2. Why this represents a gap
3. Potential methodology to address it

Focus on questions that are specific, novel, and researchable."""

        try:
            response = self.assistant._call_claude(
                prompt,
                "You are a research advisor helping identify promising research directions.",
            )

            # Parse response into questions (simple parsing)
            ai_questions = []
            lines = response.split("\n")
            current_question = None

            for line in lines:
                line = line.strip()
                if line and ("?" in line or line.startswith("Question")):
                    if current_question:
                        ai_questions.append(current_question)
                    # Extract question text
                    question_text = line
                    for prefix in ["1.", "2.", "3.", "4.", "5.", "-", "*", "Question:", "Q:"]:
                        if question_text.startswith(prefix):
                            question_text = question_text[len(prefix):].strip()
                    current_question = {
                        "question": question_text,
                        "gap_type": "ai_identified",
                        "rationale": "Identified through AI analysis of the corpus",
                        "severity": "medium",
                    }

            if current_question:
                ai_questions.append(current_question)

            return ai_questions[:num_questions]

        except Exception as e:
            # Log the exception but continue with rule-based analysis
            logger.warning(f"AI question generation failed: {e}")
            return []

    def generate_gap_report(
        self,
        citations: List[Dict[str, Any]],
        themes: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Generate comprehensive gap analysis report.

        Args:
            citations: List of citation dictionaries.
            themes: Optional theme analysis results.

        Returns:
            Comprehensive gap analysis report.
        """
        # Run all analyses
        coverage = self.analyze_coverage(citations, themes)
        temporal_gaps = self.find_temporal_gaps(citations)
        methodological_gaps = self.find_methodological_gaps(citations)
        geographic_gaps = self.find_geographic_gaps(citations)
        research_questions = self.suggest_research_questions(citations, themes)

        # Calculate summary statistics
        high_severity_count = sum(
            1 for gaps in [temporal_gaps, methodological_gaps, geographic_gaps]
            for gap in gaps if gap.get("severity") == "high"
        )
        medium_severity_count = sum(
            1 for gaps in [temporal_gaps, methodological_gaps, geographic_gaps]
            for gap in gaps if gap.get("severity") == "medium"
        )

        # Extract years for temporal summary
        years = []
        for citation in citations:
            year = self._extract_year(citation)
            if year:
                years.append(year)

        temporal_summary = {
            "min_year": min(years) if years else None,
            "max_year": max(years) if years else None,
            "total_years": max(years) - min(years) + 1 if years else 0,
            "gap_years": sum(g["duration"] for g in temporal_gaps),
        }

        return {
            "summary": {
                "total_citations": len(citations),
                "total_gaps_found": len(temporal_gaps) + len(methodological_gaps) + len(geographic_gaps),
                "high_severity_gaps": high_severity_count,
                "medium_severity_gaps": medium_severity_count,
                "temporal_range": temporal_summary,
            },
            "coverage_analysis": coverage,
            "temporal_gaps": temporal_gaps,
            "methodological_gaps": methodological_gaps,
            "geographic_gaps": geographic_gaps,
            "suggested_research_questions": research_questions,
            "recommendations": self._generate_recommendations(
                temporal_gaps, methodological_gaps, geographic_gaps
            ),
        }

    def _generate_recommendations(
        self,
        temporal_gaps: List[Dict[str, Any]],
        methodological_gaps: List[Dict[str, Any]],
        geographic_gaps: List[Dict[str, Any]],
    ) -> List[str]:
        """Generate prioritized recommendations based on gaps."""
        recommendations = []

        # High-priority temporal gaps
        for gap in temporal_gaps:
            if gap.get("severity") == "high":
                recommendations.append(
                    f"Investigate research developments between {gap['start_year']}-{gap['end_year']} "
                    f"({gap['duration']} year gap with only {gap['total_publications']} publications)"
                )

        # High-priority methodological gaps
        for gap in methodological_gaps:
            if gap.get("severity") == "high":
                recommendations.append(gap["suggestion"])

        # High-priority geographic gaps
        for gap in geographic_gaps:
            if gap.get("severity") == "high":
                recommendations.append(gap["suggestion"])

        # Medium-priority gaps
        for gap in temporal_gaps + methodological_gaps + geographic_gaps:
            if gap.get("severity") == "medium" and len(recommendations) < 10:
                if "suggestion" in gap:
                    recommendations.append(gap["suggestion"])

        return recommendations[:10]  # Limit to top 10
