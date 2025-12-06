"""
Retrieval Helper Functions
High-level functions for retrieving relevant resume content for job applications.
"""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..models import JobDescription, CandidateProfile

from .sentence_bert import SentenceBertEncoder
from .faiss_index import ResumeFaissIndex


def retrieve_relevant_experiences(
    job: "JobDescription",
    resume: "CandidateProfile",
    encoder: SentenceBertEncoder,
    index: ResumeFaissIndex,
    top_k: int = 10
) -> dict[str, list[dict]]:
    """
    Retrieve relevant resume experiences for each job responsibility.

    For each responsibility in the job description, searches the FAISS index
    to find the most relevant resume bullets. This provides context for
    tailoring resume content to match job requirements.

    Args:
        job: Target job description
        resume: Candidate's resume profile
        encoder: SentenceBERT encoder instance
        index: Built FAISS index of resume bullets
        top_k: Number of relevant bullets to retrieve per responsibility
               (default: 10, increased from 5 for better skill coverage)

    Returns:
        Dictionary mapping each responsibility text to list of retrieved items:
        {
            "Design ML pipelines": [
                {"experience_id": "exp-001", "text": "...", "score": 0.85},
                ...
            ],
            ...
        }

    Example:
        >>> encoder = SentenceBertEncoder()
        >>> index = ResumeFaissIndex(encoder)
        >>> index.build_from_experiences(resume.experiences)
        >>> results = retrieve_relevant_experiences(job, resume, encoder, index)
        >>> for resp, items in results.items():
        ...     print(f"{resp[:50]}... -> {len(items)} relevant bullets")
    """
    if not index.is_built():
        raise RuntimeError(
            "FAISS index must be built before retrieval. "
            "Call index.build_from_experiences(resume.experiences) first."
        )

    if not job.responsibilities:
        raise ValueError("Job has no responsibilities to search for")

    results = {}

    for responsibility in job.responsibilities:
        # Search for relevant bullets
        retrieved_items = index.search(responsibility, top_k=top_k)
        results[responsibility] = retrieved_items

    return results


def retrieve_for_skills(
    skills: list[str],
    encoder: SentenceBertEncoder,
    index: ResumeFaissIndex,
    top_k: int = 3
) -> dict[str, list[dict]]:
    """
    Retrieve relevant resume bullets for a list of skills.

    Useful for finding evidence of specific skills in resume history.

    Args:
        skills: List of skills to search for (e.g., ["Python", "AWS"])
        encoder: SentenceBERT encoder instance
        index: Built FAISS index of resume bullets
        top_k: Number of relevant bullets per skill

    Returns:
        Dictionary mapping each skill to list of relevant bullets

    Example:
        >>> results = retrieve_for_skills(
        ...     ["Python", "Machine Learning", "AWS"],
        ...     encoder,
        ...     index
        ... )
        >>> for skill, bullets in results.items():
        ...     print(f"{skill}: {len(bullets)} examples found")
    """
    if not index.is_built():
        raise RuntimeError("FAISS index must be built before retrieval")

    results = {}

    for skill in skills:
        # Create a query that emphasizes experience with the skill
        query = f"experience with {skill}"
        retrieved_items = index.search(query, top_k=top_k)
        results[skill] = retrieved_items

    return results


def get_top_matching_experiences(
    job: "JobDescription",
    resume: "CandidateProfile",
    encoder: SentenceBertEncoder,
    index: ResumeFaissIndex,
    top_k: int = 10
) -> list[dict]:
    """
    Get overall top-k matching bullets for the entire job.

    Searches using the full job search text (title + responsibilities + skills)
    to find the most relevant resume bullets overall.

    Args:
        job: Target job description
        resume: Candidate's resume profile
        encoder: SentenceBERT encoder instance
        index: Built FAISS index of resume bullets
        top_k: Total number of relevant bullets to retrieve

    Returns:
        List of retrieved items sorted by relevance score (descending)

    Example:
        >>> top_matches = get_top_matching_experiences(job, resume, encoder, index)
        >>> for match in top_matches[:3]:
        ...     print(f"[{match['score']:.3f}] {match['text'][:60]}...")
    """
    if not index.is_built():
        raise RuntimeError("FAISS index must be built before retrieval")

    # Use job's search text as query
    query = job.get_search_text()

    # Search for top matches
    results = index.search(query, top_k=top_k)

    return results


def deduplicate_retrieved_items(items: list[dict]) -> list[dict]:
    """
    Remove duplicate retrieved items based on text.

    Keeps the item with the highest score for each unique text.

    Args:
        items: List of retrieved items with 'text' and 'score' keys

    Returns:
        Deduplicated list of items
    """
    seen_texts = {}

    for item in items:
        text = item["text"]
        if text not in seen_texts or item["score"] > seen_texts[text]["score"]:
            seen_texts[text] = item

    # Return sorted by score (descending)
    return sorted(seen_texts.values(), key=lambda x: x["score"], reverse=True)


def aggregate_retrieval_results(
    responsibility_results: dict[str, list[dict]],
    top_k_overall: int = 10
) -> list[dict]:
    """
    Aggregate retrieval results from multiple responsibilities.

    Combines all retrieved items, deduplicates, and returns top-k overall.

    Args:
        responsibility_results: Results from retrieve_relevant_experiences()
        top_k_overall: Number of top items to return after aggregation

    Returns:
        Deduplicated list of top-k items sorted by score

    Example:
        >>> results = retrieve_relevant_experiences(job, resume, encoder, index)
        >>> top_items = aggregate_retrieval_results(results, top_k_overall=10)
        >>> print(f"Found {len(top_items)} unique relevant bullets")
    """
    # Collect all items
    all_items = []
    for items in responsibility_results.values():
        all_items.extend(items)

    # Deduplicate
    unique_items = deduplicate_retrieved_items(all_items)

    # Return top-k
    return unique_items[:top_k_overall]
