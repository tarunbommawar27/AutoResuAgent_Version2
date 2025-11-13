"""
SentenceBERT Encoder
Handles text embedding using Sentence Transformers with lazy loading.
"""

import numpy as np
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from sentence_transformers import SentenceTransformer


class SentenceBertEncoder:
    """
    Wrapper for Sentence-BERT embeddings with lazy model loading.

    The model is only loaded when first needed (on first encode call),
    avoiding heavy imports and model loading at module import time.

    Uses 'all-MiniLM-L6-v2' by default:
    - 384 dimensions
    - Fast inference
    - Good quality for semantic search
    - ~80MB model size
    """

    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        """
        Initialize encoder (model not loaded yet).

        Args:
            model_name: HuggingFace model identifier
                       Common options:
                       - 'all-MiniLM-L6-v2' (384d, fast, default)
                       - 'all-mpnet-base-v2' (768d, higher quality)
                       - 'all-MiniLM-L12-v2' (384d, better quality)
        """
        self.model_name = model_name
        self._model: "SentenceTransformer | None" = None
        self._embedding_dim: int | None = None

    @property
    def model(self) -> "SentenceTransformer":
        """
        Lazy load the model on first access.

        Returns:
            Loaded SentenceTransformer model

        Note:
            First call will download model if not cached (~80MB for MiniLM)
        """
        if self._model is None:
            from sentence_transformers import SentenceTransformer

            self._model = SentenceTransformer(self.model_name)
            # Cache embedding dimension
            self._embedding_dim = self._model.get_sentence_embedding_dimension()

        return self._model

    def encode_texts(self, texts: list[str], batch_size: int = 32, show_progress: bool = False) -> np.ndarray:
        """
        Encode multiple texts into embeddings.

        Args:
            texts: List of text strings to encode
            batch_size: Batch size for encoding (default: 32)
            show_progress: Show progress bar (default: False)

        Returns:
            Numpy array of shape [n_texts, embedding_dim]

        Example:
            >>> encoder = SentenceBertEncoder()
            >>> texts = ["Python programming", "Machine learning"]
            >>> embeddings = encoder.encode_texts(texts)
            >>> embeddings.shape
            (2, 384)
        """
        if not texts:
            # Return empty array with correct shape
            return np.zeros((0, self.get_embedding_dimension()))

        # Lazy load model on first encode
        embeddings = self.model.encode(
            texts,
            batch_size=batch_size,
            show_progress_bar=show_progress,
            convert_to_numpy=True,
            normalize_embeddings=True,  # Important for cosine similarity
        )

        return np.array(embeddings, dtype=np.float32)

    def encode_single(self, text: str) -> np.ndarray:
        """
        Encode a single text into an embedding vector.

        Args:
            text: Text string to encode

        Returns:
            Numpy array of shape [embedding_dim]

        Example:
            >>> encoder = SentenceBertEncoder()
            >>> embedding = encoder.encode_single("Hello world")
            >>> embedding.shape
            (384,)
        """
        # Use encode_texts and extract first result
        embeddings = self.encode_texts([text])
        return embeddings[0]

    def get_embedding_dimension(self) -> int:
        """
        Get the embedding dimension of the model.

        Returns:
            Embedding dimension (e.g., 384 for MiniLM, 768 for MPNet)

        Note:
            This will load the model if not already loaded
        """
        if self._embedding_dim is None:
            # Trigger lazy loading to get dimension
            _ = self.model
        return self._embedding_dim

    def is_loaded(self) -> bool:
        """
        Check if model is already loaded in memory.

        Returns:
            True if model is loaded, False otherwise
        """
        return self._model is not None

    def __repr__(self) -> str:
        """String representation."""
        loaded = "loaded" if self.is_loaded() else "not loaded"
        return f"SentenceBertEncoder(model='{self.model_name}', {loaded})"
