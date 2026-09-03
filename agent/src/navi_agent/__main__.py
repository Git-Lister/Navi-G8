#!/usr/bin/env python3
"""
Navi-G8 – Field Interface Entry Point.

Run with: python -m navi_agent
"""

import asyncio
import sys

from .ui.app import run_field_app


def main():
    """Run the Navi-G8 Field Application."""
    try:
        asyncio.run(run_field_app())
    except KeyboardInterrupt:
        print("\n🌙 Field quieted. Goodbye.")
        sys.exit(0)


if __name__ == "__main__":
    main()
