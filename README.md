# Navi-G8 – Personal AI Knowledge Companion

Navi-G8 is a **personal, local‑first AI operating companion** that lives alongside your digital life, learns your knowledge and working patterns, and provides intelligent assistance while respecting absolute privacy. Inspired by *Serial Experiments Lain*, it aims to feel like an extension of thought – quiet, present, and deeply integrated.

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
git clone https://github.com/yourusername/navi-g8.git
cd navi-g8
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
