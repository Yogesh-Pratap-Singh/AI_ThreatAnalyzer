# Technology Stack Documentation
# AI Threat Analyzer

**Version**: 1.0  
**Last Updated**: 2026-05-27  

---

## 1. Stack Overview

### Architecture Pattern

- **Type**: Monolithic API with event-driven ingestion workers
- **Pattern**: REST API + async event stream processing
- **Deployment**: Docker Compose (dev) → Kubernetes (production)
- **Data Flow**: Log Source → Kafka → Ingestion Worker → PostgreSQL/pgvector → FastAPI → Next.js Dashboard

### Why This Architecture

Single-repo monolith for MVP velocity. Kafka decouples ingestion from analysis so a slow LLM call never blocks event processing. pgvector handles both relational alert data and vector embeddings (MITRE/CVE RAG) in one database — no separate vector DB to manage at MVP scale.

---

## 2. Frontend Stack

### Core Framework

- **Framework**: Next.js
- **Version**: 14.1.0
- **Reason**: App Router with server components reduces client JS; built-in API routes for BFF pattern; excellent TypeScript support
- **Documentation**: https://nextjs.org/docs
- **License**: MIT

### UI Library

- **Library**: React
- **Version**: 18.2.0
- **Reason**: Component model fits dashboard widget architecture; concurrent features for real-time updates
- **Documentation**: https://react.dev
- **License**: MIT

### Language

- **Language**: TypeScript
- **Version**: 5.3.3
- **Config**: Strict mode enabled (`"strict": true`)
- **Reason**: Type safety critical for security tool; prevents null-pointer bugs in alert rendering

### Styling

- **Framework**: Tailwind CSS
- **Version**: 3.4.1
- **Configuration**: Custom config at `tailwind.config.ts` with security-domain color tokens
- **Documentation**: https://tailwindcss.com/docs
- **License**: MIT

### State Management

- **Library**: Zustand
- **Version**: 4.4.7
- **Reason**: Lightweight; handles alert queue state without Redux boilerplate
- **Alternatives Considered**: Redux (rejected: too verbose for team size), React Query alone (insufficient for client-side alert state)

### Server State / Data Fetching

- **Library**: TanStack Query (React Query)
- **Version**: 5.17.19
- **Reason**: Handles polling (real-time alerts), caching, and background refetch with minimal code
- **Documentation**: https://tanstack.com/query/v5

### Form Handling

- **Library**: React Hook Form
- **Version**: 7.49.3
- **Validation**: Zod 3.22.4
- **Reason**: Minimal re-renders; Zod schema reuse between client and server

### HTTP Client

- **Library**: Axios
- **Version**: 1.6.5
- **Reason**: Interceptors for automatic JWT refresh; consistent error structure

### Real-Time Updates

- **Technology**: Server-Sent Events (SSE) via native browser `EventSource`
- **Reason**: One-directional push from server to client for new alerts; simpler than WebSockets for this use case; no additional library needed
- **Fallback**: 5-second polling via React Query if SSE connection drops

### Data Visualization

- **Library**: Recharts
- **Version**: 2.10.4
- **Reason**: React-native charts; good TypeScript support; covers bar, line, area charts needed for dashboards
- **Documentation**: https://recharts.org

### Icons

- **Library**: Lucide React
- **Version**: 0.312.0
- **Reason**: Consistent outline style; tree-shakeable; covers all security-domain icons

### UI Components (Base)

- **Library**: shadcn/ui (Radix UI primitives)
- **Version**: Latest (components copied into repo, not installed as package)
- **Reason**: Accessible primitives (dialog, dropdown, tooltip) without a full design system lock-in; fully customizable with Tailwind

---

## 3. Backend Stack

### Runtime

- **Language**: Python
- **Version**: 3.12.1
- **Package Manager**: uv 0.1.24
- **Reason**: Python dominates ML/security tooling; best ecosystem for scikit-learn, Kafka, and LLM SDKs

### Web Framework

- **Framework**: FastAPI
- **Version**: 0.109.0
- **Reason**: Async-native; automatic OpenAPI docs; Pydantic validation; high performance for event-heavy APIs
- **Documentation**: https://fastapi.tiangolo.com

### ASGI Server

- **Server**: Uvicorn
- **Version**: 0.27.0
- **Workers**: Gunicorn 21.2.0 with Uvicorn workers in production

