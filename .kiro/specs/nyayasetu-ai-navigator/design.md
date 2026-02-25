# NyayaSetu AI Navigator – Technical Design

## 1. System Overview

NyayaSetu AI is a production-grade, voice-first legal AI system designed to democratize access to consumer rights in India. This is not a prototype chatbot—it is a legally aware, governed AI system built for regulatory compliance, explainability, and inclusion.

### Core Design Principles

**Safety-First AI Governance:**
- The RAG Engine is strictly constrained to respond only using retrieved legal context from authoritative sources
- Multi-layer hallucination prevention with confidence scoring and entailment validation
- Every legal claim is traceable to specific sections of the Consumer Protection Act, 2019
- Low-confidence responses trigger mandatory human escalation, never incorrect guidance

**Regulatory Compliance by Design:**
- Full DPDP Act 2023 compliance with data minimization, consent management, and 30-day deletion workflows
- IT Act 2000 alignment with AES-256 encryption, audit logging, and breach notification procedures
- WCAG 2.1 AA accessibility verified through automated and manual testing
- All personal data stored within India (AWS ap-south-1 Mumbai region)

**Inclusion-First Architecture:**
- Voice-first interaction optimized for users with limited digital literacy
- Multilingual support (English, Hindi, regional languages) with <15% Word Error Rate target
- Low-bandwidth optimization for 2G networks (50-100 Kbps) using Opus codec compression
- Offline capability via Progressive Web App with service worker caching

**Production Readiness:**
- Configuration-driven jurisdiction thresholds updatable without code redeployment
- Comprehensive AI observability tracking citation accuracy (≥95%), hallucination rate (≤2%), and routing accuracy (≥95%)
- Progressive degradation architecture maintaining core functionality during partial failures
- Multi-region deployment with <4 hour RTO and <1 hour RPO

### Architecture Philosophy

5-layer architecture with clear separation of concerns:

```
┌─────────────────────────────────────────────────────┐
│  User (Voice/Text Input)                            │
└────────────────┬────────────────────────────────────┘
                 ↓
┌─────────────────────────────────────────────────────┐
│  Frontend Layer (PWA)                               │
│  • Voice capture + STT/TTS                          │
│  • Offline capability + draft storage               │
│  • Responsive design (320px-428px)                  │
└────────────────┬────────────────────────────────────┘
                 ↓
┌─────────────────────────────────────────────────────┐
│  Application Layer                                  │
│  • AI Orchestrator (intent classification)          │
│  • RAG Engine (retrieval + generation + citation)   │
│  • Grievance Router (config-driven thresholds)      │
│  • Complaint Drafter (template-based generation)    │
└────────────────┬────────────────────────────────────┘
                 ↓
┌─────────────────────────────────────────────────────┐
│  Data Layer                                         │
│  • Legal Knowledge Base (vectorized Act + rules)    │
│  • Vector Database (1536-dim embeddings)            │
│  • User Data Store (encrypted PostgreSQL)           │
│  • Audit Log Store (immutable logs, 90-day)         │
└────────────────┬────────────────────────────────────┘
                 ↓
┌─────────────────────────────────────────────────────┐
│  Response Delivery                                  │
│  • Legal text + citations + confidence score        │
│  • Audio synthesis (TTS)                            │
│  • Mechanism recommendations with explanations      │
└─────────────────────────────────────────────────────┘
```

All inter-service communication uses TLS 1.3. JWT-based authentication. RESTful APIs.

## 2. Component Architecture

**Frontend Layer**:
- Progressive Web App (React + TypeScript)
- Web Speech API with cloud STT/TTS fallback
- Service Worker for offline capability and draft storage
- Responsive mobile-first design (320px-428px)

**Application Layer**:
- **AI Orchestrator**: Central coordinator managing intent classification and context (Redis-backed)
- **RAG Engine**: Vector retrieval + LLM generation with mandatory citation enforcement
- **Complaint Drafter**: Guided workflow with template-based document generation
- **Grievance Router**: Configuration-driven threshold comparison and mechanism recommendation
- **Session Manager**: JWT tokens with OTP authentication, 24-hour session validity

**Data Layer**:
- **Legal Knowledge Base**: Consumer Protection Act 2019 chunked and vectorized (Pinecone/Weaviate)
- **Vector Database**: 1536-dimensional embeddings with cosine similarity search
- **User Data Store**: PostgreSQL with AES-256 encryption and row-level security
- **Audit Log Store**: Immutable logs with 90-day retention (CloudWatch/Elasticsearch)

