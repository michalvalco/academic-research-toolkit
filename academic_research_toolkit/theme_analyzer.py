"""
Theme Analyzer for Academic Research

Identifies themes, concepts, and patterns in academic texts.
"""

import re
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Set
from collections import Counter, defaultdict


class ThemeAnalyzer:
    """Analyze themes and concepts in academic texts."""

    def __init__(self):
        """Initialize theme analyzer."""
        self.stop_words = self._load_stop_words()

        self.term_frequencies = Counter()
        self.term_contexts = defaultdict(list)
        self.cooccurrences = defaultdict(Counter)
        self.documents_processed = []

        self.min_term_length = 3
        self.context_window = 50
        self.cooccurrence_window = 100

    def _load_stop_words(self) -> Set[str]:
        """Load stop words for English and Slovak."""
        english = {
            "the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for",
            "of", "with", "by", "from", "as", "is", "was", "are", "were", "been",
            "be", "have", "has", "had", "do", "does", "did", "will", "would",
            "should", "could", "may", "might", "must", "can", "this", "that",
            "these", "those", "i", "you", "he", "she", "it", "we", "they",
            "what", "which", "who", "when", "where", "why", "how",
        }

        slovak = {
            "a", "aj", "ale", "alebo", "ako", "by", "bol", "bola", "boli", "bolo",
            "som", "si", "sme", "ste", "sú", "je", "má", "mať", "môže", "môžu",
            "na", "v", "vo", "z", "zo", "do", "pre", "pri", "po", "pod", "nad",
            "o", "od", "za", "s", "so", "k", "ku", "že", "aby", "ak", "keď",
            "ten", "tá", "to", "tí", "tie", "toho", "tej", "tým", "tento",
            "táto", "toto", "títo", "tieto", "bol", "bola", "bolo", "boli",
        }

        return english | slovak

    def analyze_file(self, filepath: Path) -> Dict:
        """
        Analyze a single markdown file.

        Args:
            filepath: Path to markdown file

        Returns:
            Document statistics dictionary
        """
        filepath = Path(filepath)

        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()

        content = self._skip_metadata(content)

        terms = self._extract_terms(content)

        for term in terms:
            self.term_frequencies[term] += 1

        significant_terms = [t for t, count in self.term_frequencies.most_common(50)]
        for term in significant_terms:
            contexts = self._extract_contexts(content, term)
            self.term_contexts[term].extend(contexts)

        self._find_cooccurrences(content, significant_terms)

        doc_stats = {
            "filename": filepath.name,
            "total_words": len(content.split()),
            "unique_terms": len(set(terms)),
            "processed": datetime.now().isoformat(),
        }

        self.documents_processed.append(doc_stats)
        return doc_stats

    def analyze_text(self, content: str, document_name: str = "text") -> Dict:
        """
        Analyze text content directly.

        Args:
            content: Text content to analyze
            document_name: Name for this document

        Returns:
            Document statistics dictionary
        """
        content = self._skip_metadata(content)
        terms = self._extract_terms(content)

        for term in terms:
            self.term_frequencies[term] += 1

        significant_terms = [t for t, count in self.term_frequencies.most_common(50)]
        for term in significant_terms:
            contexts = self._extract_contexts(content, term)
            self.term_contexts[term].extend(contexts)

        self._find_cooccurrences(content, significant_terms)

        doc_stats = {
            "filename": document_name,
            "total_words": len(content.split()),
            "unique_terms": len(set(terms)),
            "processed": datetime.now().isoformat(),
        }

        self.documents_processed.append(doc_stats)
        return doc_stats

    def analyze_directory(self, dirpath: Path) -> List[Dict]:
        """
        Analyze all markdown files in a directory.

        Args:
            dirpath: Directory path

        Returns:
            List of document statistics
        """
        dirpath = Path(dirpath)
        md_files = list(dirpath.glob("*.md"))

        for md_file in md_files:
            self.analyze_file(md_file)

        return self.documents_processed

    def _skip_metadata(self, content: str) -> str:
        """Skip the metadata section."""
        parts = content.split("## Extracted Text", 1)
        if len(parts) == 2:
            return parts[1]
        return content

    def _extract_terms(self, text: str) -> List[str]:
        """Extract meaningful terms from text."""
        text = text.lower()
        words = re.findall(r"\b[a-záčďéíľňóôŕšťúýž]+\b", text, re.UNICODE)

        terms = [
            w for w in words
            if w not in self.stop_words and len(w) >= self.min_term_length
        ]

        return terms

    def _extract_contexts(self, text: str, term: str) -> List[str]:
        """Extract context snippets where term appears."""
        contexts = []
        text_lower = text.lower()
        term_lower = term.lower()

        pos = 0
        while True:
            pos = text_lower.find(term_lower, pos)
            if pos == -1:
                break

            start = max(0, pos - self.context_window)
            end = min(len(text), pos + len(term) + self.context_window)

            context = text[start:end].strip()
            contexts.append(context)

            pos += len(term)

        return contexts[:3]

    def _find_cooccurrences(self, text: str, terms: List[str]) -> None:
        """Find terms that frequently appear together."""
        text_lower = text.lower()

        for i, term1 in enumerate(terms):
            positions = [
                m.start()
                for m in re.finditer(r"\b" + re.escape(term1) + r"\b", text_lower)
            ]

            for pos in positions:
                window_start = max(0, pos - self.cooccurrence_window)
                window_end = min(len(text), pos + self.cooccurrence_window)
                window = text_lower[window_start:window_end]

                for term2 in terms[i + 1 :]:
                    if term2 in window:
                        self.cooccurrences[term1][term2] += 1
                        self.cooccurrences[term2][term1] += 1

    def identify_themes(self) -> List[Dict]:
        """Identify major themes from term analysis."""
        themes = []
        top_terms = self.term_frequencies.most_common(30)

        for term, frequency in top_terms:
            doc_appearances = sum(
                1 for doc in self.documents_processed if term in str(doc)
            )
            uniqueness = 1.0 / (1.0 + doc_appearances)
            importance = frequency * (1 + uniqueness)

            related = []
            if term in self.cooccurrences:
                related = [
                    {"term": t, "strength": count}
                    for t, count in self.cooccurrences[term].most_common(5)
                ]

            contexts = self.term_contexts.get(term, [])[:3]

            theme = {
                "term": term,
                "frequency": frequency,
                "importance": round(importance, 2),
                "related_terms": related,
                "sample_contexts": contexts,
            }

            themes.append(theme)

        themes.sort(key=lambda x: x["importance"], reverse=True)
        return themes

    def identify_clusters(self) -> List[Dict]:
        """Identify clusters of related terms (concept groups)."""
        clusters = []
        processed = set()

        top_terms = [term for term, _ in self.term_frequencies.most_common(50)]

        for seed_term in top_terms:
            if seed_term in processed:
                continue

            if seed_term not in self.cooccurrences:
                continue

            cluster_terms = [seed_term]
            related = self.cooccurrences[seed_term].most_common(5)

            for related_term, strength in related:
                if strength >= 3:
                    cluster_terms.append(related_term)
                    processed.add(related_term)

            if len(cluster_terms) > 1:
                cluster = {
                    "central_term": seed_term,
                    "related_terms": cluster_terms[1:],
                    "cohesion": len(cluster_terms),
                    "total_mentions": sum(
                        self.term_frequencies[t] for t in cluster_terms
                    ),
                }
                clusters.append(cluster)
                processed.add(seed_term)

        clusters.sort(key=lambda x: x["cohesion"], reverse=True)
        return clusters

    def generate_insights(self) -> Dict:
        """Generate research insights and opportunities."""
        themes = self.identify_themes()
        clusters = self.identify_clusters()

        dominant = themes[:5] if themes else []

        emerging = [t for t in themes if 3 <= t["frequency"] <= 10][:5]

        single_mentions = [
            term for term, count in self.term_frequencies.items() if count == 1
        ]

        insights = {
            "dominant_themes": dominant,
            "emerging_themes": emerging,
            "concept_clusters": clusters[:5],
            "potential_gaps": {
                "count": len(single_mentions),
                "examples": single_mentions[:10],
            },
            "corpus_statistics": {
                "total_documents": len(self.documents_processed),
                "unique_terms": len(self.term_frequencies),
                "total_terms": sum(self.term_frequencies.values()),
            },
        }

        return insights

    def save_analysis(self, output_dir: Path, analysis_name: str = "analysis") -> Dict[str, str]:
        """
        Save analysis results.

        Args:
            output_dir: Output directory
            analysis_name: Base name for output files

        Returns:
            Dictionary with output file paths
        """
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        insights = self.generate_insights()

        json_path = output_dir / f"{analysis_name}_themes.json"
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(insights, f, indent=2, ensure_ascii=False)

        freq_path = output_dir / f"{analysis_name}_frequencies.json"
        freq_data = {
            "top_50_terms": [
                {"term": term, "frequency": count}
                for term, count in self.term_frequencies.most_common(50)
            ]
        }
        with open(freq_path, "w", encoding="utf-8") as f:
            json.dump(freq_data, f, indent=2, ensure_ascii=False)

        report_path = output_dir / f"{analysis_name}_report.md"
        self._generate_markdown_report(report_path, insights)

        return {
            "insights_path": str(json_path),
            "frequencies_path": str(freq_path),
            "report_path": str(report_path),
        }

    def _generate_markdown_report(self, output_path: Path, insights: Dict):
        """Generate human-readable markdown report."""
        with open(output_path, "w", encoding="utf-8") as f:
            f.write("# Theme Analysis Report\n\n")
            f.write(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")

            stats = insights["corpus_statistics"]
            f.write("## Corpus Statistics\n\n")
            f.write(f"- **Documents Analyzed:** {stats['total_documents']}\n")
            f.write(f"- **Unique Terms:** {stats['unique_terms']}\n")
            f.write(f"- **Total Term Occurrences:** {stats['total_terms']}\n\n")

            f.write("## Dominant Themes\n\n")
            for theme in insights["dominant_themes"]:
                f.write(f"### {theme['term'].title()}\n\n")
                f.write(f"- **Frequency:** {theme['frequency']} occurrences\n")
                f.write(f"- **Importance Score:** {theme['importance']}\n")

                if theme["related_terms"]:
                    f.write("- **Related Terms:**\n")
                    for rel in theme["related_terms"]:
                        f.write(f"  - {rel['term']} (co-occurs {rel['strength']} times)\n")

                f.write("\n---\n\n")

            if insights["concept_clusters"]:
                f.write("## Concept Clusters\n\n")
                for cluster in insights["concept_clusters"]:
                    f.write(f"### Cluster: {cluster['central_term'].title()}\n\n")
                    f.write(f"- **Related Terms:** {', '.join(cluster['related_terms'])}\n")
                    f.write(f"- **Total Mentions:** {cluster['total_mentions']}\n\n")

            gaps = insights["potential_gaps"]
            f.write("## Potential Research Gaps\n\n")
            f.write(f"Found **{gaps['count']}** terms mentioned only once.\n\n")


def main():
    """CLI entry point for standalone usage."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Analyze themes and concepts in academic texts"
    )
    parser.add_argument("--input", "-i", required=True, help="Markdown file or directory")
    parser.add_argument("--output", "-o", required=True, help="Directory for results")

    args = parser.parse_args()

    analyzer = ThemeAnalyzer()
    input_path = Path(args.input)

    if input_path.is_file():
        analyzer.analyze_file(input_path)
    else:
        analyzer.analyze_directory(input_path)

    analyzer.save_analysis(Path(args.output))

    print(f"\nAnalyzed {len(analyzer.documents_processed)} document(s)")
    print(f"Found {len(analyzer.term_frequencies)} unique terms")


if __name__ == "__main__":
    main()
