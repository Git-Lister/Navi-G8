# Corrected Navi-G8 Setup Script


#!/usr/bin/env python3
"""
Navi-G8 Project Setup Script
Run this script in the root of your new navi-g8 repository to create the full project structure.
"""

import os
import datetime
from pathlib import Path

# -------------------- Configuration --------------------
PROJECT_NAME = "Navi-G8"
AUTHOR = "Your Name"  # Change as desired
DATE = datetime.date.today().isoformat()

# Base directory (current working directory)
BASE_DIR = Path.cwd()

# -------------------- Helper to write files --------------------
def write_file(path: Path, content: str):
    """Write content to a file, creating parent directories if needed."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"Created: {path}")

# -------------------- File Contents (with escaped curly braces) --------------------

README_CONTENT = f"""# {PROJECT_NAME} – Personal AI Knowledge Companion

{PROJECT_NAME} is a **personal, local‑first AI operating companion** that lives alongside your digital life, learns your knowledge and working patterns, and provides intelligent assistance while respecting absolute privacy. Inspired by *Serial Experiments Lain*, it aims to feel like an extension of thought – quiet, present, and deeply integrated.

## Features (Phase 1)
- Console‑style chat interface (dark, terminal‑like)
- Knowledge capture into a Markdown vault
- Semantic search across your documents and notes
- Hybrid search (keyword + vector) with RAG and citations
- Local LLM integration via Ollama, with optional fallback to free online APIs
- Privacy‑first: all processing local, no telemetry

## Quick Start (for developers)

### Prerequisites
- Docker and Docker Compose
- Ollama (with models like `deepseek-r1:7b`, `nomic-embed-text`)
- Node.js 20+ (for frontend development)
- Python 3.12+ (for backend, if not using Docker)

### Running with Docker (recommended)
```bash
git clone https://github.com/yourusername/{PROJECT_NAME.lower()}.git
cd {PROJECT_NAME.lower()}
cp .env.example .env
# Edit .env with your settings (especially OLLAMA_BASE_URL and SEARXNG_HOST)
docker compose up --build
```

Then open http://localhost:3000 and create a local account.

For detailed setup, see `docs/installation.md`.

## Documentation
- `CONTEXT.md` – LLM‑friendly project summary (start here for AI assistants)
- `DESIGN.md` – Full design document
- `DECISIONS.md` – Architecture Decision Records
- `ROADMAP.md` – Development phases and progress

## License
MIT
"""

CONTEXT_CONTENT = f"""# {PROJECT_NAME} – Project Context (Updated {DATE})

## 🎯 Vision
{PROJECT_NAME} is a personal, local‑first AI companion that lives alongside the user’s digital life, learns their knowledge and working patterns, and provides intelligent assistance while respecting absolute privacy. It takes aesthetic inspiration from *Serial Experiments Lain*: a "ghost in the machine" that feels like an extension of thought.

## 🏗️ Architecture Overview

```
Tauri Console (React) ↔ FastAPI Backend ↔ PostgreSQL (pgvector) + Redis
                         ↳ Ollama (local models) + optional free APIs (OpenRouter/Gemini)
                         ↳ SearxNG (self‑hosted web search)
                         ↳ Connectors: local folders, GitHub
```

- **Backend**: FastAPI (Python 3.12+), Celery for background tasks, PostgreSQL with pgvector for vector search.
- **Frontend**: React + Vite (web prototype) → Tauri (desktop app with console aesthetic).
- **LLM Router**: Model profiles (YAML) for local vs. API, with fallback logic.
- **Search**: Hybrid (PostgreSQL full‑text + pgvector) with RAG and citations.
- **Transparency**: Collapsible explanations for answers (sources, reasoning).
- **Logging**: Encrypted JSON logs for future self‑improvement.

## 📁 Key Files & Modules
| Path | Purpose |
|------|---------|
| `backend/app/main.py` | FastAPI entry point |
| `backend/app/routers/chat.py` | Chat endpoint |
| `backend/app/services/search.py` | Hybrid search logic |
| `backend/app/services/llm_router.py` | Model routing |
| `backend/app/connectors/` | Local folder, GitHub connectors |
| `frontend/src/App.tsx` | Main React component |
| `frontend/src/components/Console.tsx` | Terminal‑style UI |
| `scripts/pack-context.sh` | Generate context bundle for LLMs |

## 🧠 Current Development Focus
- **Phase 1 – MVP** (Core):
  - [x] Initial project structure set up
  - [ ] Basic chat with local Ollama models
  - [ ] File upload and indexing (Docling + embeddings)
  - [ ] Hybrid search (keyword + vector)
  - [ ] React console prototype with terminal aesthetic
  - [ ] Collapsible explanations (citations)
  - [ ] Encrypted logging
- **Active branch**: `main` (initial scaffolding)

