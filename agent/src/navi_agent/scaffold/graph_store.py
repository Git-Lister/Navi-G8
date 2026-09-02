"""
Navi-G8 Graph Store – SQLite-backed persistent event trace.

Provides CRUD operations for nodes and edges, with temporal querying.
All operations are synchronous (SQLite is local) but wrapped for async use.
"""

import json
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from .models import (
    Clarification,
    Edge,
    EdgeType,
    FalseProblemFlag,
    FieldState,
    Node,
    NodeType,
    Perturbation,
    Session,
    Stream,
    Trajectory,
    TrajectoryStatus,
)

# ─── Schema ────────────────────────────────────────────────────────────

SCHEMA = """
-- Nodes table (all node types stored here)
CREATE TABLE IF NOT EXISTS nodes (
    id TEXT PRIMARY KEY,
    type TEXT NOT NULL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    metadata TEXT,  -- JSON blob for flexible fields
    -- Type-specific fields (nullable)
    description TEXT,
    bearing TEXT,
    status TEXT,
    history TEXT,  -- JSON list
    path TEXT,
    signature TEXT,
    volatility REAL,
    version INTEGER,
    stack_trace TEXT,
    severity TEXT,
    frequency INTEGER,
    resolved INTEGER,  -- boolean
    resolution_insight TEXT,
    rationale TEXT,
    resolved_nodes TEXT,  -- JSON list
    context TEXT,
    started_at TEXT,
    ended_at TEXT,
    coherence_history TEXT  -- JSON list
);

-- Edges table
CREATE TABLE IF NOT EXISTS edges (
    id TEXT PRIMARY KEY,
    source_id TEXT NOT NULL,
    target_id TEXT NOT NULL,
    type TEXT NOT NULL,
    created_at TEXT NOT NULL,
    metadata TEXT,  -- JSON blob
    FOREIGN KEY (source_id) REFERENCES nodes(id),
    FOREIGN KEY (target_id) REFERENCES nodes(id)
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_nodes_type ON nodes(type);
CREATE INDEX IF NOT EXISTS idx_nodes_status ON nodes(status);
CREATE INDEX IF NOT EXISTS idx_nodes_created_at ON nodes(created_at);
CREATE INDEX IF NOT EXISTS idx_edges_source ON edges(source_id);
CREATE INDEX IF NOT EXISTS idx_edges_target ON edges(target_id);
CREATE INDEX IF NOT EXISTS idx_edges_type ON edges(type);
"""


# ─── Graph Store ──────────────────────────────────────────────────────


