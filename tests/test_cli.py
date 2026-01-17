"""Tests for CLI interface."""

import pytest
import sys
from unittest.mock import patch
from pathlib import Path

from academic_research_toolkit.cli import main


class TestCLI:
    """Tests for CLI functionality."""

    def test_main_no_args(self, capsys):
        """Test main with no arguments shows help."""
        with patch.object(sys, "argv", ["research-toolkit"]):
            result = main()

        assert result == 0
        captured = capsys.readouterr()
        assert "research-toolkit" in captured.out or "usage" in captured.out.lower()

    def test_main_version(self, capsys):
        """Test --version flag."""
        with patch.object(sys, "argv", ["research-toolkit", "--version"]):
            with pytest.raises(SystemExit) as exc_info:
                main()

        # argparse exits with 0 for --version
        assert exc_info.value.code == 0

    def test_main_help(self, capsys):
        """Test --help flag."""
        with patch.object(sys, "argv", ["research-toolkit", "--help"]):
            with pytest.raises(SystemExit) as exc_info:
                main()

        assert exc_info.value.code == 0
        captured = capsys.readouterr()
        assert "pdf" in captured.out
        assert "cite" in captured.out

    def test_pdf_command_missing_input(self, capsys):
        """Test pdf command with missing input."""
        with patch.object(sys, "argv", ["research-toolkit", "pdf", "-i", "/nonexistent", "-o", "/tmp"]):
            result = main()

        assert result == 1
        captured = capsys.readouterr()
        assert "not found" in captured.out.lower() or "error" in captured.out.lower()

    def test_cite_command_missing_input(self, capsys):
        """Test cite command with missing input."""
        with patch.object(sys, "argv", ["research-toolkit", "cite", "-i", "/nonexistent", "-o", "/tmp"]):
            result = main()

        assert result == 1

    def test_theme_command_missing_input(self, capsys):
        """Test theme command with missing input."""
        with patch.object(sys, "argv", ["research-toolkit", "theme", "-i", "/nonexistent", "-o", "/tmp"]):
            result = main()

        assert result == 1

    def test_biblio_command_invalid_format(self, capsys):
        """Test biblio command with invalid format."""
        # Using argparse choices, this should fail before our code runs
        with patch.object(sys, "argv", ["research-toolkit", "biblio", "-i", "/tmp/test.json", "-o", "/tmp/out.md", "-f", "invalid"]):
            with pytest.raises(SystemExit):
                main()

    def test_cite_with_file(self, temp_dir, sample_markdown_file, capsys):
        """Test cite command with actual file."""
        output_dir = temp_dir / "output"

        with patch.object(sys, "argv", [
            "research-toolkit", "cite",
            "-i", str(sample_markdown_file),
            "-o", str(output_dir)
        ]):
            result = main()

        # Should succeed
        assert result == 0
        captured = capsys.readouterr()
        assert "citation" in captured.out.lower()

    def test_theme_with_file(self, temp_dir, sample_markdown_file, capsys):
        """Test theme command with actual file."""
        output_dir = temp_dir / "output"

        with patch.object(sys, "argv", [
            "research-toolkit", "theme",
            "-i", str(sample_markdown_file),
            "-o", str(output_dir)
        ]):
            result = main()

        # Should succeed
        assert result == 0
        captured = capsys.readouterr()
        assert "theme" in captured.out.lower() or "complete" in captured.out.lower()


class TestCLISubcommands:
    """Tests for CLI subcommand parsing."""

    def test_pdf_subcommand_help(self, capsys):
        """Test pdf subcommand help."""
        with patch.object(sys, "argv", ["research-toolkit", "pdf", "--help"]):
            with pytest.raises(SystemExit) as exc_info:
                main()

        assert exc_info.value.code == 0
        captured = capsys.readouterr()
        assert "pdf" in captured.out.lower() or "extract" in captured.out.lower()

    def test_cite_subcommand_help(self, capsys):
        """Test cite subcommand help."""
        with patch.object(sys, "argv", ["research-toolkit", "cite", "--help"]):
            with pytest.raises(SystemExit) as exc_info:
                main()

        assert exc_info.value.code == 0

    def test_biblio_subcommand_formats(self, capsys):
        """Test biblio subcommand shows format options."""
        with patch.object(sys, "argv", ["research-toolkit", "biblio", "--help"]):
            with pytest.raises(SystemExit):
                main()

        captured = capsys.readouterr()
        assert "apa" in captured.out
        assert "mla" in captured.out
        assert "chicago" in captured.out
