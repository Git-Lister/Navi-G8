#!/usr/bin/env python3
"""
Navi-G8 Repository Scaffolder (Corrected)
- Uses setuptools for editable installs.
- Replaces llms with openai.
- Proper src layout with __init__.py in both src/ and navi_agent/.
"""

import os
import sys
from pathlib import Path

FILES = {}

def add_file(path, content):
    FILES[path] = content

# === .gitignore ===
add_file(".gitignore", """# Python
__pycache__/
*.py[cod]
*$py.class
.venv/
venv/
ENV/
env/
*.so
*.egg
*.egg-info/
dist/
build/
*.log
.pytest_cache/
.mypy_cache/
.ruff_cache/

# Rust
/target/
**/*.rs.bk
*.pdb
console/src-tauri/target/

# Node
node_modules/
dist/
dist-ssr/
*.local

# Environment & Config
.env
.env.local
config.local.toml

# OS
.DS_Store
Thumbs.db
*.swp
*.swo

# Navi-G8 specific
logs/
*.db
*.sqlite3
""")

# === .env.example ===
add_file(".env.example", """# LLM API Keys (optional, only needed if using cloud models)
OPENAI_API_KEY=sk-...
GROQ_API_KEY=...

# Local LLM (Ollama)
OLLAMA_BASE_URL=http://localhost:11434

# Search API (optional, for web_search tool)
TAVILY_API_KEY=...
""")

# === config.toml ===
add_file("config.toml", """# Navi-G8 Main Configuration

[workspace]
watch_folders = ["~/Documents", "~/Projects"]
exclude_extensions = [".tmp", ".log", ".pyc", ".class"]
max_file_size_bytes = 1048576

[llm]
primary_model = "llama3.1"
primary_base = "http://localhost:11434/v1"
fallback_model = "llama-3.1-70b-versatile"
fallback_base = "https://api.groq.com/openai/v1"
allow_cloud = false

[agent]
system_prompt = "You are Navi-G8, a helpful assistant."
max_iterations = 5

[logging]
level = "INFO"
json_format = true
log_dir = "~/.navi-g8/logs"
retention_days = 30

[meta]
enabled = true
schedule = "0 2 * * 0"
""")

# === README.md ===
add_file("README.md", """# Navi-G8 – Workstation Cognitive Layer

A personal, self-improving background intelligence for your entire workstation.

## Features
- **Local-First** – all data stays on your machine.
- **Protocol-Driven** – built on MCP.
- **Transparent** – every decision is logged.
- **Extensible** – drop-in tools.
- **Self-Improving** – learns from interactions.

## Quick Start
1. `cd agent`
2. `python -m venv .venv && .venv\\Scripts\\activate`
3. `pip install -e .`
4. `python -m navi_agent`
""")

# === agent/pyproject.toml (Corrected) ===
add_file("agent/pyproject.toml", """[build-system]
requires = ["setuptools>=61.0", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "navi-agent"
version = "0.1.0"
description = "Agent Core for Navi-G8"
readme = "README.md"
authors = [{ name = "Your Name", email = "you@example.com" }]
license = { text = "MIT" }
requires-python = ">=3.12"
dependencies = [
    "mcp[cli]>=1.0.0",
    "openai>=1.0.0",
    "structlog>=24.0.0",
    "tomli>=2.0.0",
    "watchdog>=4.0.0",
    "pandas>=2.0.0",
    "cryptography>=42.0.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=8.0.0",
    "pytest-asyncio>=0.23.0",
    "ruff>=0.6.0",
    "mypy>=1.10.0",
    "pre-commit>=3.7.0",
]

[tool.setuptools]
package-dir = { "" = "src" }

[tool.setuptools.packages.find]
where = ["src"]
include = ["navi_agent*"]

[tool.ruff]
line-length = 100
target-version = "py312"

[tool.mypy]
python_version = "3.12"
strict = true
ignore_missing_imports = true

[tool.pytest.ini_options]
asyncio_mode = "auto"
testpaths = ["tests"]
""")

# === agent/src/__init__.py (needed for package) ===
add_file("agent/src/__init__.py", "")

# === agent/src/navi_agent/__init__.py ===
add_file("agent/src/navi_agent/__init__.py", "")

# === agent/src/navi_agent/__main__.py ===
add_file("agent/src/navi_agent/__main__.py", """#!/usr/bin/env python3
from navi_agent.core import run_agent
import asyncio

if __name__ == "__main__":
    asyncio.run(run_agent())
""")

