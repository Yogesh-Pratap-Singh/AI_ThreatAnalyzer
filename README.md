# AI ThreatAnalyzer 🛡️

AI ThreatAnalyzer is a premium cybersecurity intelligence and log monitoring platform designed for real-time security operations center (SOC) triage, threat classification, and AI-assisted investigation.

It leverages a hybrid machine learning pipeline running natively on the host (featuring an **Isolation Forest** anomaly detector and an **in-memory vector RAG search** for threat intelligence correlation) to detect security anomalies and explain threats using Claude 3.5 Sonnet via the OpenRouter API.

---

## 🏗️ Architecture & Adaptations

To run natively and efficiently on a local host without Docker/Kubernetes, the platform implements:
1. **In-Memory Event Bus**: Replaces Apache Kafka using `asyncio.Queue` with async background workers (Normalization, ML Scoring, and Alert Generation) inside the FastAPI process monolith.
2. **In-Memory Cache (Redis Fallback)**: Replaces Redis with a local TTL-expiring caching manager for sessions, rate-limits, and AI prompt results.
3. **In-Memory Vector Search**: Avoids database-level C-extensions like `pgvector` by loading and computing cosine similarities using `scikit-learn` and `NumPy` over the MITRE ATT&CK knowledge base.
4. **Active ML Anomaly Scoring**: Extracts network traffic features and scores exfiltration patterns using a local pre-trained `IsolationForest` model.

---

## 🛠️ Technology Stack

* **Backend**: FastAPI, SQLAlchemy (async pg), Alembic, Pydantic, scikit-learn, NumPy, SentenceTransformers (`all-MiniLM-L6-v2`), httpx, Pytest.
* **Frontend**: Next.js 14 (App Router), TypeScript, Tailwind CSS, Zustand, Recharts, Lucide React, Axios.
* **Database**: PostgreSQL 16.

---

## 🚀 Getting Started (Natives Windows Setup)

### Prerequisites
* Python 3.12+
* Node.js v18+
* PostgreSQL 16 server running on port `5432`

---

### 1. Database Configuration & Schema Setup
Make sure you have a database named `threat_analyzer` created in your local PostgreSQL instance.

In `backend/.env`, verify your connection parameters. By default, it uses:
```env
ANOMALY_THRESHOLD=0.50
# Add your OpenRouter Claude key here to enable automated AI threat summaries:
# OPENROUTER_API_KEY=your_openrouter_api_key
```

Run Alembic schema migrations:
```powershell
cd backend
.venv\Scripts\python.exe -m alembic upgrade head
```

---

### 2. Seed Database
Seed the 13 core MITRE ATT&CK techniques (RAG embeddings) and the default analyst/ingest keys:
```powershell
# In the root workspace directory
backend\.venv\Scripts\python.exe scripts/seed_knowledge_base.py
backend\.venv\Scripts\python.exe scripts/seed_user.py
```
*Seeding allocates:*
* Default analyst credentials: `analyst@yourorg.com` / `Password123`
* Default network data source ID: `8b9b8b20-df5b-4395-8e31-862d66579b29` (API Key: `dev-api-key-12345`)

---

### 3. Start Development Servers

#### Start FastAPI Backend
```powershell
cd backend
..\backend\.venv\Scripts\uvicorn.exe app.main:app --port 8000
```

#### Start Next.js Frontend
```powershell
cd frontend
npm run dev
```
Open [http://localhost:3000](http://localhost:3000) in your browser.

---

## 🧪 Testing & Simulation

### Run Unit Tests
Run the Pytest suite verifying custom cache TTLs, scoring formulas, and vector distance matching:
```powershell
cd backend
.venv\Scripts\python.exe -m pytest
```

### Ingest Simulated Security Logs
Trigger a simulation injecting standard logs along with a massive 75MB exfiltration event at 3:15 AM:
```powershell
backend\.venv\Scripts\python.exe scripts/simulate_ingest.py
```
Go back to the browser at [http://localhost:3000/dashboard](http://localhost:3000/dashboard) to view the exfiltration alert populate in real time!

---

## 🛡️ API Spec — Ingestion
* **Endpoint**: `POST http://localhost:8000/api/v1/ingest/events`
* **Headers**:
  * `X-Source-API-Key`: `dev-api-key-12345`
  * `Content-Type`: `application/json`
* **Body**:
  ```json
  {
    "source_id": "8b9b8b20-df5b-4395-8e31-862d66579b29",
    "events": [
      {
        "timestamp": "2026-05-28T03:15:00",
        "source_ip": "192.168.1.159",
        "dest_ip": "198.51.100.42",
        "source_port": 49152,
        "dest_port": 8043,
        "protocol": "TCP",
        "event_type": "data_exfiltration",
        "bytes": 78643200,
        "raw": {
          "log_detail": "Outbound connection to unclassified external IP with high transfer volume"
        }
      }
    ]
  }
  ```
