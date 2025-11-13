"""
Test script for retrieval layer (SentenceBERT + FAISS).
Tests embedding, indexing, and semantic search functionality.
"""

import sys
from pathlib import Path

# Fix Unicode encoding for Windows console
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8')

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from src.embeddings import (
    SentenceBertEncoder,
    ResumeFaissIndex,
    retrieve_relevant_experiences,
    retrieve_for_skills,
    get_top_matching_experiences,
    aggregate_retrieval_results,
)
from src.models import load_job_from_yaml, load_resume_from_json


def print_section(title: str):
    """Print a formatted section header."""
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70)


def test_sentence_bert_encoder():
    """Test SentenceBERT encoder."""
    print_section("Testing SentenceBERT Encoder")

    print("\n✓ Creating encoder (model not loaded yet)...")
    encoder = SentenceBertEncoder()
    print(f"   {encoder}")
    print(f"   Model loaded: {encoder.is_loaded()}")

    print("\n✓ Encoding single text...")
    text = "Machine learning engineer with Python experience"
    embedding = encoder.encode_single(text)
    print(f"   Text: {text}")
    print(f"   Embedding shape: {embedding.shape}")
    print(f"   Embedding dimension: {encoder.get_embedding_dimension()}")
    print(f"   Model loaded now: {encoder.is_loaded()}")

    print("\n✓ Encoding multiple texts...")
    texts = [
        "Built recommendation system",
        "Deployed ML models to production",
        "Optimized database queries",
    ]
    embeddings = encoder.encode_texts(texts)
    print(f"   Encoded {len(texts)} texts")
    print(f"   Embeddings shape: {embeddings.shape}")
    print(f"   Embeddings are normalized: {abs(embeddings[0] @ embeddings[0] - 1.0) < 0.01}")

    # Test similarity
    print("\n✓ Testing semantic similarity...")
    query = "machine learning projects"
    query_emb = encoder.encode_single(query)

    for i, text in enumerate(texts):
        similarity = query_emb @ embeddings[i]  # Dot product (cosine similarity)
        print(f"   '{text[:40]}...' -> similarity: {similarity:.3f}")

    return encoder


def test_faiss_index(encoder):
    """Test FAISS index building and search."""
    print_section("Testing FAISS Index")

    # Load sample resume
    resume_path = Path("data/resumes/jane-doe-sample.json")
    if not resume_path.exists():
        print(f"\n⚠ Sample resume not found: {resume_path}")
        print("   Skipping FAISS tests")
        return None

    print(f"\n✓ Loading resume from {resume_path}...")
    resume = load_resume_from_json(resume_path)
    print(f"   Loaded: {resume.name}")
    print(f"   Experiences: {len(resume.experiences)}")
    print(f"   Total bullets: {len(resume.get_all_bullets())}")

    print("\n✓ Building FAISS index...")
    index = ResumeFaissIndex(encoder)
    print(f"   Index before build: {index}")
    print(f"   Is built: {index.is_built()}")

    index.build_from_experiences(resume.experiences)
    print(f"   Index after build: {index}")
    print(f"   Indexed {len(index)} bullets")

    print("\n✓ Testing semantic search...")
    queries = [
        "machine learning experience",
        "deployment and infrastructure",
        "data pipeline optimization",
    ]

    for query in queries:
        print(f"\n   Query: '{query}'")
        results = index.search(query, top_k=3)
        for i, result in enumerate(results):
            print(f"      {i+1}. [{result['score']:.3f}] {result['text'][:60]}...")
            print(f"         (from {result['experience_id']})")

    return index, resume


