"""
Navi-G8 Scaffold Data Models

Defines the core entities of the cognitive field: Trajectories, Streams,
Perturbations, Clarifications, and FalseProblemFlags. All models are Pydantic
for validation and serialization.

Based on the Ghost-in-the-Share Blueprint (v2.1).
"""

import uuid
from datetime import datetime, timezone
from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

# ─── Enums ──────────────────────────────────────────────────────────────


class TrajectoryStatus(str, Enum):
    """Status of a high-level trajectory."""

    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    ABANDONED = "abandoned"


class NodeType(str, Enum):
    """Type of node in the graph."""

    TRAJECTORY = "trajectory"
    STREAM = "stream"
    PERTURBATION = "perturbation"
    CLARIFICATION = "clarification"
    FALSE_PROBLEM_FLAG = "false_problem_flag"
    SESSION = "session"


class EdgeType(str, Enum):
    """Type of edge in the graph."""

    PRECEDES = "precedes"  # Temporal ordering (A happened before B)
    DEPENDS_ON = "depends_on"  # Structural dependency
    ADDRESSES = "addresses"  # Clarification resolves a trajectory/perturbation
    FLAGS = "flags"  # FalseProblemFlag attached to a node
    EMERGES_FROM = "emerges_from"  # Perturbation emerges from a stream
    BELONGS_TO = "belongs_to"  # Node belongs to a session


# ─── Node Models ────────────────────────────────────────────────────────


class Node(BaseModel):
    """Base node for all scaffold entities."""

    model_config = ConfigDict(use_enum_values=True)

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    type: NodeType
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    metadata: dict[str, Any] = Field(default_factory=dict)


class Trajectory(Node):
    """A high-level goal or direction of movement."""

    type: NodeType = NodeType.TRAJECTORY
    description: str
    bearing: str = "Initial exploration"  # Current direction
    status: TrajectoryStatus = TrajectoryStatus.ACTIVE
    history: list[str] = Field(default_factory=list)  # Timeline of bearing adjustments


class Stream(Node):
    """A file, function, or module – treated as a process, not a thing."""

    type: NodeType = NodeType.STREAM
    path: str
    signature: str | None = None
    volatility: float = 0.0  # 0.0 = stable, 1.0 = extremely volatile
    version: int = 1  # Number of times changed


class Perturbation(Node):
    """A runtime error or unexpected behaviour – a disturbance in the field."""

    type: NodeType = NodeType.PERTURBATION
    description: str
    stack_trace: str | None = None
    severity: str = "medium"  # low | medium | high
    frequency: int = 1
    resolved: bool = False
    resolution_insight: str | None = None


class Clarification(Node):
    """A decision or moment of insight that resolves a trajectory or perturbation."""

    type: NodeType = NodeType.CLARIFICATION
    description: str
    rationale: str  # The insight that led to this clarification
    resolved_nodes: list[str] = Field(default_factory=list)  # IDs of nodes this clarifies


class FalseProblemFlag(Node):
    """A flag indicating we may be asking the wrong question."""

    type: NodeType = NodeType.FALSE_PROBLEM_FLAG
    description: str
    context: str  # Where did this arise?
    resolved: bool = False
    resolution_insight: str | None = None


class Session(Node):
    """A transient instance of the cognitive field."""

    type: NodeType = NodeType.SESSION
    started_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    ended_at: datetime | None = None
    coherence_history: list[float] = Field(default_factory=list)


# ─── Edge Model ────────────────────────────────────────────────────────


class Edge(BaseModel):
    """A relationship between two nodes."""

    model_config = ConfigDict(use_enum_values=True)

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    source_id: str
    target_id: str
    type: EdgeType
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    metadata: dict[str, Any] = Field(default_factory=dict)


# ─── Field State ────────────────────────────────────────────────────────


class FieldState(BaseModel):
    """The complete state of the cognitive field at a given moment."""

    model_config = ConfigDict(use_enum_values=True)

    session_id: str
    trajectories: list[Trajectory] = Field(default_factory=list)
    streams: list[Stream] = Field(default_factory=list)
    perturbations: list[Perturbation] = Field(default_factory=list)
    clarifications: list[Clarification] = Field(default_factory=list)
    false_problem_flags: list[FalseProblemFlag] = Field(default_factory=list)
    edges: list[Edge] = Field(default_factory=list)
    coherence: float = 0.5  # 0.0–1.0
    last_insight: str | None = None

    def get_active_trajectories(self) -> list[Trajectory]:
        """Return all active trajectories."""
        return [t for t in self.trajectories if t.status == TrajectoryStatus.ACTIVE]

    def get_volatile_streams(self, threshold: float = 0.5) -> list[Stream]:
        """Return streams with volatility above the threshold."""
        return [s for s in self.streams if s.volatility >= threshold]

    def get_unresolved_flags(self) -> list[FalseProblemFlag]:
        """Return all unresolved false problem flags."""
        return [f for f in self.false_problem_flags if not f.resolved]