# === agent/src/navi_agent/core.py (Corrected imports) ===
add_file("agent/src/navi_agent/core.py", """import os
from pathlib import Path

import structlog
from mcp.server.fastmcp import FastMCP

from navi_agent.gateway import LLMGateway
from navi_agent.tools.file_tools import list_directory, read_file, write_file
from navi_agent.tools.web_tools import web_search

# Configure structured logging
log_dir = Path(os.getenv("NAVI_LOG_DIR", "~/.navi-g8/logs")).expanduser()
log_dir.mkdir(parents=True, exist_ok=True)

structlog.configure(
    processors=[
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.JSONRenderer(),
    ],
    context_class=dict,
    logger_factory=structlog.PrintLoggerFactory(),
)
logger = structlog.get_logger()

class NaviAgent:
    def __init__(self):
        self.mcp = FastMCP("Navi-G8 Agent")
        self.gateway = LLMGateway()
        self._register_tools()

    def _register_tools(self):
        self.mcp.tool()(read_file)
        self.mcp.tool()(write_file)
        self.mcp.tool()(list_directory)
        self.mcp.tool()(web_search)
        logger.info("tools_registered", count=4)

    async def run(self):
        logger.info("agent_starting", protocol="MCP")
        await self.mcp.run_stdio_async()

async def run_agent():
    agent = NaviAgent()
    await agent.run()
""")

# === agent/src/navi_agent/gateway.py (Using openai) ===
add_file("agent/src/navi_agent/gateway.py", """import os
from typing import List, Dict, Optional
from openai import OpenAI
import structlog

logger = structlog.get_logger()

class LLMGateway:
    def __init__(self):
        self.primary_base = os.getenv("NAVI_PRIMARY_BASE", "http://localhost:11434/v1")
        self.primary_model = os.getenv("NAVI_PRIMARY_MODEL", "llama3.1")
        self.fallback_base = os.getenv("NAVI_FALLBACK_BASE", "https://api.groq.com/openai/v1")
        self.fallback_model = os.getenv("NAVI_FALLBACK_MODEL", "llama-3.1-70b-versatile")
        self.allow_cloud = os.getenv("NAVI_ALLOW_CLOUD", "false").lower() == "true"
        self.api_key = os.getenv("OPENAI_API_KEY")

        self._primary_client = OpenAI(base_url=self.primary_base, api_key="ollama")
        self._fallback_client = None
        if self.allow_cloud and self.api_key:
            self._fallback_client = OpenAI(base_url=self.fallback_base, api_key=self.api_key)

    async def generate(self, prompt: str, system: Optional[str] = None) -> str:
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        try:
            resp = self._primary_client.chat.completions.create(
                model=self.primary_model,
                messages=messages,
                temperature=0.7,
                max_tokens=4096,
            )
            logger.info("llm_success", model=self.primary_model)
            return resp.choices[0].message.content
        except Exception as e:
            logger.warning("llm_primary_failed", error=str(e))
            if self._fallback_client:
                try:
                    resp = self._fallback_client.chat.completions.create(
                        model=self.fallback_model,
                        messages=messages,
                        temperature=0.7,
                        max_tokens=4096,
                    )
                    logger.info("llm_fallback_success", model=self.fallback_model)
                    return resp.choices[0].message.content
                except Exception as e2:
                    logger.error("llm_fallback_failed", error=str(e2))
                    raise RuntimeError("All LLM providers failed.")
            raise

    async def chat(self, messages: List[Dict[str, str]]) -> str:
        system = next((m["content"] for m in messages if m["role"] == "system"), None)
        user = next((m["content"] for m in messages if m["role"] == "user"), "")
        return await self.generate(user, system=system)
""")

