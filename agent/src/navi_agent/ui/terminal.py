"""
Navi-G8 Field Terminal – The sensory manifestation of the cognitive field.

Input and output interleaved in a single stream. No `$` prompt – just the field.
Displays a subtle pulse indicating field coherence.
"""

import sys
from typing import Awaitable, Callable, List, Optional

from rich.align import Align
from rich.columns import Columns
from rich.console import Console
from rich.live import Live
from rich.markdown import Markdown
from rich.panel import Panel
from rich.prompt import Prompt
from rich.text import Text

console = Console()


class FieldTerminal:
    """
    The terminal as a field – interleaved input/output with coherence indication.

    Usage:
        terminal = FieldTerminal()
        terminal.display("Welcome to the field.")
        user_input = await terminal.prompt()
    """

    def __init__(self, coherence: float = 0.5):
        self.history: List[str] = []
        self.coherence = coherence
        self._prompt_visible = False

    def _coherence_indicator(self) -> str:
        """Return a visual indicator of field coherence."""
        if self.coherence >= 0.8:
            return "🟢"  # High coherence – calm, steady
        elif self.coherence >= 0.5:
            return "🟡"  # Medium coherence – pulse
        else:
            return "🔴"  # Low coherence – rapid pulse

    def _coherence_color(self) -> str:
        """Return a colour based on coherence."""
        if self.coherence >= 0.8:
            return "green"
        elif self.coherence >= 0.5:
            return "yellow"
        else:
            return "red"

    def display(self, content: str, style: str = "white", as_markdown: bool = False) -> None:
        """
        Display content in the field.

        Args:
            content: The text to display.
            style: Rich style string.
            as_markdown: Whether to render as Markdown.
        """
        # Add a subtle field marker
        indicator = self._coherence_indicator()
        color = self._coherence_color()

        # Format the output
        if as_markdown:
            rendered = Markdown(content)
            console.print(rendered)
        else:
            # Wrap in a subtle panel for insight/action blocks
            if "INSIGHT" in content or "insight" in content[:20].lower():
                panel = Panel(
                    content,
                    title="[bold cyan]💡 Insight[/bold cyan]",
                    border_style="cyan",
                    padding=(0, 1),
                )
                console.print(panel)
            elif "ACTION" in content or "action" in content[:20].lower():
                panel = Panel(
                    content,
                    title="[bold yellow]⚡ Action[/bold yellow]",
                    border_style="yellow",
                    padding=(0, 1),
                )
                console.print(panel)
            else:
                console.print(content, style=style)

        self.history.append(content)

    def display_field_state(self, summary: dict) -> None:
        """
        Display the current field state.

        Args:
            summary: A dictionary from orchestrator.get_reentry_summary()
        """
        lines = []

        if summary.get("has_state", False):
            field = summary.get("field")
            active = summary.get("active_trajectories", [])
            flags = summary.get("unresolved_flags", [])
            volatile = summary.get("volatile_streams", [])

            lines.append(f"[bold]🌐 Field State[/bold]")
            lines.append(f"  Coherence: {field.coherence:.2f}" if field else "")
            lines.append(f"  Active trajectories: {len(active)}")
            lines.append(f"  Unresolved flags: {len(flags)}")
            lines.append(f"  Volatile streams: {len(volatile)}")

            if active:
                lines.append(f"  → Current: {active[0].description}")
            if flags:
                lines.append(f"  ⚠️  Pending: {flags[0].description}")

        else:
            lines.append("[dim]No previous field state.[/dim]")
            lines.append("[dim]This is a new session.[/dim]")

        panel = Panel(
            "\n".join(lines),
            title="[bold cyan]🧭 Field Status[/bold cyan]",
            border_style="cyan",
            padding=(0, 1),
        )
        console.print(panel)

    def display_boot_reminder(self) -> None:
        """Display a subtle reminder of the field's nature."""
        console.print(
            "[dim]💡 Remember: insight precedes ecstasy. What false problem are you dissolving today?[/dim]",
            style="dim italic",
        )

    async def prompt(self, placeholder: Optional[str] = None) -> str:
        """
        Get input from the user – the field speaks.

        Args:
            placeholder: Optional placeholder text.

        Returns:
            The user's input.
        """
        # Show the field is listening
        indicator = self._coherence_indicator()
        color = self._coherence_color()

        # Display a subtle prompt – no `$`, just a gentle nudge
        console.print(
            f"[{color}]➜[/{color}] ",
            end="",
            style=color,
        )

        # Use rich's Prompt with a custom style
        if placeholder:
            user_input = Prompt.ask(f"[{color}]➜[/{color}]", default=placeholder)
        else:
            user_input = Prompt.ask(f"[{color}]➜[/{color}]")

        # Record the input in history
        self.history.append(f"> {user_input}")

        return user_input.strip()

    def update_coherence(self, coherence: float) -> None:
        """Update the field coherence value."""
        self.coherence = max(0.0, min(1.0, coherence))


# ─── Test ─────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import asyncio

    async def test_terminal():
        terminal = FieldTerminal(coherence=0.75)
        terminal.display("Welcome to the Navi-G8 field.", style="bold cyan")
        terminal.display_field_state({"has_state": False})
        terminal.display_boot_reminder()

        user_input = await terminal.prompt("Type something...")
        terminal.display(f"You said: {user_input}", style="green")

    asyncio.run(test_terminal())
