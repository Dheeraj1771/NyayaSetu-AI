#!/usr/bin/env python3
"""
NyayaSetu AI - RAG Knowledge Base Foundation Setup
Day 0: Process Consumer Protection Act, 2019 PDF into structured, embedded knowledge base
"""

import json
import re
import os
from typing import List, Dict, Any
from pathlib import Path

# PDF extraction
try:
    import PyPDF2
    PDF_LIBRARY = "PyPDF2"
except ImportError:
    try:
        import pdfplumber
        PDF_LIBRARY = "pdfplumber"
    except ImportError:
        print("ERROR: No PDF library found. Install with: pip install PyPDF2 or pip install pdfplumber")
        exit(1)

# Embeddings
try:
    from sentence_transformers import SentenceTransformer
    EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
    print(f"Using sentence-transformers for embeddings: {EMBEDDING_MODEL}")
except ImportError:
    print("WARNING: sentence-transformers not found. Install with: pip install sentence-transformers")
    print("Proceeding without embeddings generation...")
    EMBEDDING_MODEL = None


class CPAKnowledgeBaseBuilder:
    """Build structured knowledge base from Consumer Protection Act, 2019 PDF"""
    
    def __init__(self, pdf_path: str, output_dir: str = "knowledge_base"):
        self.pdf_path = pdf_path
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        
        # Chunking configuration
        self.target_chunk_size = 850  # tokens (700-1000 range, targeting middle)
        self.chunk_overlap = 125  # tokens (100-150 range)
        self.avg_chars_per_token = 4  # Approximation for English text
        
        # Initialize embedding model if available
        self.embedding_model = None
        if EMBEDDING_MODEL:
            try:
                self.embedding_model = SentenceTransformer(EMBEDDING_MODEL)
                print(f"✓ Embedding model loaded: {EMBEDDING_MODEL}")
            except Exception as e:
                print(f"WARNING: Could not load embedding model: {e}")
        
        self.chunks = []
        self.raw_text = ""
        self.cleaned_text = ""
    
    def extract_text_from_pdf(self) -> str:
        """Extract text from PDF preserving structure"""
        print(f"\n[Step 1] Extracting text from {self.pdf_path}...")
        
        text = ""
        
        if PDF_LIBRARY == "pdfplumber":
            import pdfplumber
            with pdfplumber.open(self.pdf_path) as pdf:
                for page_num, page in enumerate(pdf.pages, 1):
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n"
                print(f"✓ Extracted {len(pdf.pages)} pages using pdfplumber")
        
        else:  # PyPDF2
            with open(self.pdf_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                for page_num, page in enumerate(pdf_reader.pages, 1):
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n"
                print(f"✓ Extracted {len(pdf_reader.pages)} pages using PyPDF2")
        
        self.raw_text = text
        print(f"✓ Total characters extracted: {len(text):,}")
        return text
    
    def clean_text(self, text: str) -> str:
        """Clean extracted text while preserving legal structure"""
        print("\n[Step 2] Cleaning extracted content...")
        
        # Remove page numbers (standalone numbers)
        text = re.sub(r'\n\s*\d+\s*\n', '\n', text)
        
        # Remove excessive whitespace
        text = re.sub(r'\n\s*\n\s*\n+', '\n\n', text)
        text = re.sub(r' +', ' ', text)
        
        # Remove common header/footer patterns
        text = re.sub(r'THE GAZETTE OF INDIA.*?\n', '', text, flags=re.IGNORECASE)
        text = re.sub(r'EXTRAORDINARY.*?\n', '', text, flags=re.IGNORECASE)
        
        # Preserve section numbering and structure
        # Ensure section numbers are properly formatted
        text = re.sub(r'\n(\d+)\.\s+', r'\n\nSection \1. ', text)
        
        # Clean up but preserve chapter markers
        # Only normalize uppercase CHAPTER markers (actual headers), not lowercase references
        text = re.sub(r'CHAPTER\s+([IVX]+)', r'\n\nCHAPTER \1', text)
        
        self.cleaned_text = text.strip()
        print(f"✓ Cleaned text: {len(self.cleaned_text):,} characters")
        print(f"✓ Reduction: {len(self.raw_text) - len(self.cleaned_text):,} characters removed")
        
        return self.cleaned_text
    
    def extract_structure(self, text: str) -> List[Dict[str, Any]]:
        """Extract hierarchical structure from legal document"""
        print("\n[Step 3] Extracting document structure...")
        
        sections = []
        current_chapter = "Preliminary"
        
        # Improved chapter detection with multi-line title support
        # First, find all chapter markers and their positions
        # IMPORTANT: Only match uppercase "CHAPTER" (actual headers), not lowercase "Chapter" (references)
        chapter_pattern = r'CHAPTER\s+([IVXLC]+)'
        chapter_matches = list(re.finditer(chapter_pattern, text))
        
        # Build a map of chapter positions to full chapter info
        chapter_map = {}
        for i, match in enumerate(chapter_matches):
            chapter_num = match.group(1)
            start_pos = match.end()
            
            # Determine end position (next chapter or end of text)
            if i + 1 < len(chapter_matches):
                end_pos = chapter_matches[i + 1].start()
            else:
                end_pos = len(text)
            
            # Extract text after "CHAPTER X" until next section or chapter
            chapter_text = text[start_pos:min(start_pos + 500, end_pos)]
            
            # Extract chapter title (next non-empty lines after CHAPTER marker)
            # Stop at Section marker or excessive whitespace
            lines = chapter_text.split('\n')
            title_parts = []
            
            for line in lines:
                line = line.strip()
                if not line:
                    # Allow one empty line, but stop at multiple
                    if title_parts:
                        break
                    continue
                
                # Stop if we hit a section marker
                if re.match(r'Section\s+\d+', line, re.IGNORECASE):
                    break
                
                # Stop if we hit another structural marker
                if re.match(r'CHAPTER\s+[IVXLC]+', line, re.IGNORECASE):
                    break
                
                # Skip lines that look like section content (start with numbers or lowercase)
                if re.match(r'^\d+\.', line) or (line and line[0].islower()):
                    break
                
                # Skip lines that are too long (likely section content)
                if len(line) > 100:
                    break
                
                # Add to title
                title_parts.append(line)
                
                # Stop after collecting reasonable title (usually 1-2 lines for chapter titles)
                if len(title_parts) >= 2:
                    break
            
            # Join title parts and clean up
            chapter_title = ' '.join(title_parts).strip()
            
            # Remove common artifacts
            chapter_title = re.sub(r'\s+', ' ', chapter_title)  # Normalize whitespace
            chapter_title = re.sub(r'^[:\-\s]+', '', chapter_title)  # Remove leading punctuation
            chapter_title = re.sub(r'[:\-\s]+$', '', chapter_title)  # Remove trailing punctuation
            
            # Fix PDF extraction spacing issues
            # Pattern: "C ONSUMER" -> "CONSUMER" (remove space between single capital and following capitals)
            while re.search(r'([A-Z])\s+([A-Z])', chapter_title):
                chapter_title = re.sub(r'([A-Z])\s+([A-Z])', r'\1\2', chapter_title)
            
            # Now we have something like "CONSUMERPROTECTIONCOUNCILS"
            # We need to split it into words. Use a simple heuristic:
            # Common legal/administrative words to help split
            common_words = [
                'CONSUMER', 'PROTECTION', 'COUNCILS', 'CENTRAL', 'AUTHORITY',
                'DISPUTES', 'REDRESSAL', 'COMMISSION', 'MEDIATION', 'PRODUCT',
                'LIABILITY', 'OFFENCES', 'PENALTIES', 'MISCELLANEOUS',
                'PRELIMINARY', 'AND', 'THE', 'OF'
            ]
            
            # Try to split by known words
            temp_title = chapter_title
            for word in sorted(common_words, key=len, reverse=True):  # Longest first
                # Add space before the word if it's not at the start
                temp_title = re.sub(f'(?<!^)({word})', r' \1', temp_title)
            
            # If we successfully split some words, use it
            if ' ' in temp_title and temp_title != chapter_title:
                chapter_title = temp_title
            
            # Clean up multiple spaces
            chapter_title = re.sub(r'\s+', ' ', chapter_title).strip()
            
            # Title case for better readability
            if chapter_title:
                # Capitalize first letter of each word
                chapter_title = ' '.join(word.capitalize() for word in chapter_title.split())
            
            # Validate title - if it looks corrupted, use generic name
            # Check for: too short, no letters, starts with punctuation, or contains too much punctuation
            is_valid = (
                chapter_title and 
                len(chapter_title) >= 3 and 
                any(c.isalpha() for c in chapter_title) and
                not chapter_title[0] in '.,;:()[]{}' and
                sum(c in '.,;:()[]{}' for c in chapter_title) < len(chapter_title) / 3
            )
            
            if not is_valid:
                chapter_title = f"Chapter {chapter_num}"
            
            # Store in map
            chapter_map[match.start()] = {
                'number': chapter_num,
                'title': chapter_title,
                'full_name': f"Chapter {chapter_num}: {chapter_title}"
            }
        
        # Split by sections
        section_pattern = r'(?=\n\s*Section\s+\d+\.)'
        parts = re.split(section_pattern, text)
        
        for part in parts:
            if not part.strip():
                continue
            
            # Find which chapter this section belongs to
            # Look for the most recent chapter marker before this section
            part_start = text.find(part)
            
            for chapter_pos in sorted(chapter_map.keys(), reverse=True):
                if chapter_pos < part_start:
                    current_chapter = chapter_map[chapter_pos]['full_name']
                    break
            
            # Extract section number and content
            section_match = re.search(r'Section\s+(\d+)\.\s*(.+?)(?=\n\s*Section\s+\d+\.|$)', part, re.DOTALL)
            
            if section_match:
                section_num = section_match.group(1)
                section_content = section_match.group(2).strip()
                
                # Extract section title (usually first line or bold text)
                title_match = re.search(r'^(.+?)(?:\.|—|\n)', section_content)
                section_title = title_match.group(1).strip() if title_match else f"Section {section_num}"
                
                sections.append({
                    'chapter': current_chapter,
                    'section': f"Section {section_num}",
                    'title': section_title,
                    'content': section_content
                })
        
        print(f"✓ Extracted {len(sections)} sections")
        
        # Print chapter summary for verification
        unique_chapters = sorted(set(s['chapter'] for s in sections))
        print(f"✓ Identified {len(unique_chapters)} chapters:")
        for chapter in unique_chapters:
            print(f"  - {chapter}")
        
        return sections
    
    def create_chunks(self, sections: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Create chunks with metadata following the specified strategy"""
        print("\n[Step 4] Creating chunks with metadata...")
        
        chunks = []
        
        for section in sections:
            content = section['content']
            
            # Calculate size in approximate tokens
            content_length = len(content)
            estimated_tokens = content_length // self.avg_chars_per_token
            
            target_chars = self.target_chunk_size * self.avg_chars_per_token
            overlap_chars = self.chunk_overlap * self.avg_chars_per_token
            
            # If section fits in one chunk, keep it whole
            if estimated_tokens <= self.target_chunk_size:
                chunk = {
                    'text': content,
                    'metadata': {
                        'act': 'Consumer Protection Act, 2019',
                        'chapter': section['chapter'],
                        'section': section['section'],
                        'title': section['title'],
                        'language': 'English'
                    }
                }
                chunks.append(chunk)
            
            else:
                # Split large sections into overlapping chunks
                start = 0
                chunk_num = 1
                
                while start < content_length:
                    end = start + target_chars
                    
                    # Try to break at sentence boundary
                    if end < content_length:
                        # Look for sentence end within next 200 chars
                        sentence_end = content.find('. ', end, end + 200)
                        if sentence_end != -1:
                            end = sentence_end + 1
                    
                    chunk_text = content[start:end].strip()
                    
                    chunk = {
                        'text': chunk_text,
                        'metadata': {
                            'act': 'Consumer Protection Act, 2019',
                            'chapter': section['chapter'],
                            'section': f"{section['section']} (Part {chunk_num})",
                            'title': section['title'],
                            'language': 'English'
                        }
                    }
                    chunks.append(chunk)
                    
                    # Move start position with overlap
                    start = end - overlap_chars
                    chunk_num += 1
        
        self.chunks = chunks
        print(f"✓ Created {len(chunks)} chunks")
        print(f"✓ Average chunk size: {sum(len(c['text']) for c in chunks) // len(chunks):,} characters")
        
        return chunks
    
    def generate_embeddings(self, chunks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Generate embeddings for each chunk"""
        print("\n[Step 5] Generating embeddings...")
        
        if not self.embedding_model:
            print("⚠ Skipping embeddings (model not available)")
            return chunks
        
        texts = [chunk['text'] for chunk in chunks]
        
        print(f"Generating embeddings for {len(texts)} chunks...")
        embeddings = self.embedding_model.encode(texts, show_progress_bar=True)
        
        # Add embeddings to chunks
        for i, chunk in enumerate(chunks):
            chunk['embedding'] = embeddings[i].tolist()
        
        print(f"✓ Generated {len(embeddings)} embeddings")
        print(f"✓ Embedding dimension: {len(embeddings[0])}")
        
        return chunks
    
    def save_knowledge_base(self, chunks: List[Dict[str, Any]]):
        """Save knowledge base in structured format"""
        print("\n[Step 6] Saving knowledge base...")
        
        # Save full knowledge base
        kb_path = self.output_dir / "knowledge_base.json"
        with open(kb_path, 'w', encoding='utf-8') as f:
            json.dump(chunks, f, indent=2, ensure_ascii=False)
        print(f"✓ Saved full knowledge base: {kb_path}")
        
        # Save metadata only (for quick inspection)
        metadata_only = [{'metadata': c['metadata'], 'text_preview': c['text'][:200] + '...'} for c in chunks]
        metadata_path = self.output_dir / "metadata_index.json"
        with open(metadata_path, 'w', encoding='utf-8') as f:
            json.dump(metadata_only, f, indent=2, ensure_ascii=False)
        print(f"✓ Saved metadata index: {metadata_path}")
        
        # Save Pinecone-ready format
        pinecone_format = []
        for i, chunk in enumerate(chunks):
            entry = {
                'id': f"cpa2019_chunk_{i}",
                'values': chunk.get('embedding', []),
                'metadata': {
                    **chunk['metadata'],
                    'text': chunk['text']
                }
            }
            pinecone_format.append(entry)
        
        pinecone_path = self.output_dir / "pinecone_ready.json"
        with open(pinecone_path, 'w', encoding='utf-8') as f:
            json.dump(pinecone_format, f, indent=2, ensure_ascii=False)
        print(f"✓ Saved Pinecone-ready format: {pinecone_path}")
        
        # Save summary statistics
        stats = {
            'total_chunks': len(chunks),
            'total_sections': len(set(c['metadata']['section'] for c in chunks)),
            'total_chapters': len(set(c['metadata']['chapter'] for c in chunks)),
            'avg_chunk_size_chars': sum(len(c['text']) for c in chunks) // len(chunks),
            'has_embeddings': 'embedding' in chunks[0] if chunks else False,
            'embedding_dimension': len(chunks[0]['embedding']) if chunks and 'embedding' in chunks[0] else 0
        }
        
        stats_path = self.output_dir / "stats.json"
        with open(stats_path, 'w', encoding='utf-8') as f:
            json.dump(stats, f, indent=2)
        print(f"✓ Saved statistics: {stats_path}")
        
        return stats
    
    def build(self):
        """Execute full knowledge base building pipeline"""
        print("=" * 70)
        print("NyayaSetu AI - RAG Knowledge Base Foundation Setup")
        print("Processing: Consumer Protection Act, 2019")
        print("=" * 70)
        
        # Step 1: Extract
        raw_text = self.extract_text_from_pdf()
        
        # Step 2: Clean
        cleaned_text = self.clean_text(raw_text)
        
        # Step 3: Structure
        sections = self.extract_structure(cleaned_text)
        
        # Step 4: Chunk
        chunks = self.create_chunks(sections)
        
        # Step 5: Embed
        chunks_with_embeddings = self.generate_embeddings(chunks)
        
        # Step 6: Save
        stats = self.save_knowledge_base(chunks_with_embeddings)
        
        # Print summary
        print("\n" + "=" * 70)
        print("KNOWLEDGE BASE BUILD COMPLETE")
        print("=" * 70)
        print(f"Total chunks created: {stats['total_chunks']}")
        print(f"Total sections: {stats['total_sections']}")
        print(f"Total chapters: {stats['total_chapters']}")
        print(f"Average chunk size: {stats['avg_chunk_size_chars']} characters")
        print(f"Embeddings generated: {'Yes' if stats['has_embeddings'] else 'No'}")
        if stats['has_embeddings']:
            print(f"Embedding dimension: {stats['embedding_dimension']}")
        
        # Show sample chunk
        if chunks:
            print("\n" + "-" * 70)
            print("SAMPLE CHUNK:")
            print("-" * 70)
            sample = chunks[0]
            print(f"Metadata: {json.dumps(sample['metadata'], indent=2)}")
            print(f"\nText preview: {sample['text'][:300]}...")
            print("-" * 70)
        
        print(f"\n✓ Knowledge base saved to: {self.output_dir}/")
        print("✓ Ready for vector database ingestion")
        
        return stats


def main():
    """Main execution"""
    # Get the project root directory (two levels up from this script)
    script_dir = Path(__file__).parent
    project_root = script_dir.parent.parent
    
    pdf_path = project_root / "data" / "raw" / "CPA2019.pdf"
    output_dir = project_root / "knowledge_base"
    
    if not pdf_path.exists():
        print(f"ERROR: {pdf_path} not found")
        print(f"Expected location: data/raw/CPA2019.pdf")
        return
    
    builder = CPAKnowledgeBaseBuilder(str(pdf_path), str(output_dir))
    builder.build()


if __name__ == "__main__":
    main()
