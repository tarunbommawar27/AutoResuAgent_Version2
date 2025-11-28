"""
FAISS Vector Store
Handles indexing and similarity search for resume experiences using FAISS.
"""

import numpy as np
from typing import TYPE_CHECKING

# Import Experience and Project for type hints
if TYPE_CHECKING:
    import faiss
    from ..models import Experience, Project

from .sentence_bert import SentenceBertEncoder


class ResumeFaissIndex:
    """
    FAISS-based vector store for resume experience semantic search.

    Uses IndexFlatIP (inner product) for cosine similarity search.
    Stores embeddings of resume bullets with metadata for retrieval.

    Example:
        >>> encoder = SentenceBertEncoder()
        >>> index = ResumeFaissIndex(encoder)
        >>> index.build_from_experiences(resume.experiences)
        >>> results = index.search("machine learning experience", top_k=3)
    """

    def __init__(self, encoder: SentenceBertEncoder):
        """
        Initialize FAISS index with encoder.

        Args:
            encoder: SentenceBertEncoder instance for embedding text

        Note:
            Index is not built until build_from_experiences() is called
        """
        self.encoder = encoder
        self._index: "faiss.IndexFlatIP | None" = None
        self.embeddings: np.ndarray | None = None
        self.metadata: list[dict] = []  # {"experience_id": str, "text": str}

    @property
    def index(self) -> "faiss.IndexFlatIP":
        """
        Get the FAISS index, creating it if needed.

        Returns:
            FAISS IndexFlatIP instance

        Raises:
            RuntimeError: If index not built yet
        """
        if self._index is None:
            raise RuntimeError(
                "Index not built. Call build_from_experiences() first."
            )
        return self._index

    def build_from_experiences(
        self,
        experiences: list["Experience"],
        projects: list["Project"] | None = None
    ) -> None:
        """
        Build FAISS index from resume experiences and optionally projects.

        Each bullet point from each experience/project becomes a searchable item.
        Stores source_id, source_type, and bullet text as metadata for retrieval.

        Args:
            experiences: List of Experience objects from resume
            projects: Optional list of Project objects from resume

        Example:
            >>> from src.models import load_resume_from_json
            >>> resume = load_resume_from_json(Path("data/resumes/jane-doe.json"))
            >>> index.build_from_experiences(resume.experiences, resume.projects)
            >>> print(f"Indexed {len(index)} bullets")
        """
        import faiss

        # Extract all bullets with their source IDs and types
        all_texts = []
        all_metadata = []

        # Add experience bullets
        for exp in experiences:
            for bullet in exp.bullets:
                all_texts.append(bullet)
                all_metadata.append({
                    "experience_id": exp.id,  # Keep for backwards compatibility
                    "source_id": exp.id,
                    "source_type": "experience",
                    "text": bullet,
                })

        # Add project bullets if provided
        if projects:
            for proj in projects:
                for bullet in proj.bullets:
                    all_texts.append(bullet)
                    all_metadata.append({
                        "experience_id": proj.id,  # Keep for backwards compatibility
                        "source_id": proj.id,
                        "source_type": "project",
                        "text": bullet,
                    })

        if not all_texts:
            raise ValueError("No bullets found in experiences or projects. Cannot build index.")

        # Generate embeddings
        print(f"Encoding {len(all_texts)} bullets...")
        embeddings = self.encoder.encode_texts(all_texts, show_progress=True)

        # Create FAISS index (IndexFlatIP for cosine similarity with normalized vectors)
        dimension = embeddings.shape[1]
        self._index = faiss.IndexFlatIP(dimension)

        # Add embeddings to index
        self._index.add(embeddings)

        # Store embeddings and metadata
        self.embeddings = embeddings
        self.metadata = all_metadata

        print(f"Built FAISS index with {len(self)} items")

    def search(self, query: str, top_k: int = 5) -> list[dict]:
        """
        Search for top-k most similar resume bullets.

        Args:
            query: Query text (e.g., job responsibility or skill)
            top_k: Number of results to return

        Returns:
            List of dictionaries with keys:
            - experience_id: str
            - text: str (the bullet text)
            - score: float (cosine similarity, higher is better)

        Example:
            >>> results = index.search("machine learning projects", top_k=3)
            >>> for r in results:
            ...     print(f"[{r['score']:.3f}] {r['text'][:60]}...")
        """
        # Encode query
        query_embedding = self.encoder.encode_single(query)

        # Reshape for FAISS (expects 2D array)
        query_embedding = query_embedding.reshape(1, -1)

        # Search index
        scores, indices = self.index.search(query_embedding, top_k)

        # Build results with metadata
        results = []
        for score, idx in zip(scores[0], indices[0]):
            if idx == -1:  # FAISS returns -1 for empty slots
                continue

            meta = self.metadata[idx]
            results.append({
                "experience_id": meta["experience_id"],  # Backwards compatible
                "source_id": meta.get("source_id", meta["experience_id"]),
                "source_type": meta.get("source_type", "experience"),
                "text": meta["text"],
                "score": float(score),
            })

        return results

    def get_all_bullets_for_experience(self, experience_id: str) -> list[str]:
        """
        Get all bullets for a specific experience ID.

        Args:
            experience_id: Experience ID to find

        Returns:
            List of bullet texts for that experience
        """
        return [
            item["text"]
            for item in self.metadata
            if item["experience_id"] == experience_id
        ]

    def is_built(self) -> bool:
        """Check if index has been built."""
        return self._index is not None

    def __len__(self) -> int:
        """Return number of vectors in index."""
        return len(self.metadata)

    def __repr__(self) -> str:
        """String representation."""
        if self.is_built():
            return f"ResumeFaissIndex({len(self)} bullets indexed)"
        return "ResumeFaissIndex(not built)"
