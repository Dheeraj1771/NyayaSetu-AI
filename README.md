# NyayaSetu AI – Legal RAG Engine

> Production-grade RAG system for Consumer Protection Act, 2019 with multi-layered hybrid retrieval and structured scenario reasoning

## What This System Does

NyayaSetu AI is a legal AI engine that provides accurate, source-grounded answers to consumer rights questions. It combines multi-layered hybrid retrieval (vector similarity + legal structure boosting) with query-type aware generation to deliver structured legal analysis. The system handles definitions, procedural queries, and real-world scenarios with confidence calibration and mandatory citation enforcement.

## Key Features

- **Multi-Layered Hybrid Retrieval**: Vector similarity + BM25 + legal structure boosting (Chapter I for definitions, Chapter IV for procedures, Chapter VI for liability)
- **Query-Type Classification**: Automatic detection of definitions, procedural queries, and scenarios with tailored retrieval strategies
- **Structured Scenario Reasoning**: 6-step mandatory format for legal analysis (Legal Status → Violation → Provisions → Remedies → Forum → Conclusion)
- **Scenario-Specific Confidence Calibration**: Adaptive thresholds for complex multi-section queries
- **AWS Bedrock Integration**: Claude 3 Haiku with cost optimization (600 tokens, 0.1 temperature, 2000 token context cap)
- **Clean Modular Architecture**: Separation of retrieval, generation, and API layers

## Architecture Overview

```
User Query
    ↓
Enhanced Retrieval Engine
    ├─ Query Type Detection (Definition/Procedural/Scenario)
    ├─ Vector Similarity Search (sentence-transformers)
    ├─ Legal Structure Boosting (Chapter-aware)
    └─ Dynamic top_k (5/6/7 based on query type)
    ↓
Query-Type Aware Prompt Builder
    ├─ Standard Prompt (Definitions/Procedural)
    └─ Structured Scenario Prompt (6-step format)
    ↓
AWS Bedrock (Claude 3 Haiku)
    ├─ Context Truncation (2000 token limit)
    ├─ Source-Grounded Generation
    └─ Citation Enforcement
    ↓
Confidence Calibration
    ├─ Standard: top_score + supporting evidence
    └─ Scenario-Specific: lenient thresholds (0.72/0.80)
    ↓
Structured Response (Answer + Sources + Confidence)
```

## Project Structure

```
NyayaSetu-AI/
├── src/
│   ├── api/
│   │   └── main.py                  # FastAPI backend with lifespan management
│   └── rag/
│       ├── retrieval_engine.py      # Multi-layered hybrid retrieval
│       ├── bedrock_generator.py     # Query-type aware generation
│       ├── rag_kb_setup.py          # Knowledge base builder
│       ├── query_single.py          # CLI query tool
│       └── validate_setup.py        # Setup validator
├── frontend/
│   ├── index.html                   # Web interface
│   ├── styles.css                   # Premium UI
│   └── script.js                    # Frontend logic
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

## Example Query

**Scenario Query:**
```
"I purchased a defective AC and the seller refused refund."
```

**Structured Response:**
```
Answer:

1. Legal Status:
   Yes, qualifies as a consumer under Section 2(7) as goods were purchased for consideration.

2. Nature of Violation:
   Defect in goods (product not functioning as expected).

3. Applicable Provisions:
   - Chapter I: Section 2(7) - Consumer definition
   - Chapter IV: Consumer Disputes Redressal
   - Section 35: Complaint filing provisions

4. Remedies Available:
   - Replacement of defective AC
   - Refund of amount paid
   - Compensation for loss

5. Appropriate Forum:
   District Consumer Commission (based on transaction value)

6. Conclusion:
   Consumer has right to file complaint for defective goods. Limitation period: 2 years from cause of action.

Sources:
- Section 2(7): Consumer definition
- Chapter IV: Complaint and remedies
- Section 35: Filing provisions

Confidence: High
```

## Design Principles

- **No Hardcoded Section Numbers**: All legal references retrieved dynamically from knowledge base
- **No Rule-Based Fixed Answers**: Generation driven by retrieved context, not predefined templates
- **Retrieval-Driven Generation**: LLM constrained to use only provided context
- **Clean Separation of Concerns**: Retrieval, generation, and API layers independently testable
- **Production-Ready Architecture**: Cost optimization, error handling, graceful degradation

## Technical Highlights

- **Embedding Model**: sentence-transformers/all-MiniLM-L6-v2 (384-dim, fast inference)
- **Knowledge Base**: 111 chunks, 99 sections, 8 chapters from Consumer Protection Act, 2019
- **Retrieval Strategy**: Cosine similarity + Chapter-aware boosting (0.15-0.20 boost for relevant chapters)
- **LLM**: Claude 3 Haiku via AWS Bedrock (ap-south-1)
- **Cost Optimization**: 600 max tokens, 0.1 temperature, 2000 token context cap
- **Response Time**: ~300-500ms average (retrieval + generation)
- **Confidence Calibration**: Adaptive thresholds based on query complexity

## License

See [LICENSE](LICENSE) file.
