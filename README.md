# NyayaSetu AI – Intelligent Consumer Law Assistant

> AI-powered legal assistance for Consumer Protection Act, 2019 using Retrieval-Augmented Generation

---

## Problem Statement

Indian citizens struggle to understand complex legal language in consumer protection laws, making it difficult to know their rights and access grievance redressal mechanisms effectively.

---

## Solution

NyayaSetu AI provides instant, source-grounded answers to consumer law questions using RAG (Retrieval-Augmented Generation) powered by Amazon Bedrock and Claude 3 Haiku.

---

## Architecture

- **Embedding Model**: sentence-transformers/all-MiniLM-L6-v2 (384-dim vectors)
- **Knowledge Base**: 111 chunks from Consumer Protection Act, 2019
- **Retrieval**: Semantic search with cosine similarity (top-3)
- **Generation**: Amazon Bedrock Claude 3 Haiku (ap-south-1)
- **Backend**: FastAPI with async support
- **Frontend**: Premium web UI with responsive design
- **Deployment**: AWS EC2 (planned) + S3 static hosting (planned)

---

## Tech Stack

**AI/ML:**
- Amazon Bedrock (Claude 3 Haiku)
- sentence-transformers
- NumPy

**Backend:**
- FastAPI
- Uvicorn
- Pydantic

**Frontend:**
- HTML5/CSS3/JavaScript
- Fetch API
- Responsive design

**Document Processing:**
- pdfplumber
- PyPDF2

**Infrastructure:**
- AWS Bedrock (ap-south-1)
- AWS EC2 (deployment)
- AWS S3 (static hosting)

---

## Local Setup

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Configure AWS (optional - for Bedrock):**
   ```bash
   aws configure
   # Region: ap-south-1
   # Enable Claude 3 Haiku in Bedrock console
   ```

3. **Start backend:**
   ```bash
   uvicorn src.api.main:app --reload
   ```

4. **Start frontend:**
   ```bash
   python -m http.server 3000 --directory frontend
   ```

5. **Access application:**
   - Frontend: `http://localhost:3000`
   - API: `http://localhost:8000`
   - API Docs: `http://localhost:8000/docs`

---

## Project Structure

```
NyayaSetu-AI/
├── src/
│   ├── api/
│   │   └── main.py              # FastAPI backend
│   └── rag/
│       ├── bedrock_generator.py # Bedrock integration
│       ├── rag_kb_setup.py      # Knowledge base builder
│       ├── query_single.py      # CLI query tool
│       └── validate_setup.py    # Setup validator
├── frontend/
│   ├── index.html               # Web interface
│   ├── styles.css               # Premium UI styles
│   └── script.js                # Frontend logic
├── knowledge_base/
│   ├── knowledge_base.json      # Embeddings + metadata
│   ├── metadata_index.json      # Section index
│   └── stats.json               # KB statistics
├── data/raw/
│   └── CPA2019.pdf              # Source document
└── requirements.txt
```

---

## Current Status

- ✅ Local MVP operational
- ✅ RAG pipeline complete (retrieval + generation)
- ✅ Bedrock integration ready (Claude 3 Haiku)
- ✅ Premium web UI with responsive design
- ✅ Knowledge base with 111 chunks, 8 chapters, 99 sections
- ✅ Cost-optimized (max_tokens=600, temperature=0.1)
- ✅ Graceful fallback to retrieval-only mode
- 📋 AWS deployment planned

---

## API Usage

**Endpoint:** `POST /ask`

**Request:**
```json
{
  "question": "What is a consumer?"
}
```

**Response:**
```json
{
  "answer": "Based on the Consumer Protection Act, 2019...",
  "sources": [
    {
      "act": "Consumer Protection Act, 2019",
      "chapter": "Chapter I: Preliminary",
      "section": "Section 2(7)",
      "similarity": 0.89
    }
  ],
  "confidence": "High",
  "processing_time_ms": 320
}
```

---

## Key Features

- **Source-Grounded Responses**: Every answer cites Act, Chapter, and Section
- **Semantic Search**: Finds relevant legal text using embeddings
- **Cost-Optimized**: ~₹0.02 per query with Claude 3 Haiku
- **Fast Response**: ~300-500ms average response time
- **Graceful Degradation**: Works without Bedrock (retrieval-only mode)
- **Premium UI**: Professional legal-tech SaaS design

---

## Disclaimer

NyayaSetu AI provides informational guidance based on the Consumer Protection Act, 2019. It does not constitute legal advice. Consult qualified legal professionals for specific legal matters.

---

## License

See [LICENSE](LICENSE) file.

---

**Built for AI For Bharat Hackathon 2026**
