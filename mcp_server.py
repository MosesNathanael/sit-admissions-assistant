"""SIT Admissions Assistant: MCP server (Day 4, part 1).

Run in the Inspector (from the project root):  mcp dev mcp_server.py
"""

import json
from pathlib import Path

from mcp.server.fastmcp import FastMCP  

from rag import ask_query, MAX_DISTANCE  

DATA_FILE = Path(__file__).parent / "data" / "key_dates.json"

N_RESULTS = 5

mcp = FastMCP("SIT Admissions Assistant")


@mcp.tool()
def search_admissions_info(query: str, topic: str | None = None) -> list[dict]:
    """Search SIT admissions information and return relevant passages with sources.

    Args:
        query: The question or keywords to look up (e.g. "entry requirements for nursing").
        topic: Optional topic to narrow the search (e.g. "scholarships", "fees", "requirements").
    """
    # Your Chroma metadata has no topic field, so bias the query text instead.
    full_query = f"{topic}: {query}" if topic else query

    chunks = ask_query(full_query, N_RESULTS)

    return [
        {
            "text": c["text"],
            "title": c["title"],
            "source_url": c["url"],
            "ay": c["ay"],
            "distance": round(c["distance"], 4),
        }
        for c in chunks
        if c["distance"] <= MAX_DISTANCE
    ]


@mcp.tool()
def get_key_dates(applies_to: str | None = None) -> list[dict]:
    """Get verified SIT admissions key dates from data/key_dates.json.

    Args:
        applies_to: Optional filter, e.g. "Engineering", "Allied Health", "Early Admissions".
            Matches case-insensitively. Entries for all applicants are always included.
    """
    with open(DATA_FILE, encoding="utf-8") as f:
        dates = json.load(f)

    if not applies_to:
        return dates

    needle = applies_to.lower()
    return [
        d
        for d in dates
        if needle in d["applies_to"].lower() or d["applies_to"].lower().startswith("all ")
    ]


if __name__ == "__main__":
    mcp.run()