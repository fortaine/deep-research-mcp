"""Test clarification flow with vague queries.

This E2E test verifies that research_deep properly:
1. Detects vague queries
2. Uses SEP-1577 sampling with tools to analyze
3. Asks clarifying questions via elicitation
4. Proceeds with refined query

Requires: GEMINI_API_KEY environment variable
"""

import asyncio
import os
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastmcp import Context
from pydantic import BaseModel


class TestVagueQueryDetection:
    """Test that vague queries trigger clarification."""

    @pytest.fixture
    def vague_queries(self) -> list[str]:
        """Examples of vague queries that should trigger clarification."""
        return [
            "research AI",
            "compare python frameworks",
            "best practices",
            "analyze the market",
            "investigate trends",
            "MCP servers",
            "how to build apps",
        ]

    @pytest.fixture
    def specific_queries(self) -> list[str]:
        """Examples of specific queries that should NOT trigger clarification."""
        return [
            "Compare FastAPI vs Django for building REST APIs in 2025",
            "Research the environmental impact of electric vehicles vs gasoline cars in Europe",
            "Analyze the top 5 JavaScript testing frameworks for React applications in Q1 2026",
            "Investigate the adoption rate of Kubernetes in enterprise companies with over 1000 employees",
            "What are the security best practices for deploying Python MCP servers with OAuth 2.0?",
        ]

    @pytest.mark.asyncio
    async def test_analyzer_system_prompt_exists(self):
        """Verify the analyzer system prompt is well-structured."""
        from gemini_research_mcp.server import _ANALYZER_SYSTEM_PROMPT

        # Check key components
        assert "research query analyzer" in _ANALYZER_SYSTEM_PROMPT.lower()
        assert "vague" in _ANALYZER_SYSTEM_PROMPT.lower()
        assert "specific" in _ANALYZER_SYSTEM_PROMPT.lower()
        assert "ask_clarifying_questions" in _ANALYZER_SYSTEM_PROMPT

        # Check examples are included
        assert "compare python frameworks" in _ANALYZER_SYSTEM_PROMPT.lower()
        assert "research ai" in _ANALYZER_SYSTEM_PROMPT.lower()

    @pytest.mark.asyncio
    async def test_maybe_clarify_query_returns_original_without_context(self, vague_queries):
        """Without Context, should return original query unchanged."""
        from gemini_research_mcp.server import _maybe_clarify_query

        for query in vague_queries:
            result = await _maybe_clarify_query(query, ctx=None)
            assert result == query, f"Expected {query!r} unchanged, got {result!r}"

    @pytest.mark.asyncio
    async def test_clarify_tool_returns_empty_without_context(self, vague_queries):
        """The internal clarify tool should return empty string when no context."""
        from gemini_research_mcp.server import _ask_clarifying_questions

        result = await _ask_clarifying_questions(
            questions=["What type of AI?", "What application domain?"],
            original_query="research AI",
        )
        assert result == "", "Should return empty string without context"


@pytest.mark.skipif(
    not os.environ.get("GEMINI_API_KEY"),
    reason="GEMINI_API_KEY not set",
)
class TestVagueQueryClarificationE2E:
    """E2E tests that verify the full clarification flow.
    
    These tests use mocked sampling to avoid actual LLM calls for most cases,
    but verify the integration works end-to-end.
    """

    @pytest.mark.asyncio
    @pytest.mark.e2e
    async def test_clarify_query_via_sampling_with_mock(self):
        """Test _clarify_query_via_sampling with mocked ctx.sample()."""
        from gemini_research_mcp.server import AnalyzedQuery, _clarify_query_via_sampling

        # Create mock context with sample method
        mock_ctx = MagicMock(spec=Context)

        async def mock_sample(**kwargs):
            """Mock sampling that simulates clarification."""
            # Simulate the LLM deciding to NOT call the tool (specific query)
            result = MagicMock()
            result.result = AnalyzedQuery(
                refined_query="Compare Django, FastAPI, and Flask for REST API development in Python 2025",
                was_clarified=True,
                summary="Narrowed scope to REST APIs and 2025",
            )
            return result

        mock_ctx.sample = mock_sample

        # Test with a vague query
        result = await _clarify_query_via_sampling("compare python frameworks", mock_ctx)

        assert "Django" in result or "FastAPI" in result
        assert "2025" in result

    @pytest.mark.asyncio
    @pytest.mark.e2e
    async def test_clarify_query_sampling_fallback_on_error(self):
        """When sampling fails, should return original query."""
        from gemini_research_mcp.server import _clarify_query_via_sampling

        mock_ctx = MagicMock(spec=Context)
        mock_ctx.sample = AsyncMock(side_effect=Exception("Sampling not supported"))

        result = await _clarify_query_via_sampling("research AI", mock_ctx)

        # Should gracefully fall back to original query
        assert result == "research AI"

    @pytest.mark.asyncio
    @pytest.mark.e2e
    async def test_specific_query_passes_through(self):
        """Specific queries should pass through unchanged."""
        from gemini_research_mcp.server import AnalyzedQuery, _clarify_query_via_sampling

        mock_ctx = MagicMock(spec=Context)
        specific_query = "Compare FastAPI vs Django for building REST APIs in 2025"

        async def mock_sample(**kwargs):
            """Mock sampling that passes specific query through."""
            result = MagicMock()
            result.result = AnalyzedQuery(
                refined_query=specific_query,  # Unchanged
                was_clarified=False,
                summary="Query was already specific",
            )
            return result

        mock_ctx.sample = mock_sample

        result = await _clarify_query_via_sampling(specific_query, mock_ctx)

        assert result == specific_query


