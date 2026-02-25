#!/usr/bin/env python3
"""
Test script to demonstrate RAG knowledge base querying
"""

import json
import numpy as np
from pathlib import Path
from sentence_transformers import SentenceTransformer

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
    """Test RAG query functionality"""
    print("=" * 70)
    print("NyayaSetu AI - RAG Knowledge Base Query Test")
    print("=" * 70)
    
    # Load model
    print("\nLoading embedding model...")
    model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')
    print("✓ Model loaded")
    
    # Load knowledge base
    print("\nLoading knowledge base...")
    kb = load_knowledge_base()
    print(f"✓ Loaded {len(kb)} chunks")
    
    # Test queries
    test_queries = [
        "What are consumer rights?",
        "How to file a complaint?",
        "What is the definition of consumer?",
        "What are unfair trade practices?",
        "Who can file a consumer complaint?"
    ]
    
    print("\n" + "=" * 70)
    print("TEST QUERIES")
    print("=" * 70)
    
    for query in test_queries:
        print(f"\n📝 Query: {query}")
        print("-" * 70)
        
        results = search_knowledge_base(query, kb, model, top_k=3)
        
        for i, result in enumerate(results, 1):
            print(f"\n[Result {i}] Similarity: {result['similarity']:.4f}")
            print(f"Section: {result['metadata']['section']}")
            print(f"Chapter: {result['metadata']['chapter']}")
            print(f"Text preview: {result['text'][:200]}...")
            print()
    
    print("=" * 70)
    print("✓ Query test complete")
    print("=" * 70)

if __name__ == "__main__":
    main()