**Integration Layer**:
- RESTful API Gateway with rate limiting (100 requests/minute per API key)
- National Consumer Helpline connector
- e-Daakhil integration adapter (when available)

**Infrastructure Layer**:
- Multi-region AWS deployment (Mumbai primary, Hyderabad DR)
- Containerized services with auto-scaling policies
- Multi-AZ database deployment with automated backups
- CDN for static assets with global edge caching


## 3. Core Flow: Voice Query → Legal Response

**End-to-End Pipeline**:

1. **Voice Capture**:
   - MediaRecorder API captures audio at 16kHz
   - Opus codec compression (<50KB per 10s clip)
   - WebRTC noise suppression

2. **Speech-to-Text**:
   - Stream to AWS Transcribe / Google Cloud Speech-to-Text
   - Real-time transcription with interim results
   - Fallback to text input if WER >30% or service unavailable

3. **Intent Classification**:
   - AI Orchestrator parses transcribed text
   - Rule-based classifier: `legal_query`, `complaint_draft`, `mechanism_recommendation`, `out_of_scope`
   - Confidence threshold 0.8 for automatic routing

4. **RAG Retrieval**:
   - Query → OpenAI text-embedding-ada-002 → 1536-dim vector
   - Semantic search in vector DB for top-5 similar chunks (cosine similarity)
   - Retrieve legal text with metadata (section number, act name)

5. **Response Generation**:
   - Prompt template enforces source-grounding: "Answer ONLY using provided context"
   - GPT-4 / Claude with temperature=0.3 for deterministic responses
   - Extract citations from generated text

6. **Citation Validation**:
   - Verify all cited sections exist in retrieved context
   - Calculate confidence score: 0.4×retrieval_conf + 0.3×llm_conf + 0.3×citation_coverage
   - If confidence <0.7: add disclaimer, suggest professional consultation

7. **Hallucination Check**:
   - Entailment model verifies generated claims follow from retrieved text
   - If entailment score <0.8: flag for human review, add disclaimer

8. **Text-to-Speech**:
   - AWS Polly / Google TTS with neural voices (Hindi: Aditi, English: Joanna)
   - Progressive audio streaming (start playback before full download)
   - Synchronized text highlighting for accessibility

9. **Response Delivery**:
   - JSON response with text, audio URL, citations, confidence score
   - Conversation context stored in Redis (last 10 turns, 24-hour TTL)

**Failure Handling**:
- Vector DB down → Cached responses for common queries
- No retrieval results → Explicit "out of scope" message
- STT failure → Automatic fallback to text input
- LLM API failure → Retry 3× with exponential backoff

## 4. Grievance Routing Logic

**Configuration-Driven Thresholds**:

Jurisdiction thresholds stored in PostgreSQL `config` table, NOT hardcoded:

```sql
CREATE TABLE config (
  config_key VARCHAR(100) PRIMARY KEY,
  config_value JSONB NOT NULL,
  effective_date DATE NOT NULL,
  updated_by VARCHAR(100),
  version INT DEFAULT 1
);
```

Current thresholds (as of 2024):
- District Commission: up to ₹1 crore
- State Commission: ₹1 crore to ₹10 crore
- National Commission: above ₹10 crore

**Routing Decision Flow**:

1. **Issue Analysis**:
   - Extract issue type (defective product, deficient service, unfair trade practice)
   - Extract transaction value from user input
   - Determine jurisdiction (location-based)

2. **Threshold Comparison**:
   - Query config DB for current thresholds (cached in Redis, 1-hour TTL)
   - Compare transaction value against thresholds
   - Determine appropriate Consumer Commission tier

3. **Mechanism Recommendation**:
   - National Consumer Helpline (NCH): All issues, especially for guidance/mediation
   - e-Daakhil: Online filing when portal available
   - Consumer Commission: Judicial intervention, routed to correct tier

4. **Multi-Option Presentation**:
   - If multiple mechanisms applicable (e.g., borderline value): present all with pros/cons
   - If out of jurisdiction (criminal fraud, civil dispute): flag and suggest alternatives

5. **Explanation Generation**:
   - Generate reasoning based on issue characteristics
   - Example: "Transaction value ₹25,000 falls under District Commission jurisdiction (up to ₹1 crore)"

**Configuration Update Workflow**:

