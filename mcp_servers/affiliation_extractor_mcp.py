#!/usr/bin/env python3
"""
Author Affiliation Extractor MCP Server

Converts the standalone affiliation extractor into an MCP server that can be used
by the Claude Agent SDK or other MCP clients.

This server exposes author affiliation extraction as MCP tools.
"""

from fastmcp import FastMCP
import pdfplumber
from pathlib import Path
import json
from datetime import datetime
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict
import re


# Create the MCP server
mcp = FastMCP("Affiliation Extractor")


@dataclass
class Author:
    """Structured author information"""
    name: str
    affiliation: Optional[str] = None
    email: Optional[str] = None
    department: Optional[str] = None
    institution: Optional[str] = None
    location: Optional[str] = None
    confidence: float = 0.0


@mcp.tool()
def extract_authors(pdf_path: str, output_dir: str = "/tmp/authors") -> Dict:
    """
    Extract author names and institutional affiliations from an academic PDF.
    
    Args:
        pdf_path: Path to the PDF file to process
        output_dir: Directory where output files will be saved
        
    Returns:
        Dictionary containing:
        - success: bool
        - authors: list of author objects
        - count: number of authors found
        - json_path: path to generated JSON file
        - md_path: path to markdown report
        - error: error message if failed
    """
    try:
        # Convert string paths to Path objects
        pdf_file = Path(pdf_path)
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        if not pdf_file.exists():
            return {
                "success": False,
                "error": f"PDF file not found: {pdf_path}"
            }
        
        # Extract text from first page
        text = extract_first_page_text(pdf_file)
        
        if not text:
            return {
                "success": False,
                "error": "No text could be extracted from first page"
            }
        
        # Extract authors
        authors = extract_authors_from_text(text)
        
        # Generate output
        output_data = {
            'source': pdf_file.name,
            'processed': datetime.now().isoformat(),
            'authors': [asdict(author) for author in authors],
            'count': len(authors)
        }
        
        # Save JSON
        json_filename = pdf_file.stem + '_authors.json'
        json_path = output_path / json_filename
        
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, indent=2, ensure_ascii=False)
        
        # Save markdown
        md_filename = pdf_file.stem + '_authors.md'
        md_path = output_path / md_filename
        
        with open(md_path, 'w', encoding='utf-8') as f:
            f.write(generate_markdown_report(output_data, authors))
        
        return {
            "success": True,
            "authors": [asdict(a) for a in authors],
            "count": len(authors),
            "json_path": str(json_path),
            "md_path": str(md_path)
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


@mcp.tool()
def extract_authors_batch(input_dir: str, output_dir: str = "/tmp/authors") -> Dict:
    """
    Extract authors from all PDFs in a directory.
    
    Args:
        input_dir: Directory containing PDF files
        output_dir: Directory for output files
        
    Returns:
        Dictionary containing:
        - success: bool
        - processed: number of PDFs processed
        - failed: number of failures
        - total_authors: total authors found
        - results: list of per-file results
        - error: error message if failed
    """
    try:
        input_path = Path(input_dir)
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        pdf_files = list(input_path.glob('*.pdf'))
        
        if not pdf_files:
            return {
                "success": False,
                "error": f"No PDF files found in {input_dir}"
            }
        
        results = []
        processed = 0
        failed = 0
        total_authors = 0
        
        for pdf_file in pdf_files:
            # Process each file individually
            try:
                pdf_path = Path(pdf_file)
                
                # Extract text from first page
                text = extract_first_page_text(pdf_path)
                
                if not text:
                    failed += 1
                    results.append({
                        'file': pdf_file.name,
                        'success': False,
                        'authors': 0,
                        'error': 'No text extracted'
                    })
                    continue
                
                # Extract authors
                authors = extract_authors_from_text(text)
                
                # Generate output
                output_data = {
                    'source': pdf_path.name,
                    'processed': datetime.now().isoformat(),
                    'authors': [asdict(author) for author in authors],
                    'count': len(authors)
                }
                
                # Save JSON
                json_filename = pdf_path.stem + '_authors.json'
                json_path = output_path / json_filename
                
                with open(json_path, 'w', encoding='utf-8') as f:
                    json.dump(output_data, f, indent=2, ensure_ascii=False)
                
                # Save markdown
                md_filename = pdf_path.stem + '_authors.md'
                md_path = output_path / md_filename
                
                with open(md_path, 'w', encoding='utf-8') as f:
                    f.write(generate_markdown_report(output_data, authors))
                
                processed += 1
                total_authors += len(authors)
                
                results.append({
                    'file': pdf_file.name,
                    'success': True,
                    'authors': len(authors),
                    'error': None
                })
                
            except Exception as e:
                failed += 1
                results.append({
                    'file': pdf_file.name,
                    'success': False,
                    'authors': 0,
                    'error': str(e)
                })
        
        return {
            "success": True,
            "processed": processed,
            "failed": failed,
            "total_authors": total_authors,
            "total_files": len(pdf_files),
            "results": results
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


# ============================================================================
# Helper Functions (shared logic with standalone version)
# ============================================================================

def extract_first_page_text(pdf_path: Path) -> str:
    """Extract text from first page where author info typically appears."""
    try:
        with pdfplumber.open(pdf_path) as pdf:
            if len(pdf.pages) > 0:
                return pdf.pages[0].extract_text() or ""
    except Exception:
        pass
    return ""


def extract_emails(text: str) -> List[str]:
    """Extract all email addresses from text."""
    email_pattern = re.compile(
        r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    )
    return email_pattern.findall(text)


def extract_author_blocks(text: str) -> List[str]:
    """Split text into potential author blocks."""
    # Common section headers that appear before/after authors
    section_markers = [
        'abstract', 'introduction', 'úvod', 'keywords', 'kľúčové slová',
        'contents', 'obsah', r'\d+\.\s+[A-Z]'
    ]
    
    pattern = '|'.join(section_markers)
    parts = re.split(pattern, text, flags=re.IGNORECASE, maxsplit=1)
    
    author_section = parts[0] if parts else text
    lines = author_section.split('\n')
    
    # Filter out very short lines and page numbers
    lines = [
        line.strip() for line in lines 
        if len(line.strip()) > 3 and not re.match(r'^\d+$', line.strip())
    ]
    
    return lines


def is_affiliation_line(line: str) -> bool:
    """Check if line contains affiliation information."""
    affiliation_keywords = [
        'university', 'univerzita', 'college', 'institute', 'institut',
        'faculty', 'fakulta', 'department', 'katedra', 'school', 'škola',
        'academy', 'akadémia', 'center', 'centre', 'centrum'
    ]
    line_lower = line.lower()
    return any(keyword in line_lower for keyword in affiliation_keywords)


def is_author_name(line: str) -> bool:
    """Heuristic to detect if line is likely an author name."""
    titles = r'(?:Dr\.|Prof\.|Professor|Ph\.D\.|M\.A\.|B\.A\.|Rev\.|Fr\.)'
    cleaned = re.sub(titles, '', line, flags=re.IGNORECASE).strip()
    
    # Skip very short or very long lines
    if len(cleaned) < 3 or len(cleaned) > 60:
        return False
    
    words = cleaned.split()
    if len(words) < 1 or len(words) > 5:
        return False
    
    # Check if words start with capitals
    capital_pattern = r'^[A-ZÁČĎÉÍĽŇÓÔŔŠŤÚÝŽ]'
    capitals = sum(1 for w in words if re.match(capital_pattern, w))
    
    if capitals < len(words) / 2:
        return False
    
    if is_affiliation_line(line):
        return False
    
    # Exclude lines that look like locations (comma followed by short abbreviation)
    if ',' in line:
        parts = line.split(',')
        if len(parts) == 2:
            last_part = parts[-1].strip()
            if len(last_part) <= 3 or len(last_part.split()) == 1:
                return False
    
    return True


def parse_affiliation(text: str) -> Dict[str, Optional[str]]:
    """Parse affiliation text into components."""
    result = {
        'full': text,
        'department': None,
        'institution': None,
        'location': None
    }
    
    # Look for department patterns
    dept_match = re.search(
        r'(department|katedra|faculty|fakulta)\s+of\s+([^,\n]+)',
        text, re.IGNORECASE
    )
    if dept_match:
        result['department'] = dept_match.group(0).strip()
    
    # Look for institution
    for keyword in ['university', 'univerzita', 'institute', 'institut', 'college']:
        if keyword in text.lower():
            parts = re.split(r'[,\n]', text)
            for part in parts:
                if keyword in part.lower():
                    result['institution'] = part.strip()
                    break
            break
    
    # Look for location (typically at end after comma)
    parts = text.split(',')
    if len(parts) >= 2:
        potential_location = parts[-1].strip()
        if len(potential_location.split()) <= 3:
            result['location'] = potential_location
    
    return result


def extract_authors_from_text(text: str) -> List[Author]:
    """Extract authors and affiliations from PDF text."""
    authors = []
    emails = extract_emails(text)
    lines = extract_author_blocks(text)
    
    current_authors = []
    current_affiliation = []
    
    for line in lines:
        if not line:
            continue
        
        if is_author_name(line):
            # Save previous author if exists
            if current_authors and current_affiliation:
                affiliation_text = ' '.join(current_affiliation)
                parsed = parse_affiliation(affiliation_text)
                
                for author_name in current_authors:
                    authors.append(Author(
                        name=author_name,
                        affiliation=parsed['full'],
                        department=parsed['department'],
                        institution=parsed['institution'],
                        location=parsed['location'],
                        confidence=0.7
                    ))
                
                current_authors = []
                current_affiliation = []
            
            current_authors.append(line.strip())
        
        elif is_affiliation_line(line):
            current_affiliation.append(line.strip())
    
    # Process last author
    if current_authors and current_affiliation:
        affiliation_text = ' '.join(current_affiliation)
        parsed = parse_affiliation(affiliation_text)
        
        for author_name in current_authors:
            authors.append(Author(
                name=author_name,
                affiliation=parsed['full'],
                department=parsed['department'],
                institution=parsed['institution'],
                location=parsed['location'],
                confidence=0.7
            ))
    
    # Match emails to authors
    if emails and authors:
        for i, email in enumerate(emails):
            if i < len(authors):
                authors[i].email = email
    
    return authors


def generate_markdown_report(data: Dict, authors: List[Author]) -> str:
    """Generate markdown report of extracted authors."""
    lines = [
        f"# Author Affiliations: {data['source']}\n",
        f"**Processed:** {data['processed']}  ",
        f"**Authors Found:** {data['count']}\n",
        "---\n"
    ]
    
    if not authors:
        lines.append("*No authors detected in this document.*\n")
    else:
        for i, author in enumerate(authors, 1):
            lines.append(f"\n## {i}. {author.name}\n")
            
            if author.email:
                lines.append(f"**Email:** {author.email}  \n")
            
            if author.institution:
                lines.append(f"**Institution:** {author.institution}  \n")
            
            if author.department:
                lines.append(f"**Department:** {author.department}  \n")
            
            if author.location:
                lines.append(f"**Location:** {author.location}  \n")
            
            if author.affiliation:
                lines.append(f"\n**Full Affiliation:**  \n{author.affiliation}\n")
            
            lines.append(f"\n*Confidence: {author.confidence:.1%}*\n")
    
    return '\n'.join(lines)


if __name__ == "__main__":
    mcp.run()
