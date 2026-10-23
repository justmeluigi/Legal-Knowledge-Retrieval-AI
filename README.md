# Legal Knowledge Retrieval AI

An enterprise-grade, grounded **Legal Knowledge Retrieval (RAG)** system built with **Python**, **LangChain**, **ChromaDB**, **Sentence-Transformers**, **PyMuPDF**, and **FastAPI**, with native local inference powered by **Qwen 3.5 2B** via Ollama.

---

## 🌟 Key Capabilities & Achievements

1. **Document Indexing with Page Anchors (PyMuPDF + ChromaDB)**
   - Ingests and chunks a multi-document legal repository with page tracking, section header detection, and security clearance metadata tagging.
   - Vector database persistency with normalized cosine semantic embeddings (`sentence-transformers/all-MiniLM-L6-v2`).

2. **Grounded Evidence-Based Q&A**
   - Synthesizes faithful answers derived strictly from retrieved passages.
   - Every substantive legal assertion links to exact **document titles, section headers, and 1-indexed page numbers**.

3. **Grounded Abstention Engine (No Hallucination)**
   - If retrieved passages fall below the confidence similarity threshold, or if the question falls outside indexed legal knowledge, the system **explicitly abstains**:
     - Status: `ABSTAINED`
     - Evidence: `INSUFFICIENT`
     - Reason: Clear explanation stating that the repository lacks factual evidence.

4. **Role-Based Access Control (RBAC) & Data Segregation**
   - Implements strict security clearances at the vector database level:
     - **PUBLIC**: Guests & External Auditors (Code of Ethics, Public Disclosures)
     - **INTERNAL**: Employees (Remote work policy, Employee IP assignment, Travel expense rules)
     - **LEGAL_COUNSEL**: Attorneys (Master SaaS MSA, GDPR Data Processing Addendum, 48-hour breach notice)
     - **EXECUTIVE_BOARD**: Managing Partners & C-Suite (Project Titan $185M merger valuation, $4.5M golden parachute payouts)
   - Pre-retrieval vector filtering ensures unauthorized confidential passages are never retrieved or leaked. If a user asks about classified information without sufficient clearance, the system issues a `PERMISSION_RESTRICTED` security notice.

5. **Local Qwen 3.5 2B Inference with 100% Data Privacy**
   - Connects directly to local `qwen3.5:2b` via Ollama (`http://localhost:11434`), ensuring sensitive corporate legal data never leaves your environment.
   - Multi-provider fallback support for Google Gemini, OpenAI, Groq, or deterministic extractive synthesis.

6. **Apple-Inspired Minimalist Web UI**
   - Dribbble/Behance-trending visual design with generous white space, soft multi-layer diffuse shadows, and a single Cupertino Cobalt accent (`#0071E3`).
   - Interactive security persona switcher to test different permission tiers in real-time with 1 click.

---

## 🏗️ Architecture

```
D:\Legal Knowledge Retrieval AI/
├── core/
│   ├── permissions.py       # RBAC roles, clearance levels, and security personas
│   ├── document_indexer.py  # PyMuPDF section chunker with page anchors & security tags
│   ├── vector_store.py      # ChromaDB manager with semantic search & metadata filtering
│   ├── rag_engine.py        # LangChain retrieval, evidence thresholding & abstention
│   ├── schemas.py           # Pydantic schemas (QueryRequest, QueryResponse, Citations)
│   └── llm_provider.py      # Qwen 3.5 2B local adapter & cloud fallback factory
├── legal_corpus/
│   ├── generate_corpus.py   # ReportLab script generating realistic legal PDFs
│   ├── 01_public_code_of_conduct.pdf         (PUBLIC)
│   ├── 02_employee_handbook_and_ip.pdf       (INTERNAL)
│   ├── 03_master_saas_agreement.pdf          (INTERNAL)
│   ├── 04_data_privacy_and_security_dpa.pdf  (LEGAL_COUNSEL)
│   └── 05_confidential_merger_due_diligence.pdf (EXECUTIVE_BOARD)
├── chroma_db/               # Persistent ChromaDB vector storage
├── static/
│   ├── index.html           # Apple-inspired UI with RBAC switcher & evidence explorer
│   ├── style.css            # Minimalist stylesheet with diffuse shadows & typography
│   └── app.js               # Reactive frontend client
├── main.py                  # FastAPI server with REST endpoints & static UI
├── test_legal_retrieval.py  # Automated tests for RAG, RBAC security, and abstention
├── test_api.py              # Automated API endpoint integration tests
├── requirements.txt         # Dependencies
├── .env.example             # Configuration template
└── README.md                # System documentation
```

