#!/usr/bin/env python3
"""
Enhanced Retrieval Engine for Legal RAG
Implements multi-layered hybrid ranking for definitions, procedures, and scenarios
"""

import re
import numpy as np
from typing import List, Dict, Tuple, Set


class LegalRetrievalEngine:
    """
    Enhanced retrieval engine with multi-layered hybrid ranking
    Handles definitions, procedural queries, enforcement, and scenarios
    """
    
    # Definition query patterns
    DEFINITION_PATTERNS = [
        r'\bwho\s+is\b',
        r'\bwhat\s+is\b',
        r'\bwhat\s+are\b',
        r'\bdefine\b',
        r'\bdefinition\s+of\b',
        r'\bmeaning\s+of\b',
        r'\bunder\s+the\s+act\b',
        r'\bconsidered\s+(a|an)\b',
        r'\bmeans\s+what\b'
    ]
    
    # Procedural/Jurisdiction query patterns
    PROCEDURAL_PATTERNS = [
        r'\bjurisdiction\b',
        r'\bpecuniary\b',
        r'\bdistrict\s+commission\b',
        r'\bstate\s+commission\b',
        r'\bnational\s+commission\b',
        r'\blimitation\b',
        r'\byears?\b.*\bfile\b',
        r'\bfile\s+complaint\b',
        r'\bresides?\b',
        r'\bterritorial\b',
        r'\bappeal\b',
        r'\bpenalty\b',
        r'\bimpose\s+fine\b',
        r'\bpowers?\b',
        r'\bauthority\b',
        r'\bwhere\s+to\s+file\b',
        r'\bwhich\s+commission\b',
        r'\bhow\s+long\b',
        r'\btime\s+limit\b'
    ]
    
    # Scenario query indicators
    SCENARIO_INDICATORS = [
        r'\bi\s+(purchased|bought|hired|availed)\b',
        r'\bmy\s+(product|service|purchase)\b',
        r'\brefusing\b',
        r'\bdefective\b',
        r'\bnegligence\b',
        r'\brefund\b',
        r'\binjury\b',
        r'\bhospital\b',
        r'\bmanufacturer\b',
        r'\be-commerce\b',
        r'\bseller\b',
        r'\bremedy\b',
        r'\bcompensation\b',
        r'\bliability\b'
    ]
    
    # Legal structure markers for definitions
    DEFINITION_MARKERS = [
        '"means"',
        '"includes"',
        'means any',
        'means a',
        'means the',
        'includes any'
    ]
    
    # Procedural/Enforcement markers
    PROCEDURAL_MARKERS = [
        'shall have jurisdiction',
        'may impose',
        'penalty',
        'appeal',
        'complaint may be filed',
        'limitation period',
        'within',
        'years from',
        'pecuniary jurisdiction',
        'territorial jurisdiction',
        'powers',
        'authority to'
    ]
    
    def __init__(self, embedding_model, knowledge_base: List[Dict]):
        """
        Initialize retrieval engine
        
        Args:
            embedding_model: Sentence transformer model
            knowledge_base: List of chunks with embeddings and metadata
        """
        self.embedding_model = embedding_model
        self.knowledge_base = knowledge_base
    
    def is_definition_query(self, query: str) -> bool:
        """Detect if query is asking for a definition"""
        query_lower = query.lower()
        return any(re.search(pattern, query_lower) for pattern in self.DEFINITION_PATTERNS)
    
    def is_procedural_query(self, query: str) -> bool:
        """Detect if query is about procedures, jurisdiction, or enforcement"""
        query_lower = query.lower()
        return any(re.search(pattern, query_lower) for pattern in self.PROCEDURAL_PATTERNS)
    
    def is_scenario_query(self, query: str) -> bool:
        """Detect if query is a real-world scenario"""
        query_lower = query.lower()
        return any(re.search(pattern, query_lower) for pattern in self.SCENARIO_INDICATORS)
    
    def has_definition_markers(self, text: str) -> bool:
        """Check if text contains legal definition markers"""
        text_lower = text.lower()
        return any(marker.lower() in text_lower for marker in self.DEFINITION_MARKERS)
    
    def has_procedural_markers(self, text: str) -> bool:
        """Check if text contains procedural/enforcement markers"""
        text_lower = text.lower()
        return any(marker.lower() in text_lower for marker in self.PROCEDURAL_MARKERS)
    
    def is_chapter_one_definition(self, metadata: Dict) -> bool:
        """Check if chunk is from Chapter I (Definitions/Preliminary)"""
        chapter = metadata.get('chapter', '').lower()
        return 'chapter i' in chapter or 'preliminary' in chapter
    
    def is_chapter_three_ccpa(self, metadata: Dict) -> bool:
        """Check if chunk is from Chapter III (CCPA)"""
        chapter = metadata.get('chapter', '').lower()
        return 'chapter iii' in chapter or 'central consumer protection authority' in chapter
    
    def is_chapter_four_commissions(self, metadata: Dict) -> bool:
        """Check if chunk is from Chapter IV (Commissions)"""
        chapter = metadata.get('chapter', '').lower()
        return 'chapter iv' in chapter or 'consumer disputes redressal' in chapter
    
    def is_chapter_six_liability(self, metadata: Dict) -> bool:
        """Check if chunk is from Chapter VI (Product Liability)"""
        chapter = metadata.get('chapter', '').lower()
        return 'chapter vi' in chapter or 'product liability' in chapter
    
    def is_section_one(self, metadata: Dict) -> bool:
        """Check if chunk is from Section 1 (main definitions section)"""
        section = metadata.get('section', '').lower()
        return section.startswith('section 1')
    
    def calculate_keyword_relevance(self, query: str, text: str) -> float:
        """Calculate keyword overlap between query and text"""
        stop_words = {'is', 'a', 'an', 'the', 'what', 'who', 'under', 'act', 'means', 'of', 'in', 'to', 'for', 'can', 'i'}
        
        query_words = set(re.findall(r'\b\w+\b', query.lower())) - stop_words
        text_words = set(re.findall(r'\b\w+\b', text.lower()))
        
        if not query_words:
            return 0.0
        
        overlap = len(query_words & text_words)
        return overlap / len(query_words)
    
    def calculate_hybrid_score(
        self,
        query: str,
        chunk: Dict,
        vector_similarity: float,
        query_type: Dict
    ) -> Tuple[float, Dict]:
        """
        Calculate hybrid ranking score with multi-layered boosting
        
        Args:
            query: User query
            chunk: Knowledge base chunk
            vector_similarity: Cosine similarity score
            query_type: Dict with query type flags
            
        Returns:
            Tuple of (final_score, score_breakdown)
        """
        metadata = chunk['metadata']
        text = chunk['text']
        
        # Base score from vector similarity
        score = vector_similarity
        weights = {'vector': vector_similarity}
        
        # LAYER 1: Definition Query Boosting
        if query_type['is_definition']:
            boost = 0.0
            
            # Strong boost for Chapter I definitions
            if self.is_chapter_one_definition(metadata):
                boost += 0.15
                weights['chapter_i'] = 0.15
            
            # Strong boost for Section 1 (main definitions)
            if self.is_section_one(metadata):
                boost += 0.20
                weights['section_1'] = 0.20
            
            # Boost for definition markers in text
            if self.has_definition_markers(text):
                boost += 0.10
                weights['definition_markers'] = 0.10
            
            score += boost
        
        # LAYER 2: Procedural/Jurisdiction Query Boosting
        if query_type['is_procedural']:
            boost = 0.0
            
            # Boost for Chapter III (CCPA)
            if self.is_chapter_three_ccpa(metadata):
                boost += 0.18
                weights['chapter_iii_ccpa'] = 0.18
            
            # Boost for Chapter IV (Commissions)
            if self.is_chapter_four_commissions(metadata):
                boost += 0.18
                weights['chapter_iv_commissions'] = 0.18
            
            # Boost for procedural markers in text
            if self.has_procedural_markers(text):
                boost += 0.12
                weights['procedural_markers'] = 0.12
            
            score += boost
        
        # LAYER 3: Scenario Query Handling
        if query_type['is_scenario']:
            boost = 0.0
            
            # Moderate boost for liability chapters
            if self.is_chapter_six_liability(metadata):
                boost += 0.12
                weights['chapter_vi_liability'] = 0.12
            
            # Moderate boost for commissions (remedy)
            if self.is_chapter_four_commissions(metadata):
                boost += 0.08
                weights['chapter_iv_remedy'] = 0.08
            
            # Small boost for definitions (context)
            if self.is_chapter_one_definition(metadata) and self.has_definition_markers(text):
                boost += 0.05
                weights['definition_context'] = 0.05
            
            score += boost
        
        # Keyword relevance (universal minor weight)
        keyword_score = self.calculate_keyword_relevance(query, text)
        score += keyword_score * 0.05
        weights['keyword'] = keyword_score * 0.05
        
        # Normalize to keep score in reasonable range
        score = min(score, 1.0)
        
        breakdown = {
            'vector_similarity': vector_similarity,
            'final_score': score,
            'weights_applied': weights,
            'query_type': query_type
        }
        
        return score, breakdown
    
    def search(self, query: str, top_k: int = None) -> List[Dict]:
        """
        Search knowledge base with multi-layered hybrid ranking
        
        Args:
            query: User query
            top_k: Number of results to return (auto-adjusted based on query type)
            
        Returns:
            List of top-k ranked chunks with metadata
        """
        # Detect query types
        query_type = {
            'is_definition': self.is_definition_query(query),
            'is_procedural': self.is_procedural_query(query),
            'is_scenario': self.is_scenario_query(query)
        }
        
        # Auto-adjust top_k based on query type
        if top_k is None:
            if query_type['is_scenario']:
                top_k = 7  # Scenarios need more context
            elif query_type['is_procedural']:
                top_k = 6  # Procedural queries need multiple sections
            else:
                top_k = 5  # Definitions can use fewer
        
        # Generate query embedding
        query_embedding = self.embedding_model.encode([query])[0]
        
        # Calculate scores for all chunks
        results = []
        for chunk in self.knowledge_base:
            if 'embedding' not in chunk:
                continue
            
            # Calculate vector similarity
            chunk_embedding = np.array(chunk['embedding'])
            vector_sim = float(np.dot(query_embedding, chunk_embedding) / 
                             (np.linalg.norm(query_embedding) * np.linalg.norm(chunk_embedding)))
            
            # Calculate hybrid score with multi-layered boosting
            final_score, breakdown = self.calculate_hybrid_score(
                query, chunk, vector_sim, query_type
            )
            
            results.append({
                'similarity': final_score,
                'vector_similarity': vector_sim,
                'text': chunk['text'],
                'metadata': chunk['metadata'],
                'score_breakdown': breakdown
            })
        
        # Sort by final score and return top-k
        results.sort(key=lambda x: x['similarity'], reverse=True)
        return results[:top_k]
    
    def calculate_confidence(self, similarities: List[float]) -> str:
        """
        Calculate confidence level with improved calibration
        
        Args:
            similarities: List of similarity scores
            
        Returns:
            Confidence level: "High", "Medium", or "Low"
        """
        if not similarities:
            return "Low"
        
        # Use top score and supporting scores
        top_score = similarities[0]
        
        # Check if we have supporting evidence
        supporting_scores = [s for s in similarities[1:3] if s >= 0.75] if len(similarities) > 1 else []
        
        # Refined confidence thresholds
        if top_score >= 0.85 and len(supporting_scores) >= 1:
            return "High"
        elif top_score >= 0.80:
            return "High"
        elif top_score >= 0.70:
            return "Medium"
        else:
            return "Low"
