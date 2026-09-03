"""
Navi-G8 Field Orchestrator

The cognitive bridge between memory (Graph Store), meaning (Clarity Index),
and action (LLM Gateway). Implements the three protocols:
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

# ─── Response Models ──────────────────────────────────────────────────


@dataclass
class OrchestratorResponse:
    """Structured response from the Orchestrator."""

    insight: str  # The insight paragraph
    action: Optional[str] = None  # Proposed action (if any)
    confidence: float = 0.5  # 0.0–1.0
    clarification_id: Optional[str] = None  # ID of created Clarification node
    updated_nodes: List[str] = field(default_factory=list)  # IDs of updated nodes
    raw_response: str = ""  # Raw LLM response for debugging


# ─── System Prompt Templates ──────────────────────────────────────────


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
) -> str:
    """
    Build the enriched system prompt with field context.

    Args:
        field: The current field state.
        context_nodes: Nodes retrieved from the clarity index.
        active_trajectories: Active trajectories from the graph.
        unresolved_flags: Unresolved false problem flags.

    Returns:
        A complete system prompt string.
    """
    prompt = BASE_SYSTEM_PROMPT

    # Active trajectories
    if active_trajectories:
        prompt += "\n\n## Active Trajectories\n"
        for t in active_trajectories:
            prompt += f"- {t.description} (bearing: {t.bearing})\n"

    # Unresolved false problem flags
    if unresolved_flags:
        prompt += "\n## Unresolved False Problem Flags\n"
        for f in unresolved_flags:
            prompt += f"- {f.description} (context: {f.context})\n"

    # Context from clarity index
    if context_nodes:
        prompt += "\n## Relevant Past Context\n"
        for ctx in context_nodes[:3]:  # Limit to top 3
            if ctx.get("metadata", {}).get("description"):
                prompt += f"- {ctx['metadata']['description']}\n"

    # Field metrics
    prompt += f"\n## Field Metrics\n"
    prompt += f"- Coherence: {field.coherence:.2f}\n"
    prompt += f"- Active streams: {len(field.streams)}\n"
    prompt += f"- Active trajectories: {len(active_trajectories)}\n"
    prompt += f"- Unresolved flags: {len(unresolved_flags)}\n"

    prompt += "\nRespond with the structured format described above."
    return prompt


# ─── Parsing Helpers ──────────────────────────────────────────────────


def parse_orchestrator_response(raw: str) -> Tuple[str, Optional[str], float]:
    """
    Parse the LLM response into insight, action, and confidence.

    Args:
        raw: The raw LLM response text.

    Returns:
        A tuple of (insight, action, confidence).
    """
    insight = raw.strip()
    action = None
    confidence = 0.5

    # Extract INSIGHT section
    insight_match = re.search(r"INSIGHT:\s*(.*?)(?=ACTION:|$)", raw, re.DOTALL | re.IGNORECASE)
    if insight_match:
        insight = insight_match.group(1).strip()

    # Extract ACTION section
    action_match = re.search(r"ACTION:\s*(.*?)(?=CONFIDENCE:|$)", raw, re.DOTALL | re.IGNORECASE)
    if action_match:
        action_text = action_match.group(1).strip()
        if action_text.lower() not in ("none", "n/a", ""):
            action = action_text

    # Extract CONFIDENCE section
    conf_match = re.search(r"CONFIDENCE:\s*([\d.]+)", raw, re.IGNORECASE)
    if conf_match:
        try:
            confidence = float(conf_match.group(1))
            confidence = max(0.0, min(1.0, confidence))  # Clamp to 0-1
        except ValueError:
            pass

    return insight, action, confidence


# ─── Field Orchestrator ──────────────────────────────────────────────


class FieldOrchestrator:
    """
    The cognitive bridge between memory, meaning, and action.

    Orchestrates the flow from user input to structured response with
    field awareness, updating the graph and clarity index as needed.

    Usage:
        orch = FieldOrchestrator(graph_store, clarity_index, gateway)
        response = await orch.process("The pipeline view isn't rendering")
    """

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

    # ─── Protocol A: Re-Entry ────────────────────────────────────────

    def get_reentry_summary(self, session_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Protocol A: Generate a field state summary for re-entry.

        Args:
            session_id: Optional session ID. If not provided, gets the most recent.

        Returns:
            A dictionary with the field summary.
        """
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

        summary = (
            f"Field re-entry summary:\n"
            f"- Session: {field.session_id[:8]}...\n"
            f"- Coherence: {field.coherence:.2f}\n"
            f"- Active trajectories: {len(active)}\n"
            f"- Unresolved flags: {len(flags)}\n"
            f"- Volatile streams: {len(volatile)}\n"
        )

        if active:
            summary += f"- Current trajectory: {active[0].description}\n"

        if flags:
            summary += f"- Pending questions: {flags[0].description}\n"

        return {
            "has_state": True,
            "summary": summary,
            "field": field,
            "active_trajectories": active,
            "unresolved_flags": flags,
            "volatile_streams": volatile,
        }

    # ─── Protocol B: Execution ───────────────────────────────────────

    async def process(
        self,
        user_input: str,
        session_id: Optional[str] = None,
        system_prompt_override: Optional[str] = None,
    ) -> OrchestratorResponse:
        """
        Protocol B: Process user input with full field awareness.

        Flow:
        1. Get current field state.
        2. Query clarity index for relevant context.
        3. Build enriched system prompt.
        4. Call LLM gateway.
        5. Parse response.
        6. Update graph and clarity index.

        Args:
            user_input: The user's input text.
            session_id: Optional session ID.
            system_prompt_override: Optional override for the system prompt.

        Returns:
            An OrchestratorResponse containing insight, action, confidence.
        """
        # 1. Get field state
        field = self.graph.get_field_state(session_id)

        # If no session exists, create one
        if not field.session_id:
            session = Session()
            self.graph.add_node(session)
            self.index.add_node(session)
            self.current_session_id = session.id
            field = self.graph.get_field_state(session.id)

        session_id = self.current_session_id or field.session_id

        # 2. Query clarity index for relevant context
        context_nodes = self.index.query(user_input, n_results=5)

        # 3. Build system prompt
        if system_prompt_override:
            system_prompt = system_prompt_override
        else:
            system_prompt = build_system_prompt(
                field=field,
                context_nodes=context_nodes,
                active_trajectories=field.get_active_trajectories(),
                unresolved_flags=field.get_unresolved_flags(),
            )

        # 4. Call LLM
        raw_response = await self.gateway.generate(user_input, system=system_prompt)

        # 5. Parse response
        insight, action, confidence = parse_orchestrator_response(raw_response)

        # 6. Update the field with the new insight
        clarification = Clarification(
            description=insight[:200] + ("..." if len(insight) > 200 else ""),
            rationale=insight,
        )
        self.graph.add_node(clarification)
        self.index.add_node(clarification)

        # Link clarification to active trajectories
        for t in field.get_active_trajectories():
            self.graph.add_edge(
                Edge(
                    source_id=clarification.id,
                    target_id=t.id,
                    type=EdgeType.ADDRESSES,
                )
            )

        # If there's an action, create a stream node for it (or update existing)
        action_node_id = None
        updated_nodes = [clarification.id]

        if action and "file" in action.lower():
            # Try to extract a file path from the action
            path_match = re.search(r"([\w/\\]+\.\w+)", action)
            if path_match:
                path = path_match.group(1)
                # Check if stream already exists
                existing_streams = self.graph.query_nodes(node_type=NodeType.STREAM)
                # Type guard: filter to only Stream instances
                stream_candidates = [s for s in existing_streams if isinstance(s, Stream)]
                existing = next((s for s in stream_candidates if s.path == path), None)
                if existing:
                    # Update volatility and version – type is already Stream
                    existing.volatility = min(1.0, existing.volatility + 0.1)
                    existing.version += 1
                    self.graph.add_node(existing)
                    self.index.add_node(existing)
                    action_node_id = existing.id
                    updated_nodes.append(existing.id)
                else:
                    stream = Stream(path=path, volatility=0.3)
                    self.graph.add_node(stream)
                    self.index.add_node(stream)
                    action_node_id = stream.id
                    updated_nodes.append(stream.id)

        # Update field coherence based on confidence
        field.coherence = (field.coherence + confidence) / 2
        # Update session node with coherence and last insight
        session_node = self.graph.get_node(session_id)
        if session_node and isinstance(session_node, Session):
            session_node.coherence_history.append(field.coherence)
            # Keep history manageable
            if len(session_node.coherence_history) > 100:
                session_node.coherence_history = session_node.coherence_history[-100:]
            self.graph.add_node(session_node)

        # Return response
        return OrchestratorResponse(
            insight=insight,
            action=action,
            confidence=confidence,
            clarification_id=clarification.id,
            updated_nodes=updated_nodes,
            raw_response=raw_response,
        )

    # ─── Protocol C: Debugging ──────────────────────────────────────

    async def debug_perturbation(
        self,
        error_description: str,
        stack_trace: Optional[str] = None,
        session_id: Optional[str] = None,
    ) -> OrchestratorResponse:
        """
        Protocol C: Process an error/perturbation with root-cause clarity.

        Args:
            error_description: Description of the error.
            stack_trace: Optional stack trace.
            session_id: Optional session ID.

        Returns:
            An OrchestratorResponse with root-cause insight.
        """
        # Create perturbation node
        perturbation = Perturbation(
            description=error_description,
            stack_trace=stack_trace,
            severity="high" if stack_trace else "medium",
            resolved=False,
        )
        self.graph.add_node(perturbation)
        self.index.add_node(perturbation)

        # Build a debug-focused system prompt
        field = self.graph.get_field_state(session_id)
        debug_prompt = f"""
You are a noetic ghost debugging a perturbation in the field.

## The Perturbation
{error_description}

{f"## Stack Trace\n{stack_trace}" if stack_trace else ""}

## Your Task
1. Identify the root cause of this perturbation.
2. Determine if this is a false problem (a question we're asking incorrectly).
3. Propose a minimal diagnostic action.

## Active Trajectories
{chr(10).join(f"- {t.description}" for t in field.get_active_trajectories()) if field.get_active_trajectories() else "- None"}

Respond with:
INSIGHT: Your root-cause analysis.
ACTION: A minimal diagnostic action (or "None" if the insight is sufficient).
CONFIDENCE: A number between 0 and 1.
"""

        raw_response = await self.gateway.generate(debug_prompt, system="")
        insight, action, confidence = parse_orchestrator_response(raw_response)

        # Update the perturbation with the insight
        perturbation.resolved = True
        perturbation.resolution_insight = insight[:500]
        self.graph.add_node(perturbation)
        self.index.add_node(perturbation)

        # Create a clarification for the insight
        clarification = Clarification(
            description=f"Debug: {insight[:100]}...",
            rationale=insight,
            resolved_nodes=[perturbation.id],
        )
        self.graph.add_node(clarification)
        self.index.add_node(clarification)

        # Link clarification to the perturbation
        self.graph.add_edge(
            Edge(
                source_id=clarification.id,
                target_id=perturbation.id,
                type=EdgeType.ADDRESSES,
            )
        )

        # If this was a false problem, create a flag
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
