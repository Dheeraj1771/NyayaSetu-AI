#!/usr/bin/env python3
"""
NyayaSetu AI - FastAPI Backend
Production-grade API for RAG-powered legal assistance
"""

import json
import time
import numpy as np
from pathlib import Path
from typing import List, Dict, Optional
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from sentence_transformers import SentenceTransformer

# Import RAG components
import sys
sys.path.append(str(Path(__file__).parent.parent / "rag"))
from bedrock_generator import BedrockAnswerGenerator
from retrieval_engine import LegalRetrievalEngine


# Global state (loaded once at startup)
class AppState:
    embedding_model: Optional[SentenceTransformer] = None
    knowledge_base: Optional[List[Dict]] = None
    bedrock_generator: Optional[BedrockAnswerGenerator] = None
    retrieval_engine: Optional[LegalRetrievalEngine] = None
    bedrock_available: bool = False


app_state = AppState()


# Pydantic Models
class QuestionRequest(BaseModel):
    question: str = Field(..., min_length=3, max_length=500, description="User's legal question")


class Source(BaseModel):
    act: str
    chapter: str
    section: str
    similarity: float


class AnswerResponse(BaseModel):
    answer: str
    sources: List[Source]
    confidence: str
    processing_time_ms: int


# Lifespan context manager for startup/shutdown
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Load resources once at startup"""
    print("=" * 70)
    print("NyayaSetu AI - Starting API Server")
    print("=" * 70)
    
    # Load embedding model
    print("\n[1/3] Loading embedding model...")
    try:
        app_state.embedding_model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')
        print("✓ Embedding model loaded")
    except Exception as e:
        print(f"✗ Failed to load embedding model: {e}")
        raise
    
    # Load knowledge base
    print("\n[2/3] Loading knowledge base...")
    try:
        kb_path = Path(__file__).parent.parent.parent / "knowledge_base" / "knowledge_base.json"
        with open(kb_path, 'r', encoding='utf-8') as f:
            app_state.knowledge_base = json.load(f)
        print(f"✓ Knowledge base loaded ({len(app_state.knowledge_base)} chunks)")
        
        # Initialize enhanced retrieval engine
        app_state.retrieval_engine = LegalRetrievalEngine(
            app_state.embedding_model,
            app_state.knowledge_base
        )
        print("✓ Enhanced retrieval engine initialized")
    except Exception as e:
        print(f"✗ Failed to load knowledge base: {e}")
        raise
    
    # Initialize Bedrock generator
    print("\n[3/3] Initializing Bedrock...")
    try:
        app_state.bedrock_generator = BedrockAnswerGenerator(region_name="ap-south-1")
        app_state.bedrock_available = True
        print("✓ Bedrock initialized")
    except Exception as e:
        print(f"⚠ Bedrock initialization failed: {e}")
        print("⚠ API will run in retrieval-only mode")
        app_state.bedrock_available = False
    
    print("\n" + "=" * 70)
    print("✓ API Server Ready")
    print("=" * 70)
    
    yield
    
    # Cleanup (if needed)
    print("\nShutting down API server...")


# Initialize FastAPI app
app = FastAPI(
    title="NyayaSetu AI API",
    description="RAG-powered legal assistance for Consumer Protection Act, 2019",
    version="1.0.0",
    lifespan=lifespan
)


# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Helper functions
def cosine_similarity(vec1: np.ndarray, vec2: np.ndarray) -> float:
    """Calculate cosine similarity between two vectors"""
    return np.dot(vec1, vec2) / (np.linalg.norm(vec1) * np.linalg.norm(vec2))


def search_knowledge_base(query: str, top_k: int = None) -> List[Dict]:
    """Search knowledge base using enhanced hybrid retrieval with dynamic top_k"""
    if not app_state.retrieval_engine:
        raise HTTPException(status_code=500, detail="Retrieval engine not initialized")
    
    return app_state.retrieval_engine.search(query, top_k=top_k)


def calculate_confidence(similarities: List[float], query_type: Dict = None) -> str:
    """Calculate confidence level with scenario-specific calibration"""
    if not app_state.retrieval_engine:
        return "Low"
    
    # Check if this is a scenario query
    is_scenario = query_type and query_type.get('is_scenario', False) if query_type else False
    
    if is_scenario:
        # Scenario-specific confidence calibration
        if not similarities:
            return "Low"
        
        top_score = similarities[0]
        supporting_scores = [s for s in similarities[1:3] if s >= 0.75] if len(similarities) > 1 else []
        
        # More lenient thresholds for scenarios (complex multi-section queries)
        if top_score >= 0.80 and len(supporting_scores) >= 2:
            return "High"
        elif top_score >= 0.72:
            return "Medium"
        else:
            return "Low"
    else:
        # Standard confidence calculation for definitions and procedural queries
        return app_state.retrieval_engine.calculate_confidence(similarities)


# API Endpoints
@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "service": "NyayaSetu AI",
        "status": "operational",
        "bedrock_available": app_state.bedrock_available,
        "knowledge_base_chunks": len(app_state.knowledge_base) if app_state.knowledge_base else 0
    }


@app.post("/ask", response_model=AnswerResponse)
async def ask_question(request: QuestionRequest):
    """
    Process legal question and return RAG-generated answer
    
    - Retrieves top-3 relevant chunks from knowledge base
    - Generates answer using Bedrock Claude 3 Haiku
    - Returns structured response with sources and confidence
    """
    start_time = time.time()
    
    try:
        # Step 1: Retrieve relevant context (dynamic top_k based on query type)
        retrieved_chunks = search_knowledge_base(request.question)
        
        if not retrieved_chunks:
            raise HTTPException(status_code=404, detail="No relevant information found")
        
        # Extract query type from first chunk's score breakdown
        query_type = None
        if retrieved_chunks and 'score_breakdown' in retrieved_chunks[0]:
            query_type = retrieved_chunks[0]['score_breakdown'].get('query_type')
        
        # Calculate confidence with improved calibration for scenarios
        similarities = [chunk['similarity'] for chunk in retrieved_chunks]
        confidence = calculate_confidence(similarities, query_type)
        
        # Step 2: Generate answer using Bedrock (if available)
        if app_state.bedrock_available and app_state.bedrock_generator:
            try:
                response = app_state.bedrock_generator.generate_answer(
                    user_query=request.question,
                    retrieved_chunks=retrieved_chunks,
                    query_type=query_type
                    # Uses defaults: max_tokens=600, temperature=0.1
                )
                
                answer_text = response['answer']
                
            except Exception as e:
                # Fallback to retrieval-only mode
                print(f"Bedrock generation failed: {e}")
                answer_text = _format_retrieval_fallback(retrieved_chunks)
        else:
            # Retrieval-only mode
            answer_text = _format_retrieval_fallback(retrieved_chunks)
        
        # Step 3: Format sources
        sources = [
            Source(
                act=chunk['metadata'].get('act', 'N/A'),
                chapter=chunk['metadata'].get('chapter', 'N/A'),
                section=chunk['metadata'].get('section', 'N/A'),
                similarity=chunk['similarity']
            )
            for chunk in retrieved_chunks
        ]
        
        # Calculate processing time
        processing_time = int((time.time() - start_time) * 1000)
        
        return AnswerResponse(
            answer=answer_text,
            sources=sources,
            confidence=confidence,
            processing_time_ms=processing_time
        )
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error processing question: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


def _format_retrieval_fallback(chunks: List[Dict]) -> str:
    """Format answer from retrieved chunks (fallback mode)"""
    if not chunks:
        return "I couldn't find relevant information to answer your question."
    
    # Use the highest similarity chunk
    top_chunk = chunks[0]
    
    answer = f"""Based on the Consumer Protection Act, 2019:

{top_chunk['text'][:500]}...

Source: {top_chunk['metadata'].get('section', 'N/A')} - {top_chunk['metadata'].get('chapter', 'N/A')}

Note: This is a direct excerpt from the Act. For a more detailed explanation, please ensure Bedrock is configured."""
    
    return answer


# Run with: uvicorn src.api.main:app --reload
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
