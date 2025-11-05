#!/usr/bin/env python3
"""
Theme Analyzer MCP Server

Converts the standalone theme analyzer into an MCP server that can be used
by the Claude Agent SDK.

This server exposes theme analysis functionality as MCP tools.
"""

from fastmcp import FastMCP
import re
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Set, Tuple
from collections import Counter, defaultdict
import json


# Create the MCP server
mcp = FastMCP("Theme Analyzer")


@mcp.tool()
def analyze_themes(markdown_file: str, output_dir: str = "/tmp/themes") -> Dict:
    """
    Analyze themes and concepts in a markdown file.
    
    Args:
        markdown_file: Path to markdown file (from PDF processor)
        output_dir: Directory where output files will be saved
        
    Returns:
        Dictionary containing:
        - success: bool
        - insights: analysis insights including dominant themes, clusters, gaps
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
        
        # Initialize analysis structures
        term_frequencies = Counter()
        term_contexts = defaultdict(list)
        cooccurrences = defaultdict(Counter)
        
        # Extract terms
        terms = extract_terms(content)
        
        # Count frequencies
        for term in terms:
            term_frequencies[term] += 1
        
        # Extract contexts for significant terms
        significant_terms = [t for t, count in term_frequencies.most_common(50)]
        for term in significant_terms:
            contexts = extract_contexts(content, term)
            term_contexts[term].extend(contexts)
        
        # Find cooccurrences
        find_cooccurrences(content, significant_terms, cooccurrences)
        
        # Generate insights
        insights = generate_insights(
            term_frequencies,
            term_contexts,
            cooccurrences,
            markdown_file.name
        )
        
        # Save results
        base_name = markdown_file.stem
        
        # Save as JSON
        json_path = output_dir / f"{base_name}_themes.json"
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(insights, f, indent=2, ensure_ascii=False)
        
        # Save as markdown report
        md_path = output_dir / f"{base_name}_report.md"
        generate_markdown_report(insights, md_path)
        
        return {
            "success": True,
            "insights": insights,
            "json_path": str(json_path),
            "markdown_path": str(md_path)
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


@mcp.tool()
def analyze_themes_batch(input_dir: str, output_dir: str = "/tmp/themes") -> Dict:
    """
    Analyze themes across all markdown files in a directory.
    
    Args:
        input_dir: Directory containing markdown files
        output_dir: Directory where output files will be saved
        
    Returns:
        Dictionary containing:
        - success: bool
        - processed: list of successfully processed files
        - failed: list of failed files with errors
        - combined_insights: insights across all documents
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
        
        # For combined analysis
        all_term_frequencies = Counter()
        all_cooccurrences = defaultdict(Counter)
        
        for md_file in md_files:
            result = analyze_themes(str(md_file), str(output_dir))
            
            if result['success']:
                processed.append({
                    "filename": md_file.name,
                    "insights": result['insights']
                })
                
                # Accumulate for combined analysis
                insights = result['insights']
                for theme in insights.get('dominant_themes', []):
                    all_term_frequencies[theme['term']] += theme['frequency']
                    
            else:
                failed.append({
                    "filename": md_file.name,
                    "error": result.get('error', 'Unknown error')
                })
        
        # Generate combined insights
        combined_insights = {
            "total_documents": len(md_files),
            "successful_analyses": len(processed),
            "top_themes_across_corpus": [
                {"term": term, "total_frequency": count}
                for term, count in all_term_frequencies.most_common(20)
            ]
        }
        
        return {
            "success": True,
            "processed": processed,
            "failed": failed,
            "combined_insights": combined_insights,
            "stats": {
                "total_files": len(md_files),
                "successful": len(processed),
                "failed": len(failed)
            }
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


def skip_metadata(content: str) -> str:
    """Skip the metadata section."""
    parts = content.split('## Extracted Text', 1)
    if len(parts) == 2:
        return parts[1]
    return content


def extract_terms(text: str) -> List[str]:
    """Extract meaningful terms from text."""
    # Stop words
    stop_words = {
        'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
        'of', 'with', 'by', 'from', 'as', 'is', 'was', 'are', 'were', 'been',
        'be', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would',
        'should', 'could', 'may', 'might', 'must', 'can', 'this', 'that',
        'these', 'those', 'i', 'you', 'he', 'she', 'it', 'we', 'they',
        'what', 'which', 'who', 'when', 'where', 'why', 'how'
    }
    
    text = text.lower()
    words = re.findall(r'\b[a-záäčďéíľňóôŕšťúýž]+\b', text, re.UNICODE)
    
    terms = [w for w in words if w not in stop_words and len(w) >= 3]
    
    return terms


def extract_contexts(text: str, term: str, window: int = 50) -> List[str]:
    """Extract context snippets where term appears."""
    contexts = []
    text_lower = text.lower()
    term_lower = term.lower()
    
    pos = 0
    while True:
        pos = text_lower.find(term_lower, pos)
        if pos == -1:
            break
        
        start = max(0, pos - window)
        end = min(len(text), pos + len(term) + window)
        
        context = text[start:end].strip()
        contexts.append(context)
        
        pos += len(term)
    
    return contexts[:3]


def find_cooccurrences(text: str, terms: List[str], 
                       cooccurrences: defaultdict, window: int = 100):
    """Find terms that frequently appear together."""
    text_lower = text.lower()
    
    for i, term1 in enumerate(terms):
        positions = [m.start() for m in re.finditer(r'\b' + re.escape(term1) + r'\b', text_lower)]
        
        for pos in positions:
            window_start = max(0, pos - window)
            window_end = min(len(text), pos + window)
            window_text = text_lower[window_start:window_end]
            
            for term2 in terms[i+1:]:
                if term2 in window_text:
                    cooccurrences[term1][term2] += 1
                    cooccurrences[term2][term1] += 1


def generate_insights(term_frequencies: Counter, term_contexts: Dict,
                      cooccurrences: defaultdict, source_filename: str) -> Dict:
    """Generate research insights and opportunities."""
    
    # Identify dominant themes
    dominant = []
    for term, frequency in term_frequencies.most_common(30):
        related = []
        if term in cooccurrences:
            related = [
                {'term': t, 'strength': count}
                for t, count in cooccurrences[term].most_common(5)
            ]
        
        contexts = term_contexts.get(term, [])[:3]
        
        importance = frequency * (1 + (1.0 / (1.0 + frequency)))
        
        dominant.append({
            'term': term,
            'frequency': frequency,
            'importance': round(importance, 2),
            'related_terms': related,
            'sample_contexts': contexts
        })
    
    dominant.sort(key=lambda x: x['importance'], reverse=True)
    
    # Identify emerging themes
    emerging = [t for t in dominant if 3 <= t['frequency'] <= 10][:5]
    
    # Identify concept clusters
    clusters = []
    processed = set()
    
    for theme in dominant[:20]:
        term = theme['term']
        if term in processed:
            continue
        
        if theme['related_terms']:
            cluster_terms = [rt['term'] for rt in theme['related_terms'][:3]]
            if len(cluster_terms) > 0:
                clusters.append({
                    'central_term': term,
                    'related_terms': cluster_terms,
                    'cohesion': len(cluster_terms) + 1,
                    'total_mentions': term_frequencies[term] + sum(term_frequencies[t] for t in cluster_terms)
                })
                processed.add(term)
    
    # Identify gaps
    single_mentions = [term for term, count in term_frequencies.items() if count == 1]
    
    insights = {
        'source_file': source_filename,
        'dominant_themes': dominant[:5],
        'emerging_themes': emerging,
        'concept_clusters': clusters[:5],
        'potential_gaps': {
            'count': len(single_mentions),
            'examples': single_mentions[:10]
        },
        'corpus_statistics': {
            'unique_terms': len(term_frequencies),
            'total_terms': sum(term_frequencies.values())
        }
    }
    
    return insights


def generate_markdown_report(insights: Dict, output_path: Path):
    """Generate human-readable markdown report."""
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(f"# Theme Analysis Report\n\n")
        f.write(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        
        # Corpus statistics
        stats = insights['corpus_statistics']
        f.write(f"## Corpus Statistics\n\n")
        f.write(f"- **Unique Terms:** {stats['unique_terms']}\n")
        f.write(f"- **Total Term Occurrences:** {stats['total_terms']}\n\n")
        
        # Dominant themes
        f.write(f"## Dominant Themes\n\n")
        for theme in insights['dominant_themes']:
            f.write(f"### {theme['term'].title()}\n\n")
            f.write(f"- **Frequency:** {theme['frequency']} occurrences\n")
            f.write(f"- **Importance Score:** {theme['importance']}\n")
            
            if theme['related_terms']:
                f.write(f"- **Related Terms:**\n")
                for rel in theme['related_terms']:
                    f.write(f"  - {rel['term']} (co-occurs {rel['strength']} times)\n")
            
            if theme['sample_contexts']:
                f.write(f"\n**Sample Contexts:**\n")
                for i, ctx in enumerate(theme['sample_contexts'][:2], 1):
                    f.write(f"{i}. \"...{ctx}...\"\n\n")
            
            f.write("\n---\n\n")
        
        # Concept clusters
        if insights['concept_clusters']:
            f.write(f"## Concept Clusters\n\n")
            for cluster in insights['concept_clusters']:
                f.write(f"### Cluster: {cluster['central_term'].title()}\n\n")
                f.write(f"- **Related Terms:** {', '.join(cluster['related_terms'])}\n")
                f.write(f"- **Total Mentions:** {cluster['total_mentions']}\n\n")
        
        # Emerging themes
        if insights['emerging_themes']:
            f.write(f"## Emerging Themes\n\n")
            for theme in insights['emerging_themes']:
                f.write(f"- **{theme['term'].title()}** ({theme['frequency']} mentions)\n")
            f.write("\n")
        
        # Research gaps
        gaps = insights['potential_gaps']
        f.write(f"## Potential Research Gaps\n\n")
        f.write(f"Found **{gaps['count']}** terms mentioned only once.\n\n")
        f.write("Sample underrepresented topics:\n")
        for term in gaps['examples']:
            f.write(f"- {term}\n")


if __name__ == "__main__":
    # Run the MCP server
    mcp.run()