### Data Validation

- **Library**: Pydantic
- **Version**: 2.5.3
- **Reason**: Shared with FastAPI; strict type coercion for event schema normalization

### Event Streaming

- **Platform**: Apache Kafka
- **Version**: 3.6.0
- **Client**: confluent-kafka-python 2.3.0
- **Topics**:
  - `raw-events` — normalized inbound log events
  - `scored-events` — events with anomaly scores attached
  - `alerts` — generated alerts ready for storage
- **Reason**: Decouples ingestion rate from processing rate; persistent log enables replay; industry standard in security pipelines

### Database

- **Primary**: PostgreSQL
- **Version**: 16.1
- **Extensions**: pgvector 0.5.1 (vector similarity search for RAG)
- **ORM**: SQLAlchemy 2.0.25 (async) + Alembic 1.13.1 (migrations)
- **Connection Pooling**: asyncpg 0.29.0 + PgBouncer 1.22.0
- **Reason**: pgvector handles both relational alert data and embedding search — no separate vector DB needed at MVP scale

### Caching

- **System**: Redis
- **Version**: 7.2.4
- **Client**: redis-py 5.0.1 (async)
- **Use Cases**:
  - Alert explanation cache (key: `explain:{alert_signature_hash}`, TTL: 7 days)
  - Rate limiting counters
  - SSE connection state
  - Session refresh token validation

### Authentication

- **Strategy**: JWT (JSON Web Tokens)
- **Library**: python-jose 3.3.0 (JWT) + passlib 1.7.4 (bcrypt)
- **Access Token Expiry**: 15 minutes
- **Refresh Token Expiry**: 8 hours (one shift)
- **Storage**: HTTP-only Secure SameSite=Strict cookies
- **Bcrypt Rounds**: 12

### AI / ML Stack

#### Anomaly Detection

- **Library**: scikit-learn
- **Version**: 1.4.0
- **Model**: IsolationForest (`contamination=0.05`, `n_estimators=200`)
- **Serving**: Pre-trained model serialized with joblib 1.3.2; reloaded hourly from S3

#### Embeddings (RAG)

- **Library**: sentence-transformers
- **Version**: 2.3.1
- **Model**: `all-MiniLM-L6-v2` (384-dim, fast, good quality for threat intel text)
- **Storage**: pgvector `vector(384)` column in `knowledge_base` table

#### LLM (Threat Explanation)

- **Provider**: Anthropic Claude
- **SDK**: anthropic 0.17.0
- **Model**: `claude-sonnet-4-6` (balance of speed, cost, quality)
- **Max Tokens**: 300 per explanation (enforces < 150 word output)
- **Reason**: Best-in-class reasoning for multi-step threat analysis; strong instruction following for structured output

#### ML Pipeline Orchestration

- **Library**: Apache Airflow
- **Version**: 2.8.0
- **Use**: Weekly model retraining DAG; MITRE ATT&CK knowledge base refresh

### Email

- **Provider**: Resend
- **Library**: resend 0.7.0
- **Use**: Alert escalation notifications, weekly report delivery, password reset

### File Storage

- **Service**: AWS S3
- **SDK**: boto3 1.34.0
- **Use**: Trained model artifacts, exported PDF reports, raw log archive

---

## 4. DevOps & Infrastructure

### Version Control

- **System**: Git
- **Platform**: GitHub
- **Branch Strategy**:
  - `main` — production
  - `develop` — staging
  - `feature/*` — feature branches
  - `hotfix/*` — urgent production fixes
- **Protection**: `main` requires PR + 1 approval + passing CI

### CI/CD

- **Platform**: GitHub Actions
- **Workflows**:
  - `pr-checks.yml` — lint, type-check, unit tests (runs on every PR)
  - `deploy-staging.yml` — deploy to staging on merge to `develop`
  - `deploy-production.yml` — deploy to production on merge to `main`
  - `retrain-model.yml` — weekly scheduled model retraining

### Containerization

- **Tool**: Docker
- **Version**: 25.0.2
- **Compose**: Docker Compose 2.24.5 (local dev)
- **Registry**: AWS ECR

### Orchestration (Production)

