#!/usr/bin/env python3
"""
Citation Extractor MCP Server

Converts the standalone citation extractor into an MCP server that can be used
by the Claude Agent SDK.

This server exposes citation extraction functionality as MCP tools.
"""

from fastmcp import FastMCP
import re
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict


# Create the MCP server
mcp = FastMCP("Citation Extractor")


@dataclass
class Citation:
    """Structured citation data."""
    raw_text: str
    citation_type: str  # 'book', 'article', 'archival', 'interview', etc.
    authors: List[str]
    year: Optional[str]
    title: Optional[str]
    publisher: Optional[str]
    location: Optional[str]
    source: Optional[str]  # journal, archive, etc.
    url: Optional[str]
    notes: Optional[str]
    confidence: float  # 0.0 to 1.0


@mcp.tool()
def extract_citations(markdown_file: str, output_dir: str = "/tmp/citations") -> Dict:
    """
    Extract structured citations from a markdown file.
    
    Args:
        markdown_file: Path to markdown file (from PDF processor)
        output_dir: Directory where output files will be saved
        
    Returns:
        Dictionary containing:
        - success: bool
        - citations: list of citation dictionaries
        - stats: extraction statistics
        - json_path: path to detailed JSON output
        - markdown_path: path to human-readable report
        - error: error message if failed
    """
    try:
        markdown_file = Path(markdown_file)
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        if not markdown_file.exists():
            return {
                "success": False,
                "error": f"Markdown file not found: {markdown_file}"
            }
        
        with open(markdown_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Skip metadata section
        content = skip_metadata(content)
        
        # Extract citations
        citations = []
        lines = content.split('\n')
        stats = {
            'total_lines': len(lines),
            'citations_found': 0,
            'by_type': {}
        }
        
        current_section = None
        
        for line in lines:
            # Track section headers
            if line.startswith('#'):
                current_section = line.strip()
                continue
            
            if not line.strip():
                continue
            
            # Try to extract citation
            citation = parse_line(line, current_section)
            if citation:
                citations.append(citation)
                stats['citations_found'] += 1
                
                ctype = citation.citation_type
                stats['by_type'][ctype] = stats['by_type'].get(ctype, 0) + 1
        
        # Save results
        base_name = markdown_file.stem
        
        # Save as JSON
        json_path = output_dir / f"{base_name}_citations.json"
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump([asdict(c) for c in citations], f, indent=2, ensure_ascii=False)
        
        # Save as markdown report
        md_path = output_dir / f"{base_name}_citations.md"
        generate_markdown_report(citations, md_path, markdown_file.name, stats)
        
        return {
            "success": True,
            "citations": [asdict(c) for c in citations],
            "stats": stats,
            "json_path": str(json_path),
            "markdown_path": str(md_path)
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


@mcp.tool()
def extract_citations_batch(input_dir: str, output_dir: str = "/tmp/citations") -> Dict:
    """
    Extract citations from all markdown files in a directory.
    
    Args:
        input_dir: Directory containing markdown files
        output_dir: Directory where output files will be saved
        
    Returns:
        Dictionary containing:
        - success: bool
        - processed: list of successfully processed files
        - failed: list of failed files with errors
        - stats: overall statistics
    """
    try:
        input_dir = Path(input_dir)
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        if not input_dir.exists():
            return {
                "success": False,
                "error": f"Input directory not found: {input_dir}"
            }
        
        md_files = list(input_dir.glob('*.md'))
        
        if not md_files:
            return {
                "success": False,
                "error": f"No markdown files found in {input_dir}"
            }
        
        processed = []
        failed = []
        total_citations = 0
        
        for md_file in md_files:
            result = extract_citations(str(md_file), str(output_dir))
            
            if result['success']:
                total_citations += result['stats']['citations_found']
                processed.append({
                    "filename": md_file.name,
                    "stats": result['stats']
                })
            else:
                failed.append({
                    "filename": md_file.name,
                    "error": result.get('error', 'Unknown error')
                })
        
        return {
            "success": True,
            "processed": processed,
            "failed": failed,
            "stats": {
                "total_files": len(md_files),
                "successful": len(processed),
                "failed": len(failed),
                "total_citations": total_citations
            }
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


def skip_metadata(content: str) -> str:
    """Skip the metadata section at the beginning."""
    parts = content.split('## Extracted Text', 1)
    if len(parts) == 2:
        return parts[1]
    return content


def parse_line(line: str, section: Optional[str]) -> Optional[Citation]:
    """Try to parse a line as a citation."""
    
    if len(line) < 20:
        return None
    
    # Try each pattern type
    patterns = {
        'book': compile_book_patterns(),
        'article': compile_article_patterns(),
        'online': compile_online_patterns(),
    }
    
    for citation_type, pattern_list in patterns.items():
        for pattern in pattern_list:
            match = pattern.search(line)
            if match:
                return build_citation(line, citation_type, match, section)
    
    # If it starts with '- ' and has reasonable length, might be a citation
    if line.strip().startswith('-') and len(line) > 30:
        return Citation(
            raw_text=line.strip(),
            citation_type='unclassified',
            authors=[],
            year=extract_year(line),
            title=None,
            publisher=None,
            location=None,
            source=None,
            url=extract_url(line),
            notes=section,
            confidence=0.3
        )
    
    return None


def compile_book_patterns() -> List[re.Pattern]:
    """Regex patterns for book citations."""
    return [
        re.compile(
            r'^-?\s*([A-ZČŠŽÁÉÍÓÚÝŇĎŤĽ][^\d\.]+?)\.\s*'  # Author
            r'(\d{4})\.\s*'  # Year
            r'([^\.]+?)\.\s*'  # Title
            r'([^:]+):\s*'  # Location
            r'([^\.]+)\.',  # Publisher
            re.MULTILINE | re.UNICODE
        ),
    ]


def compile_article_patterns() -> List[re.Pattern]:
    """Regex patterns for journal articles."""
    return [
        re.compile(
            r'^-?\s*([A-ZČŠŽÁÉÍÓÚÝŇĎŤĽ][^\d\.]+?)\.\s*'  # Author
            r'(\d{4})\.\s*'  # Year
            r'"([^"]+)"\.\s*'  # Title in quotes
            r'([^\d]+?)\s+'  # Journal name
            r'(\d+)\s*'  # Volume
            r'(?:\((\d+)\))?\s*:\s*'  # Optional issue
            r'(\d+-\d+)',  # Pages
            re.MULTILINE | re.UNICODE
        ),
    ]


def compile_online_patterns() -> List[re.Pattern]:
    """Regex patterns for online sources."""
    return [
        re.compile(r'(https?://[^\s]+)', re.UNICODE),
    ]


def build_citation(line: str, ctype: str, match: re.Match, 
                   section: Optional[str]) -> Citation:
    """Build a Citation object from regex match."""
    
    if ctype == 'book':
        return Citation(
            raw_text=line.strip(),
            citation_type='book',
            authors=parse_authors(match.group(1)),
            year=match.group(2),
            title=match.group(3).strip(),
            location=match.group(4).strip(),
            publisher=match.group(5).strip(),
            source=None,
            url=None,
            notes=section,
            confidence=0.9
        )
    
    elif ctype == 'article':
        return Citation(
            raw_text=line.strip(),
            citation_type='article',
            authors=parse_authors(match.group(1)),
            year=match.group(2),
            title=match.group(3).strip(),
            source=match.group(4).strip(),
            publisher=None,
            location=None,
            url=None,
            notes=f"{section} | Vol {match.group(5)} ({match.group(6)}): {match.group(7)}",
            confidence=0.9
        )
    
    elif ctype == 'online':
        return Citation(
            raw_text=line.strip(),
            citation_type='online',
            authors=[],
            year=extract_year(line),
            title=None,
            location=None,
            publisher=None,
            source=None,
            url=match.group(1),
            notes=section,
            confidence=0.8
        )
    
    return None


def parse_authors(author_string: str) -> List[str]:
    """Parse author names from string."""
    authors = re.split(r'\s+(?:and|a)\s+|,\s*(?:and|a)\s+', author_string)
    return [a.strip() for a in authors if a.strip()]


def extract_year(text: str) -> Optional[str]:
    """Try to extract a year from text."""
    match = re.search(r'\b(19\d{2}|20\d{2})\b', text)
    return match.group(1) if match else None


def extract_url(text: str) -> Optional[str]:
    """Try to extract a URL from text."""
    match = re.search(r'https?://[^\s]+', text)
    return match.group(0) if match else None


def generate_markdown_report(citations: List[Citation], output_path: Path, 
                             source_filename: str, stats: Dict):
    """Generate a markdown report of citations."""
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(f"# Citation Analysis: {source_filename}\n\n")
        f.write(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        f.write(f"**Total Citations Found:** {len(citations)}\n\n")
        
        f.write("## Citations by Type\n\n")
        for ctype, count in sorted(stats['by_type'].items()):
            f.write(f"- **{ctype.title()}:** {count}\n")
        f.write("\n")
        
        # Group citations by type
        by_type = {}
        for citation in citations:
            ctype = citation.citation_type
            if ctype not in by_type:
                by_type[ctype] = []
            by_type[ctype].append(citation)
        
        # Write each type section
        for ctype in sorted(by_type.keys()):
            f.write(f"## {ctype.title()} Citations\n\n")
            
            for citation in by_type[ctype]:
                f.write(f"### {citation.title or 'Untitled'}\n\n")
                
                if citation.authors:
                    f.write(f"**Authors:** {', '.join(citation.authors)}\n\n")
                
                if citation.year:
                    f.write(f"**Year:** {citation.year}\n\n")
                
                if citation.location:
                    f.write(f"**Location:** {citation.location}\n\n")
                
                if citation.publisher:
                    f.write(f"**Publisher:** {citation.publisher}\n\n")
                
                if citation.source:
                    f.write(f"**Source:** {citation.source}\n\n")
                
                if citation.url:
                    f.write(f"**URL:** {citation.url}\n\n")
                
                f.write(f"**Confidence:** {citation.confidence:.0%}\n\n")
                f.write(f"**Raw Text:**\n```\n{citation.raw_text}\n```\n\n")
                f.write("---\n\n")


if __name__ == "__main__":
    # Run the MCP server
    mcp.run()