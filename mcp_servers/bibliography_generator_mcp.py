#!/usr/bin/env python3
"""
Bibliography Generator MCP Server

MCP server version of the bibliography generator for agent orchestration.
Generates formatted bibliographies from extracted citation data.

Usage:
    python mcp_servers/bibliography_generator_mcp.py
"""

from fastmcp import FastMCP
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional
import unicodedata


# Create the MCP server
mcp = FastMCP("Bibliography Generator")


@mcp.tool()
def generate_bibliography(
    citations_file: str,
    output_file: str = "/tmp/bibliography.txt",
    format_style: str = "apa"
) -> Dict:
    """
    Generate a formatted bibliography from citation JSON file.
    
    Args:
        citations_file: Path to JSON file with extracted citations
        output_file: Path where bibliography will be saved
        format_style: Citation format ('apa', 'mla', 'chicago')
        
    Returns:
        Dictionary containing:
        - success: bool
        - bibliography: formatted bibliography text
        - output_path: path to saved file
        - entry_count: number of citations formatted
        - error: error message if failed
    """
    try:
        citations_path = Path(citations_file)
        output_path = Path(output_file)
        
        if not citations_path.exists():
            return {
                "success": False,
                "error": f"Citations file not found: {citations_file}"
            }
        
        # Load citations
        with open(citations_path, 'r', encoding='utf-8') as f:
            citations = json.load(f)
        
        if not citations:
            return {
                "success": False,
                "error": "No citations found in file"
            }
        
        # Generate bibliography
        bibliography_text = format_bibliography(citations, format_style)
        
        # Save to file
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(f"# Bibliography ({format_style.upper()} Format)\n\n")
            f.write(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            f.write("---\n\n")
            f.write(bibliography_text)
            f.write("\n")
        
        return {
            "success": True,
            "bibliography": bibliography_text,
            "output_path": str(output_path),
            "entry_count": len(citations),
            "format": format_style
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


@mcp.tool()
def generate_bibliography_from_data(
    citations: List[Dict],
    format_style: str = "apa"
) -> Dict:
    """
    Generate a formatted bibliography from citation data (without file I/O).
    
    Args:
        citations: List of citation dictionaries
        format_style: Citation format ('apa', 'mla', 'chicago')
        
    Returns:
        Dictionary containing:
        - success: bool
        - bibliography: formatted bibliography text
        - entry_count: number of citations formatted
        - error: error message if failed
    """
    try:
        if not citations:
            return {
                "success": False,
                "error": "No citations provided"
            }
        
        bibliography_text = format_bibliography(citations, format_style)
        
        return {
            "success": True,
            "bibliography": bibliography_text,
            "entry_count": len(citations),
            "format": format_style
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


# Helper functions (same logic as standalone version)

def format_bibliography(citations: List[Dict], format_style: str) -> str:
    """Generate formatted bibliography from citation dictionaries."""
    format_style = format_style.lower()
    
    if format_style not in ['apa', 'mla', 'chicago']:
        raise ValueError(f"Unsupported format: {format_style}")
    
    # Sort citations
    sorted_citations = sort_citations(citations)
    
    # Format each citation
    formatted_entries = []
    for citation in sorted_citations:
        entry = format_citation(citation, format_style)
        if entry:
            formatted_entries.append(entry)
    
    # Join with appropriate spacing
    if format_style in ['apa', 'mla']:
        return '\n\n'.join(formatted_entries)
    else:  # chicago
        numbered = [f"{i+1}. {e}" for i, e in enumerate(formatted_entries)]
        return '\n\n'.join(numbered)


def sort_citations(citations: List[Dict]) -> List[Dict]:
    """Sort citations alphabetically by author last name."""
    def get_sort_key(citation: Dict) -> str:
        authors = citation.get('authors', [])
        if not authors:
            title = citation.get('title', citation.get('raw_text', ''))
            return normalize_for_sorting(title)
        
        first_author = authors[0]
        last_name = extract_last_name(first_author)
        return normalize_for_sorting(last_name)
    
    return sorted(citations, key=get_sort_key)


def extract_last_name(author: str) -> str:
    """Extract last name from author string."""
    author = author.strip()
    if ',' in author:
        return author.split(',')[0].strip()
    parts = author.split()
    return parts[-1] if parts else author


def normalize_for_sorting(text: str) -> str:
    """Normalize text for alphabetical sorting."""
    text = text.strip()
    for article in ['The ', 'A ', 'An ', 'Der ', 'Die ', 'Das ', 'Le ', 'La ', 'Les ']:
        if text.startswith(article):
            text = text[len(article):]
            break
    normalized = unicodedata.normalize('NFD', text)
    return normalized.lower()


def format_citation(citation: Dict, format_style: str) -> Optional[str]:
    """Format a single citation according to the selected style."""
    ctype = citation.get('citation_type', 'unclassified')
    
    if format_style == 'apa':
        return format_apa(citation, ctype)
    elif format_style == 'mla':
        return format_mla(citation, ctype)
    else:
        return format_chicago(citation, ctype)


def format_apa(citation: Dict, ctype: str) -> Optional[str]:
    """Format citation in APA style."""
    if ctype == 'book':
        return format_apa_book(citation)
    elif ctype == 'article':
        return format_apa_article(citation)
    elif ctype == 'online':
        return format_apa_online(citation)
    else:
        return citation.get('raw_text', '')


def format_apa_book(citation: Dict) -> str:
    """Format: Author, A. A. (Year). Title. Publisher."""
    parts = []
    
    authors = citation.get('authors', [])
    if authors:
        parts.append(format_apa_authors(authors))
    
    year = citation.get('year')
    if year:
        parts.append(f"({year}).")
    
    title = citation.get('title')
    if title:
        parts.append(f"{title}.")
    
    publisher = citation.get('publisher')
    location = citation.get('location')
    
    if location and publisher:
        parts.append(f"{location}: {publisher}.")
    elif publisher:
        parts.append(f"{publisher}.")
    
    return ' '.join(parts)


def format_apa_article(citation: Dict) -> str:
    """Format: Author, A. A. (Year). Title. Journal, volume(issue), pages."""
    parts = []
    
    authors = citation.get('authors', [])
    if authors:
        parts.append(format_apa_authors(authors))
    
    year = citation.get('year')
    if year:
        parts.append(f"({year}).")
    
    title = citation.get('title')
    if title:
        parts.append(f"{title}.")
    
    source = citation.get('source')
    if source:
        notes = citation.get('notes', '')
        parts.append(f"{source}, {notes}.")
    
    return ' '.join(parts)


def format_apa_online(citation: Dict) -> str:
    """Format: Author. (Year). Title. Retrieved from URL"""
    parts = []
    
    authors = citation.get('authors', [])
    if authors:
        parts.append(format_apa_authors(authors))
    
    year = citation.get('year')
    if year:
        parts.append(f"({year}).")
    
    title = citation.get('title')
    if title:
        parts.append(f"{title}.")
    
    url = citation.get('url')
    if url:
        parts.append(f"Retrieved from {url}")
    
    return ' '.join(parts) if parts else citation.get('raw_text', '')


def format_apa_authors(authors: List[str]) -> str:
    """Format: Last, F. M., & Last2, F. M."""
    if not authors:
        return ""
    
    formatted = [format_apa_single_author(a) for a in authors[:7]]
    
    if len(authors) > 7:
        formatted = formatted[:6] + ["..."] + [format_apa_single_author(authors[-1])]
    
    if len(formatted) == 1:
        return formatted[0]
    elif len(formatted) == 2:
        return f"{formatted[0]}, & {formatted[1]}"
    else:
        return ', '.join(formatted[:-1]) + f", & {formatted[-1]}"


def format_apa_single_author(author: str) -> str:
    """Convert 'First Last' to 'Last, F.'"""
    author = author.strip()
    
    if ',' in author:
        parts = author.split(',', 1)
        last_name = parts[0].strip()
        first_name = parts[1].strip()
    else:
        parts = author.split()
        if len(parts) >= 2:
            first_name = ' '.join(parts[:-1])
            last_name = parts[-1]
        else:
            return author
    
    initials = get_initials(first_name)
    return f"{last_name}, {initials}"


def get_initials(name: str) -> str:
    """Get initials from a name."""
    parts = name.split()
    initials = [f"{p[0].upper()}." for p in parts if p]
    return ' '.join(initials)


def format_mla(citation: Dict, ctype: str) -> Optional[str]:
    """Format: Last, First. Title. Publisher, Year."""
    parts = []
    
    authors = citation.get('authors', [])
    if authors:
        first_author = authors[0]
        if ',' in first_author:
            parts.append(first_author)
        else:
            name_parts = first_author.split()
            if len(name_parts) >= 2:
                parts.append(f"{name_parts[-1]}, {' '.join(name_parts[:-1])}")
            else:
                parts.append(first_author)
        
        if len(authors) > 1:
            parts[-1] += f", and {authors[1]}"
    
    title = citation.get('title')
    if title:
        if ctype == 'book':
            parts.append(f"{title}.")
        else:
            parts.append(f'"{title}."')
    
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


def format_chicago(citation: Dict, ctype: str) -> Optional[str]:
    """Format: First Last, Title (Publisher, Year)."""
    parts = []
    
    authors = citation.get('authors', [])
    if authors:
        parts.append(', '.join(authors))
    
    title = citation.get('title')
    if title:
        parts.append(f"{title}")
    
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


if __name__ == "__main__":
    mcp.run()