1. Administrator submits threshold update via secure API
2. Legal Reviewer approves update through approval workflow
3. On effective date, configuration automatically updated
4. Cache invalidated, all services immediately pick up new values
5. Audit log records: old_value, new_value, updated_by, timestamp, version

**Hot Configuration Updates**: Legal amendments applied without code redeployment or system downtime.


## 5. Complaint Drafting Pipeline

**Workflow State Machine**:

States: `start` → `collect_complainant` → `collect_respondent` → `collect_transaction` → `collect_issue` → `collect_relief` → `review` → `finalize`

**Information Collection**:
- Complainant: name, address, phone, email
- Respondent: business name, address, contact
- Transaction: date, amount, invoice number, payment method
- Issue: description (free text), category (dropdown), timeline
- Relief: compensation amount, replacement, refund, other

**Validation Rules**:
- Phone: 10-digit Indian mobile (6-9 prefix)
- Email: RFC 5322 compliant
- Amount: positive, max ₹10 crore
- Date: not future, within 2 years (limitation period)

**Document Generation**:

1. **Template Selection**: Jinja2 template based on Consumer Commission filing requirements
2. **Legal Provision Insertion**: Auto-select relevant sections from Consumer Protection Act based on issue category
3. **PDF Generation**: WeasyPrint / ReportLab for formatted document
4. **Plain Text Export**: For copy-paste into online forms

**Draft Storage**:
- PostgreSQL with user_id foreign key
- Auto-save every 30 seconds during collection
- Expire after 180 days of inactivity (DPDP compliance)

**Example Generated Complaint Structure**:

```
BEFORE THE DISTRICT CONSUMER DISPUTES REDRESSAL COMMISSION

Complaint under Section 35 of the Consumer Protection Act, 2019

Complainant: [Name, Address, Contact]
Respondent: [Business Name, Address]

Facts of the Case:
[User-provided description]

Transaction Details:
Date: [Date], Amount: ₹[Amount], Invoice: [Number]

Legal Provisions:
Section 2(7): Definition of Consumer
Section 2(47): Definition of Unfair Trade Practice
[Auto-selected based on issue category]

Relief Sought:
[User-specified relief]

Signature: [Digital/Manual]
Date: [Auto-filled]
```

## 6. AI Governance and Safety

**Source Grounding Enforcement**:
- Every factual claim must cite a Source_Document from the Legal_Knowledge_Base
- The RAG Engine is strictly constrained to respond only using retrieved legal context
- Prompt template enforces: "Answer ONLY using provided context. Do not generate information beyond retrieved documents."
- When no relevant source exists, the system explicitly states "I don't have information on this" rather than generating ungrounded content

**Confidence Scoring Model**:

```
confidence = 0.4 × retrieval_confidence + 0.3 × llm_confidence + 0.3 × citation_coverage

retrieval_confidence = avg(top-3 cosine similarity scores)
llm_confidence = avg(token probabilities from LLM)
citation_coverage = (claims with citations) / (total factual claims)
```

Response thresholds:
- High confidence (≥0.9): Strong affirmative language
- Medium confidence (0.7-0.9): Qualifying language ("Based on available information...")
- Low confidence (<0.7): Explicit disclaimer + mandatory professional consultation recommendation

**Hallucination Prevention Pipeline**:

Post-generation validation enforces correctness:
1. Extract all factual claims from generated response
2. Verify each claim against retrieved context using entailment model
3. If entailment score <0.8: flag for human review and add disclaimer
4. Log all flagged responses for monthly audit and model improvement

**Real-Time AI Monitoring Dashboard**:

Continuously tracked metrics:
- Citation accuracy rate (target: ≥95%)
- Hallucination rate (target: ≤2%)
- Low-confidence response rate (target: <15%)
- Retrieval relevance (target: top-3 relevant ≥90%)
- Speech-to-text WER per language (target: ≤15%)
- Routing accuracy (target: false routing ≤5%)

Monthly AI performance reports generated automatically with trend analysis and corrective action recommendations.

**Human Escalation Protocol**:

Automatic escalation triggers:
- User explicitly requests human review
- Confidence score <0.7
- Complex case beyond system capability
- Unusual patterns or potential errors detected

SLA commitments: Acknowledge within 4 hours, provide human review guidance within 24 hours.


## 7. Security and Compliance Architecture

