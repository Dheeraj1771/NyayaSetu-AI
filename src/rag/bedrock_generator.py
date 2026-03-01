#!/usr/bin/env python3
"""
NyayaSetu AI - Amazon Bedrock Integration for Answer Generation
Uses Claude 3 Haiku via Bedrock Runtime API
"""

import json
import boto3
from typing import List, Dict, Any, Optional


class BedrockAnswerGenerator:
    """Generate natural language answers using Amazon Bedrock (Claude 3 Haiku)"""
    
    # Cost optimization constants
    MAX_CONTEXT_TOKENS = 2000  # Hard limit for context size
    MAX_OUTPUT_TOKENS = 600    # Reduced from 1000 for cost efficiency
    TEMPERATURE = 0.1          # Reduced from 0.3 for deterministic legal responses
    
    def __init__(self, region_name: str = "ap-south-1"):
        """
        Initialize Bedrock Runtime client
        
        Args:
            region_name: AWS region (default: ap-south-1 Mumbai)
        """
        self.region_name = region_name
        self.model_id = "anthropic.claude-3-haiku-20240307-v1:0"
        
        try:
            self.bedrock_runtime = boto3.client(
                service_name='bedrock-runtime',
                region_name=self.region_name
            )
            print(f"✓ Bedrock Runtime client initialized (Region: {self.region_name})")
        except Exception as e:
            print(f"ERROR: Failed to initialize Bedrock client: {e}")
            print("Ensure AWS credentials are configured (root login or IAM)")
            raise
    
    def estimate_tokens(self, text: str) -> int:
        """
        Estimate token count for text
        
        Args:
            text: Input text
            
        Returns:
            Estimated token count (rough approximation)
        """
        # Rough estimate: word count * 1.3
        word_count = len(text.split())
        return int(word_count * 1.3)
    
    def truncate_context(self, retrieved_chunks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Truncate context to stay within MAX_CONTEXT_TOKENS limit
        
        Strategy:
        - Preserve highest similarity chunk fully
        - Truncate lower-ranked chunks if needed
        - Never exceed MAX_CONTEXT_TOKENS
        
        Args:
            retrieved_chunks: List of retrieved chunks (sorted by similarity)
            
        Returns:
            Truncated list of chunks
        """
        if not retrieved_chunks:
            return []
        
        truncated_chunks = []
        total_tokens = 0
        
        for i, chunk in enumerate(retrieved_chunks):
            chunk_text = chunk.get('text', '')
            chunk_tokens = self.estimate_tokens(chunk_text)
            
            # First chunk (highest similarity) - always include fully
            if i == 0:
                truncated_chunks.append(chunk)
                total_tokens += chunk_tokens
                continue
            
            # Check if adding this chunk would exceed limit
            if total_tokens + chunk_tokens <= self.MAX_CONTEXT_TOKENS:
                # Add full chunk
                truncated_chunks.append(chunk)
                total_tokens += chunk_tokens
            else:
                # Calculate remaining token budget
                remaining_tokens = self.MAX_CONTEXT_TOKENS - total_tokens
                
                if remaining_tokens > 100:  # Only add if meaningful space remains
                    # Truncate chunk to fit
                    words = chunk_text.split()
                    target_words = int(remaining_tokens / 1.3)
                    truncated_text = ' '.join(words[:target_words]) + '...'
                    
                    truncated_chunk = chunk.copy()
                    truncated_chunk['text'] = truncated_text
                    truncated_chunks.append(truncated_chunk)
                    total_tokens += self.estimate_tokens(truncated_text)
                
                # Stop processing further chunks
                break
        
        return truncated_chunks
    
    def assemble_context(self, retrieved_chunks: List[Dict[str, Any]]) -> str:
        """
        Assemble retrieved chunks into structured context
        
        Args:
            retrieved_chunks: List of retrieved chunks with metadata
            
        Returns:
            Formatted context string
        """
        context_parts = []
        
        for i, chunk in enumerate(retrieved_chunks, 1):
            metadata = chunk.get('metadata', {})
            text = chunk.get('text', '')
            
            context_part = f"""[Context {i}]
Act: {metadata.get('act', 'N/A')}
Chapter: {metadata.get('chapter', 'N/A')}
Section: {metadata.get('section', 'N/A')}

Content:
{text}
"""
            context_parts.append(context_part)
        
        return "\n---\n".join(context_parts)
    
    def build_prompt(self, user_query: str, context: str) -> tuple:
        """
        Build system and user prompts for Claude
        
        Args:
            user_query: User's question
            context: Assembled context from retrieved chunks
            
        Returns:
            Tuple of (system_prompt, user_prompt)
        """
        system_prompt = """You are NyayaSetu AI, a legal assistant specializing in Indian consumer protection law.

CRITICAL RULES:
1. Use ONLY the provided context to answer questions
2. Do NOT generate information beyond the provided context
3. If the context doesn't contain the answer, say "I don't have enough information in the provided context to answer this question."
4. Always cite the specific Act, Chapter, and Section from the context
5. Provide clear, concise explanations in simple language
6. Structure your response in the required format

RESPONSE FORMAT:
Answer:
<Your clear explanation based on the context>

Sources:
Act: <Act name from context>
Chapter: <Chapter name from context>
Section: <Section number from context>"""

        user_prompt = f"""Based on the following legal context from the Consumer Protection Act, 2019, please answer the user's question.

CONTEXT:
{context}

USER QUESTION:
{user_query}

Please provide your answer in the specified format."""

        return system_prompt, user_prompt
    
    def generate_answer(
        self,
        user_query: str,
        retrieved_chunks: List[Dict[str, Any]],
        max_tokens: int = None,
        temperature: float = None
    ) -> Dict[str, Any]:
        """
        Generate answer using Bedrock Claude 3 Haiku
        
        Args:
            user_query: User's question
            retrieved_chunks: Top-k retrieved chunks from knowledge base
            max_tokens: Maximum tokens for response (default: 600)
            temperature: Sampling temperature (default: 0.1 for deterministic responses)
            
        Returns:
            Dictionary containing:
                - answer: Generated answer text
                - sources: List of source metadata
                - raw_response: Full Bedrock response
        """
        # Use class defaults if not specified
        if max_tokens is None:
            max_tokens = self.MAX_OUTPUT_TOKENS
        if temperature is None:
            temperature = self.TEMPERATURE
        
        # Truncate context to stay within token limit
        truncated_chunks = self.truncate_context(retrieved_chunks)
        
        # Assemble context from truncated chunks
        context = self.assemble_context(truncated_chunks)
        
        # Build prompts
        system_prompt, user_prompt = self.build_prompt(user_query, context)
        
        # Prepare Converse API request
        messages = [
            {
                "role": "user",
                "content": [{"text": user_prompt}]
            }
        ]
        
        # Invoke Bedrock using Converse API
        try:
            response = self.bedrock_runtime.converse(
                modelId=self.model_id,
                messages=messages,
                system=[{"text": system_prompt}],
                inferenceConfig={
                    "maxTokens": max_tokens,
                    "temperature": temperature,
                    "topP": 0.9
                }
            )
            
            # Extract answer from response
            answer_text = response['output']['message']['content'][0]['text']
            
            # Extract sources from retrieved chunks
            sources = []
            for chunk in retrieved_chunks:
                metadata = chunk.get('metadata', {})
                sources.append({
                    'act': metadata.get('act', 'N/A'),
                    'chapter': metadata.get('chapter', 'N/A'),
                    'section': metadata.get('section', 'N/A'),
                    'similarity': chunk.get('similarity', 0.0)
                })
            
            return {
                'answer': answer_text,
                'sources': sources,
                'raw_response': response,
                'usage': {
                    'input_tokens': response.get('usage', {}).get('inputTokens', 0),
                    'output_tokens': response.get('usage', {}).get('outputTokens', 0),
                    'total_tokens': response.get('usage', {}).get('totalTokens', 0)
                }
            }
            
        except Exception as e:
            print(f"ERROR: Bedrock invocation failed: {e}")
            return {
                'answer': f"Error generating answer: {str(e)}",
                'sources': [],
                'raw_response': None,
                'usage': {}
            }
    
    def generate_answer_streaming(
        self,
        user_query: str,
        retrieved_chunks: List[Dict[str, Any]],
        max_tokens: int = None,
        temperature: float = None
    ):
        """
        Generate answer with streaming response (for future use)
        
        Args:
            user_query: User's question
            retrieved_chunks: Top-k retrieved chunks
            max_tokens: Maximum tokens for response (default: 600)
            temperature: Sampling temperature (default: 0.1)
            
        Yields:
            Chunks of generated text
        """
        # Use class defaults if not specified
        if max_tokens is None:
            max_tokens = self.MAX_OUTPUT_TOKENS
        if temperature is None:
            temperature = self.TEMPERATURE
        
        # Truncate context to stay within token limit
        truncated_chunks = self.truncate_context(retrieved_chunks)
        
        context = self.assemble_context(truncated_chunks)
        system_prompt, user_prompt = self.build_prompt(user_query, context)
        
        messages = [
            {
                "role": "user",
                "content": [{"text": user_prompt}]
            }
        ]
        
        try:
            response = self.bedrock_runtime.converse_stream(
                modelId=self.model_id,
                messages=messages,
                system=[{"text": system_prompt}],
                inferenceConfig={
                    "maxTokens": max_tokens,
                    "temperature": temperature,
                    "topP": 0.9
                }
            )
            
            # Stream response chunks
            for event in response['stream']:
                if 'contentBlockDelta' in event:
                    delta = event['contentBlockDelta']['delta']
                    if 'text' in delta:
                        yield delta['text']
                        
        except Exception as e:
            yield f"Error: {str(e)}"


def main():
    """Test Bedrock integration"""
    print("=" * 70)
    print("NyayaSetu AI - Bedrock Integration Test")
    print("=" * 70)
    
    # Initialize generator
    generator = BedrockAnswerGenerator(region_name="ap-south-1")
    
    # Mock retrieved chunks for testing
    mock_chunks = [
        {
            'text': 'Consumer means any person who buys goods or avails services for consideration.',
            'metadata': {
                'act': 'Consumer Protection Act, 2019',
                'chapter': 'Chapter I: Preliminary',
                'section': 'Section 2'
            },
            'similarity': 0.85
        }
    ]
    
    # Test query
    test_query = "What is the definition of consumer?"
    
    print(f"\nTest Query: {test_query}")
    print("-" * 70)
    
    # Generate answer
    result = generator.generate_answer(test_query, mock_chunks)
    
    print("\nGenerated Answer:")
    print(result['answer'])
    print("\nToken Usage:")
    print(f"  Input: {result['usage'].get('input_tokens', 0)}")
    print(f"  Output: {result['usage'].get('output_tokens', 0)}")
    print(f"  Total: {result['usage'].get('total_tokens', 0)}")
    
    print("\n" + "=" * 70)


if __name__ == "__main__":
    main()
