# NyayaSetu AI Navigator – Technical Design

## Overview

Production-grade, voice-first legal AI system for Indian consumer rights. RAG-based with multi-layer hallucination prevention, configurable jurisdiction engine, and DPDP Act 2023 compliance.

**Core Principles:**
- Source-grounded responses with mandatory citations (≥95% accuracy)
- Configuration-driven legal thresholds (zero-downtime updates)
- Voice-first for low-literacy users (multilingual, low-bandwidth)
- Regulatory compliance by design (DPDP Act 2023, IT Act 2000, WCAG 2.1 AA)

**Architecture:**

```
User (Voice/Text)
    ↓
Frontend (PWA: Voice capture, STT/TTS, offline capability)
    ↓
Application Layer (AI Orchestrator, RAG Engine, Complaint Drafter, Grievance Router)
    ↓
Data Layer (Legal KB, Vector DB, PostgreSQL, Audit Logs)
    ↓
Response (Legal text + citations + confidence + audio)
```

## Architecture

### Frontend Layer
- Progressive Web App (React + TypeScript)
- Web Speech API with cloud STT/TTS fallback
- Service Worker for offline capability and draft storage
- Responsive mobile-first (320px-428px), WCAG 2.1 AA compliant

### Application Layer

**AI Orchestrator:**
- Intent classification: `legal_query`, `complaint_draft`, `mechanism_recommendation`, `out_of_scope`
- Redis-backed session management (24-hour TTL, last 10 turns)
- Confidence threshold 0.8 for automatic routing

**RAG Engine:**
- Vector retrieval: OpenAI text-embedding-ada-002 (1536-dim), top-5 cosine similarity
- LLM generation: GPT-4/Claude, temperature=0.3, source-grounding enforced
- Citation validation + entailment check (BERT-based, threshold 0.8)
- Confidence scoring: `0.4×retrieval + 0.3×llm + 0.3×citation_coverage`
- Low confidence (<0.7): disclaimer + human escalation

**Complaint Drafter:**
- State machine: `start → collect_complainant → collect_respondent → collect_transaction → collect_issue → collect_relief → review → finalize`
- Jinja2 templates, WeasyPrint PDF generation
- Auto-save every 30 seconds, 180-day expiration

**Grievance Router:**
- Configuration-driven thresholds (PostgreSQL config table, Redis 1-hour cache)
- Jurisdiction determination: District (≤₹1 crore), State (₹1-10 crore), National (>₹10 crore)
- Multi-option presentation with reasoning

### Data Layer

**Legal Knowledge Base:**
- Consumer Protection Act 2019, E-Commerce Rules 2020, Direct Selling Rules 2021
- Chunking: 500-1000 tokens, section-aligned, 100-token overlap
- Metadata: section_number, act_name, effective_date
- Semantic versioning with 5-year archive

**Vector Database:**
- Pinecone/Weaviate with 1536-dim embeddings
- Cosine similarity search, <100ms retrieval

**User Data Store:**
- PostgreSQL with AES-256 encryption, row-level security
- Multi-AZ deployment, automated backups (30-day retention)

**Audit Log Store:**
- Immutable logs, 90-day retention (CloudWatch/Elasticsearch)
- All data access events logged

### Integration Layer
- RESTful API Gateway with rate limiting (100 req/min per API key)
- National Consumer Helpline connector
- e-Daakhil integration adapter

### Infrastructure Layer
- Multi-region AWS (Mumbai primary, Hyderabad DR)
- ECS Fargate with auto-scaling (CPU target 70%)
- Multi-AZ PostgreSQL with read replicas
- RTO <4 hours, RPO <1 hour

## Components and Interfaces

### Voice Query → Legal Response Pipeline