**Encryption Standards**:
- At rest: AES-256 encryption (PostgreSQL Transparent Data Encryption, S3 Server-Side Encryption with KMS)
- In transit: TLS 1.3 for all connections with HSTS enforcement
- Application-level: Phone numbers hashed using SHA-256 with salt, JWT secrets stored in AWS Secrets Manager

**Authentication & Authorization**:
- OTP-based authentication (passwordless for accessibility)
- JWT tokens valid 24 hours with httpOnly cookies
- Role-Based Access Control (RBAC):
  - End User: Access only to own data
  - Administrator: View audit logs, update configuration (all actions logged)
  - Legal Reviewer: Approve knowledge base updates
  - Auditor: Read-only access to logs and compliance reports

**Data Isolation and Privacy**:
- PostgreSQL row-level security enforces strict user data isolation
- Users cannot access other users' drafts or personal information
- Cross-user access attempts logged and blocked (403 Forbidden response)
- All data stored within India (AWS Mumbai region) for DPDP Act compliance

**Consent Management**:
- Explicit consent required before collecting personal data
- Granular consent options (essential services vs. optional analytics)
- Consent records maintained with: user_id, consent_type, action (granted/withdrawn), timestamp
- Consent withdrawal triggers immediate data deletion workflow

**Data Deletion Workflows**:
- User-initiated deletion: Complete data erasure within 30 days (DPDP Act requirement)
- Automated expiration: Drafts after 180 days inactivity, sessions after 24 hours
- Audit logs: 90-day retention, then archived to S3 Glacier for 5 years

**Threat Mitigation**:
- SQL Injection: Parameterized queries and ORM usage
- XSS: Content Security Policy headers and React JSX automatic escaping
- CSRF: CSRF tokens and SameSite cookie attributes
- DoS: Rate limiting (100 req/min), AWS WAF, CloudFront DDoS protection
- MITM: TLS 1.3 with HSTS header enforcement

**Security Monitoring**:
- AWS GuardDuty for threat detection and anomaly identification
- CloudWatch alarms for unusual access patterns
- Quarterly penetration testing by external security firm

## 8. Deployment and Scalability

**Cloud Topology**:
- Primary region: AWS Mumbai (ap-south-1)
- Disaster recovery: AWS Hyderabad (ap-south-2)
- Multi-availability zone deployment for high availability

**Container Orchestration**:
- Serverless container platform (ECS Fargate)
- Service resource allocation:
  - AI Orchestrator: 2 vCPU, 4 GB RAM, minimum 3 tasks
  - RAG Engine: 4 vCPU, 8 GB RAM, minimum 5 tasks
  - Complaint Drafter: 2 vCPU, 4 GB RAM, minimum 2 tasks
  - Grievance Router: 1 vCPU, 2 GB RAM, minimum 2 tasks

**Auto-Scaling Policies**:
- Target CPU utilization: 70%
- Scale-out trigger: CPU >80%
- Scale-in trigger: CPU <50%
- Step scaling for traffic spikes: CPU >90% → add 50% capacity
- Minimum 2 tasks per service (high availability)
- Maximum 20 tasks per service (cost control)
- Cooldown period: 300 seconds

**Load Balancing**:
- Application Load Balancer in public subnets
- Health checks: HTTP GET /health every 30 seconds
- Sticky sessions enabled for conversation continuity

**Database Scaling**:
- Managed PostgreSQL with multi-AZ deployment
- Auto-scaling storage: 100 GB baseline → 1 TB maximum
- Read replicas: 2 instances for read-heavy workloads

**Multi-Region Failover**:
- Active-passive configuration
- Cross-region database replication (replication lag <5 seconds)
- Cross-region object storage replication (<15 minutes for 99.99% of objects)
- DNS-based health checks trigger automatic failover
- Recovery Time Objective (RTO): <4 hours
- Recovery Point Objective (RPO): <1 hour

**Backup Strategy**:
- Automated daily database backups (30-day retention)
- Point-in-time recovery capability (up to 5 minutes before failure)
- Object storage versioning (last 10 versions retained)
- Lifecycle policies: Archive to Glacier after 90 days
- Infrastructure as Code (Terraform) version-controlled in Git

**Monitoring and Alerting**:
- CloudWatch metrics: CPU, memory, latency, error rate
- Distributed tracing for end-to-end request flow analysis
- Critical alerts: PagerDuty integration
- Warning alerts: Slack integration
- SLA targets: 99% uptime, 95% of requests <3 seconds latency


## 9. Key Technical Innovations