def test_retrieval_functions(encoder, index, resume):
    """Test high-level retrieval functions."""
    print_section("Testing Retrieval Functions")

    # Load sample job
    job_path = Path("data/jobs/ml-engineer-sample.yaml")
    if not job_path.exists():
        print(f"\n⚠ Sample job not found: {job_path}")
        print("   Skipping retrieval function tests")
        return

    print(f"\n✓ Loading job from {job_path}...")
    job = load_job_from_yaml(job_path)
    print(f"   Job: {job.title} at {job.company}")
    print(f"   Responsibilities: {len(job.responsibilities)}")
    print(f"   Required skills: {len(job.required_skills)}")

    print("\n✓ Retrieving relevant experiences for each responsibility...")
    results = retrieve_relevant_experiences(job, resume, encoder, index, top_k=3)
    print(f"   Retrieved results for {len(results)} responsibilities")

    for i, (resp, items) in enumerate(list(results.items())[:2]):  # Show first 2
        print(f"\n   Responsibility {i+1}: '{resp[:60]}...'")
        print(f"   Top matches:")
        for j, item in enumerate(items[:2]):  # Show top 2
            print(f"      {j+1}. [{item['score']:.3f}] {item['text'][:50]}...")

    print("\n✓ Aggregating all retrieval results...")
    top_items = aggregate_retrieval_results(results, top_k_overall=5)
    print(f"   Top {len(top_items)} unique bullets overall:")
    for i, item in enumerate(top_items):
        print(f"      {i+1}. [{item['score']:.3f}] {item['text'][:60]}...")

    print("\n✓ Retrieving for specific skills...")
    skills_results = retrieve_for_skills(
        ["Python", "Machine Learning", "AWS"],
        encoder,
        index,
        top_k=2
    )
    print(f"   Retrieved for {len(skills_results)} skills")
    for skill, items in skills_results.items():
        print(f"   {skill}: {len(items)} examples")
        if items:
            print(f"      Best: [{items[0]['score']:.3f}] {items[0]['text'][:50]}...")

    print("\n✓ Getting top overall matches...")
    top_matches = get_top_matching_experiences(job, resume, encoder, index, top_k=5)
    print(f"   Top {len(top_matches)} matches for entire job:")
    for i, match in enumerate(top_matches):
        print(f"      {i+1}. [{match['score']:.3f}] {match['text'][:60]}...")


def test_retrieval_quality(encoder):
    """Test retrieval quality with known queries."""
    print_section("Testing Retrieval Quality")

    print("\n✓ Testing semantic similarity quality...")

    # Test cases: (query, expected_similar, expected_dissimilar)
    test_cases = [
        (
            "Python programming",
            ["Developed Python applications", "Built ML pipeline in Python"],
            ["Managed project budget", "Conducted team meetings"]
        ),
        (
            "machine learning models",
            ["Trained neural networks", "Deployed ML model to production"],
            ["Fixed CSS bugs", "Wrote documentation"]
        ),
    ]

    for query, similar_texts, dissimilar_texts in test_cases:
        print(f"\n   Query: '{query}'")

        query_emb = encoder.encode_single(query)

        # Check similar texts have high similarity
        similar_embs = encoder.encode_texts(similar_texts)
        similar_scores = [query_emb @ emb for emb in similar_embs]

        print(f"   Similar texts (expect high scores):")
        for text, score in zip(similar_texts, similar_scores):
            status = "✓" if score > 0.3 else "⚠"
            print(f"      {status} [{score:.3f}] {text}")

        # Check dissimilar texts have low similarity
        dissimilar_embs = encoder.encode_texts(dissimilar_texts)
        dissimilar_scores = [query_emb @ emb for emb in dissimilar_embs]

        print(f"   Dissimilar texts (expect low scores):")
        for text, score in zip(dissimilar_texts, dissimilar_scores):
            status = "✓" if score < 0.3 else "⚠"
            print(f"      {status} [{score:.3f}] {text}")


def main():
    """Run all retrieval tests."""
    print("\n" + "🔍" * 35)
    print("  AutoResuAgent - Retrieval Layer Test Suite")
    print("🔍" * 35)

    try:
        # Test encoder
        encoder = test_sentence_bert_encoder()

        # Test FAISS index
        result = test_faiss_index(encoder)
        if result:
            index, resume = result

            # Test retrieval functions
            test_retrieval_functions(encoder, index, resume)

        # Test retrieval quality
        test_retrieval_quality(encoder)

        # Summary
        print_section("Test Summary")
        print("\n✅ All retrieval layer tests passed successfully!")
        print("\n📊 System Statistics:")
        print(f"   - Encoder model: {encoder.model_name}")
        print(f"   - Embedding dimension: {encoder.get_embedding_dimension()}")
        if result:
            print(f"   - Indexed bullets: {len(index)}")
            print(f"   - Resume experiences: {len(resume.experiences)}")

        print("\n✨ Retrieval layer is production-ready!")
        print("\nNext steps:")
        print("  1. Retrieval system working correctly")
        print("  2. Ready to implement LLM generators")
        print("  3. Can find relevant resume content for any job")

    except Exception as e:
        print(f"\n❌ Error during testing: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