1. **Voice Capture:** MediaRecorder API, 16kHz, Opus codec (<50KB/10s), WebRTC noise suppression
2. **STT:** AWS Transcribe/Google Cloud Speech-to-Text, real-time, fallback to text if WER >30%
3. **Intent Classification:** Rule-based, confidence threshold 0.8
4. **RAG Retrieval:** Query embedding → vector search → top-5 chunks
5. **Response Generation:** Prompt enforces source-grounding, temperature=0.3
6. **Citation Validation:** Verify all citations exist in retrieved context
7. **Hallucination Check:** Entailment model, threshold 0.8, flag if below
8. **TTS:** AWS Polly/Google TTS, progressive streaming
9. **Response Delivery:** JSON with text, audio URL, citations, confidence

**Failure Handling:**
- Vector DB down → Cached responses
- No retrieval → "Out of scope" message
- STT failure → Text input fallback
- LLM API failure → 3× retry with exponential backoff

### Grievance Routing Logic

**Configuration Schema:**

```sql
CREATE TABLE config (
  config_key VARCHAR(100) PRIMARY KEY,
  config_value JSONB NOT NULL,
  effective_date DATE NOT NULL,
  updated_by VARCHAR(100),
  version INT DEFAULT 1
);

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

**Routing Flow:**
1. Extract issue type, transaction value, jurisdiction
2. Query config DB for thresholds (Redis cached, 1-hour TTL)
3. Compare value against thresholds
4. Determine Consumer Commission tier
5. Recommend mechanisms: NCH (all), e-Daakhil (online), Consumer Commission (judicial)
6. Generate reasoning explanation

**Configuration Update:** Admin API → Legal reviewer approval → Effective date → Auto-update → Cache invalidation → Audit log

### Complaint Drafting

**Information Collection:**
- Complainant: name, address, phone, email
- Respondent: business name, address, contact
- Transaction: date, amount, invoice, payment method
- Issue: description, category, timeline
- Relief: compensation, replacement, refund, other

**Validation:**
- Phone: 10-digit Indian mobile (6-9 prefix)
- Email: RFC 5322 compliant
- Amount: positive, max ₹10 crore
- Date: not future, within 2 years

**Document Structure:**

```
BEFORE THE DISTRICT CONSUMER DISPUTES REDRESSAL COMMISSION
Complaint under Section 35 of the Consumer Protection Act, 2019

Complainant: [Name, Address, Contact]
Respondent: [Business Name, Address]

Facts: [User description]
Transaction: Date, Amount, Invoice
Legal Provisions: [Auto-selected sections]
Relief Sought: [User-specified]

Signature, Date
```

## Data Models

### Database Schema

```sql
CREATE TABLE users (
  user_id UUID PRIMARY KEY,
  phone_hash VARCHAR(64) UNIQUE,
  language VARCHAR(10),
  consent_given BOOLEAN,
  consent_timestamp TIMESTAMP
);

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
```

### API Design

**Base URL:** `https://api.nyayasetu.gov.in/v1`

**Authentication:** JWT in `Authorization: Bearer <token>` header

**Endpoints:**

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

**Rate Limiting:**
- Per-user: 60 req/min (query), 10 req/min (complaint)
- Per-API-key: 100 req/min, 10,000 req/day

**Error Format:**

```json
{
  "status": "error",
  "error": {
    "code": "ERROR_CODE",
    "message": "Human-readable message",
    "details": { "field": "field_name", "provided_value": "..." }
  },
  "metadata": { "request_id": "uuid", "timestamp": "ISO8601" }
}
```

**Status Codes:** 200 (success), 400 (bad request), 401 (unauthorized), 403 (forbidden), 429 (rate limit), 500 (server error), 503 (unavailable)

## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system—a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*

### Property 1: Speech-to-Text Accuracy
*For any* voice input in supported languages, the Word Error Rate SHALL be ≤15%
**Validates: Requirements 1.1**

### Property 2: Citation Requirement
*For any* legal query response, all factual claims SHALL cite specific Source_Documents with section references
**Validates: Requirements 2.2**