## 🔑 Key Decisions (with rationale)
- **Use PostgreSQL + pgvector** instead of dedicated vector DB → simpler ops, good enough for personal scale.
- **Start with two connectors (local folders, GitHub)** → avoid feature creep; others can be added later.
- **Build new frontend from scratch** (React + Tauri) rather than using SurfSense’s Next.js → full control over aesthetic.
- **Model profiles via YAML** → user‑configurable, easy to add new providers.
- **Encrypted logs** → privacy while enabling future personalisation.

## ⚙️ Configuration
- Environment variables are documented in `.env.example`.
- Model profiles are defined in `config/models.yaml`.
- SearxNG is expected at `http://host.docker.internal:8080` (override via `SEARXNG_HOST`).

## 🧪 How to Test
1. Start backend: `docker compose up backend` (or `cd backend && uvicorn app.main:app --reload`)
2. Start frontend: `cd frontend && npm run dev`
3. Open http://localhost:3000, register, and try:
   - Upload a PDF and ask a question.
   - Run `:search quantum physics` to test semantic search.
   - Check logs in `~/.navig8/logs/` (encrypted).

## 📌 Next Steps / Open Questions
- [ ] Implement LLM router with fallback to free APIs.
- [ ] Add GitHub OAuth flow and indexing.
- [ ] Decide on encryption key management (OS keyring vs. password‑derived).
- [ ] Test performance of DeepSeek‑R1 32B quantised on RTX 3060.
"""

# DESIGN.md – Full design document (with escaped braces)
DESIGN_FULL = f"""# {PROJECT_NAME} – Personal AI Knowledge Companion  
## Comprehensive Design Document  

**Version:** 2.0  
**Date:** {DATE}  
**Status:** Draft for Review  

---

## 1. Executive Summary  

{PROJECT_NAME} is a **personal, local-first AI operating companion** – a system that lives alongside the user’s digital life, learns their knowledge and working patterns, and provides intelligent assistance while respecting absolute privacy. Named after the NAVI terminal in *Serial Experiments Lain*, it aims to feel like an extension of thought rather than a collection of disconnected tools.

The system is designed for a single power user (researcher/developer) who works across many documents, code repositories, and notes. It provides:
- A **console‑style interface** (dark, terminal‑like) for natural chat and commands.
- **Knowledge capture** into a structured Markdown vault.
- **Semantic search** across the vault using hybrid (keyword + vector) methods.
- **AI‑assisted enrichment**: summaries, tags, connections, and podcast generation.
- **Transparency**: every answer explains its sources and reasoning.
- **Privacy by design**: all processing is local by default, with optional use of free online APIs when local resources are insufficient – all under user control.

Development is phased:
- **Phase 1 (Core)**: Chat, capture, search, logging.
- **Phase 2 (Intelligence)**: Enrichment, proactive suggestions, podcast generation.
- **Phase 3 (Ghost)**: Optional persistent overlay/HUD, voice I/O.

The architecture is **cherry‑picked from best‑of‑breed open‑source projects** (SurfSense, OER_Phoenix, BookForge) but built as a fresh, lean codebase tailored exactly to the vision.

---

## 2. Goals & Non‑Goals  

### Goals  
- **Personal knowledge assistant** for a single user, deeply integrated with their files and workflows.  
- **Local‑first**: all core data and processing reside on the user’s machine.  
- **Hybrid model usage**: use local LLMs (via Ollama) for speed and privacy; fall back to free online APIs (OpenRouter, Gemini) for heavier tasks when needed, with explicit user consent.  
- **Transparency**: clearly label AI‑generated content, provide citations and “why this result?” explanations.  
- **Extensible**: modular design allows adding new connectors, enrichment modules, and output formats.  
- **Open‑source & free**: no subscriptions, no vendor lock‑in.  
- **Aesthetic fidelity**: the interface deliberately echoes the *Lain* NAVI console – dark, monospaced, slightly uncanny.  

### Non‑Goals  
- **Multi‑user support** or team collaboration (no RBAC, no real‑time shared spaces).  
- **Cloud‑hosted version** – everything is self‑hosted.  
- **Mobile apps** (though the web frontend could be accessed on mobile browsers, not a priority).  
- **Support for every possible connector** – start with essential ones (local folders, GitHub); others may be added later via community contributions.  
- **Real‑time collaboration** (like SurfSense’s ElectricSQL) – too complex for a single‑user system.  

---

## 3. System Overview & Architecture  

{PROJECT_NAME} consists of a **backend** (FastAPI) that handles all data, search, and AI orchestration, and a **frontend** (Tauri + React) that provides the console interface. The two communicate over local HTTP and WebSocket.

