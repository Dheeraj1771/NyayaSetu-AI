# NyayaSetu AI – Legal RAG Engine

> Production-grade RAG system for Consumer Protection Act, 2019 with multi-layered hybrid retrieval, structured scenario reasoning, and full multilingual support

## What This System Does

NyayaSetu AI is a legal AI engine that provides accurate, source-grounded answers to consumer rights questions in 5 Indian languages. It combines multi-layered hybrid retrieval (vector similarity + legal structure boosting) with query-type aware generation to deliver structured legal analysis. The system handles definitions, procedural queries, and real-world scenarios with confidence calibration and mandatory citation enforcement. Multilingual support is implemented as a clean wrapper layer that translates queries and responses while keeping the core RAG engine unchanged.

## Key Features

- **Multi-Layered Hybrid Retrieval**: Vector similarity + legal structure boosting (Chapter I for definitions, Chapter IV for procedures, Chapter VI for liability)
- **Query-Type Classification**: Automatic detection of definitions, procedural queries, and scenarios with tailored retrieval strategies
- **Structured Scenario Reasoning**: 6-step mandatory format for legal analysis (Legal Status → Violation → Provisions → Remedies → Forum → Conclusion)
- **Scenario-Specific Confidence Calibration**: Adaptive thresholds for complex multi-section queries
- **Full Multilingual Support**: Complete UI and response translation in 5 Indian languages with translation wrapper architecture
- **AWS Bedrock Integration**: Claude 3 Haiku with cost optimization (600 tokens, 0.1 temperature, 2000 token context cap)
- **Clean Modular Architecture**: Separation of retrieval, generation, translation, and API layers

## Supported Languages

- 🇬🇧 English (en)
- 🇮🇳 Hindi - हिंदी (hi)
- 🇮🇳 Tamil - தமிழ் (ta)
- 🇮🇳 Telugu - తెలుగు (te)
- 🇮🇳 Marathi - मराठी (mr)

## Voice Support

Voice input (Speech-to-Text) and voice output (Text-to-Speech) using Web Speech API. Microphone button for voice queries, speaker button to listen to answers. Supports all 5 languages with Indian locale variants (en-IN, hi-IN, ta-IN, te-IN, mr-IN). Frontend-only implementation, no external APIs required.

## Architecture Overview

High-level pipeline showing multilingual wrapper around core RAG:

```
User Query (Any Language)
    ↓
Translation Layer (if non-English) → Query to English
    ↓
Core RAG Engine (English Internal - UNCHANGED)
    ├─ Enhanced Retrieval (Query Type Detection + Hybrid Ranking)
    ├─ Bedrock Generation (Structured Prompts)
    └─ Confidence Calibration
    ↓
Translation Layer (if non-English) → Response to Original Language
    ↓
Structured Response (Answer + Sources + Confidence)
```

**Key Design**: Core RAG system remains unchanged. Multilingual support acts as a wrapper layer that translates input/output while preserving all internal logic, structured formatting, and confidence scoring.

## Project Structure

```
NyayaSetu-AI/
├── src/
│   ├── api/
│   │   └── main.py                  # FastAPI backend with multilingual support
│   └── rag/
│       ├── retrieval_engine.py      # Multi-layered hybrid retrieval
│       ├── bedrock_generator.py     # Query-type aware generation
│       ├── translation_service.py   # Multilingual translation wrapper
│       ├── rag_kb_setup.py          # Knowledge base builder
│       ├── query_single.py          # CLI query tool
│       └── validate_setup.py        # Setup validator
├── frontend/
│   ├── locales/                     # Translation files (en, hi, ta, te, mr)
│   │   ├── en.json
│   │   ├── hi.json
│   │   ├── ta.json
│   │   ├── te.json
│   │   └── mr.json
│   ├── index.html                   # Web interface with i18n
│   ├── styles.css                   # Premium UI with language selector
│   └── script.js                    # Frontend logic with i18n support
├── knowledge_base/
│   ├── knowledge_base.json          # 111 chunks with 384-dim embeddings
│   ├── metadata_index.json          # Section index
│   └── stats.json                   # KB statistics
├── data/raw/
│   └── CPA2019.pdf                  # Consumer Protection Act, 2019
└── requirements.txt
```

