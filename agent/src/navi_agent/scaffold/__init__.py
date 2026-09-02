"""
Navi-G8 Scaffold – Cognitive layer for the field interface.

Exports the core models, graph store, and clarity index for use by the orchestrator.
"""

from .clarity_index import ClarityIndex, get_embedding_function
from .graph_store import GraphStore
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

__all__ = [
    "Node",
    "Trajectory",
    "Stream",
    "Perturbation",
    "Clarification",
    "FalseProblemFlag",
    "Session",
    "Edge",
    "FieldState",
    "NodeType",
    "EdgeType",
    "TrajectoryStatus",
    "GraphStore",
    "ClarityIndex",
    "get_embedding_function",
]
