# Architecture Decision Records

## [2026-02-26] Use PostgreSQL + pgvector for vector storage

**Context**: Need to store embeddings for semantic search. Options: dedicated vector DB (Pinecone, Weaviate) or PostgreSQL with pgvector.

**Decision**: Use PostgreSQL + pgvector.

**Consequences**:
- Simpler operations (one database).
- Good enough performance for personal scale.
- No external dependencies, fully local.

## [2026-02-26] Build new frontend from scratch (React + Tauri) instead of adapting SurfSense's Next.js

**Context**: SurfSense has a functional Next.js frontend, but it's designed for team collaboration and lacks the desired aesthetic.

**Decision**: Build a new frontend using React + Vite for rapid prototyping, then wrap with Tauri for desktop.

**Consequences**:
- Full control over UI/UX.
- More development work upfront, but cleaner codebase.
- Can iterate quickly on the console aesthetic.

## [2026-02-26] Start with only two connectors: local folders and GitHub

**Context**: SurfSense has many connectors, but most are unnecessary for a personal tool.

**Decision**: Implement only local folder watcher and GitHub initially; others can be added later via plugins if needed.

**Consequences**:
- Simpler codebase, faster to MVP.
- Easier to maintain.
- User can still add new connectors by contributing.

## [2026-02-26] Use YAML for model profiles

**Context**: Users need to configure which models to use for different tasks (fast local vs. smart API).

**Decision**: Store profiles in a `models.yaml` file, editable by the user.

**Consequences**:
- Easy to add new providers without code changes.
- Profiles can be shared or version‑controlled.
- Slightly more complex parsing, but worth it.

## [2026-02-26] Encrypt interaction logs for privacy

**Context**: Logs are essential for future self‑improvement, but must not leak personal data.

**Decision**: Encrypt logs at rest using a key derived from the user's password (or stored in OS keyring).

**Consequences**:
- Strong privacy protection.
- User must remember password to access logs.
- Adds some complexity to logging module.