class TestResearchDeepWithClarification:
    """Integration tests for research_deep tool with clarification phase."""

    @pytest.mark.asyncio
    async def test_research_deep_tool_structure(self):
        """Verify research_deep tool has correct structure for clarification."""
        from fastmcp.client import Client

        from gemini_research_mcp.server import mcp

        async with Client(mcp) as client:
            tools = await client.list_tools()
            tool = next((t for t in tools if t.name == "research_deep"), None)

            assert tool is not None
            assert "comprehensive" in tool.description.lower() or "autonomous" in tool.description.lower()

            # Check it has optional task support
            if tool.execution:
                assert tool.execution.taskSupport == "optional"

    @pytest.mark.asyncio
    async def test_research_deep_accepts_vague_queries(self):
        """research_deep should accept vague queries (clarification happens inside)."""
        from fastmcp.client import Client

        from gemini_research_mcp.server import mcp

        async with Client(mcp) as client:
            tools = await client.list_tools()
            tool = next((t for t in tools if t.name == "research_deep"), None)

            # Check input schema allows any string query
            input_schema = tool.inputSchema
            query_prop = input_schema.get("properties", {}).get("query", {})
            assert query_prop.get("type") == "string"
            # No minLength or pattern restrictions


class TestClarificationWithElicitation:
    """Test the elicitation flow within clarification."""

    @pytest.mark.asyncio
    async def test_ask_clarifying_questions_with_mock_elicit(self):
        """Test _ask_clarifying_questions with mocked elicitation."""
        from gemini_research_mcp.server import _ask_clarifying_questions
        import gemini_research_mcp.server as server_module

        # Create mock context with elicit method
        mock_ctx = MagicMock(spec=Context)

        async def mock_elicit(message, response_type):
            result = MagicMock()
            result.action = "accept"
            result.data = {
                "answer_1": "Web frameworks for REST APIs",
                "answer_2": "Production use in 2025",
            }
            return result

        mock_ctx.elicit = mock_elicit

        # Set the global context
        original_ctx = server_module._clarification_context
        server_module._clarification_context = mock_ctx

        try:
            result = await _ask_clarifying_questions(
                questions=["What type of frameworks?", "What time period?"],
                original_query="compare python frameworks",
            )

            # Should have collected answers
            assert "Web frameworks" in result or "REST APIs" in result or "2025" in result
        finally:
            server_module._clarification_context = original_ctx

    @pytest.mark.asyncio
    async def test_ask_clarifying_questions_handles_skip(self):
        """When user skips elicitation, should return empty string."""
        from gemini_research_mcp.server import _ask_clarifying_questions
        import gemini_research_mcp.server as server_module

        mock_ctx = MagicMock(spec=Context)

        async def mock_elicit(message, response_type):
            result = MagicMock()
            result.action = "cancel"  # User cancelled/skipped
            result.data = None
            return result

        mock_ctx.elicit = mock_elicit

        original_ctx = server_module._clarification_context
        server_module._clarification_context = mock_ctx

        try:
            result = await _ask_clarifying_questions(
                questions=["What type?"],
                original_query="research AI",
            )

            assert result == ""
        finally:
            server_module._clarification_context = original_ctx


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
