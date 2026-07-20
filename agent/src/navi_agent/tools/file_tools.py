from pathlib import Path
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
        return [TextContent(type="text", text="\n".join(items) or "Empty")]
    except Exception as e:
        return [TextContent(type="text", text=f"Error: {e}")]