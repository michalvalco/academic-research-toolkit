#!/usr/bin/env python3
"""
Bibliography Generator for Academic Research

Generates formatted bibliographies from extracted citation data.
Supports multiple citation formats (APA, MLA, Chicago) with proper handling
of Slovak characters and author names.

Usage:
    python bibliography_generator.py --input <citations.json> --output <bibliography.txt> --format apa
"""

import argparse
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional
import unicodedata


class BibliographyGenerator:
    """Generate formatted bibliographies from citation data."""
    
    def __init__(self, format_style: str = 'apa'):
        """
        Initialize bibliography generator.
        
        Args:
            format_style: Citation format ('apa', 'mla', 'chicago')
        """
        self.format_style = format_style.lower()
        self.supported_formats = ['apa', 'mla', 'chicago']
        
        if self.format_style not in self.supported_formats:
            raise ValueError(
                f"Unsupported format: {format_style}. "
                f"Supported formats: {', '.join(self.supported_formats)}"
            )
    
    def generate_from_file(self, citations_file: Path) -> str:
        """
        Generate bibliography from a citations JSON file.
        
        Args:
            citations_file: Path to citations JSON file
            
        Returns:
            Formatted bibliography as string
        """
        print(f"\nGenerating {self.format_style.upper()} bibliography from: {citations_file.name}")
        
        # Load citations
        with open(citations_file, 'r', encoding='utf-8') as f:
            citations = json.load(f)
        
        if not citations:
            print("  ⚠ No citations found in file")
            return ""
        
        # Generate bibliography
        bibliography = self.generate_bibliography(citations)
        
        print(f"  ✓ Generated {len(citations)} bibliography entries")
        
        return bibliography
    
    def generate_bibliography(self, citations: List[Dict]) -> str:
        """
        Generate formatted bibliography from citation dictionaries.
        
        Args:
            citations: List of citation dictionaries
            
        Returns:
            Formatted bibliography as string
        """
        # Sort citations alphabetically by author (last name)
        sorted_citations = self._sort_citations(citations)
        
        # Format each citation
        formatted_entries = []
        for citation in sorted_citations:
            entry = self._format_citation(citation)
            if entry:
                formatted_entries.append(entry)
        
        # Join with appropriate spacing
        if self.format_style == 'apa':
            # APA uses hanging indent, single entry per line
            bibliography = '\n\n'.join(formatted_entries)
        elif self.format_style == 'mla':
            # MLA uses hanging indent
            bibliography = '\n\n'.join(formatted_entries)
        else:  # chicago
            # Chicago uses footnote numbering
            numbered_entries = [
                f"{i+1}. {entry}" 
                for i, entry in enumerate(formatted_entries)
            ]
            bibliography = '\n\n'.join(numbered_entries)
        
        return bibliography
    
    def _sort_citations(self, citations: List[Dict]) -> List[Dict]:
        """
        Sort citations alphabetically by author last name.
        Handles Slovak characters properly.
        """
        def get_sort_key(citation: Dict) -> str:
            """Extract sortable key from citation."""
            authors = citation.get('authors', [])
            
            if not authors:
                # No author: use title or raw text
                title = citation.get('title', citation.get('raw_text', ''))
                return self._normalize_for_sorting(title)
            
            # Get first author's last name
            first_author = authors[0]
            last_name = self._extract_last_name(first_author)
            
            return self._normalize_for_sorting(last_name)
        
        return sorted(citations, key=get_sort_key)
    
    def _extract_last_name(self, author: str) -> str:
        """
        Extract last name from author string.
        Handles formats like "John Smith" or "Smith, John"
        """
        author = author.strip()
        
        # Format: "Last, First"
        if ',' in author:
            parts = author.split(',')
            return parts[0].strip()
        
        # Format: "First Last" or "First Middle Last"
        parts = author.split()
        if parts:
            return parts[-1]  # Last word is last name
        
        return author
    
    def _normalize_for_sorting(self, text: str) -> str:
        """
        Normalize text for alphabetical sorting.
        Converts Slovak characters to sortable equivalents while preserving order.
        """
        # Remove leading articles
        text = text.strip()
        for article in ['The ', 'A ', 'An ', 'Der ', 'Die ', 'Das ', 'Le ', 'La ', 'Les ']:
            if text.startswith(article):
                text = text[len(article):]
                break
        
        # Normalize unicode (decompose accented characters)
        normalized = unicodedata.normalize('NFD', text)
        
        # Convert to lowercase for case-insensitive sorting
        return normalized.lower()
    
    def _format_citation(self, citation: Dict) -> Optional[str]:
        """
        Format a single citation according to the selected style.
        
        Args:
            citation: Citation dictionary
            
        Returns:
            Formatted citation string or None if citation cannot be formatted
        """
        citation_type = citation.get('citation_type', 'unclassified')
        
        if self.format_style == 'apa':
            return self._format_apa(citation, citation_type)
        elif self.format_style == 'mla':
            return self._format_mla(citation, citation_type)
        else:  # chicago
            return self._format_chicago(citation, citation_type)
    
    def _format_apa(self, citation: Dict, ctype: str) -> Optional[str]:
        """Format citation in APA style."""
        
        if ctype == 'book':
            return self._format_apa_book(citation)
        elif ctype == 'article':
            return self._format_apa_article(citation)
        elif ctype == 'online':
            return self._format_apa_online(citation)
        elif ctype == 'interview':
            return self._format_apa_interview(citation)
        else:
            # Unclassified or other types - use raw text
            return citation.get('raw_text', '')
    
    def _format_apa_book(self, citation: Dict) -> str:
        """
        Format book citation in APA style.
        Format: Author, A. A. (Year). Title of work. Publisher.
        """
        parts = []
        
        # Authors
        authors = citation.get('authors', [])
        if authors:
            formatted_authors = self._format_apa_authors(authors)
            parts.append(formatted_authors)
        
        # Year
        year = citation.get('year')
        if year:
            parts.append(f"({year}).")
        
        # Title (italicized in actual APA, we'll use plain text)
        title = citation.get('title')
        if title:
            parts.append(f"{title}.")
        
        # Publisher
        publisher = citation.get('publisher')
        location = citation.get('location')
        
        if location and publisher:
            parts.append(f"{location}: {publisher}.")
        elif publisher:
            parts.append(f"{publisher}.")
        
        return ' '.join(parts)
    
    def _format_apa_article(self, citation: Dict) -> str:
        """
        Format article citation in APA style.
        Format: Author, A. A. (Year). Title of article. Title of Journal, volume(issue), pages.
        """
        parts = []
        
        # Authors
        authors = citation.get('authors', [])
        if authors:
            formatted_authors = self._format_apa_authors(authors)
            parts.append(formatted_authors)
        
        # Year
        year = citation.get('year')
        if year:
            parts.append(f"({year}).")
        
        # Article title
        title = citation.get('title')
        if title:
            parts.append(f"{title}.")
        
        # Journal information
        source = citation.get('source')
        if source:
            # Extract volume/issue/pages from notes if available
            notes = citation.get('notes', '')
            parts.append(f"{source}, {notes}.")
        
        return ' '.join(parts)
    
    def _format_apa_online(self, citation: Dict) -> str:
        """
        Format online source in APA style.
        Format: Author. (Year). Title. Retrieved from URL
        """
        parts = []
        
        # Authors
        authors = citation.get('authors', [])
        if authors:
            formatted_authors = self._format_apa_authors(authors)
            parts.append(formatted_authors)
        
        # Year
        year = citation.get('year')
        if year:
            parts.append(f"({year}).")
        
        # Title
        title = citation.get('title')
        if title:
            parts.append(f"{title}.")
        
        # URL
        url = citation.get('url')
        if url:
            parts.append(f"Retrieved from {url}")
        
        return ' '.join(parts) if parts else citation.get('raw_text', '')
    
    def _format_apa_interview(self, citation: Dict) -> str:
        """Format interview citation in APA style."""
        parts = []
        
        # Interviewee
        authors = citation.get('authors', [])
        if authors:
            formatted_authors = self._format_apa_authors(authors)
            parts.append(formatted_authors)
        
        # Year
        year = citation.get('year')
        if year:
            parts.append(f"({year}).")
        
        # Title/source
        source = citation.get('source')
        if source:
            parts.append(f"{source}.")
        
        return ' '.join(parts)
    
    def _format_apa_authors(self, authors: List[str]) -> str:
        """
        Format author names in APA style.
        Format: Last, F. M., & Last2, F. M.
        """
        if not authors:
            return ""
        
        formatted = []
        for author in authors[:7]:  # APA lists up to 7 authors
            formatted.append(self._format_apa_single_author(author))
        
        if len(authors) > 7:
            # More than 7 authors: show first 6, then "...", then last
            formatted = formatted[:6]
            formatted.append("...")
            formatted.append(self._format_apa_single_author(authors[-1]))
        
        if len(formatted) == 1:
            return formatted[0]
        elif len(formatted) == 2:
            return f"{formatted[0]}, & {formatted[1]}"
        else:
            return ', '.join(formatted[:-1]) + f", & {formatted[-1]}"
    
    def _format_apa_single_author(self, author: str) -> str:
        """
        Format single author name in APA style.
        Converts "First Last" to "Last, F."
        """
        author = author.strip()
        
        # Already in "Last, First" format
        if ',' in author:
            parts = author.split(',', 1)
            last_name = parts[0].strip()
            first_name = parts[1].strip()
        else:
            # "First Last" format
            parts = author.split()
            if len(parts) >= 2:
                first_name = ' '.join(parts[:-1])
                last_name = parts[-1]
            else:
                # Only one name
                return author
        
        # Get initials
        initials = self._get_initials(first_name)
        
        return f"{last_name}, {initials}"
    
    def _get_initials(self, name: str) -> str:
        """Get initials from a name."""
        parts = name.split()
        initials = [f"{p[0].upper()}." for p in parts if p]
        return ' '.join(initials)
    
    def _format_mla(self, citation: Dict, ctype: str) -> Optional[str]:
        """
        Format citation in MLA style.
        Format: Last, First. Title. Publisher, Year.
        """
        # Simplified MLA format
        parts = []
        
        # Authors
        authors = citation.get('authors', [])
        if authors:
            # MLA: Last, First for first author only
            first_author = authors[0]
            if ',' in first_author:
                parts.append(first_author)
            else:
                name_parts = first_author.split()
                if len(name_parts) >= 2:
                    parts.append(f"{name_parts[-1]}, {' '.join(name_parts[:-1])}")
                else:
                    parts.append(first_author)
            
            # Additional authors: First Last
            if len(authors) > 1:
                parts[-1] += f", and {authors[1]}"
        
        # Title
        title = citation.get('title')
        if title:
            if ctype == 'book':
                parts.append(f"{title}.")
            else:
                parts.append(f'"{title}."')
        
        # Publisher/Source
        publisher = citation.get('publisher')
        source = citation.get('source')
        year = citation.get('year')
        
        if ctype == 'book' and publisher:
            parts.append(f"{publisher},")
        elif source:
            parts.append(f"{source},")
        
        if year:
            parts.append(f"{year}.")
        
        return ' '.join(parts) if parts else citation.get('raw_text', '')
    
    def _format_chicago(self, citation: Dict, ctype: str) -> Optional[str]:
        """
        Format citation in Chicago style (notes-bibliography).
        Format: First Last, Title (Publisher, Year).
        """
        # Simplified Chicago format
        parts = []
        
        # Authors (Chicago uses First Last)
        authors = citation.get('authors', [])
        if authors:
            parts.append(', '.join(authors))
        
        # Title
        title = citation.get('title')
        if title:
            parts.append(f"{title}")
        
        # Publication info
        publisher = citation.get('publisher')
        location = citation.get('location')
        year = citation.get('year')
        
        pub_info = []
        if location:
            pub_info.append(location)
        if publisher:
            pub_info.append(publisher)
        if year:
            pub_info.append(year)
        
        if pub_info:
            parts.append(f"({', '.join(pub_info)})")
        
        return ', '.join(parts) if parts else citation.get('raw_text', '')
    
    def save_bibliography(self, bibliography: str, output_path: Path):
        """Save bibliography to file."""
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            # Header
            f.write(f"# Bibliography ({self.format_style.upper()} Format)\n\n")
            f.write(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            f.write("---\n\n")
            
            # Bibliography entries
            f.write(bibliography)
            f.write("\n")
        
        print(f"\n  ✓ Saved bibliography to: {output_path}")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Generate formatted bibliographies from citation data',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python bibliography_generator.py --input citations.json --output bibliography.txt
  python bibliography_generator.py -i citations.json -o bib.txt --format mla
  python bibliography_generator.py -i citations.json -o bib.txt --format chicago
        """
    )
    
    parser.add_argument(
        '--input', '-i',
        required=True,
        help='JSON file with extracted citations'
    )
    
    parser.add_argument(
        '--output', '-o',
        required=True,
        help='Output file for formatted bibliography'
    )
    
    parser.add_argument(
        '--format', '-f',
        default='apa',
        choices=['apa', 'mla', 'chicago'],
        help='Citation format (default: apa)'
    )
    
    args = parser.parse_args()
    
    # Validate input
    input_path = Path(args.input)
    if not input_path.exists():
        print(f"Error: Input file not found: {input_path}")
        exit(1)
    
    if not input_path.suffix == '.json':
        print(f"Warning: Input file should be a JSON file from citation extractor")
    
    # Generate bibliography
    generator = BibliographyGenerator(format_style=args.format)
    bibliography = generator.generate_from_file(input_path)
    
    if bibliography:
        # Save to file
        output_path = Path(args.output)
        generator.save_bibliography(bibliography, output_path)
        
        print(f"\n{'='*60}")
        print(f"Bibliography generated successfully in {args.format.upper()} format")
        print(f"{'='*60}\n")
    else:
        print("\n⚠ No bibliography generated (no citations found)")
        exit(1)
    
    exit(0)


if __name__ == '__main__':
    main()
