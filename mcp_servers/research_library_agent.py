#!/usr/bin/env python3
"""
Research Library Batch Processor

A robust agent that processes entire directories of academic PDFs:
1. Extracts text from all PDFs
2. Extracts citations using Claude API
3. Analyzes themes across entire corpus
4. Generates comprehensive research briefing

Usage:
    python research_library_agent.py --input /path/to/pdfs --output /path/to/results
    
Requirements:
    - ANTHROPIC_API_KEY environment variable set
    - PDF files in input directory
"""

import sys
import os
from pathlib import Path
import json
from datetime import datetime
from typing import Dict, List
import anthropic

# Add project directory to path so we can import our tools
sys.path.insert(0, '/mnt/project')

from pdf_processor import PDFProcessor
from theme_analyzer import ThemeAnalyzer


class ResearchLibraryAgent:
    """Batch processor for academic research libraries"""
    
    def __init__(self, input_dir: str, output_dir: str, api_key: str = None):
        self.input_dir = Path(input_dir)
        self.output_dir = Path(output_dir)
        self.api_key = api_key or os.environ.get('ANTHROPIC_API_KEY')
        
        if not self.api_key:
            raise ValueError(
                "API key required. Set ANTHROPIC_API_KEY environment variable.\n"
                "Get your key at: https://console.anthropic.com/"
            )
        
        # Create output directories
        self.pdf_output = self.output_dir / '1_extracted_text'
        self.citations_output = self.output_dir / '2_citations'
        self.themes_output = self.output_dir / '3_themes'
        self.briefings_output = self.output_dir / '4_briefings'
        
        for dir_path in [self.pdf_output, self.citations_output, 
                         self.themes_output, self.briefings_output]:
            dir_path.mkdir(parents=True, exist_ok=True)
        
        # Initialize Claude client
        self.client = anthropic.Anthropic(api_key=self.api_key)
        
        # Track processing
        self.processed_files = []
        self.failed_files = []
        self.total_api_cost = 0.0
        
    def run(self):
        """Execute the complete batch processing workflow"""
        
        print("="*80)
        print("RESEARCH LIBRARY BATCH PROCESSOR")
        print("="*80)
        print(f"\nInput:  {self.input_dir}")
        print(f"Output: {self.output_dir}")
        print()
        
        # Find all PDFs
        pdf_files = list(self.input_dir.glob('*.pdf'))
        
        if not pdf_files:
            print(f"❌ No PDF files found in {self.input_dir}")
            return
        
        print(f"📚 Found {len(pdf_files)} PDF file(s)")
        print()
        
        # Phase 1: Extract text from all PDFs
        print("="*80)
        print("PHASE 1: PDF TEXT EXTRACTION (No API cost)")
        print("="*80)
        print()
        
        extracted_files = self._extract_all_pdfs(pdf_files)
        
        if not extracted_files:
            print("❌ No PDFs were successfully extracted")
            return
        
        # Phase 2: Extract citations using AI (uses API)
        print("\n" + "="*80)
        print("PHASE 2: CITATION EXTRACTION (Uses Claude API)")
        print("="*80)
        print()
        
        citation_results = self._extract_all_citations(extracted_files)
        
        # Phase 3: Analyze themes across corpus
        print("\n" + "="*80)
        print("PHASE 3: THEME ANALYSIS (No API cost)")
        print("="*80)
        print()
        
        theme_results = self._analyze_corpus_themes(extracted_files)
        
        # Phase 4: Generate comprehensive briefing (uses API)
        print("\n" + "="*80)
        print("PHASE 4: RESEARCH SYNTHESIS (Uses Claude API)")
        print("="*80)
        print()
        
        self._generate_corpus_briefing(extracted_files, citation_results, theme_results)
        
        # Final summary
        self._print_final_summary()
        
    def _extract_all_pdfs(self, pdf_files: List[Path]) -> List[Path]:
        """Extract text from all PDFs using the standalone PDF processor"""
        
        processor = PDFProcessor(str(self.input_dir), str(self.pdf_output))
        stats = processor.process_directory()
        
        # Find all successfully extracted markdown files
        extracted = list(self.pdf_output.glob('*.md'))
        
        print(f"\n✓ Extracted {len(extracted)} PDF(s) successfully")
        
        return extracted
    
    def _extract_all_citations(self, markdown_files: List[Path]) -> Dict:
        """Extract citations from all markdown files using Claude API"""
        
        all_citations = {}
        total_cost = 0.0
        
        print(f"Processing {len(markdown_files)} document(s)...")
        print()
        
        for i, md_file in enumerate(markdown_files, 1):
            print(f"[{i}/{len(markdown_files)}] {md_file.stem[:50]}...")
            
            try:
                # Read markdown
                with open(md_file, 'r', encoding='utf-8') as f:
                    text = f.read()
                
                # Extract citations using Claude
                citations, cost = self._extract_citations_with_claude(text, md_file.stem)
                
                all_citations[md_file.stem] = citations
                total_cost += cost
                
                print(f"    ✓ Found {len(citations.get('citations', []))} citation(s)")
                print(f"    💰 Cost: ${cost:.4f}")
                
            except Exception as e:
                print(f"    ❌ Error: {e}")
                self.failed_files.append(md_file.stem)
        
        self.total_api_cost += total_cost
        
        print()
        print(f"✓ Citation extraction complete")
        print(f"💰 Total cost: ${total_cost:.2f}")
        
        # Save combined citations database
        citations_db = self.citations_output / 'all_citations.json'
        with open(citations_db, 'w', encoding='utf-8') as f:
            json.dump(all_citations, f, indent=2, ensure_ascii=False)
        
        print(f"📄 Saved citations database: {citations_db}")
        
        return all_citations
    
    def _extract_citations_with_claude(self, text: str, source_name: str) -> tuple:
        """Extract citations from text using Claude API"""
        
        # Skip metadata section
        if '## Extracted Text' in text:
            text = text.split('## Extracted Text', 1)[1]
        
        # Estimate cost (input tokens)
        estimated_cost = len(text) / 1000000 * 3  # $3 per million tokens (approximate)
        
        prompt = f"""Extract all citations from this academic text. Focus on:
- Books (Author. Year. Title. Location: Publisher.)
- Articles (Author. Year. "Title." Journal Volume(Issue): Pages.)
- Chapters (Author. Year. "Chapter." In Book, edited by Editor, pages. Location: Publisher.)
- Newspapers and archival sources

Return ONLY valid JSON:
{{
  "citations": [
    {{
      "type": "book|article|chapter|newspaper|archival",
      "authors": ["Author Name"],
      "year": "YYYY",
      "title": "Full Title",
      "publication": "Journal/Book Name",
      "publisher": "Publisher",
      "location": "City",
      "pages": "page numbers",
      "confidence": 0.0-1.0
    }}
  ],
  "statistics": {{
    "total": 0,
    "by_type": {{}}
  }}
}}

TEXT:
{text[:50000]}"""  # Limit to ~50k chars to control cost
        
        try:
            message = self.client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=4000,
                temperature=0,
                messages=[{"role": "user", "content": prompt}]
            )
            
            response_text = message.content[0].text
            
            # Clean JSON
            if response_text.startswith("```"):
                response_text = response_text.split("```")[1]
                if response_text.startswith("json"):
                    response_text = response_text[4:]
                response_text = response_text.strip()
            
            citations = json.loads(response_text)
            
            # Save individual citation file
            citation_file = self.citations_output / f"{source_name}_citations.json"
            with open(citation_file, 'w', encoding='utf-8') as f:
                json.dump(citations, f, indent=2, ensure_ascii=False)
            
            return citations, estimated_cost
            
        except Exception as e:
            return {"citations": [], "error": str(e)}, estimated_cost
    
    def _analyze_corpus_themes(self, markdown_files: List[Path]) -> Dict:
        """Analyze themes across entire corpus"""
        
        analyzer = ThemeAnalyzer()
        
        # Process all files
        for md_file in markdown_files:
            print(f"  Analyzing: {md_file.stem[:50]}...")
            analyzer.analyze_file(md_file)
        
        # Generate insights
        analyzer.save_analysis(self.themes_output, 'corpus')
        
        # Print summary
        analyzer.print_summary()
        
        # Return insights for briefing generation
        insights = analyzer.generate_insights()
        
        return insights
    
    def _generate_corpus_briefing(self, markdown_files: List[Path], 
                                  citations: Dict, themes: Dict):
        """Generate comprehensive research briefing across all documents"""
        
        print("Generating comprehensive research briefing...")
        print()
        
        # Prepare summary data
        summary_data = {
            "total_documents": len(markdown_files),
            "document_titles": [f.stem for f in markdown_files],
            "total_citations": sum(len(c.get('citations', [])) for c in citations.values()),
            "dominant_themes": themes.get('dominant_themes', [])[:10],
            "concept_clusters": themes.get('concept_clusters', [])[:5],
        }
        
        # Create prompt for synthesis
        prompt = f"""You are a research synthesis expert. Create a comprehensive research briefing based on the analysis of {len(markdown_files)} academic papers.

CORPUS OVERVIEW:
- Total documents: {summary_data['total_documents']}
- Total citations found: {summary_data['total_citations']}
- Top themes: {', '.join([t['term'] for t in summary_data['dominant_themes'][:5]])}

DOMINANT THEMES:
{json.dumps(summary_data['dominant_themes'], indent=2)}

CONCEPT CLUSTERS:
{json.dumps(summary_data['concept_clusters'], indent=2)}

Create a research briefing with:
1. Executive Summary (2-3 paragraphs)
2. Major Themes Across Corpus (top 5 themes with frequencies)
3. Concept Clusters (relationships between themes)
4. Research Gaps Identified
5. Key Insights and Patterns
6. Recommendations for Further Research

Keep it scholarly but accessible. Use markdown formatting.
"""
        
        try:
            message = self.client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=3000,
                temperature=0.3,
                messages=[{"role": "user", "content": prompt}]
            )
            
            briefing = message.content[0].text
            
            # Add header with metadata
            full_briefing = f"""# Research Library Analysis
## {len(markdown_files)} Documents Processed

**Analysis Date:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}  
**Total Citations:** {summary_data['total_citations']}  
**Processing Method:** Automated batch analysis with Claude AI

---

{briefing}

---

## Appendix: Processed Documents

"""
            # List all processed documents
            for i, md_file in enumerate(markdown_files, 1):
                full_briefing += f"{i}. {md_file.stem}\n"
            
            # Save briefing
            briefing_path = self.briefings_output / 'research_library_briefing.md'
            with open(briefing_path, 'w', encoding='utf-8') as f:
                f.write(full_briefing)
            
            print(f"✓ Comprehensive briefing generated")
            print(f"📄 Saved to: {briefing_path}")
            
            # Estimate cost
            cost = len(prompt) / 1000000 * 3
            self.total_api_cost += cost
            
        except Exception as e:
            print(f"❌ Error generating briefing: {e}")
    
    def _print_final_summary(self):
        """Print final processing summary"""
        
        print("\n" + "="*80)
        print("PROCESSING COMPLETE")
        print("="*80)
        print()
        print(f"📊 Summary:")
        print(f"  Total PDFs processed:  {len(self.processed_files) + len(self.failed_files)}")
        print(f"  ✓ Successful:          {len(self.processed_files)}")
        print(f"  ❌ Failed:              {len(self.failed_files)}")
        print()
        print(f"💰 Total API cost:       ${self.total_api_cost:.2f}")
        print()
        print(f"📁 Output locations:")
        print(f"  Extracted text:        {self.pdf_output}")
        print(f"  Citations database:    {self.citations_output}")
        print(f"  Theme analysis:        {self.themes_output}")
        print(f"  Research briefing:     {self.briefings_output}")
        print()
        print("="*80)
        print()


