#!/usr/bin/env python3
"""
AI-Powered Citation Extractor

Uses Claude API to extract citations from academic text where traditional
pattern matching fails (footnotes, mixed layouts, etc.)

This demonstrates the pragmatic approach: use AI for fuzzy parsing tasks.
"""

import anthropic
import json
import os
from pathlib import Path
from typing import List, Dict


def extract_citations_with_claude(markdown_text: str, api_key: str = None) -> Dict:
    """
    Use Claude to extract citations from markdown text.
    
    Args:
        markdown_text: The full text of the processed PDF
        api_key: Anthropic API key (or will use ANTHROPIC_API_KEY env var)
    
    Returns:
        Dictionary containing extracted citations and metadata
    """
    
    # Get API key from parameter or environment
    if not api_key:
        api_key = os.environ.get('ANTHROPIC_API_KEY')
    
    if not api_key:
        raise ValueError(
            "API key required. Set ANTHROPIC_API_KEY environment variable or pass api_key parameter.\n"
            "Get your key at: https://console.anthropic.com/"
        )
    
    # Initialize Claude client
    client = anthropic.Anthropic(api_key=api_key)
    
    # Craft the extraction prompt
    prompt = f"""You are a scholarly citation extraction assistant. Analyze the following academic text and extract ALL citations, references, and bibliographic information.

This text was extracted from a PDF and may have formatting issues (mixed columns, footnotes interspersed with main text, etc.). Your task is to identify and extract citations despite these issues.

IMPORTANT EXTRACTION RULES:
1. Look for authors, years, titles, publishers, locations, page numbers
2. Include citations from footnotes (often at bottom of pages)
3. Include inline citations like (Author Year)
4. Include full bibliographic entries
5. Capture journal articles, books, archival sources, and online sources
6. Note the approximate location in the text (page/section if visible)

OUTPUT FORMAT:
Provide a JSON object with this structure:
{{
  "citations": [
    {{
      "type": "book|article|chapter|online|archival",
      "authors": ["Author Name"],
      "year": "YYYY",
      "title": "Full Title",
      "publication": "Journal Name or Book Title",
      "publisher": "Publisher Name",
      "location": "City, State/Country",
      "pages": "page numbers",
      "url": "if applicable",
      "raw_text": "original citation text as found",
      "context": "where found (footnote X, page Y, etc.)",
      "confidence": 0.0-1.0
    }}
  ],
  "statistics": {{
    "total_found": 0,
    "by_type": {{}},
    "unique_authors": []
  }}
}}

TEXT TO ANALYZE:
---
{markdown_text}
---

Extract all citations now. Return ONLY the JSON object, no other text.
"""
    
    # Call Claude API
    print("📡 Sending to Claude API for citation extraction...")
    print(f"   Text length: {len(markdown_text):,} characters")
    print(f"   Estimated cost: ~${len(markdown_text) / 1000000 * 3:.2f}")
    print()
    
    message = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=4000,
        temperature=0,  # Low temperature for factual extraction
        messages=[
            {"role": "user", "content": prompt}
        ]
    )
    
    # Extract the response
    response_text = message.content[0].text
    
    # Parse JSON response
    # Remove markdown code blocks if present
    if response_text.startswith("```"):
        response_text = response_text.split("```")[1]
        if response_text.startswith("json"):
            response_text = response_text[4:]
        response_text = response_text.strip()
    
    try:
        citations_data = json.loads(response_text)
    except json.JSONDecodeError as e:
        print(f"⚠️  Warning: Failed to parse JSON response")
        print(f"Error: {e}")
        print(f"Response preview: {response_text[:500]}")
        citations_data = {"citations": [], "error": "Failed to parse response"}
    
    return citations_data


