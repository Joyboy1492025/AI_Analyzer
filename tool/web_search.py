"""Web search tool (DuckDuckGo)."""

from langchain_core.tools import tool


@tool
def web_search(query: str) -> str:
    """Search latest information from the internet."""
    from langchain_community.tools import DuckDuckGoSearchRun

    return DuckDuckGoSearchRun().run(query)