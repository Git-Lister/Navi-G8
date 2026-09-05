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
from ..scaffold.models import Session
from ..scaffold.orchestrator import FieldOrchestrator
from .boot import BootSequence
from .terminal import FieldTerminal

console = Console()

SESSION_FILE = Path.home() / ".navi-g8" / "session_id.txt"


def _save_session_id(session_id: str) -> None:
    SESSION_FILE.parent.mkdir(parents=True, exist_ok=True)
    SESSION_FILE.write_text(session_id)


def _load_session_id() -> Optional[str]:
    if SESSION_FILE.exists():
        return SESSION_FILE.read_text().strip()
    return None


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
        if graph_path is None:
            graph_path = Path.home() / ".navi-g8" / "field.db"
        if index_path is None:
            index_path = Path.home() / ".navi-g8" / "clarity_index"

        self.graph_path = graph_path
        self.index_path = index_path
        self.use_local_embedding = use_local_embedding

        self.graph_store: Optional[GraphStore] = None
        self.clarity_index: Optional[ClarityIndex] = None
        self.gateway: Optional[LLMGateway] = None
        self.orchestrator: Optional[FieldOrchestrator] = None
        self.terminal: Optional[FieldTerminal] = None
        self.boot: Optional[BootSequence] = None

        self.session_id: Optional[str] = None
        self.running = False

    def _init_components(self) -> None:
        self.graph_store = GraphStore(self.graph_path)
        self.graph_store.init_db()

        self.clarity_index = ClarityIndex(
            self.index_path,
            use_local_embedding=self.use_local_embedding,
        )

        self.gateway = LLMGateway()

        self.orchestrator = FieldOrchestrator(
            self.graph_store,
            self.clarity_index,
            self.gateway,
        )

        self.terminal = FieldTerminal(coherence=0.5)
        self.boot = BootSequence()

    async def run(self) -> None:
        self._init_components()
        self.boot.run()

        # ─── Protocol A: Re-Entry ────────────────────────────────────
        saved_session_id = _load_session_id()

        if saved_session_id:
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

        # ─── Create session if none exists ──────────────────────────
        if not self.session_id:
            session = Session()
            self.graph_store.add_node(session)
            self.clarity_index.add_node(session)
            self.session_id = session.id
            self.orchestrator.current_session_id = session.id
            _save_session_id(self.session_id)
            self.terminal.display(f"📝 New session created: {session.id[:8]}...", style="dim")

        # ─── Display initial field state ─────────────────────────────
        summary = self.orchestrator.get_reentry_summary(self.session_id)
        self.terminal.display_field_state(summary)

        self.terminal.display_boot_reminder()

        # ─── Main Loop ──────────────────────────────────────────────
        self.running = True
        while self.running:
            try:
                user_input = await self.terminal.prompt()

                if user_input.lower() in ("exit", "quit", "goodbye"):
                    self.terminal.display("🌙 The field is quieting. Goodbye.", style="dim")
                    break

                if user_input.lower() == "reset session":
                    self.session_id = None
                    _save_session_id("")
                    self.terminal.display("🔄 Session reset.", style="yellow")
                    continue

                response = await self.orchestrator.process(
                    user_input,
                    session_id=self.session_id,
                )

                # ─── Update terminal coherence ──────────────────────
                self.terminal.update_coherence(response.confidence)

                # ─── Display insights ────────────────────────────────
                if response.insight:
                    self.terminal.display(
                        f"\n💡 {response.insight}", style="cyan", as_markdown=True
                    )

                if response.action:
                    self.terminal.display(f"\n⚡ {response.action}", style="yellow")

                # ─── Display confidence ──────────────────────────────
                # FIXED: This now shows response.confidence (0.80, 0.75, etc.)
                self.terminal.display(
                    f"\n📊 Confidence: {response.confidence:.2f}",
                    style="dim",
                )

                # ─── Save session ──────────────────────────────────────
                if self.orchestrator.current_session_id:
                    self.session_id = self.orchestrator.current_session_id
                    _save_session_id(self.session_id)

            except KeyboardInterrupt:
                self.terminal.display("\n\n🌙 Field interrupted. Goodbye.", style="dim")
                break
            except Exception as e:
                self.terminal.display(f"\n⚠️ Perturbation: {e}", style="red")
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
        self.running = False


async def run_field_app(
    graph_path: Optional[Path] = None,
    index_path: Optional[Path] = None,
    use_local_embedding: bool = True,
) -> None:
    app = FieldApp(
        graph_path=graph_path,
        index_path=index_path,
        use_local_embedding=use_local_embedding,
    )
    await app.run()


def main():
    asyncio.run(run_field_app())


if __name__ == "__main__":
    main()