class GraphStore:
    """
    SQLite-backed graph store for Navi-G8's event trace.

    Usage:
        store = GraphStore("~/.navi-g8/graph.db")
        store.init_db()
        node = Trajectory(description="Build pipeline")
        store.add_node(node)
        store.add_edge(Edge(source_id=node.id, target_id=other.id, type=EdgeType.PRECEDES))
    """

    def __init__(self, db_path: Union[str, Path]):
        self.db_path = Path(db_path).expanduser().resolve()
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

    def _connect(self) -> sqlite3.Connection:
        """Get a connection with row_factory for dict access."""
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        return conn

    def init_db(self) -> None:
        """Create tables if they don't exist."""
        with self._connect() as conn:
            conn.executescript(SCHEMA)

    # ─── Node Operations ──────────────────────────────────────────────

    def add_node(self, node: Node) -> None:
        """Insert a node into the graph."""
        with self._connect() as conn:
            # Convert node to dict
            data = node.model_dump(mode="json")
            # Flatten type-specific fields
            row = {
                "id": data.get("id"),
                "type": data.get("type"),
                "created_at": data.get("created_at"),
                "updated_at": data.get("updated_at"),
                "metadata": json.dumps(data.get("metadata", {})),
                "description": data.get("description"),
                "bearing": data.get("bearing"),
                "status": data.get("status"),
                "history": json.dumps(data.get("history", [])) if data.get("history") else None,
                "path": data.get("path"),
                "signature": data.get("signature"),
                "volatility": data.get("volatility"),
                "version": data.get("version"),
                "stack_trace": data.get("stack_trace"),
                "severity": data.get("severity"),
                "frequency": data.get("frequency"),
                "resolved": 1 if data.get("resolved") else 0,
                "resolution_insight": data.get("resolution_insight"),
                "rationale": data.get("rationale"),
                "resolved_nodes": json.dumps(data.get("resolved_nodes", []))
                if data.get("resolved_nodes")
                else None,
                "context": data.get("context"),
                "started_at": data.get("started_at"),
                "ended_at": data.get("ended_at"),
                "coherence_history": json.dumps(data.get("coherence_history", []))
                if data.get("coherence_history")
                else None,
            }
            # Build INSERT statement dynamically
            columns = ", ".join(row.keys())
            placeholders = ", ".join("?" * len(row))
            query = f"INSERT OR REPLACE INTO nodes ({columns}) VALUES ({placeholders})"
            conn.execute(query, list(row.values()))

    def get_node(self, node_id: str) -> Optional[Node]:
        """Retrieve a node by ID, returning the appropriate model type."""
        with self._connect() as conn:
            row = conn.execute("SELECT * FROM nodes WHERE id = ?", (node_id,)).fetchone()
            if not row:
                return None
            return self._row_to_node(row)

    def get_nodes(self, node_ids: List[str]) -> List[Node]:
        """Retrieve multiple nodes by ID."""
        if not node_ids:
            return []
        with self._connect() as conn:
            placeholders = ", ".join("?" * len(node_ids))
            rows = conn.execute(
                f"SELECT * FROM nodes WHERE id IN ({placeholders})", node_ids
            ).fetchall()
            return [self._row_to_node(row) for row in rows]

    def query_nodes(
        self,
        node_type: Optional[NodeType] = None,
        status: Optional[TrajectoryStatus] = None,
        resolved: Optional[bool] = None,
        limit: int = 100,
    ) -> List[Node]:
        """Query nodes with filters."""
        with self._connect() as conn:
            conditions = []
            params = []
            if node_type:
                conditions.append("type = ?")
                params.append(node_type.value)
            if status:
                conditions.append("status = ?")
                params.append(status.value)
            if resolved is not None:
                conditions.append("resolved = ?")
                params.append(1 if resolved else 0)

            where = " AND ".join(conditions) if conditions else "1=1"
            query = f"SELECT * FROM nodes WHERE {where} LIMIT ?"
            params.append(limit)
            rows = conn.execute(query, params).fetchall()
            return [self._row_to_node(row) for row in rows]

    # ─── Edge Operations ──────────────────────────────────────────────

    def add_edge(self, edge: Edge) -> None:
        """Insert an edge into the graph."""
        with self._connect() as conn:
            conn.execute(
                "INSERT OR REPLACE INTO edges (id, source_id, target_id, type, created_at, metadata) VALUES (?, ?, ?, ?, ?, ?)",
                (
                    edge.id,
                    edge.source_id,
                    edge.target_id,
                    edge.type.value,
                    edge.created_at.isoformat(),
                    json.dumps(edge.metadata),
                ),
            )

    def get_edges(
        self, source_id: Optional[str] = None, target_id: Optional[str] = None
    ) -> List[Edge]:
        """Retrieve edges with optional source/target filters."""
        with self._connect() as conn:
            conditions = []
            params = []
            if source_id:
                conditions.append("source_id = ?")
                params.append(source_id)
            if target_id:
                conditions.append("target_id = ?")
                params.append(target_id)

            where = " AND ".join(conditions) if conditions else "1=1"
            rows = conn.execute(f"SELECT * FROM edges WHERE {where}", params).fetchall()
            return [
                Edge(
                    id=row["id"],
                    source_id=row["source_id"],
                    target_id=row["target_id"],
                    type=EdgeType(row["type"]),
                    created_at=datetime.fromisoformat(row["created_at"]),
                    metadata=json.loads(row["metadata"]) if row["metadata"] else {},
                )
                for row in rows
            ]

    def get_adjacent_nodes(self, node_id: str, direction: str = "both") -> List[Node]:
        """Get all nodes connected to the given node."""
        with self._connect() as conn:
            if direction == "outgoing":
                rows = conn.execute(
                    "SELECT n.* FROM nodes n JOIN edges e ON n.id = e.target_id WHERE e.source_id = ?",
                    (node_id,),
                ).fetchall()
            elif direction == "incoming":
                rows = conn.execute(
                    "SELECT n.* FROM nodes n JOIN edges e ON n.id = e.source_id WHERE e.target_id = ?",
                    (node_id,),
                ).fetchall()
            else:  # both
                rows = conn.execute(
                    """
                    SELECT n.* FROM nodes n JOIN edges e ON n.id = e.target_id WHERE e.source_id = ?
                    UNION
                    SELECT n.* FROM nodes n JOIN edges e ON n.id = e.source_id WHERE e.target_id = ?
                    """,
                    (node_id, node_id),
                ).fetchall()
            return [self._row_to_node(row) for row in rows]

    # ─── Field State ──────────────────────────────────────────────────

    def get_field_state(self, session_id: Optional[str] = None) -> FieldState:
        """
        Retrieve the complete field state for a session.
        If no session_id is provided, gets the most recent session.
        """
        with self._connect() as conn:
            # Find the session
            if session_id:
                session_row = conn.execute(
                    "SELECT * FROM nodes WHERE id = ? AND type = 'session'", (session_id,)
                ).fetchone()
            else:
                session_row = conn.execute(
                    "SELECT * FROM nodes WHERE type = 'session' ORDER BY created_at DESC LIMIT 1"
                ).fetchone()

            if not session_row:
                return FieldState(session_id="", coherence=0.5)

            session_id = session_row["id"]

            # Get all nodes in this session (connected via BELONGS_TO)
            node_rows = conn.execute(
                """
                SELECT n.* FROM nodes n
                JOIN edges e ON n.id = e.target_id
                WHERE e.source_id = ? AND e.type = 'belongs_to'
                """,
                (session_id,),
            ).fetchall()

            nodes = [self._row_to_node(row) for row in node_rows]

            # Get all edges in this session (any edge connected to these nodes)
            node_ids = [n.id for n in nodes]
            if node_ids:
                placeholders = ", ".join("?" * len(node_ids))
                edge_rows = conn.execute(
                    f"""
                    SELECT * FROM edges
                    WHERE source_id IN ({placeholders}) OR target_id IN ({placeholders})
                    """,
                    node_ids + node_ids,
                ).fetchall()
                edges = [
                    Edge(
                        id=row["id"],
                        source_id=row["source_id"],
                        target_id=row["target_id"],
                        type=EdgeType(row["type"]),
                        created_at=datetime.fromisoformat(row["created_at"]),
                        metadata=json.loads(row["metadata"]) if row["metadata"] else {},
                    )
                    for row in edge_rows
                ]
            else:
                edges = []

            # Extract typed nodes
            trajectories = [n for n in nodes if isinstance(n, Trajectory)]
            streams = [n for n in nodes if isinstance(n, Stream)]
            perturbations = [n for n in nodes if isinstance(n, Perturbation)]
            clarifications = [n for n in nodes if isinstance(n, Clarification)]
            flags = [n for n in nodes if isinstance(n, FalseProblemFlag)]

            # Get coherence from session metadata
            session = self._row_to_node(session_row)
            coherence = session.metadata.get("coherence", 0.5)

            return FieldState(
                session_id=session_id,
                trajectories=trajectories,
                streams=streams,
                perturbations=perturbations,
                clarifications=clarifications,
                false_problem_flags=flags,
                edges=edges,
                coherence=coherence,
                last_insight=session.metadata.get("last_insight"),
            )

    # ─── Helpers ──────────────────────────────────────────────────────

    def _row_to_node(self, row: sqlite3.Row) -> Node:
        """Convert a database row to the appropriate Node subclass."""
        node_type = NodeType(row["type"])
        metadata = json.loads(row["metadata"]) if row["metadata"] else {}

        # Common fields
        base_kwargs = {
            "id": row["id"],
            "created_at": datetime.fromisoformat(row["created_at"]),
            "updated_at": datetime.fromisoformat(row["updated_at"]),
            "metadata": metadata,
        }

        if node_type == NodeType.TRAJECTORY:
            return Trajectory(
                **base_kwargs,
                description=row["description"],
                bearing=row["bearing"] or "Initial exploration",
                status=TrajectoryStatus(row["status"])
                if row["status"]
                else TrajectoryStatus.ACTIVE,
                history=json.loads(row["history"]) if row["history"] else [],
            )
        elif node_type == NodeType.STREAM:
            return Stream(
                **base_kwargs,
                path=row["path"],
                signature=row["signature"],
                volatility=row["volatility"] or 0.0,
                version=row["version"] or 1,
            )
        elif node_type == NodeType.PERTURBATION:
            return Perturbation(
                **base_kwargs,
                description=row["description"],
                stack_trace=row["stack_trace"],
                severity=row["severity"] or "medium",
                frequency=row["frequency"] or 1,
                resolved=bool(row["resolved"]),
                resolution_insight=row["resolution_insight"],
            )
        elif node_type == NodeType.CLARIFICATION:
            return Clarification(
                **base_kwargs,
                description=row["description"],
                rationale=row["rationale"],
                resolved_nodes=json.loads(row["resolved_nodes"]) if row["resolved_nodes"] else [],
            )
        elif node_type == NodeType.FALSE_PROBLEM_FLAG:
            return FalseProblemFlag(
                **base_kwargs,
                description=row["description"],
                context=row["context"],
                resolved=bool(row["resolved"]),
                resolution_insight=row["resolution_insight"],
            )
        elif node_type == NodeType.SESSION:
            return Session(
                **base_kwargs,
                started_at=datetime.fromisoformat(row["started_at"])
                if row["started_at"]
                else datetime.utcnow(),
                ended_at=datetime.fromisoformat(row["ended_at"]) if row["ended_at"] else None,
                coherence_history=json.loads(row["coherence_history"])
                if row["coherence_history"]
                else [],
            )
        else:
            # Fallback
            return Node(type=node_type, **base_kwargs)

    # ─── Cleanup ──────────────────────────────────────────────────────

    def close(self) -> None:
        """Close any open connections (no-op for sqlite3)."""
        pass