### Property 3: Out-of-Scope Detection
*For any* query without relevant legal information, the system SHALL return an explicit "out of scope" message
**Validates: Requirements 2.3**

### Property 4: Citation Accuracy
*For any* generated response, citation accuracy SHALL be ≥95%
**Validates: Requirements 2.4**

### Property 5: Hallucination Rate
*For any* set of responses, hallucination rate SHALL be ≤2%
**Validates: Requirements 2.5**

### Property 6: Low Confidence Flagging
*For any* response with confidence <0.7, the system SHALL flag as uncertain and suggest professional consultation
**Validates: Requirements 2.6**

### Property 7: Context Retention
*For any* follow-up question within a session, the system SHALL maintain context from previous messages
**Validates: Requirements 3.2**

### Property 8: Mechanism Recommendation
*For any* consumer issue with transaction value and jurisdiction, the Grievance Router SHALL recommend appropriate mechanisms
**Validates: Requirements 4.2**

### Property 9: Recommendation Explanation
*For any* mechanism recommendation, the system SHALL explain why that mechanism is appropriate
**Validates: Requirements 4.3**

### Property 10: Configurable Thresholds
*For any* threshold update, changes SHALL be version-controlled and logged
**Validates: Requirements 4.6**

### Property 11: Routing Accuracy
*For any* set of grievance routing decisions, false routing rate SHALL be ≤5%
**Validates: Requirements 4.7**

### Property 12: Complaint Information Collection
*For any* complaint drafting session, the system SHALL collect complainant, respondent, transaction, issue, and relief information
**Validates: Requirements 5.2**

### Property 13: Complaint Document Generation
*For any* completed information collection, the system SHALL generate a structured complaint document
**Validates: Requirements 5.3**

### Property 14: JWT Token Validity
*For any* authenticated user, JWT token SHALL be valid for 24 hours
**Validates: Requirements 6.1**

### Property 15: Session Restoration
*For any* active session, returning users SHALL have conversation context and drafts restored
**Validates: Requirements 6.4**

### Property 16: Response Latency
*For any* user query, 95% of responses SHALL be returned within 3 seconds
**Validates: Requirements 7.1**

### Property 17: RAG Performance
*For any* RAG query, retrieval and generation SHALL complete within 2 seconds
**Validates: Requirements 7.2**

### Property 18: Uptime
*For any* 30-day period, system uptime SHALL be ≥99%
**Validates: Requirements 7.3**

### Property 19: Encryption at Rest
*For any* stored data, encryption SHALL use AES-256
**Validates: Requirements 8.1**

### Property 20: Encryption in Transit
*For any* data transmission, TLS 1.3 or higher SHALL be used
**Validates: Requirements 8.2**

### Property 21: Data Deletion
*For any* user deletion request, all user data SHALL be permanently removed within 30 days
**Validates: Requirements 8.4**

### Property 22: Knowledge Base Versioning
*For any* legal amendment, the system SHALL initiate update workflow requiring legal expert approval
**Validates: Requirements 9.2**

### Property 23: Version Tagging
*For any* response, the system SHALL tag with the knowledge base version used
**Validates: Requirements 9.5**

### Property 24: Mobile Responsiveness
*For any* mobile device with 320px-428px width, the interface SHALL display responsively
**Validates: Requirements 10.1**

### Property 25: Touch Target Size
*For any* interactive element, touch targets SHALL be minimum 44px
**Validates: Requirements 10.2**

### Property 26: API Rate Limiting
*For any* API key, requests SHALL be rate-limited to 100 per minute
**Validates: Requirements 12.4**

### Property 27: Citation Display
*For any* legal information response, the system SHALL include citations to specific Source_Documents
**Validates: Requirements 13.1**

### Property 28: AI-Generated Indication
*For any* response, the system SHALL clearly indicate when content is AI-generated versus direct legal text
**Validates: Requirements 13.4**

### Property 29: Performance Monitoring
*For any* time period, the system SHALL log citation accuracy, hallucination rate, routing accuracy, voice WER, and confidence distributions
**Validates: Requirements 14.3**

