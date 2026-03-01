#!/usr/bin/env python3
"""
NyayaSetu AI - Single Query RAG Pipeline
Quick test script for single queries with Bedrock integration
"""

import json
import sys
import numpy as np
from pathlib import Path
from sentence_transformers import SentenceTransformer
from bedrock_generator import BedrockAnswerGenerator


def load_knowledge_base(kb_path=None):
    """Load the knowledge base"""
    if kb_path is None:
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
    query_embedding = model.encode([query])[0]
    
    results = []
    for chunk in kb:
        if 'embedding' in chunk:
            similarity = cosine_similarity(query_embedding, chunk['embedding'])
            results.append({
                'similarity': similarity,
                'text': chunk['text'],
                'metadata': chunk['metadata']
            })
    
    results.sort(key=lambda x: x['similarity'], reverse=True)
    return results[:top_k]


def main():
    """Single query RAG pipeline"""
    # Get query from command line or use default
    if len(sys.argv) > 1:
        query = ' '.join(sys.argv[1:])
    else:
        query = "What is the definition of consumer?"
    
    print("=" * 70)
    print("NyayaSetu AI - RAG Pipeline (Single Query)")
    print("=" * 70)
    print(f"\nQuery: {query}")
    print("=" * 70)
    
    # Load resources
    print("\n[1/4] Loading embedding model...")
    model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')
    print("✓ Loaded")
    
    print("\n[2/4] Loading knowledge base...")
    kb = load_knowledge_base()
    print(f"✓ Loaded {len(kb)} chunks")
    
    print("\n[3/4] Retrieving relevant context...")
    results = search_knowledge_base(query, kb, model, top_k=3)
    print(f"✓ Retrieved top-3 chunks")
    print(f"   Similarities: {', '.join([f'{r['similarity']:.4f}' for r in results])}")
    
    print("\n[4/4] Generating answer with Bedrock (Claude 3 Haiku)...")
    try:
        generator = BedrockAnswerGenerator(region_name="ap-south-1")
        
        response = generator.generate_answer(
            user_query=query,
            retrieved_chunks=results
            # Uses class defaults: max_tokens=600, temperature=0.1
        )
        
        print("\n" + "=" * 70)
        print("ANSWER:")
        print("=" * 70)
        print(response['answer'])
        
        print("\n" + "=" * 70)
        print("METADATA:")
        print("=" * 70)
        print(f"Token Usage: {response['usage'].get('total_tokens', 0)} tokens")
        print(f"  - Input:  {response['usage'].get('input_tokens', 0)}")
        print(f"  - Output: {response['usage'].get('output_tokens', 0)}")
        print("=" * 70)
        
    except Exception as e:
        print(f"\n✗ Error: {e}")
        print("\nRetrieved Context (Fallback):")
        for i, result in enumerate(results, 1):
            print(f"\n[{i}] {result['metadata']['section']} - {result['metadata']['chapter']}")
            print(f"    Similarity: {result['similarity']:.4f}")
            print(f"    {result['text'][:150]}...")


if __name__ == "__main__":
    main()
