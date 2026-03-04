#!/usr/bin/env python3
"""
Translation Service for Multilingual Support
Wrapper layer for translating queries and responses using Bedrock
"""

import boto3
import json
from typing import Optional


class TranslationService:
    """
    Translation service using AWS Bedrock Claude for deterministic translations
    Acts as a wrapper layer - does not modify core RAG logic
    """
    
    # Language codes and names
    SUPPORTED_LANGUAGES = {
        'en': 'English',
        'hi': 'Hindi',
        'ta': 'Tamil',
        'te': 'Telugu',
        'mr': 'Marathi'
    }
    
    def __init__(self, region_name: str = "ap-south-1"):
        """
        Initialize translation service
        
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
            print(f"✓ Translation service initialized (Region: {self.region_name})")
        except Exception as e:
            print(f"WARNING: Translation service initialization failed: {e}")
            self.bedrock_runtime = None
    
    def is_translation_needed(self, language: str) -> bool:
        """
        Check if translation is needed
        
        Args:
            language: Language code
            
        Returns:
            True if translation needed, False otherwise
        """
        return language != 'en' and language in self.SUPPORTED_LANGUAGES
    
    def translate_to_english(self, text: str, source_language: str) -> str:
        """
        Translate text from source language to English
        
        Args:
            text: Text to translate
            source_language: Source language code
            
        Returns:
            Translated text in English
        """
        if not self.is_translation_needed(source_language):
            return text
        
        if not self.bedrock_runtime:
            print("WARNING: Translation service not available, returning original text")
            return text
        
        try:
            source_lang_name = self.SUPPORTED_LANGUAGES.get(source_language, source_language)
            
            system_prompt = f"""You are a professional translator specializing in legal terminology.

CRITICAL RULES:
1. Translate ONLY from {source_lang_name} to English
2. Preserve the exact meaning and intent
3. Maintain legal terminology accuracy
4. Do NOT add explanations or commentary
5. Do NOT summarize or paraphrase
6. Return ONLY the translated text

If the input is already in English, return it unchanged."""

            user_prompt = f"""Translate the following {source_lang_name} text to English:

{text}

Translation:"""

            messages = [
                {
                    "role": "user",
                    "content": [{"text": user_prompt}]
                }
            ]
            
            response = self.bedrock_runtime.converse(
                modelId=self.model_id,
                messages=messages,
                system=[{"text": system_prompt}],
                inferenceConfig={
                    "maxTokens": 500,
                    "temperature": 0.1,  # Deterministic
                    "topP": 0.9
                }
            )
            
            translated_text = response['output']['message']['content'][0]['text'].strip()
            return translated_text
            
        except Exception as e:
            print(f"ERROR: Translation to English failed: {e}")
            # Fallback: return original text
            return text
    
    def translate_from_english(self, text: str, target_language: str) -> str:
        """
        Translate text from English to target language
        
        Args:
            text: Text to translate (in English)
            target_language: Target language code
            
        Returns:
            Translated text in target language
        """
        if not self.is_translation_needed(target_language):
            return text
        
        if not self.bedrock_runtime:
            print("WARNING: Translation service not available, returning original text")
            return text
        
        try:
            target_lang_name = self.SUPPORTED_LANGUAGES.get(target_language, target_language)
            
            system_prompt = f"""You are a professional translator specializing in legal terminology.

CRITICAL RULES:
1. Translate ONLY from English to {target_lang_name}
2. Preserve ALL formatting (line breaks, numbering, bullet points, section headers)
3. Preserve ALL structure (numbered lists, bold markers like **text**)
4. Maintain legal terminology accuracy
5. Do NOT add explanations or commentary
6. Do NOT summarize or alter meaning
7. Do NOT hallucinate information
8. Return ONLY the translated text with exact same formatting

FORMATTING PRESERVATION:
- Keep numbered lists: 1., 2., 3., etc.
- Keep section headers: **Header:**
- Keep line breaks and spacing
- Keep bullet points and indentation"""

            user_prompt = f"""Translate the following English text to {target_lang_name}, preserving ALL formatting and structure:

{text}

Translation:"""

            messages = [
                {
                    "role": "user",
                    "content": [{"text": user_prompt}]
                }
            ]
            
            response = self.bedrock_runtime.converse(
                modelId=self.model_id,
                messages=messages,
                system=[{"text": system_prompt}],
                inferenceConfig={
                    "maxTokens": 2000,  # Longer for structured responses
                    "temperature": 0.1,  # Deterministic
                    "topP": 0.9
                }
            )
            
            translated_text = response['output']['message']['content'][0]['text'].strip()
            return translated_text
            
        except Exception as e:
            print(f"ERROR: Translation from English failed: {e}")
            # Fallback: return original text
            return text
    
    def translate_query_and_response(
        self,
        query: str,
        response_text: str,
        language: str
    ) -> tuple:
        """
        Translate query to English and response back to target language
        
        Args:
            query: User query in target language
            response_text: Response in English
            language: Target language code
            
        Returns:
            Tuple of (english_query, translated_response)
        """
        # Translate query to English
        english_query = self.translate_to_english(query, language)
        
        # Translate response to target language
        translated_response = self.translate_from_english(response_text, language)
        
        return english_query, translated_response


def main():
    """Test translation service"""
    print("=" * 70)
    print("Translation Service Test")
    print("=" * 70)
    
    service = TranslationService(region_name="ap-south-1")
    
    # Test Hindi translation
    hindi_query = "उपभोक्ता की परिभाषा क्या है?"
    print(f"\nOriginal (Hindi): {hindi_query}")
    
    english_query = service.translate_to_english(hindi_query, 'hi')
    print(f"Translated to English: {english_query}")
    
    # Test response translation
    english_response = """Answer:

1. **Legal Status:**
   The person qualifies as a consumer under Section 2(7).

2. **Nature of Violation:**
   Defect in goods.

Sources:
- Section 2(7): Consumer definition"""
    
    print(f"\nOriginal Response (English):\n{english_response}")
    
    hindi_response = service.translate_from_english(english_response, 'hi')
    print(f"\nTranslated Response (Hindi):\n{hindi_response}")
    
    print("\n" + "=" * 70)


if __name__ == "__main__":
    main()