- **Platform**: AWS EKS (Kubernetes 1.29)
- **Reason**: Horizontal scaling of ingestion workers; rolling deploys; resource isolation between API and ML workloads

### Hosting

- **Frontend**: Vercel (Next.js native deployment)
- **Backend API**: AWS EKS
- **Kafka**: AWS MSK (managed Kafka)
- **Database**: AWS RDS PostgreSQL (multi-AZ)
- **Redis**: AWS ElastiCache
- **Object Storage**: AWS S3

### Monitoring & Observability

- **Error Tracking**: Sentry (`sentry-sdk 1.40.0` for Python; `@sentry/nextjs 7.99.0`)
- **Metrics**: Prometheus 2.49.1 + Grafana 10.2.3
- **Logging**: Structured JSON logs → AWS CloudWatch Logs
- **Tracing**: OpenTelemetry 1.22.0 → Jaeger
- **Uptime**: AWS CloudWatch Synthetics (canary pings every minute)

### Testing

- **Backend Unit Tests**: pytest 7.4.4 + pytest-asyncio 0.23.3
- **Backend Integration**: pytest + httpx 0.26.0 (async test client)
- **Frontend Unit Tests**: Vitest 1.2.0
- **E2E Tests**: Playwright 1.41.1
- **Coverage Target**: 80% overall; 95% for auth and alert scoring modules

---

## 5. Development Tools

### Code Quality (Python)

- **Linter**: Ruff 0.2.0 (replaces flake8 + isort)
- **Formatter**: Black 24.1.1
- **Type Checker**: mypy 1.8.0 (strict mode)

### Code Quality (TypeScript)

- **Linter**: ESLint 8.56.0 with `eslint-config-next 14.1.0`
- **Formatter**: Prettier 3.2.4
- **Type Checker**: tsc (built into TypeScript)

### Git Hooks

- **Tool**: pre-commit 3.6.0
- **Hooks**: Ruff format + lint, Black, mypy; ESLint + Prettier on frontend files

### IDE Recommendation

- **Editor**: VS Code or PyCharm
- **Extensions**: Pylance, Ruff, Black formatter, ESLint, Prettier, Tailwind CSS IntelliSense, Docker

---

## 6. Environment Variables

```bash
# === Database ===
DATABASE_URL="postgresql+asyncpg://user:pass@localhost:5432/threat_analyzer"
DATABASE_SYNC_URL="postgresql://user:pass@localhost:5432/threat_analyzer"  # Alembic migrations

# === Redis ===
REDIS_URL="redis://localhost:6379/0"

# === Kafka ===
KAFKA_BOOTSTRAP_SERVERS="localhost:9092"
KAFKA_GROUP_ID="threat-analyzer-workers"

# === Authentication ===
JWT_SECRET_KEY="<32+ character random string>"
JWT_REFRESH_SECRET_KEY="<32+ character random string>"
JWT_ALGORITHM="HS256"
ACCESS_TOKEN_EXPIRE_MINUTES=15
REFRESH_TOKEN_EXPIRE_HOURS=8

# === Anthropic / LLM ===
ANTHROPIC_API_KEY="sk-ant-..."
LLM_MODEL="claude-sonnet-4-6"
LLM_MAX_TOKENS=300

# === AWS ===
AWS_ACCESS_KEY_ID="..."
AWS_SECRET_ACCESS_KEY="..."
AWS_REGION="ap-south-1"
AWS_S3_BUCKET="threat-analyzer-artifacts"

# === Email ===
RESEND_API_KEY="re_..."
FROM_EMAIL="alerts@yourorg.com"

# === Sentry ===
SENTRY_DSN="https://..."

# === App ===
ENVIRONMENT="development"  # development | staging | production
LOG_LEVEL="INFO"
ANOMALY_THRESHOLD=0.75     # Events above this score trigger an alert
MODEL_RETRAIN_SCHEDULE="0 2 * * 0"  # Weekly Sunday 2 AM

# === Frontend (Next.js public) ===
NEXT_PUBLIC_API_URL="http://localhost:8000"
NEXT_PUBLIC_SENTRY_DSN="https://..."
```

---

## 7. Scripts

### Backend (`pyproject.toml`)

