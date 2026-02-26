# Navi-G8 Development Roadmap

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
