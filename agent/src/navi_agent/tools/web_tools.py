import os
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
                output = [f"- {r['title']}: {r['url']}\n  {r['content'][:200]}..." for r in results]
                return [TextContent(type="text", text="\n\n".join(output) or "No results")]
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
                return [TextContent(type="text", text="\n".join(output[:num_results]) or "No results")]
        except Exception as e:
            return [TextContent(type="text", text=f"Search error: {e}")]