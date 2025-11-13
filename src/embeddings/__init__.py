"""
Embeddings Package
Handles text encoding and vector search with SentenceBERT and FAISS.
"""

from .sentence_bert import SentenceBertEncoder
from .faiss_index import ResumeFaissIndex
from .retriever import (
    retrieve_relevant_experiences,
    retrieve_for_skills,
    get_top_matching_experiences,
    deduplicate_retrieved_items,
    aggregate_retrieval_results,
)

__all__ = [
    # Core classes
    "SentenceBertEncoder",
    "ResumeFaissIndex",
    # Retrieval functions
    "retrieve_relevant_experiences",
    "retrieve_for_skills",
    "get_top_matching_experiences",
    "deduplicate_retrieved_items",
    "aggregate_retrieval_results",
]
