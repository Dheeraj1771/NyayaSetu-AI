#!/usr/bin/env python3
"""
NyayaSetu AI - Complete RAG Pipeline with Bedrock Integration
Retrieval + Generation using Amazon Bedrock (Claude 3 Haiku)
"""

import json
import numpy as np
from pathlib import Path
from sentence_transformers import SentenceTransformer
from bedrock_generator import BedrockAnswerGenerator

def load_knowledge_base(kb_path=None):
    """Load the knowledge base"""
    if kb_path is None:
        # Get project root (two levels up from this script)
        script_dir = Path(__file__).parent
        project_root = script_dir.parent.parent
        kb_path = project_root / "knowledge_base" / "knowledge_base.json"
    
    with open(kb_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def cosine_similarity(vec1, vec2):
    """Calculate cosine similarity between two vectors"""
    vec1 = np.array(vec1)
    vec2 = np.array(vec2)
    return np.dot(vec1, vec2) / (np.linalg.norm(vec1) * np.linalg.norm(vec2))

def search_knowledge_base(query, kb, model, top_k=3):
    """Search knowledge base using semantic similarity"""
    # Generate query embedding
    query_embedding = model.encode([query])[0]
    
    # Calculate similarities
    results = []
    for chunk in kb:
        if 'embedding' in chunk:
            similarity = cosine_similarity(query_embedding, chunk['embedding'])
            results.append({
                'similarity': similarity,
                'text': chunk['text'],
                'metadata': chunk['metadata']
            })
    
    # Sort by similarity
    results.sort(key=lambda x: x['similarity'], reverse=True)
    
    return results[:top_k]

def main():
    """Complete RAG pipeline with Bedrock answer generation"""
    print("=" * 70)
    print("NyayaSetu AI - Complete RAG Pipeline (Retrieval + Generation)")
    print("=" * 70)
    
    # Load embedding model
    print("\n[1/5] Loading embedding model...")
    model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')
    print("✓ Model loaded")
    
    # Load knowledge base
    print("\n[2/5] Loading knowledge base...")
    kb = load_knowledge_base()
    print(f"✓ Loaded {len(kb)} chunks")
    
    # Initialize Bedrock generator
    print("\n[3/5] Initializing Bedrock (Claude 3 Haiku)...")
    try:
        generator = BedrockAnswerGenerator(region_name="ap-south-1")
        bedrock_available = True
    except Exception as e:
        print(f"⚠ Bedrock initialization failed: {e}")
        print("⚠ Falling back to retrieval-only mode")
        bedrock_available = False
    
    # Test queries
    test_queries = [
        "What are consumer rights?",
        "How to file a complaint?",
        "What is the definition of consumer?",
        "What are unfair trade practices?",
        "Who can file a consumer complaint?"
    ]
    
    print("\n" + "=" * 70)
    print("RUNNING RAG PIPELINE")
    print("=" * 70)
    
    for query_num, query in enumerate(test_queries, 1):
        print(f"\n{'=' * 70}")
        print(f"Query {query_num}/{len(test_queries)}: {query}")
        print("=" * 70)
        
        # Step 1: Retrieve top-3 chunks
        print("\n[4/5] Retrieving relevant context...")
        results = search_knowledge_base(query, kb, model, top_k=3)
        print(f"✓ Retrieved top-3 chunks (similarities: {[f'{r['similarity']:.4f}' for r in results]})")
        
        if bedrock_available:
            # Step 2: Generate answer using Bedrock
            print("\n[5/5] Generating answer with Bedrock...")
            try:
                response = generator.generate_answer(
                    user_query=query,
                    retrieved_chunks=results
                    # Uses class defaults: max_tokens=600, temperature=0.1
                )
                
                # Display generated answer
                print("\n" + "─" * 70)
                print("GENERATED ANSWER:")
                print("─" * 70)
                print(response['answer'])
                print("\n" + "─" * 70)
                print("TOKEN USAGE:")
                print(f"  Input:  {response['usage'].get('input_tokens', 0)} tokens")
                print(f"  Output: {response['usage'].get('output_tokens', 0)} tokens")
                print(f"  Total:  {response['usage'].get('total_tokens', 0)} tokens")
                print("─" * 70)
                
            except Exception as e:
                print(f"✗ Error generating answer: {e}")
                print("\nFalling back to raw retrieval results:")
                display_retrieval_results(results)
        else:
            # Fallback: Display raw retrieval results
            print("\n[RETRIEVAL-ONLY MODE]")
            display_retrieval_results(results)
    
    print("\n" + "=" * 70)
    print("✓ RAG Pipeline Complete")
    print("=" * 70)


def display_retrieval_results(results):
    """Display raw retrieval results (fallback mode)"""
    print("\nRetrieved Chunks:")
    for i, result in enumerate(results, 1):
        print(f"\n[Chunk {i}] Similarity: {result['similarity']:.4f}")
        print(f"Chapter: {result['metadata']['chapter']}")
        print(f"Section: {result['metadata']['section']}")
        print(f"Text: {result['text'][:200]}...")
        print()

if __name__ == "__main__":
    main()
