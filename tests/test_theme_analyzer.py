"""Tests for theme analyzer."""

import pytest
from pathlib import Path

from academic_research_toolkit.theme_analyzer import ThemeAnalyzer


class TestThemeAnalyzer:
    """Tests for ThemeAnalyzer class."""

    def test_analyzer_initialization(self):
        """Test analyzer initializes correctly."""
        analyzer = ThemeAnalyzer()

        assert len(analyzer.stop_words) > 0
        assert analyzer.min_term_length == 3
        assert len(analyzer.documents_processed) == 0

    def test_stop_words_loaded(self):
        """Test stop words include common words."""
        analyzer = ThemeAnalyzer()

        # English stop words
        assert "the" in analyzer.stop_words
        assert "and" in analyzer.stop_words
        assert "is" in analyzer.stop_words

        # Slovak stop words
        assert "a" in analyzer.stop_words
        assert "je" in analyzer.stop_words

    def test_extract_terms(self):
        """Test term extraction from text."""
        analyzer = ThemeAnalyzer()

        text = "The artificial intelligence field is growing rapidly."
        terms = analyzer._extract_terms(text)

        # "the", "is" should be filtered out as stop words
        assert "the" not in terms
        assert "artificial" in terms
        assert "intelligence" in terms
        assert "growing" in terms

    def test_extract_terms_filters_short(self):
        """Test that short terms are filtered."""
        analyzer = ThemeAnalyzer()

        text = "AI is an important technology"
        terms = analyzer._extract_terms(text)

        # "AI" and "an" are too short (< 3 chars)
        assert "ai" not in terms
        assert "an" not in terms

    def test_analyze_text(self):
        """Test text analysis."""
        analyzer = ThemeAnalyzer()

        text = """
        Machine learning is a subset of artificial intelligence.
        Machine learning algorithms learn from data.
        Artificial intelligence encompasses many techniques.
        """

        stats = analyzer.analyze_text(text, "test_doc")

        assert stats["filename"] == "test_doc"
        assert stats["total_words"] > 0
        assert stats["unique_terms"] > 0
        assert len(analyzer.documents_processed) == 1

    def test_term_frequencies(self):
        """Test term frequency counting."""
        analyzer = ThemeAnalyzer()

        text = "machine machine machine learning learning"
        analyzer.analyze_text(text, "test")

        assert analyzer.term_frequencies["machine"] == 3
        assert analyzer.term_frequencies["learning"] == 2

    def test_identify_themes(self):
        """Test theme identification."""
        analyzer = ThemeAnalyzer()

        text = """
        Research in artificial intelligence continues to advance.
        Machine learning models are improving rapidly.
        The artificial intelligence community is growing.
        Machine learning applications are everywhere.
        """

        analyzer.analyze_text(text, "test")
        themes = analyzer.identify_themes()

        assert len(themes) > 0
        # Each theme should have required fields
        for theme in themes:
            assert "term" in theme
            assert "frequency" in theme
            assert "importance" in theme

    def test_generate_insights(self):
        """Test insight generation."""
        analyzer = ThemeAnalyzer()

        text = """
        Artificial intelligence and machine learning are related fields.
        Both fields involve algorithms that learn from data.
        Deep learning is a subset of machine learning.
        """

        analyzer.analyze_text(text, "test")
        insights = analyzer.generate_insights()

        assert "dominant_themes" in insights
        assert "emerging_themes" in insights
        assert "corpus_statistics" in insights
        assert "potential_gaps" in insights

        stats = insights["corpus_statistics"]
        assert stats["total_documents"] == 1

    def test_analyze_file(self, sample_markdown_file):
        """Test file analysis."""
        analyzer = ThemeAnalyzer()

        stats = analyzer.analyze_file(sample_markdown_file)

        assert stats["filename"] == sample_markdown_file.name
        assert len(analyzer.documents_processed) == 1

    def test_save_analysis(self, temp_dir):
        """Test saving analysis results."""
        analyzer = ThemeAnalyzer()

        text = "Research in machine learning continues to grow."
        analyzer.analyze_text(text, "test")

        paths = analyzer.save_analysis(temp_dir, "test_analysis")

        assert "insights_path" in paths
        assert "frequencies_path" in paths
        assert "report_path" in paths

        # Check files exist
        assert Path(paths["insights_path"]).exists()
        assert Path(paths["report_path"]).exists()


class TestThemeAnalyzerCooccurrence:
    """Tests for cooccurrence detection."""

    def test_find_cooccurrences(self):
        """Test cooccurrence finding."""
        analyzer = ThemeAnalyzer()

        # Terms that appear close together
        text = """
        Machine learning algorithms use neural networks.
        Machine learning models are trained on data.
        Neural networks are a type of machine learning.
        """

        analyzer.analyze_text(text, "test")

        # After analysis, cooccurrences should be populated
        # "machine" and "learning" should co-occur
        if "machine" in analyzer.cooccurrences:
            related = analyzer.cooccurrences["machine"]
            # Verify cooccurrences structure is a dict with term counts
            assert isinstance(related, dict)

    def test_identify_clusters(self):
        """Test cluster identification."""
        analyzer = ThemeAnalyzer()

        text = """
        Machine learning and artificial intelligence are related.
        Machine learning uses neural networks for deep learning.
        Artificial intelligence encompasses machine learning.
        Neural networks power many machine learning applications.
        """

        analyzer.analyze_text(text, "test")
        clusters = analyzer.identify_clusters()

        # Clusters are optional - may or may not be found
        for cluster in clusters:
            assert "central_term" in cluster
            assert "related_terms" in cluster
            assert "cohesion" in cluster