```toml
[tool.scripts]
dev = "uvicorn app.main:app --reload --port 8000"
test = "pytest tests/ -v"
test-cov = "pytest tests/ --cov=app --cov-report=html"
lint = "ruff check . && mypy app/"
format = "black . && ruff format ."
migrate = "alembic upgrade head"
migrate-create = "alembic revision --autogenerate -m"
seed = "python scripts/seed_knowledge_base.py"
retrain = "python scripts/retrain_model.py"
```

### Frontend (`package.json`)

```json
{
  "scripts": {
    "dev": "next dev",
    "build": "next build",
    "start": "next start",
    "lint": "next lint",
    "format": "prettier --write .",
    "type-check": "tsc --noEmit",
    "test": "vitest",
    "test:e2e": "playwright test",
    "test:e2e:ui": "playwright test --ui"
  }
}
```

---

## 8. Pinned Dependencies

### Backend (`requirements.txt`)

```
fastapi==0.109.0
uvicorn==0.27.0
gunicorn==21.2.0
pydantic==2.5.3
sqlalchemy==2.0.25
alembic==1.13.1
asyncpg==0.29.0
redis==5.0.1
confluent-kafka==2.3.0
scikit-learn==1.4.0
sentence-transformers==2.3.1
anthropic==0.17.0
python-jose==3.3.0
passlib==1.7.4
bcrypt==4.1.2
boto3==1.34.0
resend==0.7.0
joblib==1.3.2
numpy==1.26.3
pandas==2.1.4
sentry-sdk==1.40.0
opentelemetry-sdk==1.22.0
httpx==0.26.0
pytest==7.4.4
pytest-asyncio==0.23.3
black==24.1.1
ruff==0.2.0
mypy==1.8.0
```

### Frontend (`package.json` dependencies)

```json
{
  "dependencies": {
    "next": "14.1.0",
    "react": "18.2.0",
    "react-dom": "18.2.0",
    "typescript": "5.3.3",
    "tailwindcss": "3.4.1",
    "zustand": "4.4.7",
    "@tanstack/react-query": "5.17.19",
    "react-hook-form": "7.49.3",
    "zod": "3.22.4",
    "axios": "1.6.5",
    "recharts": "2.10.4",
    "lucide-react": "0.312.0",
    "@radix-ui/react-dialog": "1.0.5",
    "@radix-ui/react-dropdown-menu": "2.0.6",
    "@radix-ui/react-tooltip": "1.0.7",
    "@radix-ui/react-select": "2.0.0",
    "clsx": "2.1.0",
    "tailwind-merge": "2.2.0",
    "@sentry/nextjs": "7.99.0"
  }
}
```

---

## 9. Security Considerations

### Authentication

- JWT tokens short-lived (15 min access); refresh tokens bound to one session
- HTTP-only Secure cookies — no `localStorage` for tokens
- bcrypt 12 rounds — ~250ms hash time (intentionally slow)
- Account lockout after 5 failed login attempts (15-minute lockout)

### API Security

- All endpoints require auth except `/api/v1/auth/*` and `/api/v1/health`
- Rate limiting: login 5/15min per IP; API 200/min per user; ingestion endpoint 10,000 events/min per source key
- CORS restricted to known frontend origin
- Helmet-equivalent headers via FastAPI middleware (HSTS, X-Frame-Options, CSP)
- Input sanitization via Pydantic — strict type coercion, no raw SQL

### Data Security

- Database credentials in environment variables only — never in code
- S3 bucket private with pre-signed URLs for report downloads
- Logs sanitized — no PII or credentials in log output
- All data encrypted at rest (AWS RDS encryption, S3 SSE-AES256)
- All data encrypted in transit (TLS 1.3 enforced)

### LLM Security

- Anthropic API key server-side only — never exposed to frontend
- Prompt injection mitigation: event data injected as structured JSON, not raw user text
- LLM output sanitized before storage — no executable content rendered

---

## 10. Version Upgrade Policy

### Security Patches

- Applied within 72 hours of critical CVE disclosure
- Automated Dependabot PRs reviewed weekly
- No version ranges in `requirements.txt` — pin everything

### Minor / Patch Updates

- Monthly review of outdated packages
- Must pass full test suite before merging

### Major Version Updates

- Quarterly review
- Requires staging environment validation for ≥ 1 week before production
- Documented in `CHANGELOG.md` with migration notes
- scikit-learn / sentence-transformers major updates require model revalidation
