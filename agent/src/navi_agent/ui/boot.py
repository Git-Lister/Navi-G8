"""
Navi-G8 Boot Ritual – The Awakening of the Field.

A progressive, aesthetic sequence that transitions from darkness to
field awareness. Sets the tone for the session.
"""

import sys
import time
from typing import Optional

from rich.align import Align
from rich.console import Console
from rich.layout import Layout
from rich.live import Live
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.text import Text

console = Console()


class BootSequence:
    """
    The boot ritual – a progressive awakening of the field.

    Usage:
        boot = BootSequence()
        boot.run()
    """

    def __init__(self, title: str = "Navi-G8", version: str = "0.2.0"):
        self.title = title
        self.version = version
        self.steps = [
            ("🌱 Waking the field...", 0.8),
            ("📖 Loading the Cognitive Weave...", 1.0),
            ("🔗 Connecting to the Graph Store...", 0.6),
            ("🧠 Activating the Clarity Index...", 0.8),
            ("✨ Field is coherent. Welcome.", 0.4),
        ]

    def run(self) -> None:
        """Run the boot sequence."""
        console.clear()

        # Title screen
        title_text = Text()
        title_text.append(f"\n  {self.title}\n", style="bold cyan")
        title_text.append(f"  v{self.version}\n", style="dim")
        title_text.append("  — A Cognitive Field Interface —\n", style="italic yellow")

        console.print(Align.center(title_text))

        # Animated boot steps
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
            transient=False,
        ) as progress:
            task = progress.add_task("[cyan]Initialising...", total=len(self.steps))

            for step_text, duration in self.steps:
                progress.update(task, description=f"[cyan]{step_text}")
                time.sleep(duration)
                progress.advance(task, 1)

        # Final state
        console.print("\n")
        panel = Panel(
            "✨ The field is awake.\nType your first perturbation to begin.",
            title="[bold green]NAVI-G8 ONLINE[/bold green]",
            border_style="green",
            padding=(1, 2),
        )
        console.print(panel)
        console.print("\n")

    def quick_boot(self) -> None:
        """Quick boot with minimal output (for testing)."""
        console.print("[bold cyan]🌱 Field waking...[/bold cyan]", end=" ")
        for _ in range(3):
            time.sleep(0.2)
            console.print(".", end="", style="dim")
        console.print(" [bold green]✅[/bold green]")
        console.print("[dim]Type your first perturbation.[/dim]\n")


if __name__ == "__main__":
    # Test the boot sequence
    boot = BootSequence()
    boot.run()
