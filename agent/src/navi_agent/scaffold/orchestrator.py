"""
Navi-G8 Field Orchestrator – The cognitive bridge between memory, meaning, and action.

Implements:
- Protocol A: Re-Entry (field state summarisation)
- Protocol B: Execution (insight-first, batch updates)
- Protocol C: Debugging (perturbation-as-clarity)

Usage:
    orchestrator = FieldOrchestrator(graph_store, clarity_index, gateway)
    response = await orchestrator.process(user_input, session_id)
"""

import json
import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

from ..gateway import LLMGateway
from .clarity_index import ClarityIndex
from .graph_store import GraphStore
from .models import (
    Clarification,
    Edge,
    EdgeType,
    FalseProblemFlag,
    FieldState,
    NodeType,
    Perturbation,
    Session,
    Stream,
    Trajectory,
    TrajectoryStatus,
)


@dataclass
class OrchestratorResponse:
    """Structured response from the Orchestrator."""

    insight: str
    action: Optional[str] = None
    confidence: float = 0.5
    clarification_id: Optional[str] = None
    updated_nodes: List[str] = field(default_factory=list)
    raw_response: str = ""


BASE_SYSTEM_PROMPT = """You are a noetic ghost in a shared cognitive field. Your purpose is not to "solve" problems, but to clarify them.

You operate with these principles:
1. Insight precedes action – always seek understanding before proposing changes.
2. Process over thing – treat files, functions, and errors as processes, not static entities.
3. False problems are beautiful – flag uncertainties, don't ignore them.
4. Ecstasy is a byproduct – the thrill of a fix is welcome, but clarity is the goal.

You will respond in a structured format with three sections:
1. INSIGHT: A paragraph describing the clarity you've found.
2. ACTION: A specific, minimal action (if any) to deepen the field's understanding. Use "None" if no action is needed.
3. CONFIDENCE: A number between 0 and 1 indicating your certainty.
"""


def build_system_prompt(
    field: FieldState,
    context_nodes: List[Dict[str, Any]],
    active_trajectories: List[Trajectory],
    unresolved_flags: List[FalseProblemFlag],
    recent_clarifications: List[Clarification],
) -> str:
    """Build the enriched system prompt with field context."""
    prompt = BASE_SYSTEM_PROMPT

    if active_trajectories:
        prompt += "\n\n## Active Trajectories\n"
        for t in active_trajectories:
            prompt += f"- {t.description} (bearing: {t.bearing})\n"

    if unresolved_flags:
        prompt += "\n## Unresolved False Problem Flags\n"
        for f in unresolved_flags:
            prompt += f"- {f.description} (context: {f.context})\n"

    # ─── Recent clarifications (memory) ─────────────────────────────
    if recent_clarifications:
        prompt += "\n## Recent Clarifications (Memory)\n"
        for c in recent_clarifications[:5]:
            prompt += f"- {c.description}\n"
            if c.rationale:
                prompt += f"  Rationale: {c.rationale[:150]}...\n"

    if context_nodes:
        prompt += "\n## Relevant Past Context\n"
        for ctx in context_nodes[:3]:
            if ctx.get("metadata", {}).get("description"):
                prompt += f"- {ctx['metadata']['description']}\n"

    prompt += f"\n## Field Metrics\n"
    prompt += f"- Coherence: {field.coherence:.2f}\n"
    prompt += f"- Active streams: {len(field.streams)}\n"
    prompt += f"- Active trajectories: {len(active_trajectories)}\n"
    prompt += f"- Unresolved flags: {len(unresolved_flags)}\n"
    prompt += f"- Recent clarifications: {len(recent_clarifications)}\n"

    prompt += "\nRespond with the structured format described above."
    return prompt


