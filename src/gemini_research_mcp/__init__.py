"""Gemini Research MCP Server

AI-powered research using Gemini:
- research_quick: Fast grounded search (Gemini + Google Search)
- research_deep: Comprehensive research (Deep Research Agent, requires MCP Tasks)
- research_followup: Continue conversation after research completes
"""

__version__ = "0.1.0"

from gemini_research_mcp.citations import process_citations
from gemini_research_mcp.deep import (
    deep_research,
    deep_research_stream,
    research_followup,
)
from gemini_research_mcp.quick import quick_research
from gemini_research_mcp.server import main, mcp
from gemini_research_mcp.types import (
    DeepResearchError,
    DeepResearchProgress,
    DeepResearchResult,
    DeepResearchUsage,
    ParsedCitation,
    ResearchResult,
    Source,
)

__all__ = [
    "__version__",
    "DeepResearchError",
    "DeepResearchProgress",
    "DeepResearchResult",
    "DeepResearchUsage",
    "ParsedCitation",
    "ResearchResult",
    "Source",
    "quick_research",
    "deep_research",
    "deep_research_stream",
    "research_followup",
    "process_citations",
    "main",
    "mcp",
]
