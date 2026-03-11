# Architecture & Design Decisions

## System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         Users' Browsers                         │
│              (Chrome, Firefox, Safari, etc.)                    │
└────────────────────┬─────────────────────────────────────────────┘
                     │ HTTPS (TLS 1.3)
                     │
         ┌───────────┴───────────┐
         │                       │
    ┌────▼──────┐          ┌────▼──────────┐
    │ Vercel    │          │   Nginx       │
    │ CDN       │          │   Reverse     │
    │ (Global)  │          │   Proxy       │
    └────┬──────┘          └────┬──────────┘
         │                       │
    ┌────▼──────────────────────▼─────┐
    │   Next.js Frontend                │
    │ ┌─────────────────────────────┐   │
    │ │  React Components           │   │
    │ │  • FileUploader             │   │
    │ │  • StatusMessage            │   │
    │ │  Axios HTTP Client          │   │
    │ └─────────────────────────────┘   │
    │  Port: 3000                       │
    └────┬──────────────────────────────┘
         │
         │ CORS-Validated Requests
         │ multipart/form-data
         │ 60s timeout
         │
    ┌────▼──────────────────────────────────┐
    │   Docker Container (Backend)           │
    │ ┌──────────────────────────────────┐   │
    │ │  FastAPI Web Application         │   │
    │ │                                   │   │
    │ │  Routes:                         │   │
    │ │  • POST /api/v1/upload-and-...   │   │
    │ │  • GET /health                   │   │
    │ │  • GET /docs (Swagger)           │   │
    │ │                                   │   │
    │ │  Middleware:                     │   │
    │ │  • CORS (strict origins)         │   │
    │ │  • Rate Limiter (5 req/min)      │   │
    │ │  • Request Validation            │   │
    │ ├──────────────────────────────────┤   │
    │ │  Data Processing Pipeline        │   │
    │ │                                   │   │
    │ │  1. File Validation              │   │
    │ │     - Extension: .csv, .xlsx     │   │
    │ │     - Size: < 10MB               │   │
    │ │     - MIME type check            │   │
    │ │                                   │   │
    │ │  2. CSV/XLSX Parsing             │   │
    │ │     - Pandas DataFrame           │   │
    │ │     - Memory buffer (no disk)    │   │
    │ │     - Data validation            │   │
    │ │                                   │   │
    │ │  3. AI Summarization             │   │
    │ │     - Gemini API integration     │   │
    │ │     - Prompt engineering         │   │
    │ │     - 300-400 word output        │   │
    │ │                                   │   │
    │ │  4. Email Delivery               │   │
    │ │     - SMTP (Gmail/custom)        │   │
    │ │     - HTML template              │   │
    │ │     - Transaction logging        │   │
    │ ├──────────────────────────────────┤   │
    │ │  External Dependencies           │   │
    │ │  • google-generativeai (Gemini)  │   │
    │ │  • smtplib (Email)               │   │
    │ │  • pandas (Data processing)      │   │
    │ │  • slowapi (Rate limiting)       │   │
    │ │  • uvicorn (ASGI server)         │   │
    │ └──────────────────────────────────┘   │
    │  Port: 8000 (internal)                 │
    │  Health Check: /health every 30s       │
    │  Non-root user (UID 1000)              │
    └────┬──────────────────────────────────┘
         │
         ├─────────────────────────────────────┐
         │                                     │
    ┌────▼──────────┐              ┌──────────▼────┐
    │  Google       │              │    SMTP       │
    │  Gemini API   │              │    Server     │
    │  (Cloud)      │              │  (Gmail/Other)│
    │  • Parsing    │              │  • Auth       │
    │  • Analysis   │              │  • Send email │
    │  • Insights   │              └───────────────┘
    └───────────────┘
```

---

## Technology Stack Rationale

### Frontend: Next.js + React

**Why Next.js?**
- ✅ Production-ready framework with built-in optimizations
- ✅ Server-side rendering (SEO, performance)
- ✅ Static site generation (fast deployment)
- ✅ API routes (future expansion)
- ✅ Built-in CSS support
- ✅ Excellent Vercel integration

**Alternative Considered:**
- ❌ Create React App: More boilerplate, fewer optimizations
- ❌ Vite: Faster dev, but less opinionated structure
- ✅ Next.js wins for production-grade SPA

### Backend: FastAPI

**Why FastAPI?**
- ✅ Modern Python framework, excellent performance
- ✅ Automatic OpenAPI/Swagger generation
- ✅ Type hints for data validation (Pydantic)
- ✅ Built-in async/await support
- ✅ Easy to test and deploy
- ✅ Great for rapid development

**Alternative Considered:**
- Node.js Express: Possible, but Python better for AI/data processing
- Django: Overkill for this use case
- Flask: Less opinionated, more boilerplate needed
- ✅ FastAPI wins for speed + features

### AI Model: Google Gemini API

**Why Gemini?**
- ✅ Free tier with generous limits
- ✅ Excellent multilingual support
- ✅ Fast response times (2-5 seconds)
- ✅ Good context understanding
- ✅ Cost-effective scaling

**Alternatives Considered:**
- OpenAI GPT-4: More expensive, slower free tier
- Anthropic Claude: Good, but less generous free tier
- Groq Llama: Faster, but smaller context
- Local LLM: Privacy better, but requires GPU
- ✅ Gemini wins for balance of cost/performance

### Containerization: Docker

**Why Docker?**
- ✅ Reproducible environments across all machines
- ✅ Language-agnostic deployment
- ✅ Easy scaling and orchestration
- ✅ Security isolation between services
- ✅ Industry standard for DevOps

**Multi-stage Builds:**
```dockerfile
# Frontend example
FROM node:18 AS builder    # Build image (large)
RUN npm run build

