import os
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