```
┌─────────────────────────────────────────────────────────────┐
│                      Tauri Console (React)                   │
│  - Custom terminal UI                                        │
│  - Communicates via REST/WebSocket (localhost)               │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                      FastAPI Backend                         │
├─────────────────────────────────────────────────────────────┤
│ Core Modules:                                                │
│  • Auth (local password)                                     │
│  • Chat & Command Engine                                     │
│  • Hybrid Search (PostgreSQL full‑text + pgvector)           │
│  • RAG with citations                                         │
│  • LLM Router (profiles + fallback)                          │
│  • Logger (encrypted JSON)                                    │
│  • Background Workers (Celery) for enrichment, TTS           │
├─────────────────────────────────────────────────────────────┤
│ Connectors (hard‑coded, minimal):                             │
│  • Local folder watcher                                       │
│  • GitHub (via OAuth)                                         │
│  • (Future: Notion, email)                                    │
├─────────────────────────────────────────────────────────────┤
│ External Services:                                            │
│  • PostgreSQL + pgvector                                      │
│  • Redis (Celery broker)                                      │
│  • Ollama (local models)                                      │
│  • SearxNG (self‑hosted web search)                           │
│  • Free APIs (OpenRouter, Gemini) – optional                  │
└─────────────────────────────────────────────────────────────┘
```

**Data Flow**  
1. User types a message or command in the console.  
2. Frontend sends request to backend API (`/api/chat`).  
3. Backend parses intent:  
   - If a question, it invokes **LLM Router** with the chosen profile.  
   - If it needs context (RAG), **Hybrid Search** retrieves relevant vault entries.  
   - The LLM generates a response with citations.  
4. Response is streamed back to frontend (WebSocket for real‑time).  
5. All interactions are logged (encrypted) for future self‑improvement.  
6. Background tasks (e.g., indexing new files, enrichment) are queued via Celery.

---

## 4. Component Specifications  

### 4.1 Backend (FastAPI)  

- **Framework**: FastAPI (Python 3.12+).  
  - Automatic OpenAPI docs at `/docs`.  
  - Async support for concurrency.  
  - Dependency injection for clean separation.  

- **Database**: PostgreSQL 14+ with **pgvector** extension.  
  - Stores:  
    - `users` table (local auth only – hashed passwords).  
    - `vault_entries` (Markdown content, metadata, tags, timestamps).  
    - `embeddings` (vector column for each chunk, linked to vault entry).  
    - `interaction_logs` (encrypted JSON).  
  - Hybrid search: `tsvector` (keywords) combined with `<#>` (cosine distance) via a weighted query.  

- **Task Queue**: Celery with Redis broker.  
  - Handles long‑running tasks:  
    - Document parsing (Docling).  
    - Embedding generation.  
    - Note enrichment (summaries, tags).  
    - Podcast generation (TTS).  
  - Flower for monitoring (optional).  

- **File Parsing**: Docling (IBM).  
  - Local, supports PDF, DOCX, images, HTML, CSV.  
  - No API key, fully private.  

- **Web Search**: Self‑hosted SearxNG.  
  - The backend queries SearxNG via its JSON API.  
  - Configured to use privacy‑friendly engines (DuckDuckGo, etc.).  
  - Results are treated as external sources and cited accordingly.  

### 4.2 Frontend (React + Vite → Tauri)  

**Phase 1a – Web Prototype (React + Vite)**  
- Purpose: Rapidly iterate on the NAVI console aesthetic and UX.  
- Tech: React 18+, Vite, CSS modules (or Tailwind for quick styling).  
- Features:  
  - Chat interface with message history.  
  - Command input (e.g., `:search quantum physics`, `:capture https://...`).  
  - Collapsible explanations (sources, reasoning).  
  - Settings panel for model profiles, API keys, and connector configuration.  
  - Real‑time updates via WebSocket.  

**Phase 1b – Tauri Desktop App**  
- Wraps the React build into a native app using Tauri.  
- Benefits:  
  - Small footprint (uses system webview).  
  - Access to system features: global hotkeys, system tray, window management.  
  - Can run in background and show notifications.  
- Additional features:  
  - Global shortcut (e.g., `Ctrl+Shift+N`) to open console.  
  - System tray icon with quick commands.  
  - Future overlay capability (always‑on‑top window).  

### 4.3 LLM Router  

- **Model Profiles** (user‑configurable via YAML file):  
  ```yaml
  profiles:
    fast_local:
      provider: ollama
      model: deepseek-r1:7b
      description: "Fast responses, good for quick questions"
    smart_api:
      provider: openrouter
      model: deepseek/deepseek-r1-0528:free
      description: "Deep reasoning, may be slower"
    balanced:
      provider: ollama
      model: llama3.2
      description: "Default local model"
  ```  
- **Routing Logic**:  
  - User can select a profile per chat or let the system choose based on task (e.g., `/reason` uses `smart_api`, `/fast` uses `fast_local`).  
  - If an API call fails (rate limit, network), fallback to a designated local profile with a notification.  
- **Provider Abstraction**:  
  - Common interface for Ollama, OpenRouter, Gemini, etc.  
  - Use environment variables for API keys (stored locally, never shared).  

### 4.4 Hybrid Search & RAG  

- **Indexing Pipeline**:  
  - When a new note/file is added:  
    1. Split content into chunks (e.g., 500 words, with overlap).  
    2. Generate embeddings using `all-MiniLM-L6-v2` (or a chosen model).  
    3. Store chunks and embeddings in PostgreSQL.  
  - Metadata (tags, source) also indexed for faceted search.  