### 1. Voice-First Legal AI for Low-Literacy Users

**Innovation**: Conversational AI interface optimized for users with limited digital literacy, using voice as primary modality.

**Technical Approach**:
- Real-time speech-to-text with noise filtering (WebRTC)
- Multilingual support (English, Hindi, 5+ regional languages)
- Automatic fallback to text input when voice fails
- Low-bandwidth optimization (Opus codec, <50KB per 10 seconds)
- Offline capability via PWA service worker

**Why This Matters**: Generic legal chatbots assume text literacy and high bandwidth. NyayaSetu democratizes access for 500M+ Indians with limited English/digital literacy, making legal information accessible to those who need it most.

### 2. Configurable Jurisdiction Engine

**Innovation**: Legal jurisdiction thresholds stored in database configuration, updatable without code redeployment.

**Technical Approach**:
- PostgreSQL config table with version control
- Admin API for threshold updates with legal reviewer approval workflow
- Redis caching (1-hour TTL) for performance
- Complete audit trail: old_value, new_value, updated_by, timestamp
- Immediate propagation via cache invalidation

**Why This Matters**: Traditional legal systems require code changes and redeployment for legal amendments. NyayaSetu adapts to Consumer Protection Act amendments within hours, not weeks, with zero downtime.

### 3. Source-Grounded RAG with Hallucination Guardrails

**Innovation**: Multi-layer hallucination prevention ensuring all legal claims are traceable to authoritative documents.

**Technical Approach**:
- Mandatory citation requirement enforced in prompt template
- Confidence scoring: retrieval + LLM + citation coverage
- Post-generation entailment check (BERT-based validation)
- Low-confidence responses flagged with disclaimers
- Human escalation for confidence <0.7

**Why This Matters**: Generic AI chatbots hallucinate legal advice, creating liability and user harm. NyayaSetu's citation accuracy ≥95% and hallucination rate ≤2% make it trustworthy for legal guidance where accuracy is non-negotiable.

### 4. Comprehensive AI Observability

**Innovation**: Real-time monitoring dashboard tracking AI quality metrics, not just infrastructure metrics.

**Technical Approach**:
- Citation accuracy tracking (manual audit sampling)
- Hallucination detection (automated entailment checks)
- Retrieval relevance measurement (test set evaluation)
- Speech-to-text WER per language and accent
- Routing accuracy audits (monthly sampling)
- Automated monthly AI performance reports

**Why This Matters**: Most AI systems monitor uptime and latency but ignore output quality. NyayaSetu proactively detects AI quality degradation, enabling continuous improvement through data-driven insights before users are impacted.

### 5. Progressive Degradation Architecture

**Innovation**: System maintains core functionality even when components fail, with clear user communication.

**Technical Approach**:
- Degradation levels: Full → Minor → Moderate → Severe → Maintenance
- Automatic fallbacks: Voice → Text, RAG → Cached responses, Config DB → Cached thresholds
- Status banner informs users of degraded features
- Circuit breakers prevent cascade failures
- Graceful error messages with alternative contact methods (NCH helpline)

**Why This Matters**: Generic systems fail completely or silently degrade. NyayaSetu maintains 99% uptime even with partial failures, ensuring users always have a path to assistance—critical for vulnerable populations with limited alternatives.

### 6. DPDP Act 2023 Compliance by Design

**Innovation**: Data protection built into architecture from day one, not retrofitted.

**Technical Approach**:
- Data minimization: Collect only essential data
- Consent management: Granular, auditable consent records
- Automated data deletion workflow: 30-day deletion guarantee
- Comprehensive audit logging: All data access events logged
- Data residency: All personal data stored in India (AWS Mumbai)

**Why This Matters**: Most AI systems bolt on compliance after launch, creating vulnerabilities. NyayaSetu's compliance-by-design approach ensures full DPDP Act 2023 adherence, building user trust through transparency and demonstrating responsible AI governance.

### 7. Multilingual Legal Knowledge Base

**Innovation**: Consumer Protection Act chunked, vectorized, and indexed for semantic search across languages.

**Technical Approach**:
- Document chunking: 500-1000 tokens per chunk, section-aligned
- Vector embeddings: OpenAI text-embedding-ada-002 (1536-dimensional)
- Metadata tagging: section_number, act_name, effective_date
- Version control: Semantic versioning with 5-year archive
- Update workflow: Source validation → Legal review → Embedding regeneration → Regression testing