## Setup Instructions

**1. Clone and Install**
```bash
git clone <repository-url>
cd NyayaSetu-AI
pip install -r requirements.txt
```

**2. Configure AWS Credentials**
```bash
aws configure
# Region: ap-south-1 (Mumbai)
# Enable Claude 3 Haiku in Bedrock console
```

**3. Start Backend**
```bash
uvicorn src.api.main:app --reload
# API: http://localhost:8000
# Docs: http://localhost:8000/docs
```

**4. Start Frontend**
```bash
python -m http.server 3000 --directory frontend
# Frontend: http://localhost:3000
```

## API Usage

**Endpoint:** `POST /ask`

**Request with Language Parameter:**
```json
{
  "question": "उपभोक्ता क्या है?",
  "language": "hi"
}
```

**Response:**
```json
{
  "answer": "उपभोक्ता संरक्षण अधिनियम, 2019 के अनुसार...",
  "sources": [
    {
      "act": "Consumer Protection Act, 2019",
      "chapter": "Chapter I: Preliminary",
      "section": "Section 2(7)",
      "similarity": 0.89
    }
  ],
  "confidence": "High",
  "processing_time_ms": 850
}
```

**Supported Language Codes:** `en`, `hi`, `ta`, `te`, `mr`

## Example Query

**Scenario Query (English):**
```
"I purchased a defective AC and the seller refused refund."
```

**Structured Response:**
```
Answer:

1. Legal Status:
   Yes, qualifies as a consumer under Section 2(7).

2. Nature of Violation:
   Defect in goods (product not functioning as expected).

3. Applicable Provisions:
   - Chapter I: Section 2(7) - Consumer definition
   - Chapter IV: Consumer Disputes Redressal

4. Remedies Available:
   - Replacement of defective AC
   - Refund of amount paid
   - Compensation for loss

5. Appropriate Forum:
   District Consumer Commission (based on transaction value)

6. Conclusion:
   Consumer has right to file complaint for defective goods.

Sources:
- Section 2(7): Consumer definition
- Chapter IV: Complaint and remedies

Confidence: High
```

**Same query works in Hindi, Tamil, Telugu, or Marathi with response in the same language.**

## Design Principles

- **No Hardcoded Section Numbers**: All legal references retrieved dynamically from knowledge base
- **No Rule-Based Fixed Answers**: Generation driven by retrieved context, not predefined templates
- **Retrieval-Driven Generation**: LLM constrained to use only provided context
- **Translation Wrapper Architecture**: Core RAG unchanged, multilingual support as external layer
- **Clean Separation of Concerns**: Retrieval, generation, translation, and API layers independently testable
- **Production-Ready Architecture**: Cost optimization, error handling, graceful degradation

## Technical Highlights

- **Embedding Model**: sentence-transformers/all-MiniLM-L6-v2 (384-dim, fast inference)
- **Knowledge Base**: 111 chunks, 99 sections, 8 chapters from Consumer Protection Act, 2019
- **Retrieval Strategy**: Cosine similarity + Chapter-aware boosting (0.15-0.20 boost for relevant chapters)
- **LLM**: Claude 3 Haiku via AWS Bedrock (ap-south-1)
- **Translation**: Same Claude 3 Haiku model with deterministic settings (temperature 0.1)
- **Cost Optimization**: 600 max tokens, 0.1 temperature, 2000 token context cap
- **Response Time**: ~300-500ms (English), ~800-1500ms (with translation)
- **Confidence Calibration**: Adaptive thresholds based on query complexity

## License

See [LICENSE](LICENSE) file.