- **Search**:  
  - User query → keyword search (PostgreSQL `tsvector`) + semantic search (pgvector cosine).  
  - Results fused using Reciprocal Rank Fusion (RRF) or weighted sum.  
  - Top‑k chunks retrieved.  

- **RAG with Citations**:  
  - Retrieved chunks are inserted into a prompt that instructs the LLM to cite sources (e.g., `[1]`, `[2]`).  
  - LLM generates answer; frontend renders citations as links to source notes.  

### 4.5 Transparency Features  

- **Collapsible Explanation**: Each answer includes a small `[?]` icon.  
  - Clicking expands to show:  
    - Which model profile was used.  
    - Which sources were retrieved (with relevance scores).  
    - Any fallback actions taken.  
- **Labeling AI‑Generated Content**: Any field added by AI (summaries, tags) is clearly marked (e.g., `✨ AI‑generated summary`).  
- **Provenance**: Original sources (file paths, URLs) are always visible.  

### 4.6 Logger (Self‑Improvement)  

- **Data Logged**:  
  - Timestamp, query, response, retrieved sources, user feedback (if any).  
  - Model used, latency, token counts.  
- **Storage**: Logs are encrypted at rest using a key derived from user password (or stored in OS keyring).  
- **User Control**: Interface to view, export, or delete logs.  
- **Future Use**: Logs can be used to train a small personal reranker or to identify usage patterns for proactive suggestions.  

### 4.7 Connectors (Hard‑coded Essentials)  

- **Local Folder Watcher**:  
  - User specifies one or more directories.  
  - Backend watches for changes (using `watchdog` library) and automatically indexes new/modified files.  
- **GitHub Connector**:  
  - OAuth flow: user creates a GitHub OAuth app and provides credentials.  
  - Fetches repos, issues, PRs, and READMEs; indexes them.  
  - Periodic sync (configurable).  
- **Future**: Notion, Gmail, Slack (patterns from SurfSense, but added only if needed).  

---

## 5. Technology Stack Rationale  

