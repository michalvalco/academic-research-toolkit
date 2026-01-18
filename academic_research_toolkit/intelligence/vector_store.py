"""
Vector store for semantic search over academic documents.

Uses numpy for vector operations and supports multiple embedding providers.
"""

import hashlib
import json
import pickle
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple

try:
    import numpy as np
except ImportError:
    np = None  # type: ignore


@dataclass
class Document:
    """A document chunk with its embedding and metadata."""

    doc_id: str
    text: str
    embedding: Optional[List[float]] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    chunk_index: int = 0


class VectorStore:
    """Semantic vector store for academic documents.

    Supports chunking, embedding, and cosine similarity search.
    Can use OpenAI, Anthropic (via voyageai), or local embeddings.
    """

    # Default chunking parameters
    DEFAULT_CHUNK_SIZE = 1000
    DEFAULT_CHUNK_OVERLAP = 200

    def __init__(
        self,
        embedding_model: str = "text-embedding-3-small",
        embedding_provider: str = "openai",
        chunk_size: int = DEFAULT_CHUNK_SIZE,
        chunk_overlap: int = DEFAULT_CHUNK_OVERLAP,
    ):
        """Initialize the vector store.

        Args:
            embedding_model: Name of the embedding model to use.
            embedding_provider: Provider for embeddings ('openai', 'anthropic', 'local').
            chunk_size: Maximum characters per chunk.
            chunk_overlap: Overlap between consecutive chunks.
        """
        if np is None:
            raise ImportError(
                "numpy is required for VectorStore. "
                "Install with: pip install academic-research-toolkit[intelligence]"
            )

        self.embedding_model = embedding_model
        self.embedding_provider = embedding_provider
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

        self.documents: List[Document] = []
        self._embedding_cache: Dict[str, List[float]] = {}
        self._token_usage: Dict[str, int] = {"total": 0, "cached": 0}

        # Lazy-loaded embedding function
        self._embed_fn: Optional[Callable] = None

    @property
    def dimension(self) -> int:
        """Return the embedding dimension."""
        if not self.documents or self.documents[0].embedding is None:
            return 0
        return len(self.documents[0].embedding)

    def _get_text_hash(self, text: str) -> str:
        """Generate a hash for text to use as cache key."""
        return hashlib.md5(text.encode()).hexdigest()

    def _init_embedding_function(self) -> Callable:
        """Initialize the embedding function based on provider."""
        if self._embed_fn is not None:
            return self._embed_fn

        if self.embedding_provider == "openai":
            self._embed_fn = self._openai_embed
        elif self.embedding_provider == "anthropic":
            # Anthropic doesn't have native embeddings yet, use voyageai
            self._embed_fn = self._voyage_embed
        elif self.embedding_provider == "local":
            self._embed_fn = self._local_embed
        else:
            raise ValueError(f"Unknown embedding provider: {self.embedding_provider}")

        return self._embed_fn

    def _openai_embed(self, texts: List[str]) -> List[List[float]]:
        """Get embeddings using OpenAI API."""
        try:
            import openai
        except ImportError:
            raise ImportError(
                "openai package required for OpenAI embeddings. "
                "Install with: pip install openai"
            )

        client = openai.OpenAI()

        # Process in batches to handle rate limits
        embeddings = []
        batch_size = 100

        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]
            response = client.embeddings.create(
                model=self.embedding_model,
                input=batch
            )
            for item in response.data:
                embeddings.append(item.embedding)

            # Track token usage
            if hasattr(response, 'usage'):
                self._token_usage["total"] += response.usage.total_tokens

        return embeddings

    def _voyage_embed(self, texts: List[str]) -> List[List[float]]:
        """Get embeddings using VoyageAI (for Anthropic users)."""
        try:
            import voyageai
        except ImportError:
            raise ImportError(
                "voyageai package required for Anthropic-compatible embeddings. "
                "Install with: pip install voyageai"
            )

        client = voyageai.Client()

        # Use voyage model if anthropic provider is selected
        model = "voyage-2" if self.embedding_model == "text-embedding-3-small" else self.embedding_model

        embeddings = []
        batch_size = 128

        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]
            result = client.embed(batch, model=model)
            embeddings.extend(result.embeddings)

        return embeddings

    # Fixed dimension for local embeddings (hash-based)
    LOCAL_EMBED_DIM = 256

    def _local_embed(self, texts: List[str]) -> List[List[float]]:
        """Generate simple local embeddings using hash-based approach.

        This is a fallback for when no external API is available.
        Uses a hash-based approach to ensure consistent dimensions.
        """
        embeddings = []

        for text in texts:
            # Use fixed-size vector with hash-based word placement
            vec = np.zeros(self.LOCAL_EMBED_DIM)

            for word in text.lower().split():
                word = ''.join(c for c in word if c.isalnum())
                if word and len(word) >= 2:
                    # Hash word to get consistent index
                    word_hash = hash(word) % self.LOCAL_EMBED_DIM
                    vec[word_hash] += 1

            # Normalize
            norm = np.linalg.norm(vec)
            if norm > 0:
                vec = vec / norm

            embeddings.append(vec.tolist())

        return embeddings

    def _chunk_text(self, text: str) -> List[str]:
        """Split text into overlapping chunks.

        Args:
            text: Text to chunk.

        Returns:
            List of text chunks.
        """
        if len(text) <= self.chunk_size:
            return [text]

        chunks = []
        start = 0

        while start < len(text):
            end = start + self.chunk_size

            # Try to break at sentence boundary
            if end < len(text):
                # Look for sentence-ending punctuation
                for sep in ['. ', '.\n', '! ', '!\n', '? ', '?\n']:
                    last_sep = text[start:end].rfind(sep)
                    if last_sep > self.chunk_size // 2:
                        end = start + last_sep + len(sep)
                        break

            chunk = text[start:end].strip()
            if chunk:
                chunks.append(chunk)

            start = end - self.chunk_overlap
            if start >= len(text):
                break

        return chunks

    def add_document(
        self,
        doc_id: str,
        text: str,
        metadata: Optional[Dict[str, Any]] = None,
        chunk: bool = True,
    ) -> int:
        """Embed and store a document.

        Args:
            doc_id: Unique identifier for the document.
            text: Document text content.
            metadata: Optional metadata (title, authors, year, etc.).
            chunk: Whether to chunk the document.

        Returns:
            Number of chunks added.
        """
        metadata = metadata or {}

        if chunk:
            chunks = self._chunk_text(text)
        else:
            chunks = [text]

        embed_fn = self._init_embedding_function()

        # Check cache for existing embeddings
        texts_to_embed = []
        cache_keys = []

        for chunk_text in chunks:
            cache_key = self._get_text_hash(chunk_text)
            cache_keys.append(cache_key)
            if cache_key not in self._embedding_cache:
                texts_to_embed.append(chunk_text)

        # Get new embeddings
        if texts_to_embed:
            new_embeddings = embed_fn(texts_to_embed)
            embed_idx = 0
            for i, cache_key in enumerate(cache_keys):
                if cache_key not in self._embedding_cache:
                    self._embedding_cache[cache_key] = new_embeddings[embed_idx]
                    embed_idx += 1
                else:
                    self._token_usage["cached"] += 1

        # Create documents
        for i, (chunk_text, cache_key) in enumerate(zip(chunks, cache_keys)):
            doc = Document(
                doc_id=f"{doc_id}_chunk_{i}" if len(chunks) > 1 else doc_id,
                text=chunk_text,
                embedding=self._embedding_cache[cache_key],
                metadata={
                    **metadata,
                    "original_doc_id": doc_id,
                    "chunk_index": i,
                    "total_chunks": len(chunks),
                },
                chunk_index=i,
            )
            self.documents.append(doc)

        return len(chunks)

    def add_citations(self, citations: List[Dict[str, Any]]) -> int:
        """Index citations for semantic search.

        Args:
            citations: List of citation dictionaries.

        Returns:
            Number of citations indexed.
        """
        count = 0
        for i, citation in enumerate(citations):
            # Build searchable text from citation fields
            parts = []

            if citation.get("title"):
                parts.append(citation["title"])

            if citation.get("authors"):
                if isinstance(citation["authors"], list):
                    parts.append(", ".join(citation["authors"]))
                else:
                    parts.append(str(citation["authors"]))

            if citation.get("raw_text"):
                parts.append(citation["raw_text"])

            text = " ".join(parts)
            if not text.strip():
                continue

            doc_id = citation.get("doi") or f"citation_{i}"

            metadata = {
                "title": citation.get("title"),
                "authors": citation.get("authors"),
                "year": citation.get("year"),
                "source": citation.get("source"),
                "citation_type": citation.get("citation_type"),
                "doi": citation.get("doi"),
                "raw_text": citation.get("raw_text"),
            }

            self.add_document(doc_id, text, metadata, chunk=False)
            count += 1

        return count

    def _cosine_similarity(
        self,
        query_vec: np.ndarray,
        doc_vecs: np.ndarray,
    ) -> np.ndarray:
        """Compute cosine similarity between query and documents.

        Args:
            query_vec: Query embedding vector.
            doc_vecs: Matrix of document embeddings.

        Returns:
            Array of similarity scores.
        """
        # Normalize query
        query_norm = np.linalg.norm(query_vec)
        if query_norm > 0:
            query_vec = query_vec / query_norm

        # Normalize documents
        doc_norms = np.linalg.norm(doc_vecs, axis=1, keepdims=True)
        doc_norms = np.where(doc_norms > 0, doc_norms, 1)
        doc_vecs_norm = doc_vecs / doc_norms

        # Compute cosine similarity
        similarities = np.dot(doc_vecs_norm, query_vec)

        return similarities

    def search(
        self,
        query: str,
        top_k: int = 5,
        threshold: float = 0.0,
        filter_fn: Optional[Callable[[Document], bool]] = None,
    ) -> List[Dict[str, Any]]:
        """Find semantically similar documents.

        Args:
            query: Search query text.
            top_k: Number of results to return.
            threshold: Minimum similarity score (0-1).
            filter_fn: Optional function to filter documents.

        Returns:
            List of results with document, score, and metadata.
        """
        if not self.documents:
            return []

        # Get query embedding
        embed_fn = self._init_embedding_function()
        query_embedding = embed_fn([query])[0]
        query_vec = np.array(query_embedding)

        # Filter documents if needed
        filtered_docs = self.documents
        if filter_fn:
            filtered_docs = [d for d in self.documents if filter_fn(d)]

        if not filtered_docs:
            return []

        # Build document matrix
        doc_vecs = np.array([d.embedding for d in filtered_docs])

        # Compute similarities
        similarities = self._cosine_similarity(query_vec, doc_vecs)

        # Get top-k results
        top_indices = np.argsort(similarities)[::-1][:top_k]

        results = []
        for idx in top_indices:
            score = float(similarities[idx])
            if score < threshold:
                continue

            doc = filtered_docs[idx]
            results.append({
                "doc_id": doc.doc_id,
                "text": doc.text,
                "score": score,
                "metadata": doc.metadata,
            })

        return results

    def save(self, path: Path) -> None:
        """Persist vector store to disk.

        Args:
            path: Path to save the vector store.
        """
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)

        data = {
            "embedding_model": self.embedding_model,
            "embedding_provider": self.embedding_provider,
            "chunk_size": self.chunk_size,
            "chunk_overlap": self.chunk_overlap,
            "documents": [
                {
                    "doc_id": d.doc_id,
                    "text": d.text,
                    "embedding": d.embedding,
                    "metadata": d.metadata,
                    "chunk_index": d.chunk_index,
                }
                for d in self.documents
            ],
            "embedding_cache": self._embedding_cache,
            "token_usage": self._token_usage,
        }

        with open(path, "wb") as f:
            pickle.dump(data, f)

    def load(self, path: Path) -> None:
        """Load vector store from disk.

        Args:
            path: Path to load the vector store from.
        """
        path = Path(path)

        with open(path, "rb") as f:
            data = pickle.load(f)

        self.embedding_model = data["embedding_model"]
        self.embedding_provider = data["embedding_provider"]
        self.chunk_size = data["chunk_size"]
        self.chunk_overlap = data["chunk_overlap"]
        self._embedding_cache = data.get("embedding_cache", {})
        self._token_usage = data.get("token_usage", {"total": 0, "cached": 0})

        self.documents = [
            Document(
                doc_id=d["doc_id"],
                text=d["text"],
                embedding=d["embedding"],
                metadata=d["metadata"],
                chunk_index=d["chunk_index"],
            )
            for d in data["documents"]
        ]

    def get_stats(self) -> Dict[str, Any]:
        """Get statistics about the vector store.

        Returns:
            Dictionary with store statistics.
        """
        return {
            "document_count": len(self.documents),
            "embedding_dimension": self.dimension,
            "embedding_model": self.embedding_model,
            "embedding_provider": self.embedding_provider,
            "chunk_size": self.chunk_size,
            "chunk_overlap": self.chunk_overlap,
            "cache_size": len(self._embedding_cache),
            "token_usage": self._token_usage,
        }

    def clear(self) -> None:
        """Clear all documents from the store."""
        self.documents = []
        self._embedding_cache = {}
        self._token_usage = {"total": 0, "cached": 0}