FROM node:18-alpine        # Runtime image (small)
COPY --from=builder .next  # Only production artifacts
```
**Benefit:** ~60% image size reduction

---

## Design Patterns Used

### 1. **Separation of Concerns**
```python
# Backend: Clear module boundaries
├── main.py (API routes & configuration)
├── helpers.py (Business logic - future)
├── security.py (Authentication - future)
└── models.py (Data models - future)
```

### 2. **Factory Pattern**
```python
# AI Summary Generator (factory for different AI backends)
def get_ai_engine(model_type):
    if model_type == "gemini":
        return GeminiEngine()
    elif model_type == "groq":
        return GroqEngine()
```

### 3. **Middleware Pattern**
```python
# CORS, Rate Limiting, Logging applied via middleware
app.add_middleware(CORSMiddleware, ...)
app.state.limiter = Limiter(...)
```

### 4. **Dependency Injection**
```python
# FastAPI dependencies for reusable logic
async def verify_api_key(x_api_key: str = None):
    if not x_api_key:
        raise HTTPException(status_code=401)

@app.post("/api/protected")
async def protected_route(verified=Depends(verify_api_key)):
    pass
```

### 5. **Component-Based Frontend**
```jsx
// React component hierarchy
<App />
├── <FileUploader /> (state + logic)
└── <StatusMessage /> (presentation)
```

---

## Data Flow Deep Dive

### File Upload Flow

```
1. USER ACTION
   └─ Selects file (FileUploader.js)

2. CLIENT-SIDE VALIDATION
   └─ Check extension (.csv, .xlsx)
   └─ Check file size (~before upload)

3. FORM DATA PREPARATION
   └─ FormData API with file + email
   └─ Set Content-Type: multipart/form-data

4. HTTP REQUEST (axios)
   └─ POST /api/v1/upload-and-summarize
   └─ Timeout: 60 seconds
   └─ Handle CORS preflight

5. SERVER RECEIVES REQUEST
   └─ CORS validation
   └─ Rate limit check (slow API)
   └─ Request parsing
```

### Processing Flow

```
1. SERVER-SIDE VALIDATION
   ├─ File size check (< 10MB)
   ├─ Extension whitelist validation
   ├─ Email format validation
   └─ Return 400 if invalid

2. FILE PARSING
   ├─ Read from multipart upload
   ├─ Detect format (CSV vs XLSX)
   ├─ Parse to pandas DataFrame
   ├─ Basic data validation
   └─ Return 422 if malformed

3. AI SUMMARIZATION
   ├─ Build context string from data
   ├─ Craft detailed prompt
   ├─ Call Gemini API
   ├─ Stream response (if needed)
   ├─ Extract text summary
   └─ Handle API errors (retry logic - future)

4. EMAIL PREPARATION
   ├─ Create HTML template
   ├─ Prepare MIME multipart message
   ├─ Add headers (From, To, Subject)
   └─ Create Text + HTML versions

5. EMAIL SENDING
   ├─ Establish SMTP connection
   ├─ Authentication
   ├─ Send message
   ├─ Log transaction
   └─ Handle delivery errors

6. RESPONSE TO CLIENT
   ├─ Return 200 + success object
   ├─ Include summary_id for tracking
   └─ Update UI with success message
```

---

## Security Architecture

### Layer 1: Network Security
```
POST /api/v1/upload-and-summarize
├─ HTTPS/TLS 1.3 only (production)
├─ CORS allows specific origins only
├─ Prevents cross-site requests
└─ Prevents data interception
```

### Layer 2: Application Security
```
Request Validation
├─ File extension whitelist
├─ File size limit (10MB)
├─ Email format regex
└─ DataFrame integrity checks

Rate Limiting
├─ 5 requests per minute per IP
├─ Prevents brute force & DOS
└─ Graceful 429 response

Input Sanitization
├─ No SQL injection (no database)
├─ No command injection
├─ CSV parsing via pandas (safe)
└─ Email headers validated
```

### Layer 3: Infrastructure Security
```
Docker Security
├─ Non-root user (UID 1000)
├─ Read-only filesystem (future)
├─ Resource limits enforcement
└─ Health checks for availability