def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Batch process academic PDFs with AI-powered analysis',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Process all PDFs in a directory
  python research_library_agent.py --input ~/research/papers --output ~/research/analysis
  
  # Process with API key specified
  ANTHROPIC_API_KEY='your-key' python research_library_agent.py -i ./pdfs -o ./results

Cost Estimate:
  - PDF extraction: FREE
  - Theme analysis: FREE
  - Citation extraction: ~$0.01-0.03 per paper
  - Final synthesis: ~$0.05
  
  Total for 50 papers: ~$0.50-1.50
        """
    )
    
    parser.add_argument(
        '--input', '-i',
        required=True,
        help='Directory containing PDF files to process'
    )
    
    parser.add_argument(
        '--output', '-o',
        required=True,
        help='Directory for output files'
    )
    
    args = parser.parse_args()
    
    # Check for API key
    api_key = os.environ.get('ANTHROPIC_API_KEY')
    if not api_key:
        print("❌ ERROR: ANTHROPIC_API_KEY not set")
        print()
        print("To use this tool:")
        print("1. Get an API key from https://console.anthropic.com/")
        print("2. Set it in your environment:")
        print("   export ANTHROPIC_API_KEY='your-key-here'")
        print("3. Run this script again")
        print()
        sys.exit(1)
    
    try:
        agent = ResearchLibraryAgent(args.input, args.output, api_key)
        agent.run()
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Processing interrupted by user")
        sys.exit(1)
        
    except Exception as e:
        print(f"\n❌ Fatal error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()