def save_citations(citations_data: Dict, output_dir: Path, source_name: str):
    """Save extracted citations in multiple formats"""
    
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Save as JSON
    json_path = output_dir / f"{source_name}_citations_ai.json"
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(citations_data, f, indent=2, ensure_ascii=False)
    
    print(f"✓ JSON saved: {json_path}")
    
    # Generate markdown report
    md_path = output_dir / f"{source_name}_citations_ai.md"
    with open(md_path, 'w', encoding='utf-8') as f:
        f.write(f"# Citations Extracted by Claude AI\n\n")
        f.write(f"**Source:** {source_name}\n")
        f.write(f"**Extraction Method:** AI-powered (Claude Sonnet 4)\n\n")
        
        if 'citations' in citations_data:
            citations = citations_data['citations']
            f.write(f"**Total Citations Found:** {len(citations)}\n\n")
            
            # Group by type
            by_type = {}
            for cit in citations:
                ctype = cit.get('type', 'unknown')
                if ctype not in by_type:
                    by_type[ctype] = []
                by_type[ctype].append(cit)
            
            f.write("## Citations by Type\n\n")
            for ctype, count in sorted([(k, len(v)) for k, v in by_type.items()], 
                                       key=lambda x: x[1], reverse=True):
                f.write(f"- **{ctype.title()}:** {count}\n")
            f.write("\n")
            
            # List all citations
            f.write("## All Citations\n\n")
            for i, cit in enumerate(citations, 1):
                f.write(f"### {i}. {cit.get('title', 'Untitled')}\n\n")
                
                if cit.get('authors'):
                    f.write(f"**Authors:** {', '.join(cit['authors'])}\n\n")
                
                if cit.get('year'):
                    f.write(f"**Year:** {cit['year']}\n\n")
                
                if cit.get('publication'):
                    f.write(f"**Publication:** {cit['publication']}\n\n")
                
                if cit.get('publisher'):
                    f.write(f"**Publisher:** {cit['publisher']}\n\n")
                
                if cit.get('location'):
                    f.write(f"**Location:** {cit['location']}\n\n")
                
                if cit.get('pages'):
                    f.write(f"**Pages:** {cit['pages']}\n\n")
                
                if cit.get('context'):
                    f.write(f"**Found in:** {cit['context']}\n\n")
                
                f.write(f"**Type:** {cit.get('type', 'unknown')}\n\n")
                f.write(f"**Confidence:** {cit.get('confidence', 0):.0%}\n\n")
                
                if cit.get('raw_text'):
                    f.write(f"**Original text:**\n```\n{cit['raw_text']}\n```\n\n")
                
                f.write("---\n\n")
    
    print(f"✓ Report saved: {md_path}")


def main():
    """Main execution"""
    
    print("="*70)
    print("AI-POWERED CITATION EXTRACTOR")
    print("Uses Claude API to extract citations from messy academic text")
    print("="*70)
    print()
    
    # Check for API key
    api_key = os.environ.get('ANTHROPIC_API_KEY')
    
    if not api_key:
        print("⚠️  ANTHROPIC_API_KEY not found in environment")
        print()
        print("To use this tool:")
        print("1. Get an API key from https://console.anthropic.com/")
        print("2. Set it in your environment:")
        print("   export ANTHROPIC_API_KEY='your-key-here'")
        print("3. Run this script again")
        print()
        print("💡 TIP: The API costs about $0.01-0.03 per document")
        print()
        return
    
    # Input file
    markdown_file = Path('/tmp/stolarik_analysis/Marian_Stolarik_-_Slovak_Fraternal-Benefit_societies_in_NA_1883-1993.md')
    
    if not markdown_file.exists():
        print(f"❌ Input file not found: {markdown_file}")
        return
    
    # Read the markdown
    print(f"📄 Reading: {markdown_file.name}")
    with open(markdown_file, 'r', encoding='utf-8') as f:
        markdown_text = f.read()
    
    print(f"   Length: {len(markdown_text):,} characters")
    print()
    
    # Extract citations using Claude
    try:
        citations_data = extract_citations_with_claude(markdown_text, api_key)
        
        print()
        print("✅ Extraction complete!")
        print()
        
        if 'citations' in citations_data:
            num_citations = len(citations_data['citations'])
            print(f"📚 Found {num_citations} citations")
            
            if 'statistics' in citations_data:
                stats = citations_data['statistics']
                if 'by_type' in stats:
                    print(f"\nBreakdown:")
                    for ctype, count in sorted(stats['by_type'].items(), 
                                               key=lambda x: x[1], reverse=True):
                        print(f"  - {ctype}: {count}")
        
        # Save results
        output_dir = Path('/tmp/stolarik_citations_ai')
        source_name = markdown_file.stem
        
        print()
        save_citations(citations_data, output_dir, source_name)
        print()
        print("="*70)
        
    except Exception as e:
        print(f"❌ Error: {e}")
        print()
        print("If this is an API key error, make sure:")
        print("1. Your API key is valid")
        print("2. You have credits in your Anthropic account")
        print("3. The key has proper permissions")


if __name__ == '__main__':
    main()