**Why This Matters**: Generic legal chatbots use unstructured documents or manual Q&A. NyayaSetu's semantic search retrieves relevant legal text in <100ms with 90%+ accuracy, supporting legal amendments without system downtime.

### 8. Accessibility-First Design

**Innovation**: WCAG 2.1 AA compliance verified through automated and manual testing.

**Technical Approach**:
- Semantic HTML with ARIA labels and keyboard navigation
- Screen reader compatibility (JAWS, NVDA, VoiceOver)
- Color contrast ratios: 4.5:1 (normal text), 3:1 (large text)
- Touch targets: minimum 44×44 CSS pixels
- Automated testing: axe-core integrated in CI/CD pipeline
- Quarterly manual audits by accessibility specialist

**Why This Matters**: Most legal tech ignores accessibility, excluding 70M+ Indians with disabilities. NyayaSetu's accessibility-first approach ensures inclusive access, expanding reach to underserved populations and demonstrating commitment to digital inclusion.


## 10. API Design

### REST API Structure

**Base URL**: `https://api.nyayasetu.gov.in/v1`

**Authentication**: JWT token in `Authorization: Bearer <token>` header

**Core Endpoints**:

```
POST /auth/request-otp
POST /auth/verify-otp
POST /auth/logout

POST /query
  Request: { query_text, language, session_id }
  Response: { response_text, response_audio_url, citations, confidence }

POST /complaint/draft
GET /complaint/draft/{draft_id}
POST /complaint/finalize/{draft_id}

POST /grievance/recommend
  Request: { issue_category, transaction_amount, issue_description }
  Response: { recommendations[], confidence }

GET /user/data
POST /user/delete

GET /admin/config
PUT /admin/config/{config_key}
```

**Rate Limiting**:
- Per-user: 60 req/min (query), 10 req/min (complaint draft)
- Per-API-key: 100 req/min, 10,000 req/day
- Rate limit headers: X-RateLimit-Limit, X-RateLimit-Remaining, X-RateLimit-Reset

**Error Response Format**:

```json
{
  "status": "error",
  "error": {
    "code": "ERROR_CODE",
    "message": "Human-readable error message",
    "details": { "field": "field_name", "provided_value": "..." }
  },
  "metadata": { "request_id": "uuid", "timestamp": "ISO8601" }
}
```

**HTTP Status Codes**:
- 200: Success
- 400: Bad request (validation error)
- 401: Unauthorized (invalid/expired token)
- 403: Forbidden (insufficient permissions)
- 429: Too many requests (rate limit)
- 500: Internal server error
- 503: Service unavailable

## 11. Data Architecture

### Legal Knowledge Base

**Content**: Consumer Protection Act 2019, E-Commerce Rules 2020, Direct Selling Rules 2021, official notifications

**Processing Pipeline**:
1. Ingestion: Load PDFs from official government sources
2. Text extraction: pdfplumber / BeautifulSoup
3. Chunking: 500-1000 tokens, section-aligned, 100-token overlap
4. Metadata tagging: document_name, section_number, effective_date
5. Embedding generation: OpenAI text-embedding-ada-002
6. Vector storage: Pinecone/Weaviate with metadata

**Version Control**:
- Semantic versioning (v1.2.0)
- Update workflow: Source validation → Legal review → Embedding regeneration → Regression testing → Approval → Deployment
- Previous versions archived 5 years
- All responses tagged with KB version used

### Database Schema (PostgreSQL)

```sql
-- Users
CREATE TABLE users (
  user_id UUID PRIMARY KEY,
  phone_hash VARCHAR(64) UNIQUE,
  language VARCHAR(10),
  consent_given BOOLEAN,
  consent_timestamp TIMESTAMP
);

-- Complaint drafts
CREATE TABLE complaint_drafts (
  draft_id UUID PRIMARY KEY,
  user_id UUID REFERENCES users(user_id) ON DELETE CASCADE,
  complainant_data JSONB,
  respondent_data JSONB,
  transaction_data JSONB,
  issue_description TEXT,
  relief_sought TEXT,
  status VARCHAR(20),
  expires_at TIMESTAMP DEFAULT NOW() + INTERVAL '180 days'
);

-- Configuration
CREATE TABLE config (
  config_key VARCHAR(100) PRIMARY KEY,
  config_value JSONB NOT NULL,
  effective_date DATE NOT NULL,
  updated_by VARCHAR(100),
  version INT DEFAULT 1
);

-- Configuration history
CREATE TABLE config_history (
  history_id UUID PRIMARY KEY,
  config_key VARCHAR(100),
  old_value JSONB,
  new_value JSONB,
  version INT,
  updated_by VARCHAR(100),
  updated_at TIMESTAMP,
  approved_by VARCHAR(100)
);
```

