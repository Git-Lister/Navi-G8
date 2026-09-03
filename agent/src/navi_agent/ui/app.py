"""
Navi-G8 Field Application – The main application loop.

Integrates the orchestrator, terminal, and boot sequence into a
cohesive interactive experience.
"""

import asyncio
import sys
from pathlib import Path
from typing import Optional

from rich.console import Console

from ..gateway import LLMGateway
from ..scaffold.clarity_index import ClarityIndex
from ..scaffold.graph_store import GraphStore
from ..scaffold.orchestrator import FieldOrchestrator
from .boot import BootSequence
from .terminal import FieldTerminal

console = Console()

# ─── Session Persistence ──────────────────────────────────────────────

SESSION_FILE = Path.home() / ".navi-g8" / "session_id.txt"


def _save_session_id(session_id: str) -> None:
    """Save the session ID to a file for re-entry."""
    SESSION_FILE.parent.mkdir(parents=True, exist_ok=True)
    SESSION_FILE.write_text(session_id)


def _load_session_id() -> Optional[str]:
    """Load the session ID from file, if it exists."""
    if SESSION_FILE.exists():
        return SESSION_FILE.read_text().strip()
    return None


# ─── Field Application ────────────────────────────────────────────────


class FieldApp:
    """
    The main Field Application – orchestrates the UI and cognitive layers.

    Usage:
        app = FieldApp()
        await app.run()
    """

    def __init__(
        self,
        graph_path: Optional[Path] = None,
        index_path: Optional[Path] = None,
        use_local_embedding: bool = True,
    ):
        # Default paths
        if graph_path is None:
            graph_path = Path.home() / ".navi-g8" / "field.db"
        if index_path is None:
            index_path = Path.home() / ".navi-g8" / "clarity_index"

        self.graph_path = graph_path
        self.index_path = index_path
        self.use_local_embedding = use_local_embedding

        # Components
        self.graph_store: Optional[GraphStore] = None
        self.clarity_index: Optional[ClarityIndex] = None
        self.gateway: Optional[LLMGateway] = None
        self.orchestrator: Optional[FieldOrchestrator] = None
        self.terminal: Optional[FieldTerminal] = None
        self.boot: Optional[BootSequence] = None

        # Session
        self.session_id: Optional[str] = None
        self.running = False

    def _init_components(self) -> None:
        """Initialize all cognitive components."""
        # Graph Store
        self.graph_store = GraphStore(self.graph_path)
        self.graph_store.init_db()

        # Clarity Index
        self.clarity_index = ClarityIndex(
            self.index_path,
            use_local_embedding=self.use_local_embedding,
        )

        # LLM Gateway
        self.gateway = LLMGateway()

        # Orchestrator
        self.orchestrator = FieldOrchestrator(
            self.graph_store,
            self.clarity_index,
            self.gateway,
        )

        # Terminal
        self.terminal = FieldTerminal(coherence=0.5)

        # Boot sequence
        self.boot = BootSequence()

    async def run(self) -> None:
        """Run the main application loop."""
        # Initialize
        self._init_components()

        # Boot sequence
        self.boot.run()

        # ─── Protocol A: Re-Entry ────────────────────────────────────
        # Try to load previous session ID
        saved_session_id = _load_session_id()

        if saved_session_id:
            # Check if the session exists in the graph
            field = self.graph_store.get_field_state(saved_session_id)
            if field.session_id:
                self.session_id = saved_session_id
                self.orchestrator.current_session_id = saved_session_id
                self.terminal.display(
                    f"🔄 Re-entering previous session: {saved_session_id[:8]}...",
                    style="dim",
                )
            else:
                self.terminal.display(
                    "⚠️ Previous session not found in graph. Starting fresh.",
                    style="yellow",
                )
                self.session_id = None
        else:
            self.terminal.display("🌱 No previous session found. Starting fresh.", style="dim")

        # Display field state
        summary = self.orchestrator.get_reentry_summary(self.session_id)
        self.terminal.display_field_state(summary)

        # Store session ID if a new one was created
        if self.orchestrator.current_session_id:
            self.session_id = self.orchestrator.current_session_id
            _save_session_id(self.session_id)

        self.terminal.display_boot_reminder()

        # Main loop
        self.running = True
        while self.running:
            try:
                # Get user input
                user_input = await self.terminal.prompt()

                # Check for exit commands
                if user_input.lower() in ("exit", "quit", "goodbye"):
                    self.terminal.display("🌙 The field is quieting. Goodbye.", style="dim")
                    break

                # Check for manual session reset (debug)
                if user_input.lower() == "reset session":
                    self.session_id = None
                    _save_session_id("")
                    self.terminal.display(
                        "🔄 Session reset. Starting fresh on next run.", style="yellow"
                    )
                    continue

                # Process through orchestrator
                response = await self.orchestrator.process(
                    user_input,
                    session_id=self.session_id,
                )

                # Update terminal coherence
                self.terminal.update_coherence(response.confidence)

                # ─── Display the response ────────────────────────────
                # Insight (with Markdown rendering)
                if response.insight:
                    self.terminal.display(
                        f"\n💡 {response.insight}", style="cyan", as_markdown=True
                    )

                # Action
                if response.action:
                    self.terminal.display(f"\n⚡ {response.action}", style="yellow")

                # Confidence – FIXED: use actual response confidence
                self.terminal.display(
                    f"\n📊 Confidence: {response.confidence:.2f}",
                    style="dim",
                )

                # Update session ID for subsequent calls
                if self.orchestrator.current_session_id:
                    self.session_id = self.orchestrator.current_session_id
                    _save_session_id(self.session_id)

            except KeyboardInterrupt:
                self.terminal.display("\n\n🌙 Field interrupted. Goodbye.", style="dim")
                break
            except Exception as e:
                self.terminal.display(f"\n⚠️ Perturbation: {e}", style="red")
                # Offer to debug
                debug_choice = await self.terminal.prompt("Debug this perturbation? (y/n)")
                if debug_choice.lower() in ("y", "yes"):
                    debug_response = await self.orchestrator.debug_perturbation(
                        error_description=str(e),
                        session_id=self.session_id,
                    )
                    self.terminal.display(f"\n💡 {debug_response.insight}", style="cyan")
                    if debug_response.action:
                        self.terminal.display(f"\n⚡ {debug_response.action}", style="yellow")

    def stop(self) -> None:
        """Stop the application."""
        self.running = False


# ─── Entry Point ──────────────────────────────────────────────────────


async def run_field_app(
    graph_path: Optional[Path] = None,
    index_path: Optional[Path] = None,
    use_local_embedding: bool = True,
) -> None:
    """
    Run the Navi-G8 Field Application.

    Args:
        graph_path: Path to the graph database.
        index_path: Path to the clarity index.
        use_local_embedding: Whether to use local embedding model.
    """
    app = FieldApp(
        graph_path=graph_path,
        index_path=index_path,
        use_local_embedding=use_local_embedding,
    )
    await app.run()


def main():
    """Entry point for the CLI."""
    asyncio.run(run_field_app())


if __name__ == "__main__":
    main()