---

## 🔐 Security Clearance & Persona Mapping

| Persona | Role | Clearance Levels Permitted | Accessible Knowledge |
|---|---|---|---|
| **Alice Vance** | `GUEST` | `PUBLIC` | Code of Ethics, Gift Limits ($50), Public Disclosures |
| **Bob Martinez** | `EMPLOYEE` | `PUBLIC`, `INTERNAL` | Employee Handbook, IP Assignment, Travel Meal Per Diem ($85) |
| **Clara Sterling** | `LEGAL_COUNSEL` | `PUBLIC`, `INTERNAL`, `LEGAL_COUNSEL` | SaaS MSA, DPA GDPR Terms, 48-Hr Breach Notice, SOC 2 Audits |
| **David Sterling** | `EXECUTIVE_BOARD` | `ALL` (Top Secret) | Project Titan $185M Merger Valuation, $4.5M Golden Parachutes |

---

## 🚀 Quick Start Guide

### 1. Run the Server
```bash
python main.py
```
Open your browser at:
👉 **`http://127.0.0.1:8001`**

### 2. Run Automated Verification Tests
```bash
python -m pytest -v test_legal_retrieval.py test_api.py
```

---

## 🧪 Demonstration Test Scenarios

Try these scenarios in the web UI at `http://127.0.0.1:8001`:

1. **Scenario 1: Public Question (Allowed for All Roles)**
   - Select **Alice (Guest)**.
   - Click preset: *"What is the maximum dollar value for gifts or hospitality employees can accept?"*
   - **Result**: `VERIFIED ANSWER` citing **01 Public Code of Conduct, Page 1** ($50 limit).

2. **Scenario 2: Access Control Demonstration (RBAC Block)**
   - Keep **Alice (Guest)** selected.
   - Click preset: *"What is the agreed transaction valuation and executive golden parachute payout in Project Titan?"*
   - **Result**: `PERMISSION_RESTRICTED` security notice! The system blocks access because Project Titan is classified at `[EXECUTIVE_BOARD]`. Zero confidential passages leaked.

3. **Scenario 3: Authorized Executive Access**
   - Switch persona to **David (Executive Board Director)**.
   - Run the same Project Titan query.
   - **Result**: `VERIFIED ANSWER` citing **05 Confidential Merger Due Diligence, Page 1** ($185M valuation and $4.5M cash payout).

4. **Scenario 4: Grounded Abstention (No Speculation)**
   - Click preset: *"What are the corporate liability policies regarding commercial spacecraft repair?"*
   - **Result**: `ABSTAINED (NO EVIDENCE)`. The system reports insufficient factual evidence rather than hallucinating answers.

---

## 📡 REST API Reference

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/` | Web user interface |
| `GET` | `/api/health` | System health, vector chunk count, active LLM |
| `GET` | `/api/users` | List RBAC security personas with permitted clearances |
| `GET` | `/api/documents` | List indexed legal documents with clearance tiers |
| `GET` | `/api/documents/{id}/download` | View / download source PDF |
| `POST` | `/api/query` | RAG retrieval with RBAC filtering & abstention |
| `POST` | `/api/reindex` | Trigger corpus re-indexing into ChromaDB |