## 12. Testing Strategy

### Dual Testing Approach

**Property-Based Testing** (Hypothesis / fast-check):
- 51 correctness properties derived from requirements
- Minimum 100 iterations per property test
- Tests universal behaviors across randomized inputs
- Examples:
  - Property 26: Session ID uniqueness across 10,000 sessions
  - Property 19: Tier determination correctness for all transaction values
  - Property 8: Citation requirement for all legal responses

**Unit Testing** (pytest / Vitest):
- Specific examples and edge cases
- Integration points between components
- Error conditions and validation
- Focus: Concrete scenarios, not comprehensive input coverage

**Coverage Goals**:
- Unit test coverage: ≥80% line coverage
- Critical paths: ≥95% (authentication, RAG, routing)
- All 51 correctness properties implemented

**CI/CD Pipeline**:
1. On commit: Lint, unit tests, property tests, accessibility tests
2. On PR: Integration tests, security scanning (SAST), code review
3. On merge: Deploy to staging, E2E tests, performance tests
4. On release: Deploy to production (blue-green), smoke tests, 30-min bake time

## 13. Failure Handling and Recovery

**Failure Scenarios & Recovery Strategies**:

| Failure Scenario | Recovery Strategy |
|-----------------|-------------------|
| Vector DB unavailable | Serve cached responses for common queries, retry 3× with exponential backoff |
| No retrieval results | Return explicit "out of scope" message with alternative resources |
| Low confidence (<0.7) | Add disclaimer, suggest professional consultation, log for review |
| STT service failure | Automatic fallback to text input with user notification |
| Config DB unavailable | Use cached thresholds (1-hour TTL) with disclaimer about potential staleness |
| LLM API failure | Retry 3× with exponential backoff, then return service unavailable |
| Session expired | Prompt re-authentication with session state preservation |
| Rate limit exceeded | Return 429 response with retry_after header |

**Progressive Degradation Levels**:
- Level 0 (Full Service): All features operational
- Level 1 (Minor Degradation): Non-critical features disabled (analytics, optional telemetry)
- Level 2 (Moderate Degradation): Voice input disabled, text-only mode active
- Level 3 (Severe Degradation): Only cached responses available, no new RAG queries
- Level 4 (Maintenance Mode): Read-only access, display maintenance banner

**User Communication Strategy**: Status banner clearly explains degraded features and provides alternative contact methods (National Consumer Helpline phone number, email support).

## 14. Assumptions and Constraints

**Technical Assumptions**:
- Users have minimum 2G network connectivity
- Modern bro    wsers supported (Chrome 90+, Safari 14+, Firefox 88+)
- Cloud services maintain 99.9% uptime SLA
- Speech-to-text services achieve >85% accuracy for Indian English and Hindi

**System Constraints**:
- Latency requirement: RAG responses ≤3 seconds (95th percentile)
- Cost constraint: LLM API costs <₹10 per user per month
- Bandwidth constraint: Must function on 2G networks (50-100 Kbps)
- Data residency: All personal data stored within India (DPDP Act compliance)
- Budget constraint: ₹5 crore total project budget

**External Dependencies**:
- OpenAI/Anthropic APIs for large language models
- AWS cloud services for infrastructure
- AWS Transcribe/Polly for speech services
- Pinecone/Weaviate for vector database
- Government portals (National Consumer Helpline, e-Daakhil) for integration

---

## Summary

NyayaSetu AI is a production-ready, voice-first legal AI system designed for Indian citizens. The architecture balances innovation (source-grounded RAG, configurable jurisdiction engine, comprehensive AI observability) with pragmatism (fail-safe defaults, progressive degradation, regulatory compliance by design). 

Key differentiators: Multi-layer hallucination prevention with ≥95% citation accuracy, configuration-driven legal thresholds updatable without code deployment, accessibility-first design with WCAG 2.1 AA compliance, and DPDP Act 2023 compliance built into the architecture from day one.

The system is engineered to scale to millions of users while maintaining legal accuracy, regulatory compliance, and inclusive access for users with limited digital literacy or disabilities.

