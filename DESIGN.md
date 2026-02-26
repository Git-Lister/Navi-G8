# Navi-G8 – Personal AI Knowledge Companion  
## Comprehensive Design Document  

**Version:** 2.0  
**Date:** 2026-02-26  
**Status:** Draft for Review  

---

## 1. Executive Summary  

Navi-G8 is a **personal, local-first AI operating companion** – a system that lives alongside the user’s digital life, learns their knowledge and working patterns, and provides intelligent assistance while respecting absolute privacy. Named after the NAVI terminal in *Serial Experiments Lain*, it aims to feel like an extension of thought rather than a collection of disconnected tools.

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

Navi-G8 consists of a **backend** (FastAPI) that handles all data, search, and AI orchestration, and a **frontend** (Tauri + React) that provides the console interface. The two communicate over local HTTP and WebSocket.

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
- **Community Contributions**: Once stable, we may open‑source Navi-G8; the design should be modular enough to accept plugins.  
- **Mobile Access**: Could the web frontend be adapted for mobile browsers? Possibly, but not a priority.  

---

## 11. Conclusion  

Navi-G8 is a carefully scoped, privacy‑focused personal AI companion that combines the best ideas from existing open‑source projects while stripping away unnecessary complexity. By building a fresh codebase tailored to a single user’s needs, we ensure that every feature serves a clear purpose and that the system remains maintainable and extensible.  

The phased roadmap allows for incremental delivery, with a usable console in Phase 1 and advanced features added over time. The design prioritizes **transparency**, **user control**, and **aesthetic integrity** – qualities often lacking in AI tools.  

This document provides a blueprint for implementation. It is intended to be reviewed, critiqued, and refined before development begins. With a solid foundation, Navi-G8 can become a truly personal “ghost in the machine.”  
