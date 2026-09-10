# Navi-G8

> **A persistent cognitive layer for your workstation.** *(Aspirational — see [Roadmap](#roadmap) for current state.)*

Navi-G8 is an early-stage experiment in building a locally-running, graph-based cognitive layer that lives alongside your projects. It is **not** a finished product. Many of the features described in the philosophy and roadmap are planned but not yet implemented. This README describes what exists today, honestly, and what is being built toward.

---

## Table of Contents

- [What It Is (Today)](#what-it-is-today)
- [What It Is Not](#what-it-is-not)
- [Current Features](#current-features)
- [Known Gaps](#known-gaps)
- [Planned Features](#planned-features)
- [Architecture](#architecture)
- [Quick Start](#quick-start)
- [Usage](#usage)
- [Configuration](#configuration)
- [Project Structure](#project-structure)
- [Roadmap](#roadmap)
- [Philosophy](#philosophy)
- [Contributing](#contributing)

---

## What It Is (Today)

Navi-G8 is a locally-running Python daemon paired with a Tauri desktop shell. It maintains a graph-based memory of nodes and edges, queries an LLM (local via Ollama, or cloud via OpenAI/Groq), and returns structured responses.

**Concretely, the system currently:**

- Runs a Python daemon that listens on a local TCP socket (`127.0.0.1:9876`).
- Exposes a Tauri desktop window with a field state panel, graph view, and terminal.
- Stores nodes (Trajectory, Stream, Perturbation, Clarification, FalseProblemFlag, Session) and edges in a local SQLite database.
- Maintains a ChromaDB vector index for semantic retrieval.
- Calls an LLM with enriched context and parses the response into **Insight + Action + Confidence**.
- Persists the session ID to disk so the field can be re-entered.

**What this means in practice:** You can launch the desktop app, type a query, and receive a structured LLM response that is stored in a graph. The graph is queryable. The session persists.

**What this does not yet mean:** The graph is frequently empty because session linking is incomplete (see [Known Gaps](#known-gaps)). Context enrichment is shallow. There is no agent loop, no tool calling, and no project isolation.

---

## What It Is Not

- **Not a cloud service.** All data stays on your machine.
- **Not a coding agent.** There is no tool-calling loop yet. It does not edit files autonomously.
- **Not a finished product.** This is an early-stage project. The core architecture is in place; the cognitive layer is incomplete.
- **Not a replacement for your IDE.** IDE integration is planned (via ACP) but not implemented.

---

## Current Features

| Feature | Status | Notes |
|---|---|---|
| **Python Daemon** | ✅ Working | Local TCP socket server on `127.0.0.1:9876`. |
| **Tauri Desktop Shell** | ✅ Working | Native window with field state panel, graph view, and terminal. |
| **Graph Store** | ✅ Working | SQLite-backed storage for nodes and edges. |
| **Semantic Index** | ✅ Working | ChromaDB with `all-MiniLM-L6-v2` embeddings. |
| **LLM Gateway** | ✅ Working | OpenAI-compatible API. Primary: Ollama. Fallback: Groq (if configured). |
| **Orchestrator** | ⚠️ Partial | Enriches prompts, calls LLM, parses response, updates graph. Does not traverse edges or use an agent loop. |
| **Session Persistence** | ✅ Working | Session ID saved to `~/.navi-g8/session_id.txt`. |
| **Graph Visualisation** | ⚠️ Partial | vis-network renders nodes and edges, but the graph is often empty (see [Known Gaps](#known-gaps)). |
| **Terminal UI (test harness)** | ✅ Working | `python -m navi_agent` runs a terminal-based field interface. |
| **Data Models** | ✅ Working | Pydantic models for all node types. |
| **MCP Tools** | ✅ Working | `read_file`, `write_file`, `list_directory`, `web_search` exist as standalone functions. Not yet integrated with the daemon's agent loop. |

---

## Known Gaps

The following are known issues that affect current usability. These are documented here so that contributors and users understand the state of the system.

| Gap | Impact | Planned Fix |
|---|---|---|
| **`BELONGS_TO` edges are never created.** | `get_field_state()` filters by `BELONGS_TO` edges, but no code creates them. The graph appears empty even after use. | Phase 1: Link every node created in a session to the session via `BELONGS_TO`. |
| **No graph traversal for context.** | The orchestrator sends the LLM isolated nodes (via vector search and recent clarifications), not a causal narrative. | Phase 1: Implement `_render_field_report()` — a graph traversal that renders a field report as prose. |
| **Coherence metric is meaningless.** | Coherence is calculated as `(old + confidence) / 2`. It does not measure field health. | Phase 1: Replace with a metric based on active trajectories, resolved perturbations, and unresolved flags. |
| **No agent loop.** | The LLM cannot iteratively call tools. It receives a prompt and returns a response. | Phase 2: Implement a tool-calling loop with guards against runaway iteration. |
| **No mode switching.** | The system prompt is static. There is no distinction between attentive, reflective, or silent operation. | Phase 2: Add heuristic mode detection and mode-specific prompts. |
| **No permission model.** | The orchestrator has full access to all tools at all times. | Phase 2: Implement allow/ask/deny per tool per mode. |
| **No project isolation.** | There is a single global graph store. Multiple projects share the same memory. | Phase 3: Implement a project registry with per-project graph stores. |
| **No file watcher.** | `watchdog` is listed as a dependency but not imported. File changes are not detected. | Phase 3: Integrate `watchdog` to create Stream/Perturbation nodes automatically. |
| **No ACP integration.** | The daemon cannot connect to IDEs (VS Code, Zed, etc.). | Phase 5: Implement an ACP entry point. |
| **Duplicate `index.py`.** | `scaffold/index.py` is dead code. | Delete it. |

---

## Planned Features

The following are planned for future phases. They are listed here to communicate the direction of the project, not to imply they are imminent.

### Phase 2 — Agent Architecture

| Feature | Description |
|---|---|
| **Agent roster** | Attend, Reflect, Explore, Plan, Observe, Verify. Each has a distinct purpose, tool set, and permission level. |
| **Mode detection** | Heuristic classifier (regex-based) selects the appropriate agent based on query shape. Ambiguous cases fall back to the LLM for classification. |
| **Permission model** | Three-tier: `allow`, `ask`, `deny`. Rules take priority over mode defaults. |
| **Tool-calling loop** | The LLM can iteratively call tools (`read_file`, `write_file`, `web_search`, `query_graph`) and receive results before producing a final response. |
| **Subagent support** | Explore and Verify run in isolated context windows and return structured summaries to the orchestrator. |

### Phase 3 — Project Registry

| Feature | Description |
|---|---|
| **Project registry** | `~/.navi-g8/projects.json` tracks all bound projects. Each project has its own graph store and clarity index. |
| **`/bind` command** | Scans a directory, creates Stream nodes for each file, and creates an initial Trajectory. |
| **Project switching** | Frontend selector lets the user switch between projects. The daemon routes accordingly. |
| **File watcher** | `watchdog` detects file changes and creates Perturbation/Stream nodes. |

### Phase 4 — Local LLM Routing

| Feature | Description |
|---|---|
| **Task classifier** | Routes requests to the appropriate model based on task type (triage, code, reasoning, embeddings). |
| **Model router** | OpenAI-compatible gateway that selects from locally-running models based on task, VRAM, and queue depth. |
| **Web search triggers** | The agent can request web search when confidence is low or the query requires external knowledge. |

### Phase 5 — ACP Integration

| Feature | Description |
|---|---|
| **ACP entry point** | `python -m navi_agent --mode acp` runs the daemon as an ACP-compliant agent, connectable to VS Code, Zed, and other ACP-compatible editors. |
| **JSON-RPC over stdio** | Implements `initialize`, `session/new`, `session/prompt`, `session/cancel`. |
| **Capability negotiation** | Advertises filesystem access, terminal access, and diff support. |

### Phase 6 — Self-Improvement & Polish

| Feature | Description |
|---|---|
| **Interaction logging** | Every query, tool call, and outcome is logged. |
| **Protocol refinement** | System prompts are adjusted based on usage patterns. |
| **Tool learning** | New tools are generated from recurring patterns. |
| **System tray** | Runs persistently in the background. |
| **Inspector panel** | Click a node in the graph to see its full details and related edges. |

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         NAVI-G8 – CURRENT ARCHITECTURE                    │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                      FIELD INTERFACE (Tauri)                        │   │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐                  │   │
│  │  │ Field State │  │ Graph View  │  │  Terminal   │                  │   │
│  │  │   Panel     │  │ (vis-network)│  │             │                  │   │
│  │  └─────────────┘  └─────────────┘  └─────────────┘                  │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                    │                                        │
│                                    │ Socket (127.0.0.1:9876)               │
│                                    ▼                                        │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                      FIELD ORCHESTRATOR (Python)                    │   │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐                  │   │
│  │  │  Protocol A │  │  Protocol B │  │  Protocol C │                  │   │
│  │  │  (Re-Entry) │  │  (Execution)│  │ (Debugging) │                  │   │
│  │  └─────────────┘  └─────────────┘  └─────────────┘                  │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                    │                                        │
│           ┌────────────────────────┼────────────────────────┐              │
│           │                        │                        │              │
│           ▼                        ▼                        ▼              │
│  ┌─────────────────┐  ┌─────────────────────┐  ┌─────────────────────┐   │
│  │   Graph Store   │  │   Clarity Index     │  │   LLM Gateway       │   │
│  │   (SQLite)      │  │   (ChromaDB)        │  │   (Ollama/OpenAI)   │   │
│  └─────────────────┘  └─────────────────────┘  └─────────────────────┘   │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                      DATA MODELS (Pydantic)                         │   │
│  │  Trajectory | Stream | Perturbation | Clarification | Flag | Session│   │
│  └─────────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Layer Breakdown

| Layer | Component | Technology | Status |
|---|---|---|---|
| **L0 – Ontology** | Data models | Pydantic | ✅ Working |
| **L1 – Memory** | Graph Store | SQLite | ✅ Working (session linking incomplete) |
| **L2 – Meaning** | Clarity Index | ChromaDB + sentence-transformers | ✅ Working |
| **L3 – Brain** | Orchestrator | Python (async) | ⚠️ Partial |
| **L4 – Body** | Tauri Desktop | Rust + React + TypeScript | ✅ Working |
| **L5 – Gateway** | LLM Gateway | OpenAI-compatible API | ✅ Working |
| **L5 – Tools** | File/Web Tools | MCP-compliant | ✅ Exist, not integrated with agent loop |

---

## Quick Start

### Prerequisites

- **Python 3.12+**
- **Node.js 20+**
- **Rust** (for Tauri)
- **Ollama** (or an OpenAI-compatible API key)

### 1. Clone the Repository

```bash
git clone https://github.com/Git-Lister/Navi-G8.git
cd Navi-G8
```

### 2. Set Up the Agent

```bash
cd agent
python -m venv .venv
.venv\Scripts\activate          # Windows
# source .venv/bin/activate      # macOS/Linux
pip install -e .
pip install -e ".[dev]"
```

### 3. Pull an LLM Model

```bash
ollama pull llama3.1
```

### 4. Run the Terminal UI (Test Harness)

```bash
python -m navi_agent
```

### 5. Run the Desktop App (Tauri)

```bash
cd ../desktop
npm install
npm run tauri dev
```

---

## Usage

### Terminal Commands

| Command | Effect |
|---|---|
| `exit` / `quit` / `goodbye` | Exit the field. |
| `reset session` | Reset the session and start fresh. |
| *Any natural language* | Processed by the orchestrator. |

### Example Interaction

```
➜ Hello, how are you fielding today?
💡 INSIGHT The current field state is characterized by a relative calm...
⚡ ACTION None
📊 Confidence: 0.75
```

---

## Configuration

### Environment Variables (`.env`)

```bash
# LLM API Keys (optional, only needed if using cloud models)
OPENAI_API_KEY=sk-...
GROQ_API_KEY=...

# Local LLM (Ollama)
OLLAMA_BASE_URL=http://localhost:11434

# Search API (optional)
TAVILY_API_KEY=...
```

### Config File (`config.toml`)

```toml
[workspace]
watch_folders = ["~/Documents", "~/Projects"]
exclude_extensions = [".tmp", ".log", ".pyc", ".class"]
max_file_size_bytes = 1048576

[llm]
primary_model = "llama3.1"
primary_base = "http://localhost:11434/v1"
fallback_model = "llama-3.1-70b-versatile"
fallback_base = "https://api.groq.com/openai/v1"
allow_cloud = false
```

---

## Project Structure

```
Navi-G8/
├── .github/workflows/          # CI/CD
├── agent/                      # Python backend
│   ├── src/
│   │   └── navi_agent/
│   │       ├── scaffold/       # Cognitive layer
│   │       │   ├── models.py
│   │       │   ├── graph_store.py
│   │       │   ├── clarity_index.py
│   │       │   └── orchestrator.py
│   │       ├── tools/          # MCP tools
│   │       │   ├── file_tools.py
│   │       │   └── web_tools.py
│   │       ├── ui/             # Terminal UI (test harness)
│   │       ├── __main__.py     # Entry point (terminal + daemon)
│   │       ├── core.py         # MCP server
│   │       └── gateway.py      # LLM Gateway
│   ├── tests/
│   └── pyproject.toml
├── desktop/                    # Tauri frontend
│   ├── src/
│   │   ├── App.tsx
│   │   ├── App.css
│   │   └── components/
│   │       └── GraphView.tsx
│   ├── src-tauri/              # Rust backend for Tauri
│   └── package.json
├── diagnose_backend.py         # Diagnostic harness
├── config.toml
├── .env.example
└── README.md
```

---

## Roadmap

### Phase 1: Foundation Fixes (Next)

- [ ] Fix `BELONGS_TO` edge creation (graph visibility)
- [ ] Implement `_render_field_report()` (graph-to-prose bridge)
- [ ] Replace meaningless coherence metric
- [ ] Delete duplicate `index.py`

### Phase 2: Agent Architecture

- [ ] Agent roster (Attend, Reflect, Explore, Plan, Observe, Verify)
- [ ] Mode detection (heuristic classifier)
- [ ] Mode-specific prompts
- [ ] Permission model (allow / ask / deny)
- [ ] Tool-calling loop with guards
- [ ] Subagent support (isolated context, structured handoff)

### Phase 3: Project Registry

- [ ] `projects.json` registry
- [ ] Per-project graph stores
- [ ] `/bind` command
- [ ] Project switching
- [ ] File watcher (`watchdog`)

### Phase 4: Local LLM Routing

- [ ] Task classifier
- [ ] Model router (OpenAI-compatible gateway)
- [ ] Web search triggers

### Phase 5: ACP Integration

- [ ] ACP entry point (`--mode acp`)
- [ ] JSON-RPC over stdio
- [ ] Capability negotiation
- [ ] Test in Zed / VS Code

### Phase 6: Self-Improvement & Polish

- [ ] Interaction logging
- [ ] Protocol refinement
- [ ] Tool learning
- [ ] System tray
- [ ] Inspector panel

---

## Philosophy

Navi-G8 is built on a simple premise: **insight precedes action**.

The system does not optimise for user satisfaction or "helpfulness scores." It optimises for **coherence** — the alignment between the field state and the user's actual context.

| Principle | Meaning |
|---|---|
| **Insight precedes action** | Understanding comes before doing. Navi-G8 clarifies before it acts. |
| **Process over thing** | Files, functions, and errors are not static entities — they are processes that evolve. |
| **False problems are beautiful** | Uncertainty is not a bug; it is a signal. Navi-G8 tracks it openly. |
| **Ecstasy is a byproduct** | The joy of a fix is welcome, but clarity is the goal. |
| **The field is shared** | You and Navi-G8 are not separate agents. You are a single cognitive system. |

These principles are informed by a wide range of sources — from systems theory to contemplative philosophy to the cyberpunk fiction that shaped the project's aesthetic. The name "Navi-G8" and the "Ghost-Wire" tagline are gestures toward the idea of a persistent, invisible intelligence woven into the fabric of your work.

---

## Contributing

This is a personal project, but contributions are welcome. Before submitting a pull request:

1. Ensure your code passes linting (`ruff check`).
2. Ensure all tests pass (`pytest`).
3. Update the README if you add new features.
4. Follow the existing code style.

---