### Property 30: Citation Accuracy Alert
*For any* measurement period, if citation accuracy falls below 95%, the system SHALL trigger administrator alerts
**Validates: Requirements 14.4**

### Property 31: Hallucination Alert
*For any* measurement period, if hallucination rate exceeds 2%, the system SHALL trigger immediate investigation
**Validates: Requirements 14.5**

### Property 32: Escalation Acknowledgment
*For any* escalation request, the system SHALL acknowledge within 4 hours
**Validates: Requirements 15.2**

### Property 33: Human Review SLA
*For any* escalation, the system SHALL provide human review guidance within 24 hours
**Validates: Requirements 15.3**

### Property 34: Round-Trip Property
*For any* valid complaint object, formatting then parsing then formatting SHALL produce an equivalent document
**Validates: Requirements 16.3**

## Error Handling

**Failure Scenarios:**

| Failure | Recovery |
|---------|----------|
| Vector DB unavailable | Cached responses, 3× retry with exponential backoff |
| No retrieval results | "Out of scope" message with alternative resources |
| Low confidence (<0.7) | Disclaimer, suggest professional consultation, log for review |
| STT service failure | Automatic text input fallback with notification |
| Config DB unavailable | Cached thresholds (1-hour TTL) with staleness disclaimer |
| LLM API failure | 3× retry with exponential backoff, then 503 |
| Session expired | Re-authentication prompt with state preservation |
| Rate limit exceeded | 429 response with retry_after header |

**Progressive Degradation:**
- Level 0: Full service
- Level 1: Non-critical features disabled (analytics, telemetry)
- Level 2: Voice disabled, text-only mode
- Level 3: Cached responses only, no new RAG queries
- Level 4: Read-only, maintenance banner

**User Communication:** Status banner explains degraded features, provides alternative contact methods (NCH phone, email support)

## Testing Strategy

### Dual Testing Approach

**Property-Based Testing** (Hypothesis/fast-check):
- 34 correctness properties from requirements
- Minimum 100 iterations per property test
- Tag format: `Feature: nyayasetu-ai-navigator, Property {number}: {property_text}`
- Tests universal behaviors across randomized inputs

**Unit Testing** (pytest/Vitest):
- Specific examples and edge cases
- Integration points between components
- Error conditions and validation
- Focus on concrete scenarios, not comprehensive input coverage

**Coverage Goals:**
- Unit test coverage: ≥80% line coverage
- Critical paths: ≥95% (authentication, RAG, routing)
- All 34 correctness properties implemented

**CI/CD Pipeline:**
1. On commit: Lint, unit tests, property tests, accessibility tests (axe-core)
2. On PR: Integration tests, SAST security scanning, code review
3. On merge: Deploy to staging, E2E tests, performance tests
4. On release: Blue-green deploy to production, smoke tests, 30-min bake time

### AI Observability

**Real-Time Monitoring:**
- Citation accuracy (target ≥95%)
- Hallucination rate (target ≤2%)
- Low-confidence response rate (target <15%)
- Retrieval relevance (target top-3 relevant ≥90%)
- Speech-to-text WER per language (target ≤15%)
- Routing accuracy (target false routing ≤5%)

**Monthly Reports:** Automated AI performance reports with trend analysis and corrective action recommendations

**Human Escalation:** Automatic triggers for user request, confidence <0.7, complex cases, unusual patterns. SLA: 4-hour acknowledgment, 24-hour review guidance.

## Deployment and Scalability

**Cloud Topology:**
- Primary: AWS Mumbai (ap-south-1)
- DR: AWS Hyderabad (ap-south-2)
- Multi-AZ deployment

**Container Orchestration (ECS Fargate):**
- AI Orchestrator: 2 vCPU, 4 GB RAM, min 3 tasks
- RAG Engine: 4 vCPU, 8 GB RAM, min 5 tasks
- Complaint Drafter: 2 vCPU, 4 GB RAM, min 2 tasks
- Grievance Router: 1 vCPU, 2 GB RAM, min 2 tasks

