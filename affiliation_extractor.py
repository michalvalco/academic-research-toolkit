#!/usr/bin/env python3
"""
Author Affiliation Extractor for Academic Research

Extracts author names and institutional affiliations from academic PDFs.
Designed to handle various academic paper formats and citation styles.

Usage:
    python affiliation_extractor.py --input <pdf_directory> --output <output_directory>
"""

import argparse
import pdfplumber
from pathlib import Path
import json
from datetime import datetime
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict
import re


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


class AffiliationExtractor:
    """Extract author affiliations from academic PDFs."""
    
    def __init__(self, input_dir: str, output_dir: str):
        self.input_dir = Path(input_dir)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Statistics
        self.stats = {
            'processed': 0,
            'failed': 0,
            'total': 0,
            'authors_found': 0
        }
        
        # Common academic title patterns
        self.titles = r'(?:Dr\.|Prof\.|Professor|Ph\.D\.|M\.A\.|B\.A\.|Rev\.|Fr\.)'
        
        # Email pattern
        self.email_pattern = re.compile(
            r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        )
        
        # Affiliation keywords
        self.affiliation_keywords = [
            'university', 'univerzita', 'college', 'institute', 'institut',
            'faculty', 'fakulta', 'department', 'katedra', 'school', 'škola',
            'academy', 'akadémia', 'center', 'centre', 'centrum'
        ]
    
    def extract_first_page_text(self, pdf_path: Path) -> str:
        """
        Extract text from first page where author info typically appears.
        """
        try:
            with pdfplumber.open(pdf_path) as pdf:
                if len(pdf.pages) > 0:
                    return pdf.pages[0].extract_text() or ""
        except Exception as e:
            print(f"  Warning: Could not extract text: {e}")
        return ""
    
    def extract_emails(self, text: str) -> List[str]:
        """Extract all email addresses from text."""
        return self.email_pattern.findall(text)
    
    def extract_author_blocks(self, text: str) -> List[str]:
        """
        Split text into potential author blocks.
        Heuristic: Look for patterns that indicate author sections.
        """
        # Common section headers that appear before/after authors
        section_markers = [
            'abstract', 'introduction', 'úvod', 'keywords', 'kľúčové slová',
            'contents', 'obsah', r'\d+\.\s+[A-Z]'  # numbered sections
        ]
        
        # Split at section markers (case-insensitive)
        pattern = '|'.join(section_markers)
        parts = re.split(pattern, text, flags=re.IGNORECASE, maxsplit=1)
        
        # First part likely contains author info
        author_section = parts[0] if parts else text
        
        # Split into lines for processing
        lines = author_section.split('\n')
        
        # Filter out very short lines and page numbers
        lines = [
            line.strip() for line in lines 
            if len(line.strip()) > 3 and not re.match(r'^\d+$', line.strip())
        ]
        
        return lines
    
    def is_affiliation_line(self, line: str) -> bool:
        """
        Check if line contains affiliation information.
        """
        line_lower = line.lower()
        return any(keyword in line_lower for keyword in self.affiliation_keywords)
    
    def is_author_name(self, line: str) -> bool:
        """
        Heuristic to detect if line is likely an author name.
        """
        # Remove titles
        cleaned = re.sub(self.titles, '', line, flags=re.IGNORECASE).strip()
        
        # Skip very short or very long lines
        if len(cleaned) < 3 or len(cleaned) > 60:
            return False
        
        # Author names typically:
        # - Have 2-4 words
        # - Start with capital letters
        # - Don't have many special characters
        # - Are not too long
        
        words = cleaned.split()
        if len(words) < 1 or len(words) > 5:
            return False
        
        # Check if words start with capitals (allowing for initials)
        capital_pattern = r'^[A-ZÁČĎÉÍĽŇÓÔŔŠŤÚÝŽ]'
        capitals = sum(1 for w in words if re.match(capital_pattern, w))
        
        # At least half the words should be capitalized
        if capitals < len(words) / 2:
            return False
        
        # Not an affiliation line
        if self.is_affiliation_line(line):
            return False
        
        # Exclude lines that look like locations (comma followed by short abbreviation)
        # e.g., "Stanford, CA" or "Bratislava, Slovakia"
        if ',' in line:
            parts = line.split(',')
            if len(parts) == 2:
                # If second part is 2-3 chars or ends with common country/state patterns
                last_part = parts[-1].strip()
                if len(last_part) <= 3 or len(last_part.split()) == 1:
                    return False
        
        return True
    
    def parse_affiliation(self, text: str) -> Dict[str, Optional[str]]:
        """
        Parse affiliation text into components.
        """
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
        
        # Look for institution (university, institute, etc.)
        for keyword in ['university', 'univerzita', 'institute', 'institut', 'college']:
            if keyword in text.lower():
                # Extract the institution name (usually before comma or end)
                parts = re.split(r'[,\n]', text)
                for part in parts:
                    if keyword in part.lower():
                        result['institution'] = part.strip()
                        break
                break
        
        # Look for location (city, country)
        # Typically at end after comma
        parts = text.split(',')
        if len(parts) >= 2:
            # Last part often contains location
            potential_location = parts[-1].strip()
            # Check if it looks like a location (short, capitalized)
            if len(potential_location.split()) <= 3:
                result['location'] = potential_location
        
        return result
    
    def extract_authors_from_text(self, text: str) -> List[Author]:
        """
        Extract authors and affiliations from PDF text.
        Uses heuristics to identify author blocks.
        """
        authors = []
        emails = self.extract_emails(text)
        lines = self.extract_author_blocks(text)
        
        current_authors = []
        current_affiliation = []
        
        for line in lines:
            if not line:
                continue
            
            # Check if this is an author name
            if self.is_author_name(line):
                # Save previous author if exists
                if current_authors and current_affiliation:
                    affiliation_text = ' '.join(current_affiliation)
                    parsed = self.parse_affiliation(affiliation_text)
                    
                    for author_name in current_authors:
                        authors.append(Author(
                            name=author_name,
                            affiliation=parsed['full'],
                            department=parsed['department'],
                            institution=parsed['institution'],
                            location=parsed['location'],
                            confidence=0.7  # Medium confidence for heuristic extraction
                        ))
                    
                    current_authors = []
                    current_affiliation = []
                
                # Start new author
                current_authors.append(line.strip())
            
            # Check if this is an affiliation line
            elif self.is_affiliation_line(line):
                current_affiliation.append(line.strip())
        
        # Process last author
        if current_authors and current_affiliation:
            affiliation_text = ' '.join(current_affiliation)
            parsed = self.parse_affiliation(affiliation_text)
            
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
    
    def process_pdf(self, pdf_path: Path) -> Dict:
        """
        Process a single PDF and extract author affiliations.
        """
        print(f"Processing: {pdf_path.name}")
        
        try:
            # Extract text from first page
            text = self.extract_first_page_text(pdf_path)
            
            if not text:
                print(f"  ✗ Failed: No text extracted")
                return {
                    'success': False,
                    'error': 'No text extracted from first page'
                }
            
            # Extract authors
            authors = self.extract_authors_from_text(text)
            
            if not authors:
                print(f"  ⚠ Warning: No authors found")
            else:
                print(f"  ✓ Found {len(authors)} author(s)")
            
            # Generate output
            output_data = {
                'source': pdf_path.name,
                'processed': datetime.now().isoformat(),
                'authors': [asdict(author) for author in authors],
                'count': len(authors)
            }
            
            # Save JSON
            json_filename = pdf_path.stem + '_authors.json'
            json_path = self.output_dir / json_filename
            
            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump(output_data, f, indent=2, ensure_ascii=False)
            
            # Save markdown
            md_filename = pdf_path.stem + '_authors.md'
            md_path = self.output_dir / md_filename
            
            with open(md_path, 'w', encoding='utf-8') as f:
                f.write(self._generate_markdown_report(output_data, authors))
            
            print(f"  → Saved: {json_path.name}, {md_path.name}")
            
            self.stats['authors_found'] += len(authors)
            
            return {
                'success': True,
                'authors': len(authors),
                'json_path': str(json_path),
                'md_path': str(md_path)
            }
            
        except Exception as e:
            print(f"  ✗ Failed: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _generate_markdown_report(self, data: Dict, authors: List[Author]) -> str:
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
    
    def process_all(self):
        """Process all PDFs in input directory."""
        pdf_files = list(self.input_dir.glob('*.pdf'))
        self.stats['total'] = len(pdf_files)
        
        if not pdf_files:
            print(f"No PDF files found in {self.input_dir}")
            return
        
        print("=" * 70)
        print("AUTHOR AFFILIATION EXTRACTOR")
        print("=" * 70)
        print(f"\nInput:  {self.input_dir}")
        print(f"Output: {self.output_dir}")
        print(f"Files:  {len(pdf_files)}\n")
        
        for pdf_path in pdf_files:
            result = self.process_pdf(pdf_path)
            
            if result['success']:
                self.stats['processed'] += 1
            else:
                self.stats['failed'] += 1
        
        # Print summary
        print("\n" + "=" * 70)
        print("SUMMARY")
        print("=" * 70)
        print(f"Total PDFs:       {self.stats['total']}")
        print(f"✓ Processed:      {self.stats['processed']}")
        print(f"✗ Failed:         {self.stats['failed']}")
        print(f"👤 Authors found:  {self.stats['authors_found']}")
        print(f"\nResults saved to: {self.output_dir}")


def main():
    parser = argparse.ArgumentParser(
        description='Extract author affiliations from academic PDFs',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python affiliation_extractor.py --input ./pdfs --output ./authors
  python affiliation_extractor.py -i ~/research/papers -o ~/research/authors
  
Notes:
  - Works best with standard academic paper formats
  - Extracts from first page where authors typically appear
  - Handles English and Slovak text
  - Output includes JSON and Markdown formats
        """
    )
    
    parser.add_argument(
        '--input', '-i',
        required=True,
        help='Directory containing PDF files'
    )
    
    parser.add_argument(
        '--output', '-o',
        required=True,
        help='Directory for output files'
    )
    
    args = parser.parse_args()
    
    extractor = AffiliationExtractor(args.input, args.output)
    extractor.process_all()


if __name__ == '__main__':
    main()