# === agent/src/navi_agent/tools/file_tools.py ===
add_file("agent/src/navi_agent/tools/file_tools.py", """from pathlib import Path
from mcp.types import TextContent

async def read_file(path: str) -> list[TextContent]:
    try:
        p = Path(path).expanduser().resolve()
        if not p.exists():
            return [TextContent(type="text", text=f"File not found: {path}")]
        return [TextContent(type="text", text=p.read_text(encoding="utf-8"))]
    except Exception as e:
        return [TextContent(type="text", text=f"Error: {e}")]

async def write_file(path: str, content: str) -> list[TextContent]:
    try:
        p = Path(path).expanduser().resolve()
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content, encoding="utf-8")
        return [TextContent(type="text", text=f"Written to {path}")]
    except Exception as e:
        return [TextContent(type="text", text=f"Error: {e}")]

async def list_directory(path: str = ".") -> list[TextContent]:
    try:
        p = Path(path).expanduser().resolve()
        if not p.is_dir():
            return [TextContent(type="text", text=f"Not a directory: {path}")]
        items = [f"{'📁' if f.is_dir() else '📄'} {f.name}" for f in p.iterdir()]
        return [TextContent(type="text", text="\\n".join(items) or "Empty")]
    except Exception as e:
        return [TextContent(type="text", text=f"Error: {e}")]""")

# === agent/src/navi_agent/tools/web_tools.py (simplified) ===
add_file("agent/src/navi_agent/tools/web_tools.py", """import os
import httpx
from mcp.types import TextContent

TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")

async def web_search(query: str, num_results: int = 5) -> list[TextContent]:
    if TAVILY_API_KEY:
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                resp = await client.post(
                    "https://api.tavily.com/search",
                    json={"api_key": TAVILY_API_KEY, "query": query, "max_results": num_results}
                )
                data = resp.json()
                results = data.get("results", [])
                output = [f"- {r['title']}: {r['url']}\\n  {r['content'][:200]}..." for r in results]
                return [TextContent(type="text", text="\\n\\n".join(output) or "No results")]
        except Exception as e:
            return [TextContent(type="text", text=f"Search error: {e}")]
    else:
        # Free fallback (DuckDuckGo)
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                resp = await client.get(
                    "https://api.duckduckgo.com/",
                    params={"q": query, "format": "json", "no_html": 1, "skip_disambig": 1}
                )
                data = resp.json()
                topics = data.get("RelatedTopics", [])
                output = [f"- {t['Text']} ({t.get('FirstURL', '')})" for t in topics if "Text" in t]
                return [TextContent(type="text", text="\\n".join(output[:num_results]) or "No results")]
        except Exception as e:
            return [TextContent(type="text", text=f"Search error: {e}")]""")

# === agent/tests/unit/test_tools.py (minimal) ===
add_file("agent/tests/unit/test_tools.py", """import pytest
from navi_agent.tools.file_tools import read_file, write_file, list_directory

@pytest.mark.asyncio
async def test_read_file(tmp_path):
    f = tmp_path / "test.txt"
    f.write_text("hello")
    result = await read_file(str(f))
    assert "hello" in result[0].text

@pytest.mark.asyncio
async def test_write_file(tmp_path):
    f = tmp_path / "new.txt"
    await write_file(str(f), "content")
    assert f.read_text() == "content"

@pytest.mark.asyncio
async def test_list_directory(tmp_path):
    (tmp_path / "a.txt").touch()
    (tmp_path / "b").mkdir()
    result = await list_directory(str(tmp_path))
    assert "a.txt" in result[0].text
    assert "b" in result[0].text""")

# === Additional files (just the essentials) ===
add_file("agent/README.md", "# Navi-G8 Agent Core")
add_file("scripts/setup.sh", "#!/bin/bash\necho 'Run pip install -e . in agent/ instead.'")
add_file("CONTRIBUTING.md", "# Contributing\nSee README.")
add_file(".pre-commit-config.yaml", """repos:
  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.6.0
    hooks:
      - id: ruff
        args: [--fix]
      - id: ruff-format
""")
add_file("justfile", """default:
    @echo "Use pip install -e . in agent/ instead of just."
""")

# === Main ===
def generate(target):
    target = Path(target).resolve()
    if target.exists():
        if input(f"Overwrite {target}? (y/N) ").strip().lower() != 'y':
            print("Aborted.")
            return
    target.mkdir(parents=True, exist_ok=True)
    for path, content in FILES.items():
        full = target / path
        full.parent.mkdir(parents=True, exist_ok=True)
        if full.exists() and full.name == ".env":
            continue
        full.write_text(content, encoding="utf-8")
        print(f"Created: {path}")
    print("\n✅ Done! Now follow these steps:")
    print("1. cd", target)
    print("2. python -m venv agent/.venv")
    print("3. agent\\.venv\\Scripts\\activate")
    print("4. cd agent && pip install -e .")
    print("5. python -m navi_agent")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python scaffold.py <target_dir>")
        sys.exit(1)
    generate(sys.argv[1])