Environment Security
├─ API keys in .env (not in code)
├─ Secrets rotation support
├─ No credentials in logs
└─ No sensitive data exposed via API
```

### Layer 4: API Security
```
Future Enhancements
├─ API key authentication (header)
├─ Request signing (HMAC)
├─ JWT tokens for sessions
└─ OAuth2 for 3rd party integration
```

---

## Error Handling Strategy

### User-Facing Errors (4xx)
```javascript
// Clear, non-technical messages
400 Bad Request    → "Filled in all fields"
413 Payload Too Large → "File too large (max 10MB)"
429 Too Many Requests → "Too many requests. Try again later"
```

### Server Errors (5xx)
```javascript
500 Internal Server Error → "Failed to generate summary"
503 Service Unavailable   → "Service temporarily unavailable"
```

### Logging Strategy
```python
logger.info("Summary sent to user@example.com")     # Success
logger.warning("Rate limit exceeded: 192.168.1.1")  # Warning
logger.error("Gemini API timeout")                  # Error
logger.exception("Unexpected error")                # Full traceback
```

---

## Performance Optimization

### Backend Optimization
```python
# 1. Async Operations
@app.post("/api/v1/upload-and-summarize")
async def upload(...):  # Non-blocking I/O
    df = await parse_sales_data(file)

# 2. Stream Processing
#    Large files processed in memory (BytesIO)
#    No disk I/O bottlenecks

# 3. Connection Pooling
#    SMTP connections reused (future)
#    Database connections pooled (future)
```

### Frontend Optimization
```javascript
// 1. Code Splitting
// Next.js auto-splits per route

// 2. Image Optimization
// Auto-optimize images (if added)

// 3. Lazy Loading
// Components load on demand

// 4. CSS-in-JS
// styles/file-uploader.css (scoped)
```

### Infrastructure Optimization
```yaml
# 1. Multi-stage Docker builds
# Reduces frontend image from 500MB → 200MB

# 2. Alpine Linux base images
# python:3.11-slim instead of full

# 3. Efficient health checks
# Only check /health endpoint, not full app
```

### Metrics
```
API Response Time:     ~1-2s (excluding Gemini)
Gemini API Call:       ~15-20s
Email Delivery:        ~1-2s
Total End-to-End:      ~20-30s

Frontend Bundle:       ~150KB (gzipped)
Backend Image:         ~100MB
Frontend Image:        ~200MB
```

---

## Scalability Considerations

### Horizontal Scaling
```
Current: Single instance
├─ Backend: ~50-100 req/min
└─ Frontend: Stateless (easy)

Future Scaling:
├─ Load balancer (Round-robin)
├─ Multiple backend instances
├─ Shared cache (Redis)
├─ Message queue (Celery/RabbitMQ)
└─ Database (PostgreSQL)
```

### Vertical Scaling
```
Current: t3.small (2 vCPU, 2GB RAM)
├─ Cost: ~$25/month

Upgrade Path:
├─ t3.medium (2 vCPU, 4GB RAM) → $50/month
├─ t3.large (2 vCPU, 8GB RAM) → $100/month
└─ Optimize memory before scaling
```

---

## Testing Strategy (Future Implementation)

```python
# Backend Testing
├─ Unit tests (pytest)
│  ├─ Test file validation
│  ├─ Test CSV parsing
│  └─ Test email formatting
├─ Integration tests
│  ├─ End-to-end flow
│  ├─ API response validation
│  └─ Rate limiting
└─ Load testing (locust)
   └─ Simulate 100+ concurrent users

# Frontend Testing
├─ Component tests (React Testing Library)
│  ├─ File upload interaction
│  ├─ Error message display
│  └─ Status updates
├─ E2E tests (Cypress/Playwright)
│  ├─ Full user flow
│  └─ API integration
└─ Visual regression tests
   └─ UI consistency across browsers
```

---

## Monitoring & Observability

### Metrics to Track
```
Backend:
├─ Request count (per minute)
├─ Response time (p50, p95, p99)
├─ Error rate (4xx, 5xx)
├─ Gemini API latency
├─ Email delivery success rate
└─ CPU & Memory usage

Frontend:
├─ Page load time
├─ Time to interactive
├─ Core Web Vitals
├─ JavaScript errors
└─ User conversion rate
```

### Alerting Rules
```
Alert if:
├─ Error rate > 5%
├─ Response time > 10s (p95)
├─ Gemini API unavailable
├─ Email delivery fails
├─ CPU > 80% sustained
├─ Memory > 85% sustained
└─ Health check failing
```

---

## Future Architecture Improvements

### Phase 2: Authentication & Multi-Tenant
```
Add:
├─ User authentication (OAuth2)
├─ API key management
├─ Team/organization support
├─ Usage analytics dashboard
└─ Billing integration
```

### Phase 3: Data Persistence
```
Add:
├─ PostgreSQL database
├─ Summary history
├─ User preferences
├─ Audit logging
└─ Data export features
```

### Phase 4: Advanced AI
```
Add:
├─ Multiple AI model selection
├─ Summary tone customization
├─ Custom prompt templates
├─ Sentiment analysis
└─ Predictive analytics
```

### Phase 5: Enterprise Features
```
Add:
├─ Workflow automation
├─ Webhook integration
├─ Slack/Teams bot
├─ Scheduled reports
├─ Data lake integration
└─ Advanced security (SSO, SAML)
```

---

**Last Updated:** March 2026  
**Architecture Version:** 1.0.0
