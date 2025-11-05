#!/usr/bin/env python3
"""
PDF Processor MCP Server

Converts the standalone PDF processor into an MCP server that can be used
by the Claude Agent SDK.

This server exposes the PDF processing functionality as MCP tools.
"""

from fastmcp import FastMCP
import pdfplumber
from pypdf import PdfReader
from pathlib import Path
import json
from datetime import datetime
from typing import Dict, List, Optional
import re


# Create the MCP server
mcp = FastMCP("PDF Processor")


@mcp.tool()
def process_pdf(pdf_path: str, output_dir: str = "/tmp/pdf_output") -> Dict:
    """
    Extract text and metadata from a PDF file.
    
    Args:
        pdf_path: Path to the PDF file to process
        output_dir: Directory where output files will be saved
        
    Returns:
        Dictionary containing:
        - success: bool
        - markdown_path: path to generated markdown file
        - json_path: path to metadata JSON file
        - stats: processing statistics
        - error: error message if failed
    """
    try:
        pdf_path = Path(pdf_path)
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        if not pdf_path.exists():
            return {
                "success": False,
                "error": f"PDF file not found: {pdf_path}"
            }
        
        # Extract metadata
        metadata = extract_metadata(pdf_path)
        
        # Extract text
        full_text, page_texts = extract_text(pdf_path)
        
        if not full_text:
            return {
                "success": False,
                "error": "No text could be extracted from PDF"
            }
        
        # Clean text
        full_text = clean_text(full_text)
        
        # Generate markdown
        markdown = generate_markdown(pdf_path, metadata, full_text)
        
        # Save output
        output_filename = pdf_path.stem + '.md'
        markdown_path = output_dir / output_filename
        
        with open(markdown_path, 'w', encoding='utf-8') as f:
            f.write(markdown)
        
        # Save metadata as JSON
        json_filename = pdf_path.stem + '_metadata.json'
        json_path = output_dir / json_filename
        
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, indent=2)
        
        return {
            "success": True,
            "markdown_path": str(markdown_path),
            "json_path": str(json_path),
            "stats": {
                "pages": metadata.get('page_count', 0),
                "characters": len(full_text),
                "filename": pdf_path.name
            }
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


@mcp.tool()
def process_pdf_directory(input_dir: str, output_dir: str = "/tmp/pdf_output") -> Dict:
    """
    Process all PDF files in a directory.
    
    Args:
        input_dir: Directory containing PDF files
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
        
        pdf_files = list(input_dir.glob('*.pdf'))
        
        if not pdf_files:
            return {
                "success": False,
                "error": f"No PDF files found in {input_dir}"
            }
        
        processed = []
        failed = []
        
        for pdf_file in pdf_files:
            result = process_pdf(str(pdf_file), str(output_dir))
            
            if result['success']:
                processed.append({
                    "filename": pdf_file.name,
                    "stats": result['stats']
                })
            else:
                failed.append({
                    "filename": pdf_file.name,
                    "error": result.get('error', 'Unknown error')
                })
        
        return {
            "success": True,
            "processed": processed,
            "failed": failed,
            "stats": {
                "total": len(pdf_files),
                "successful": len(processed),
                "failed": len(failed)
            }
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


def extract_metadata(pdf_path: Path) -> Dict:
    """Extract metadata from PDF using pypdf."""
    metadata = {
        'filename': pdf_path.name,
        'title': None,
        'author': None,
        'subject': None,
        'creator': None,
        'producer': None,
        'creation_date': None,
        'page_count': None
    }
    
    try:
        reader = PdfReader(str(pdf_path))
        info = reader.metadata
        
        if info:
            metadata['title'] = info.get('/Title', None)
            metadata['author'] = info.get('/Author', None)
            metadata['subject'] = info.get('/Subject', None)
            metadata['creator'] = info.get('/Creator', None)
            metadata['producer'] = info.get('/Producer', None)
            
            creation_date = info.get('/CreationDate', None)
            if creation_date:
                metadata['creation_date'] = str(creation_date)
        
        metadata['page_count'] = len(reader.pages)
        
    except Exception as e:
        # Non-critical error, return partial metadata
        pass
    
    return metadata


def extract_text(pdf_path: Path) -> tuple[str, Dict]:
    """Extract text from PDF using pdfplumber."""
    full_text = []
    page_texts = {}
    
    try:
        with pdfplumber.open(pdf_path) as pdf:
            for page_num, page in enumerate(pdf.pages, 1):
                try:
                    text = page.extract_text()
                    if text:
                        full_text.append(text)
                        page_texts[page_num] = text
                except Exception:
                    continue
    except Exception as e:
        raise Exception(f"Failed to open PDF: {e}")
    
    return '\n\n'.join(full_text), page_texts


def clean_text(text: str) -> str:
    """Basic text cleaning."""
    # Remove excessive whitespace
    text = re.sub(r'\n{3,}', '\n\n', text)
    text = re.sub(r' {2,}', ' ', text)
    
    # Remove form feed characters
    text = text.replace('\x0c', '')
    
    return text.strip()


def generate_markdown(pdf_path: Path, metadata: Dict, text: str) -> str:
    """Generate markdown output with metadata and extracted text."""
    
    md_parts = []
    
    # Header
    md_parts.append(f"# {metadata.get('title') or pdf_path.stem}\n")
    
    # Metadata section
    md_parts.append("## Document Metadata\n")
    md_parts.append(f"- **Filename:** {metadata['filename']}")
    
    if metadata.get('author'):
        md_parts.append(f"- **Author:** {metadata['author']}")
    
    if metadata.get('subject'):
        md_parts.append(f"- **Subject:** {metadata['subject']}")
    
    if metadata.get('creation_date'):
        md_parts.append(f"- **Date:** {metadata['creation_date']}")
    
    if metadata.get('page_count'):
        md_parts.append(f"- **Pages:** {metadata['page_count']}")
    
    md_parts.append(f"- **Processed:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    # Extracted text
    md_parts.append("## Extracted Text\n")
    md_parts.append(text)
    
    return '\n'.join(md_parts)


if __name__ == "__main__":
    # Run the MCP server
    mcp.run()