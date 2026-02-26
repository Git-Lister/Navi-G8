# Navi-G8 – Project Context (Updated 2026-02-26)

## 🎯 Vision
Navi-G8 is a personal, local‑first AI companion that lives alongside the user’s digital life, learns their knowledge and working patterns, and provides intelligent assistance while respecting absolute privacy. It takes aesthetic inspiration from *Serial Experiments Lain*: a "ghost in the machine" that feels like an extension of thought.

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