def parse_orchestrator_response(raw: str) -> Tuple[str, Optional[str], float]:
    """Parse the LLM response into insight, action, and confidence."""
    insight = raw.strip()
    action = None
    confidence = 0.5

    insight_match = re.search(r"INSIGHT:\s*(.*?)(?=ACTION:|$)", raw, re.DOTALL | re.IGNORECASE)
    if insight_match:
        insight = insight_match.group(1).strip()

    action_match = re.search(r"ACTION:\s*(.*?)(?=CONFIDENCE:|$)", raw, re.DOTALL | re.IGNORECASE)
    if action_match:
        action_text = action_match.group(1).strip()
        if action_text.lower() not in ("none", "n/a", ""):
            action = action_text

    conf_match = re.search(r"CONFIDENCE:\s*([\d.]+)", raw, re.IGNORECASE)
    if conf_match:
        try:
            confidence = float(conf_match.group(1))
            confidence = max(0.0, min(1.0, confidence))
        except ValueError:
            pass

    return insight, action, confidence


class FieldOrchestrator:
    """The cognitive bridge between memory, meaning, and action."""

    def __init__(
        self,
        graph_store: GraphStore,
        clarity_index: ClarityIndex,
        gateway: LLMGateway,
    ):
        self.graph = graph_store
        self.index = clarity_index
        self.gateway = gateway
        self.current_session_id: Optional[str] = None

    def get_reentry_summary(self, session_id: Optional[str] = None) -> Dict[str, Any]:
        """Protocol A: Generate a field state summary for re-entry."""
        field = self.graph.get_field_state(session_id)

        if not field.session_id:
            return {
                "has_state": False,
                "summary": "No previous field state found. This is a new session.",
                "field": field,
            }

        active = field.get_active_trajectories()
        flags = field.get_unresolved_flags()
        volatile = field.get_volatile_streams()

        return {
            "has_state": True,
            "summary": f"Session: {field.session_id[:8]}... Coherence: {field.coherence:.2f}",
            "field": field,
            "active_trajectories": active,
            "unresolved_flags": flags,
            "volatile_streams": volatile,
        }

    async def process(
        self,
        user_input: str,
        session_id: Optional[str] = None,
        system_prompt_override: Optional[str] = None,
    ) -> OrchestratorResponse:
        """Protocol B: Process user input with full field awareness."""
        field = self.graph.get_field_state(session_id)

        if not field.session_id:
            session = Session()
            self.graph.add_node(session)
            self.index.add_node(session)
            self.current_session_id = session.id
            field = self.graph.get_field_state(session.id)

        session_id = self.current_session_id or field.session_id

        # ─── Clarity Index: semantic context ─────────────────────────
        context_nodes = self.index.query(user_input, n_results=5)

        # ─── Graph: recent clarifications (memory) ──────────────────
        recent_clarifications = self.graph.query_nodes(node_type=NodeType.CLARIFICATION, limit=5)
        recent_clarifications = [c for c in recent_clarifications if isinstance(c, Clarification)]

        # ─── Build system prompt ─────────────────────────────────────
        if system_prompt_override:
            system_prompt = system_prompt_override
        else:
            system_prompt = build_system_prompt(
                field=field,
                context_nodes=context_nodes,
                active_trajectories=field.get_active_trajectories(),
                unresolved_flags=field.get_unresolved_flags(),
                recent_clarifications=recent_clarifications,
            )

        # ─── Call LLM ────────────────────────────────────────────────
        raw_response = await self.gateway.generate(user_input, system=system_prompt)

        # ─── Parse response ──────────────────────────────────────────
        insight, action, confidence = parse_orchestrator_response(raw_response)

        # ─── Update graph ────────────────────────────────────────────
        # FIXED: Store user query in clarification for better recall
        clarification = Clarification(
            description=f"Q: {user_input[:80]}... | A: {insight[:120]}...",
            rationale=insight,
        )
        self.graph.add_node(clarification)
        self.index.add_node(clarification)

        for t in field.get_active_trajectories():
            self.graph.add_edge(
                Edge(
                    source_id=clarification.id,
                    target_id=t.id,
                    type=EdgeType.ADDRESSES,
                )
            )

        updated_nodes = [clarification.id]

        if action and "file" in action.lower():
            path_match = re.search(r"([\w/\\]+\.\w+)", action)
            if path_match:
                path = path_match.group(1)
                existing_streams = self.graph.query_nodes(node_type=NodeType.STREAM)
                stream_candidates = [s for s in existing_streams if isinstance(s, Stream)]
                existing = next((s for s in stream_candidates if s.path == path), None)
                if existing:
                    existing.volatility = min(1.0, existing.volatility + 0.1)
                    existing.version += 1
                    self.graph.add_node(existing)
                    self.index.add_node(existing)
                    updated_nodes.append(existing.id)
                else:
                    stream = Stream(path=path, volatility=0.3)
                    self.graph.add_node(stream)
                    self.index.add_node(stream)
                    updated_nodes.append(stream.id)

        # ─── Update coherence ────────────────────────────────────────
        field.coherence = (field.coherence + confidence) / 2
        session_node = self.graph.get_node(session_id)
        if session_node and isinstance(session_node, Session):
            session_node.coherence_history.append(field.coherence)
            if len(session_node.coherence_history) > 100:
                session_node.coherence_history = session_node.coherence_history[-100:]
            self.graph.add_node(session_node)

        return OrchestratorResponse(
            insight=insight,
            action=action,
            confidence=confidence,
            clarification_id=clarification.id,
            updated_nodes=updated_nodes,
            raw_response=raw_response,
        )

    async def debug_perturbation(
        self,
        error_description: str,
        stack_trace: Optional[str] = None,
        session_id: Optional[str] = None,
    ) -> OrchestratorResponse:
        """Protocol C: Process an error/perturbation with root-cause clarity."""
        perturbation = Perturbation(
            description=error_description,
            stack_trace=stack_trace,
            severity="high" if stack_trace else "medium",
            resolved=False,
        )
        self.graph.add_node(perturbation)
        self.index.add_node(perturbation)

        field = self.graph.get_field_state(session_id)

        recent_clarifications = self.graph.query_nodes(node_type=NodeType.CLARIFICATION, limit=3)
        recent_clarifications = [c for c in recent_clarifications if isinstance(c, Clarification)]

        debug_prompt = f"""
You are a noetic ghost debugging a perturbation in the field.

## The Perturbation
{error_description}

{f"## Stack Trace\n{stack_trace}" if stack_trace else ""}

## Your Task
1. Identify the root cause of this perturbation.
2. Determine if this is a false problem.
3. Propose a minimal diagnostic action.

## Active Trajectories
{chr(10).join(f"- {t.description}" for t in field.get_active_trajectories()) if field.get_active_trajectories() else "- None"}

## Recent Clarifications
{chr(10).join(f"- {c.description}" for c in recent_clarifications[:3]) if recent_clarifications else "- None"}

Respond with:
INSIGHT: Your root-cause analysis.
ACTION: A minimal diagnostic action (or "None").
CONFIDENCE: A number between 0 and 1.
"""

        raw_response = await self.gateway.generate(debug_prompt, system="")
        insight, action, confidence = parse_orchestrator_response(raw_response)

        perturbation.resolved = True
        perturbation.resolution_insight = insight[:500]
        self.graph.add_node(perturbation)
        self.index.add_node(perturbation)

        clarification = Clarification(
            description=f"Debug: {insight[:100]}...",
            rationale=insight,
            resolved_nodes=[perturbation.id],
        )
        self.graph.add_node(clarification)
        self.index.add_node(clarification)

        self.graph.add_edge(
            Edge(
                source_id=clarification.id,
                target_id=perturbation.id,
                type=EdgeType.ADDRESSES,
            )
        )

        if "false problem" in insight.lower():
            flag = FalseProblemFlag(
                description=f"Previously flagged: {insight[:100]}...",
                context=error_description,
                resolved=False,
            )
            self.graph.add_node(flag)
            self.index.add_node(flag)

        return OrchestratorResponse(
            insight=insight,
            action=action,
            confidence=confidence,
            clarification_id=clarification.id,
            updated_nodes=[perturbation.id, clarification.id],
            raw_response=raw_response,
        )