| Component | Choice | Rationale | Documentation |
|-----------|--------|-----------|---------------|
| **Backend Framework** | FastAPI | High performance, async, automatic OpenAPI, large community, proven in AI apps. | [fastapi.tiangolo.com](https://fastapi.tiangolo.com/) |
| **Database** | PostgreSQL + pgvector | Robust, ACID, excellent JSON support; pgvector is the most mature open‑source vector extension. | [pgvector](https://github.com/pgvector/pgvector) |
| **Task Queue** | Celery + Redis | Mature, widely used, supports complex workflows; Redis also used for caching. | [celeryproject.org](https://docs.celeryq.dev/) |
| **Local LLM Runner** | Ollama | Simplest way to run local models; excellent CLI and API; cross‑platform. | [ollama.com](https://ollama.com/) |
| **Embeddings** | sentence‑transformers | HuggingFace library, easy to use, many pre‑trained models. | [sbert.net](https://www.sbert.net/) |
| **File Parsing** | Docling | Local, supports many formats, from IBM, actively maintained. | [github.com/DS4SD/docling](https://github.com/DS4SD/docling) |
| **Web Search** | SearxNG | Self‑hosted, privacy‑friendly, can aggregate multiple engines. | [docs.searxng.org](https://docs.searxng.org/) |
| **Frontend (web)** | React + Vite | React is ubiquitous; Vite gives instant development experience. | [vitejs.dev](https://vitejs.dev/) |
| **Desktop Wrapper** | Tauri | Small bundle size, uses system webview, strong security model. | [tauri.app](https://tauri.app/) |
| **Logging** | Loguru + cryptography | Loguru is simple and feature‑rich; cryptography for encryption. | [loguru.readthedocs.io](https://loguru.readthedocs.io/) |
| **API Fallback** | OpenRouter / Gemini | OpenRouter offers free DeepSeek tier; Gemini has generous free tier; both have OpenAI‑compatible endpoints. | [openrouter.ai](https://openrouter.ai/), [aistudio.google.com](https://aistudio.google.com/) |

All components are open‑source, well‑documented, and have active communities. They have been chosen to balance performance, privacy, and ease of development.

---

## 6. Data Model  

### Core Tables (PostgreSQL)  

**users**  
- `id` (UUID, PK)  
- `username` (text, unique)  
- `password_hash` (text)  
- `created_at` (timestamp)  

**vault_entries**  
- `id` (UUID, PK)  
- `user_id` (UUID, FK to users)  
- `path` (text) – original file path or URL  
- `title` (text)  
- `content` (text) – Markdown  
- `metadata` (JSONB) – tags, source type, enrichment flags  
- `created_at` (timestamp)  
- `updated_at` (timestamp)  

**chunks**  
- `id` (UUID, PK)  
- `vault_entry_id` (UUID, FK)  
- `content` (text)  
- `embedding` (vector) – dimension depends on model (e.g., 384 for all‑MiniLM)  
- `index` (integer) – chunk order  

**interaction_logs**  
- `id` (UUID, PK)  
- `user_id` (UUID, FK)  
- `timestamp` (timestamp)  
- `data` (encrypted JSON) – includes query, response, sources, model, etc.  

**connector_state** (for syncing)  
- `id` (UUID, PK)  
- `user_id` (UUID, FK)  
- `connector_type` (text) – e.g., 'github', 'local_folder'  
- `config` (JSONB) – e.g., path, repo list  
- `last_sync` (timestamp)  

### Vector Index  
- PostgreSQL will use HNSW or IVFFlat indexes on the `embedding` column for fast similarity search.  
- Full‑text search index on `vault_entries.content` using GIN.  

---

## 7. API Design (Key Endpoints)  

All endpoints are under `/api/v1` and require authentication (Bearer token from login).  

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/auth/register` | POST | Register new user (local) |
| `/auth/login` | POST | Login, receive token |
| `/chat` | POST | Send a message, receive streamed response (WebSocket also available) |
| `/search` | POST | Perform hybrid search, return ranked chunks |
| `/vault/entries` | GET | List vault entries |
| `/vault/upload` | POST | Upload a file (parsed via Docling) |
| `/vault/:id` | GET | Get single entry |
| `/vault/:id/enrich` | POST | Trigger enrichment (summary, tags) |
| `/connectors` | GET | List configured connectors |
| `/connectors/github/auth` | GET | Start GitHub OAuth flow |
| `/connectors/github/callback` | GET | OAuth callback |
| `/connectors/local_folder` | POST | Add a local folder to watch |
| `/logs` | GET | Get interaction logs (decrypted on‑the‑fly) |
| `/logs/:id` | DELETE | Delete a log entry |
| `/settings` | GET | Get user settings (model profiles, API keys) |
| `/settings` | PUT | Update settings |

**WebSocket**: `/ws/chat` – for real‑time message streaming and updates.  

---

## 8. Security & Privacy Considerations  

- **Local‑first**: All data resides on the user’s machine. No cloud storage unless user explicitly configures sync.  
- **Authentication**: Local password hashed with bcrypt. No third‑party authentication.  
- **API Keys**: Stored in environment variables or encrypted user settings; never shared.  
- **Encryption**: Interaction logs encrypted at rest using a key derived from user password (via Argon2).  
- **Network**: Backend only listens on `localhost` by default; can be exposed if user desires (e.g., for mobile access), but not recommended.  
- **No Telemetry**: The application does not phone home. All analytics are local and user‑controlled.  
- **Fallback APIs**: If the user enables API fallback, they must provide their own keys; the system will never use default keys.  

---

## 9. Development Roadmap  

### Phase 1 – Console MVP (Est. 3‑4 months)  
- [ ] Set up project structure (backend + frontend)  
- [ ] Implement local authentication  
- [ ] Build basic chat with model profiles (local Ollama only)  
- [ ] Implement file upload and indexing (Docling + embeddings)  
- [ ] Implement hybrid search (pgvector + full‑text)  
- [ ] Build React console prototype with terminal aesthetic  
- [ ] Add collapsible explanations (basic citations)  
- [ ] Implement logging (encrypted)  
- [ ] Package with Tauri (optional early)  
- [ ] Write documentation and tests  

### Phase 2 – Intelligence (Est. 2‑3 months)  
- [ ] Add background enrichment pipeline (summaries, tags)  
- [ ] Improve RAG with better prompting and reranking  
- [ ] Integrate TTS (Kokoro) for podcast generation  
- [ ] Add web search via SearxNG  
- [ ] Implement GitHub connector  
- [ ] Add settings UI for profiles and API keys  
- [ ] Implement API fallback (OpenRouter/Gemini) with user consent  

### Phase 3 – Ghost (Est. 3‑4 months, optional)  
- [ ] Research Windows overlay techniques (Tauri always‑on‑top)  
- [ ] Design minimal overlay UI  
- [ ] Implement global hotkeys  
- [ ] Add voice I/O (STT + TTS)  
- [ ] Implement proactive suggestions based on logs  

---

## 10. Open Questions & Future Extensions  

- **Overlay Feasibility**: Can Tauri create a truly transparent, click‑through overlay on Windows? If not, consider a separate Electron app or a system‑level tool.  
- **Enrichment Model**: Should we use a dedicated small model (e.g., BART) for summarisation instead of the 7B chat model? Trade‑off between quality and speed.  
- **Log Encryption Key Management**: Derive from password or use OS keyring? Both have trade‑offs; we'll implement a simple password‑based encryption with user option to rotate key.  
- **Backward Compatibility**: If we borrow code from SurfSense, how to keep it updated? We'll treat it as inspiration, not a dependency.  
- **Community Contributions**: Once stable, we may open‑source {PROJECT_NAME}; the design should be modular enough to accept plugins.  
- **Mobile Access**: Could the web frontend be adapted for mobile browsers? Possibly, but not a priority.  

---

## 11. Conclusion  

{PROJECT_NAME} is a carefully scoped, privacy‑focused personal AI companion that combines the best ideas from existing open‑source projects while stripping away unnecessary complexity. By building a fresh codebase tailored to a single user’s needs, we ensure that every feature serves a clear purpose and that the system remains maintainable and extensible.  

The phased roadmap allows for incremental delivery, with a usable console in Phase 1 and advanced features added over time. The design prioritizes **transparency**, **user control**, and **aesthetic integrity** – qualities often lacking in AI tools.  

This document provides a blueprint for implementation. It is intended to be reviewed, critiqued, and refined before development begins. With a solid foundation, {PROJECT_NAME} can become a truly personal “ghost in the machine.”  
"""

DECISIONS_CONTENT = f"""# Architecture Decision Records

## [{DATE}] Use PostgreSQL + pgvector for vector storage

**Context**: Need to store embeddings for semantic search. Options: dedicated vector DB (Pinecone, Weaviate) or PostgreSQL with pgvector.

**Decision**: Use PostgreSQL + pgvector.

**Consequences**:
- Simpler operations (one database).
- Good enough performance for personal scale.
- No external dependencies, fully local.

## [{DATE}] Build new frontend from scratch (React + Tauri) instead of adapting SurfSense's Next.js

**Context**: SurfSense has a functional Next.js frontend, but it's designed for team collaboration and lacks the desired aesthetic.

**Decision**: Build a new frontend using React + Vite for rapid prototyping, then wrap with Tauri for desktop.

**Consequences**:
- Full control over UI/UX.
- More development work upfront, but cleaner codebase.
- Can iterate quickly on the console aesthetic.

## [{DATE}] Start with only two connectors: local folders and GitHub

**Context**: SurfSense has many connectors, but most are unnecessary for a personal tool.

**Decision**: Implement only local folder watcher and GitHub initially; others can be added later via plugins if needed.

**Consequences**:
- Simpler codebase, faster to MVP.
- Easier to maintain.
- User can still add new connectors by contributing.

## [{DATE}] Use YAML for model profiles

**Context**: Users need to configure which models to use for different tasks (fast local vs. smart API).

**Decision**: Store profiles in a `models.yaml` file, editable by the user.

**Consequences**:
- Easy to add new providers without code changes.
- Profiles can be shared or version‑controlled.
- Slightly more complex parsing, but worth it.

## [{DATE}] Encrypt interaction logs for privacy

**Context**: Logs are essential for future self‑improvement, but must not leak personal data.

**Decision**: Encrypt logs at rest using a key derived from the user's password (or stored in OS keyring).

**Consequences**:
- Strong privacy protection.
- User must remember password to access logs.
- Adds some complexity to logging module.
"""

ROADMAP_CONTENT = f"""# {PROJECT_NAME} Development Roadmap

## Phase 1 – Console MVP (Target: 2‑3 months)
- [x] Project structure, basic setup (docker-compose, .env)
- [ ] Local authentication (register/login)
- [ ] Chat with local Ollama models (simple, no RAG)
- [ ] File upload and indexing (Docling + embeddings)
- [ ] Hybrid search (PostgreSQL full‑text + pgvector)
- [ ] React console prototype with terminal aesthetic
- [ ] Collapsible explanations (citations)
- [ ] Encrypted logging
- [ ] Basic settings UI (model profiles, API keys)
- [ ] Tauri desktop wrapper (optional early)

## Phase 2 – Intelligence (Target: 2 months after Phase 1)
- [ ] Background enrichment (summaries, tags via local LLM)
- [ ] RAG with improved prompting and reranking
- [ ] Web search via SearxNG
- [ ] GitHub connector (OAuth, indexing)
- [ ] Podcast generation (TTS via Kokoro)
- [ ] API fallback (OpenRouter, Gemini) with user consent

## Phase 3 – Ghost (Optional, future)
- [ ] Research Windows overlay techniques
- [ ] Minimal overlay UI with global hotkeys
- [ ] Voice I/O (STT + TTS)
- [ ] Proactive suggestions based on logs

## Current Status
- **Phase**: 1 (MVP) – initial scaffolding complete.
- **Next up**: Implement chat with local Ollama models.
"""

ENV_EXAMPLE_CONTENT = """# Backend Configuration
DATABASE_URL=postgresql+asyncpg://postgres:postgres@db:5432/navig8
SECRET_KEY=change-this-to-a-random-string
NEXT_FRONTEND_URL=http://localhost:3000
AUTH_TYPE=LOCAL
REGISTRATION_ENABLED=true

# Ollama
OLLAMA_BASE_URL=http://host.docker.internal:11434   # Windows/macOS
# For Linux: OLLAMA_BASE_URL=http://172.17.0.1:11434

# Model profiles (optional, can also be set in config/models.yaml)
FAST_LLM=ollama/deepseek-r1:7b
SMART_LLM=ollama/deepseek-r1:32b

# SearxNG (self-hosted web search)
SEARXNG_HOST=http://host.docker.internal:8080
SEARXNG_VERIFY_SSL=false

# File parsing
ETL_SERVICE=DOCLING

# Logging encryption (optional key, if not set will derive from password)
# LOG_ENCRYPTION_KEY=...

# API keys for fallback (optional)
OPENROUTER_API_KEY=
GEMINI_API_KEY=

# Redis (for Celery)
REDIS_URL=redis://redis:6379/0
"""

GITIGNORE_CONTENT = """# Python
__pycache__/
*.pyc
.venv/
.env

# Node
node_modules/
dist/
build/

# Tauri
src-tauri/target/

# Logs
*.log
logs/

# Context bundle
context-bundle.txt

# OS metadata
.DS_Store
Thumbs.db
"""

PACK_CONTENT = """#!/bin/bash
# pack-context.sh – Generate a context bundle for LLMs

OUTPUT="context-bundle.txt"
echo "# Navi-G8 Context Bundle – $(date)" > "$OUTPUT"
echo "" >> "$OUTPUT"

FILES=(
    "CONTEXT.md"
    "DESIGN.md"
    "DECISIONS.md"
    "ROADMAP.md"
)

for file in "${FILES[@]}"; do
    if [ -f "$file" ]; then
        echo -e "\n# $file\n" >> "$OUTPUT"
        cat "$file" >> "$OUTPUT"
    else
        echo "Warning: $file not found"
    fi
done

# Optionally add key source files (uncomment and adjust paths)
# echo -e "\n# backend/app/main.py\n" >> "$OUTPUT"
# cat backend/app/main.py >> "$OUTPUT"

echo "Bundle created: $OUTPUT"
"""

UPDATE_CONTENT = """#!/bin/bash
# update-context.sh – Suggest updates to CONTEXT.md based on recent git commits

echo "=== Recent commits ==="
git log --oneline -5

echo ""
echo "=== Current CONTEXT.md ==="
head -20 CONTEXT.md
echo "..."

echo ""
echo "Consider updating CONTEXT.md with:"
echo "- New features or changes implemented"
echo "- Current focus (active branch)"
echo "- Next steps / open questions"
echo ""
echo "You can ask an LLM to draft updates by feeding it the git log and the current CONTEXT.md."
"""

MODELS_YAML_CONTENT = """profiles:
  fast_local:
    provider: ollama
    model: deepseek-r1:7b
    description: "Fast responses, good for quick questions"
  smart_api:
    provider: openrouter
    model: deepseek/deepseek-r1-0528:free
    description: "Deep reasoning, may be slower"
  balanced:
    provider: ollama
    model: llama3.2
    description: "Default local model"
"""

DOCKER_COMPOSE_CONTENT = """version: '3.8'

services:
  db:
    image: postgres:14
    environment:
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: postgres
      POSTGRES_DB: navig8
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres"]
      interval: 5s
      timeout: 5s
      retries: 5

  redis:
    image: redis:7
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 5s
      timeout: 5s
      retries: 5

  backend:
    build: ./backend
    ports:
      - "8000:8000"
    env_file:
      - .env
    depends_on:
      db:
        condition: service_healthy
      redis:
        condition: service_healthy
    volumes:
      - ./backend:/app
      - ~/.ollama:/root/.ollama  # For Ollama access (if needed)
    extra_hosts:
      - "host.docker.internal:host-gateway"  # For accessing host services (Ollama, SearxNG)

  frontend:
    build: ./frontend
    ports:
      - "3000:3000"
    environment:
      - NEXT_PUBLIC_FASTAPI_BACKEND_URL=http://localhost:8000
      - NEXT_PUBLIC_FASTAPI_BACKEND_AUTH_TYPE=LOCAL
    depends_on:
      - backend
    volumes:
      - ./frontend:/app
      - /app/node_modules

volumes:
  postgres_data:
  redis_data:
"""

# Backend placeholders
BACKEND_MAIN_PY = '''# backend/app/main.py
from fastapi import FastAPI

app = FastAPI(title="Navi-G8 API")

@app.get("/")
def root():
    return {"message": "Navi-G8 Backend"}
'''

BACKEND_REQUIREMENTS_TXT = """fastapi==0.115.0
uvicorn[standard]==0.30.1
asyncpg==0.29.0
pgvector==0.2.5
sqlalchemy==2.0.23
celery==5.3.6
redis==5.0.1
python-dotenv==1.0.0
httpx==0.27.0
docling==0.2.0  # hypothetical version
sentence-transformers==2.5.1
loguru==0.7.2
cryptography==42.0.5
"""

BACKEND_DOCKERFILE = """FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
"""

FRONTEND_PACKAGE_JSON = """{
  "name": "navig8-frontend",
  "version": "0.1.0",
  "private": true,
  "scripts": {
    "dev": "vite",
    "build": "vite build",
    "preview": "vite preview"
  },
  "dependencies": {
    "react": "^18.2.0",
    "react-dom": "^18.2.0"
  },
  "devDependencies": {
    "@vitejs/plugin-react": "^4.0.0",
    "vite": "^5.0.0"
  }
}
"""

FRONTEND_INDEX_HTML = """<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <link rel="icon" type="image/svg+xml" href="/vite.svg" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>Navi-G8 Console</title>
  </head>
  <body>
    <div id="root"></div>
    <script type="module" src="/src/main.tsx"></script>
  </body>
</html>
"""

FRONTEND_MAIN_TSX = """import React from 'react'
import ReactDOM from 'react-dom/client'
import App from './App'
import './index.css'

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
)
"""

FRONTEND_APP_TSX = """import React from 'react'

function App() {
  return (
    <div style={{
      backgroundColor: '#0a0e12',
      color: '#33ff33',
      fontFamily: 'monospace',
      height: '100vh',
      padding: '1rem',
    }}>
      <div style={{ whiteSpace: 'pre-wrap' }}>
        Welcome to Navi-G8 Console. Type your message...
      </div>
    </div>
  )
}

export default App
"""

FRONTEND_INDEX_CSS = """body {
  margin: 0;
  padding: 0;
  background-color: #0a0e12;
  color: #33ff33;
  font-family: 'Courier New', monospace;
}
"""

FRONTEND_DOCKERFILE = """FROM node:20-alpine
WORKDIR /app
COPY package*.json ./
RUN npm install
COPY . .
EXPOSE 3000
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0"]
"""

# -------------------- Create directories and files --------------------
def main():
    print(f"Setting up {PROJECT_NAME} project in {BASE_DIR}")

    # Create directories
    dirs = [
        "backend/app/routers",
        "backend/app/services",
        "backend/app/connectors",
        "backend/app/models",
        "backend/app/core",
        "backend/tests",
        "frontend/src/components",
        "frontend/public",
        "docs",
        "scripts",
        "config",
    ]
    for d in dirs:
        (BASE_DIR / d).mkdir(parents=True, exist_ok=True)

    # Write files
    write_file(BASE_DIR / "README.md", README_CONTENT)
    write_file(BASE_DIR / "CONTEXT.md", CONTEXT_CONTENT)
    write_file(BASE_DIR / "DESIGN.md", DESIGN_FULL)
    write_file(BASE_DIR / "DECISIONS.md", DECISIONS_CONTENT)
    write_file(BASE_DIR / "ROADMAP.md", ROADMAP_CONTENT)
    write_file(BASE_DIR / ".env.example", ENV_EXAMPLE_CONTENT)
    write_file(BASE_DIR / ".gitignore", GITIGNORE_CONTENT)
    write_file(BASE_DIR / "docker-compose.yml", DOCKER_COMPOSE_CONTENT)

    write_file(BASE_DIR / "scripts/pack-context.sh", PACK_CONTENT)
    write_file(BASE_DIR / "scripts/update-context.sh", UPDATE_CONTENT)

    write_file(BASE_DIR / "config/models.yaml", MODELS_YAML_CONTENT)

    # Backend placeholders
    write_file(BASE_DIR / "backend/app/main.py", BACKEND_MAIN_PY)
    write_file(BASE_DIR / "backend/requirements.txt", BACKEND_REQUIREMENTS_TXT)
    write_file(BASE_DIR / "backend/Dockerfile", BACKEND_DOCKERFILE)
    write_file(BASE_DIR / "backend/.env", "")  # empty for now

    # Frontend placeholders
    write_file(BASE_DIR / "frontend/package.json", FRONTEND_PACKAGE_JSON)
    write_file(BASE_DIR / "frontend/index.html", FRONTEND_INDEX_HTML)
    write_file(BASE_DIR / "frontend/src/main.tsx", FRONTEND_MAIN_TSX)
    write_file(BASE_DIR / "frontend/src/App.tsx", FRONTEND_APP_TSX)
    write_file(BASE_DIR / "frontend/src/index.css", FRONTEND_INDEX_CSS)
    write_file(BASE_DIR / "frontend/Dockerfile", FRONTEND_DOCKERFILE)

    # Additional docs placeholders
    write_file(BASE_DIR / "docs/api.md", "# API Documentation\n\n(To be filled)")
    write_file(BASE_DIR / "docs/data-model.md", "# Data Model\n\n(To be filled)")
    write_file(BASE_DIR / "docs/installation.md", "# Installation Guide\n\n(To be filled)")

    # Make scripts executable (Unix-like)
    try:
        os.chmod(BASE_DIR / "scripts/pack-context.sh", 0o755)
        os.chmod(BASE_DIR / "scripts/update-context.sh", 0o755)
    except Exception:
        pass  # Windows may ignore

    print("\n✅ Project scaffold created successfully!")
    print("Next steps:")
    print("1. Review and edit .env.example, then copy to .env")
    print("2. Run `docker compose up --build` to start services")
    print("3. Open http://localhost:3000 and start developing")
    print("4. Use `./scripts/pack-context.sh` before starting a new LLM session")

if __name__ == "__main__":
    main()