#!/usr/bin/env python3
"""
Navi-G8 – Field Interface Entry Point.
"""

import asyncio
import json
import socket
import sys
from pathlib import Path


def log(msg):
    """Print a log message with flush."""
    print(msg, flush=True)


def daemon_mode():
    """Run as a local socket server, not stdin/stdout."""
    from .gateway import LLMGateway
    from .scaffold.clarity_index import ClarityIndex
    from .scaffold.graph_store import GraphStore
    from .scaffold.orchestrator import FieldOrchestrator

    try:
        graph = GraphStore(Path.home() / ".navi-g8" / "field.db")
        graph.init_db()
        log("[DAEMON] Graph store initialized")
    except Exception as e:
        log(f"[DAEMON] Graph store failed: {e}")
        return

    try:
        index = ClarityIndex(Path.home() / ".navi-g8" / "clarity_index")
        log("[DAEMON] Clarity index initialized")
    except Exception as e:
        log(f"[DAEMON] Clarity index failed: {e}")
        return

    try:
        gateway = LLMGateway()
        log("[DAEMON] LLM gateway created")
    except Exception as e:
        log(f"[DAEMON] LLM gateway failed: {e}")
        return

    try:
        orchestrator = FieldOrchestrator(graph, index, gateway)
        log("[DAEMON] Orchestrator created")
    except Exception as e:
        log(f"[DAEMON] Orchestrator failed: {e}")
        return

    # ─── Socket server ──────────────────────────────────────────────
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.bind(("127.0.0.1", 9876))
        sock.listen(1)
        log("[DAEMON] Socket bound and listening on 127.0.0.1:9876")
    except Exception as e:
        log(f"[DAEMON] Socket setup failed: {e}")
        return

    while True:
        try:
            log("[DAEMON] Waiting for connection...")
            conn, addr = sock.accept()
            log(f"[DAEMON] Connection from {addr}")
            with conn:
                while True:
                    try:
                        log("[DAEMON] Waiting for data...")
                        data = conn.recv(4096)
                        if not data:
                            log("[DAEMON] Connection closed by client")
                            break

                        text = data.decode("utf-8").strip()
                        if not text:
                            continue

                        log(f"[DAEMON] Received {len(data)} bytes: {text[:100]}")
                        request = json.loads(text)
                        log(f"[DAEMON] Parsed request: {request.get('type')}")

                        if request.get("type") == "query":
                            response = asyncio.run(
                                orchestrator.process(
                                    request.get("query", ""), session_id=request.get("session")
                                )
                            )
                            result = json.dumps(
                                {
                                    "type": "response",
                                    "insight": response.insight,
                                    "action": response.action,
                                    "confidence": response.confidence,
                                }
                            )
                            conn.sendall((result + "\n").encode("utf-8"))
                            log("[DAEMON] Response sent")

                        elif request.get("type") == "state":
                            summary = orchestrator.get_reentry_summary(request.get("session"))
                            field = summary.get("field")

                            # ─── Build nodes and edges ──────────────
                            nodes = []
                            edges = []

                            # Trajectories
                            for t in field.trajectories:
                                nodes.append(
                                    {
                                        "id": t.id,
                                        "label": t.description[:20]
                                        + ("..." if len(t.description) > 20 else ""),
                                        "type": "trajectory",
                                        "description": t.description,
                                        "status": t.status.value,
                                    }
                                )

                            # Streams
                            for s in field.streams:
                                nodes.append(
                                    {
                                        "id": s.id,
                                        "label": s.path,
                                        "type": "stream",
                                        "volatility": s.volatility,
                                        "path": s.path,
                                    }
                                )

                            # Perturbations
                            for p in field.perturbations:
                                nodes.append(
                                    {
                                        "id": p.id,
                                        "label": p.description[:20]
                                        + ("..." if len(p.description) > 20 else ""),
                                        "type": "perturbation",
                                        "description": p.description,
                                        "severity": p.severity,
                                        "resolved": p.resolved,
                                    }
                                )

                            # Clarifications
                            for c in field.clarifications:
                                nodes.append(
                                    {
                                        "id": c.id,
                                        "label": c.description[:20]
                                        + ("..." if len(c.description) > 20 else ""),
                                        "type": "clarification",
                                        "description": c.description,
                                        "rationale": c.rationale[:50]
                                        + ("..." if len(c.rationale) > 50 else ""),
                                    }
                                )

                            # FalseProblemFlags
                            for f in field.false_problem_flags:
                                nodes.append(
                                    {
                                        "id": f.id,
                                        "label": f.description[:20]
                                        + ("..." if len(f.description) > 20 else ""),
                                        "type": "flag",
                                        "description": f.description,
                                        "context": f.context,
                                        "resolved": f.resolved,
                                    }
                                )

                            # Edges
                            for e in field.edges:
                                edges.append(
                                    {
                                        "id": e.id,
                                        "from": e.source_id,
                                        "to": e.target_id,
                                        "label": e.type.value,
                                    }
                                )

                            result = json.dumps(
                                {
                                    "type": "state",
                                    "coherence": field.coherence if field else 0.5,
                                    "trajectories": len(field.trajectories),
                                    "flags": len(field.false_problem_flags),
                                    "streams": len(field.streams),
                                    "nodes": nodes,
                                    "edges": edges,
                                }
                            )
                            conn.sendall((result + "\n").encode("utf-8"))
                            log("[DAEMON] State response sent")

                        else:
                            log(f"[DAEMON] Unknown request type: {request.get('type')}")

                    except json.JSONDecodeError as e:
                        conn.sendall(
                            json.dumps({"type": "error", "message": f"Invalid JSON: {e}"}).encode(
                                "utf-8"
                            )
                        )
                        log(f"[DAEMON] JSON error: {e}")
                    except Exception as e:
                        log(f"[DAEMON] Inner loop error: {e}")
                        break

        except Exception as e:
            log(f"[DAEMON] Outer loop error: {e}")
            # Continue accepting new connections


def terminal_mode():
    """Normal interactive terminal mode."""
    from .ui.app import run_field_app

    asyncio.run(run_field_app())


if __name__ == "__main__":
    if "--mode" in sys.argv and "daemon" in sys.argv:
        daemon_mode()
    else:
        terminal_mode()