**Auto-Scaling:**
- Target CPU: 70%
- Scale-out: CPU >80%
- Scale-in: CPU <50%
- Step scaling: CPU >90% → add 50% capacity
- Min 2 tasks/service, max 20 tasks/service
- Cooldown: 300 seconds

**Load Balancing:**
- Application Load Balancer in public subnets
- Health checks: HTTP GET /health every 30 seconds
- Sticky sessions for conversation continuity

**Database:**
- Managed PostgreSQL, multi-AZ
- Auto-scaling storage: 100 GB → 1 TB max
- 2 read replicas for read-heavy workloads

**Multi-Region Failover:**
- Active-passive configuration
- Cross-region DB replication (lag <5 seconds)
- Cross-region object storage replication (<15 minutes for 99.99%)
- DNS health checks trigger automatic failover
- RTO <4 hours, RPO <1 hour

**Backup:**
- Automated daily DB backups (30-day retention)
- Point-in-time recovery (up to 5 minutes before failure)
- Object storage versioning (last 10 versions)
- Archive to Glacier after 90 days
- Infrastructure as Code (Terraform) in Git

**Monitoring:**
- CloudWatch metrics: CPU, memory, latency, error rate
- Distributed tracing for end-to-end request flow
- Critical alerts: PagerDuty
- Warning alerts: Slack
- SLA: 99% uptime, 95% of requests <3 seconds

## Security and Compliance

**Encryption:**
- At rest: AES-256 (PostgreSQL TDE, S3 SSE with KMS)
- In transit: TLS 1.3, HSTS enforcement
- Application-level: Phone numbers SHA-256 hashed with salt, JWT secrets in AWS Secrets Manager

**Authentication & Authorization:**
- OTP-based authentication (passwordless)
- JWT tokens, 24-hour validity, httpOnly cookies
- RBAC: End User (own data), Administrator (logs, config), Legal Reviewer (KB updates), Auditor (read-only logs)

**Data Isolation:**
- PostgreSQL row-level security
- Cross-user access blocked (403), logged

**Consent Management:**
- Explicit consent before data collection
- Granular options (essential vs. optional analytics)
- Consent records: user_id, type, action, timestamp
- Withdrawal triggers 30-day deletion workflow

**Data Deletion:**
- User-initiated: Complete erasure within 30 days (DPDP Act)
- Auto-expiration: Drafts after 180 days, sessions after 24 hours
- Audit logs: 90-day retention, then S3 Glacier for 5 years

**Threat Mitigation:**
- SQL Injection: Parameterized queries, ORM
- XSS: CSP headers, React JSX escaping
- CSRF: CSRF tokens, SameSite cookies
- DoS: Rate limiting (100 req/min), AWS WAF, CloudFront DDoS protection
- MITM: TLS 1.3, HSTS

**Security Monitoring:**
- AWS GuardDuty for threat detection
- CloudWatch alarms for unusual access
- Quarterly penetration testing

## Assumptions and Constraints

**Technical Assumptions:**
- Minimum 2G network connectivity
- Modern browsers (Chrome 90+, Safari 14+, Firefox 88+)
- Cloud services 99.9% uptime SLA
- STT services >85% accuracy for Indian English and Hindi

**System Constraints:**
- Latency: RAG responses ≤3 seconds (95th percentile)
- Cost: LLM API costs <₹10 per user per month
- Bandwidth: Voice optimized for 50-100 Kbps
- Data residency: All personal data in India (DPDP Act)
- Budget: ₹5 crore total project budget

**External Dependencies:**
- OpenAI/Anthropic APIs for LLMs
- AWS cloud services
- AWS Transcribe/Polly for speech
- Pinecone/Weaviate for vector DB
- Government portals (NCH, e-Daakhil) for integration
