"""CrossRef API client for citation enrichment."""

import json
import time
import urllib.parse
from pathlib import Path
from typing import Dict, List, Optional

try:
    import httpx

    HTTPX_AVAILABLE = True
except ImportError:
    HTTPX_AVAILABLE = False

try:
    import requests

    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False


class CrossRefEnricher:
    """Enrich citations using CrossRef API."""

    CROSSREF_API = "https://api.crossref.org/works"

    # Polite pool delay between requests (in seconds)
    REQUEST_DELAY = 0.5

    def __init__(self, email: Optional[str] = None):
        """
        Initialize CrossRef enricher.

        Args:
            email: Optional email for polite pool access (recommended).
                   CrossRef provides faster responses for requests that
                   include a mailto in the User-Agent.
        """
        self.email = email
        self._last_request_time = 0

        # Set up User-Agent header
        base_ua = "AcademicResearchToolkit/1.0"
        if email:
            self.user_agent = f"{base_ua} (mailto:{email})"
        else:
            self.user_agent = base_ua

    def lookup_doi(self, doi: str) -> Optional[Dict]:
        """
        Fetch metadata for a DOI from CrossRef.

        Args:
            doi: The DOI to look up (e.g., "10.1000/xyz123").

        Returns:
            Dictionary with metadata if found, None otherwise.
        """
        # Clean the DOI
        doi = self._clean_doi(doi)
        if not doi:
            return None

        url = f"{self.CROSSREF_API}/{urllib.parse.quote(doi, safe='')}"

        response = self._make_request(url)
        if response is None:
            return None

        try:
            data = response.get("message", {})
            return self._parse_work(data)
        except (KeyError, TypeError):
            return None

    def enrich_citation(self, citation: Dict) -> Dict:
        """
        Enrich a citation if DOI is present.

        Args:
            citation: Citation dictionary, optionally containing a 'doi' field.

        Returns:
            Enriched citation dictionary with additional metadata.
        """
        enriched = citation.copy()

        # If DOI is present, look it up
        doi = citation.get("doi")
        if doi:
            metadata = self.lookup_doi(doi)
            if metadata:
                enriched = self._merge_metadata(enriched, metadata)
                enriched["enriched"] = True
                enriched["enrichment_source"] = "crossref"
            return enriched

        # If no DOI but we have title/author, try to find a match
        title = citation.get("title")
        authors = citation.get("authors", [])
        author = authors[0] if isinstance(authors, list) and authors else str(authors) if authors else None

        if title:
            matches = self.search_by_title(title, author)
            if matches:
                # Use the first match (highest score)
                best_match = matches[0]
                enriched = self._merge_metadata(enriched, best_match)
                enriched["enriched"] = True
                enriched["enrichment_source"] = "crossref_search"

        return enriched

    def search_by_title(self, title: str, author: Optional[str] = None) -> List[Dict]:
        """
        Search CrossRef for works matching a title.

        Args:
            title: The title to search for.
            author: Optional author name to narrow results.

        Returns:
            List of matching works with metadata.
        """
        params = {"query.title": title, "rows": 5}

        if author:
            params["query.author"] = author

        query_string = urllib.parse.urlencode(params)
        url = f"{self.CROSSREF_API}?{query_string}"

        response = self._make_request(url)
        if response is None:
            return []

        try:
            items = response.get("message", {}).get("items", [])
            return [self._parse_work(item) for item in items if item]
        except (KeyError, TypeError):
            return []

    def enrich_citations(self, citations: List[Dict]) -> List[Dict]:
        """
        Enrich multiple citations.

        Args:
            citations: List of citation dictionaries.

        Returns:
            List of enriched citation dictionaries.
        """
        enriched = []
        for citation in citations:
            enriched_citation = self.enrich_citation(citation)
            enriched.append(enriched_citation)
        return enriched

    def save_enriched(self, citations: List[Dict], output_path: Path) -> str:
        """
        Save enriched citations to a JSON file.

        Args:
            citations: List of citation dictionaries.
            output_path: Path to output JSON file.

        Returns:
            Path to the saved file as string.
        """
        output_path = Path(output_path)
        enriched = self.enrich_citations(citations)

        with output_path.open("w", encoding="utf-8") as f:
            json.dump(enriched, f, indent=2, ensure_ascii=False)

        return str(output_path)

    def load_citations(self, citations_path: Path) -> List[Dict]:
        """
        Load citations from a JSON file.

        Args:
            citations_path: Path to JSON file containing citations.

        Returns:
            List of citation dictionaries.
        """
        citations_path = Path(citations_path)
        with citations_path.open("r", encoding="utf-8") as f:
            data = json.load(f)

        # Handle both list format and dict format with 'citations' key
        if isinstance(data, list):
            return data
        elif isinstance(data, dict) and "citations" in data:
            return data["citations"]
        else:
            return []

    def _make_request(self, url: str) -> Optional[Dict]:
        """Make an HTTP request with rate limiting."""
        # Rate limiting
        elapsed = time.time() - self._last_request_time
        if elapsed < self.REQUEST_DELAY:
            time.sleep(self.REQUEST_DELAY - elapsed)

        headers = {"User-Agent": self.user_agent}

        try:
            if HTTPX_AVAILABLE:
                with httpx.Client(timeout=30.0) as client:
                    response = client.get(url, headers=headers)
                    self._last_request_time = time.time()
                    if response.status_code == 200:
                        return response.json()
            elif REQUESTS_AVAILABLE:
                response = requests.get(url, headers=headers, timeout=30)
                self._last_request_time = time.time()
                if response.status_code == 200:
                    return response.json()
            else:
                # Fall back to urllib
                import urllib.request

                req = urllib.request.Request(url, headers=headers)
                with urllib.request.urlopen(req, timeout=30) as response:
                    self._last_request_time = time.time()
                    return json.loads(response.read().decode("utf-8"))
        except Exception:
            # Silently fail on network errors
            pass

        return None

    def _clean_doi(self, doi: str) -> Optional[str]:
        """Clean and validate a DOI string."""
        if not doi:
            return None

        doi = str(doi).strip()

        # Remove common URL prefixes
        prefixes = [
            "https://doi.org/",
            "http://doi.org/",
            "doi.org/",
            "https://dx.doi.org/",
            "http://dx.doi.org/",
            "dx.doi.org/",
            "doi:",
        ]

        for prefix in prefixes:
            if doi.lower().startswith(prefix.lower()):
                doi = doi[len(prefix) :]
                break

        # Basic DOI validation (should start with "10.")
        if doi.startswith("10."):
            return doi

        return None

    def _parse_work(self, data: Dict) -> Dict:
        """Parse CrossRef work data into our citation format."""
        result = {}

        # DOI
        if "DOI" in data:
            result["doi"] = data["DOI"]

        # Title
        titles = data.get("title", [])
        if titles:
            result["title"] = titles[0]

        # Authors
        authors = data.get("author", [])
        if authors:
            author_names = []
            for author in authors:
                given = author.get("given", "")
                family = author.get("family", "")
                if family:
                    if given:
                        author_names.append(f"{family}, {given}")
                    else:
                        author_names.append(family)
            if author_names:
                result["authors"] = author_names

        # Year (from various date fields)
        for date_field in ["published-print", "published-online", "created", "issued"]:
            date_parts = data.get(date_field, {}).get("date-parts", [[]])
            if date_parts and date_parts[0]:
                year = date_parts[0][0]
                if year:
                    result["year"] = str(year)
                    break

        # Publisher
        if "publisher" in data:
            result["publisher"] = data["publisher"]

        # Container (journal name)
        container = data.get("container-title", [])
        if container:
            result["source"] = container[0]

        # Volume and issue
        if "volume" in data:
            result["volume"] = data["volume"]
        if "issue" in data:
            result["issue"] = data["issue"]

        # Pages
        if "page" in data:
            result["pages"] = data["page"]

        # URL
        if "URL" in data:
            result["url"] = data["URL"]

        # Type mapping
        type_map = {
            "journal-article": "article",
            "book": "book",
            "book-chapter": "book",
            "proceedings-article": "article",
            "posted-content": "online",
        }
        if "type" in data:
            result["citation_type"] = type_map.get(data["type"], "unclassified")

        # ISSN
        if "ISSN" in data and data["ISSN"]:
            result["issn"] = data["ISSN"][0]

        # ISBN
        if "ISBN" in data and data["ISBN"]:
            result["isbn"] = data["ISBN"][0]

        return result

    def _merge_metadata(self, original: Dict, enriched: Dict) -> Dict:
        """
        Merge enriched metadata into original citation.

        Original values are preserved; only missing fields are filled.
        """
        result = original.copy()

        # Fields to potentially fill from enrichment
        fill_fields = [
            "doi",
            "title",
            "authors",
            "year",
            "publisher",
            "source",
            "volume",
            "issue",
            "pages",
            "url",
            "citation_type",
            "issn",
            "isbn",
        ]

        for field in fill_fields:
            if field not in result or not result[field]:
                if field in enriched and enriched[field]:
                    result[field] = enriched[field]

        return result
