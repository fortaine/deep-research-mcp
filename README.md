# Deep Research MCP Server

[![PyPI version](https://badge.fury.io/py/deep-research-mcp.svg)](https://badge.fury.io/py/deep-research-mcp)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

MCP server for AI-powered research using **Gemini + Google Grounded Search**.

## Features

| Tool | Description | Latency |
|------|-------------|---------|
| `research_quick` | Fast grounded search with citations | 5-30 sec |
| `research_deep` | Multi-step research with real-time progress ([MCP Tasks](https://spec.modelcontextprotocol.io/specification/draft/server/tasks/)) | 3-20 min |
| `research_status` | Check status of background research tasks | instant |
| `research_followup` | Ask follow-up questions about completed research | 5-30 sec |

### Advanced Features

- **File Search**: Search your own data alongside web search using `file_search_store_names`
- **Follow-up Questions**: Continue the conversation after research completes using `previous_interaction_id`
- **Format Instructions**: Control report structure (sections, tables, tone)

## Installation

### From PyPI

```bash
pip install deep-research-mcp
# or
uv add deep-research-mcp
```

### From Source

```bash
git clone https://github.com/fortaine/deep-research-mcp
cd deep-research-mcp
uv sync
```

## Configuration

Create a `.env` file or set environment variables:

```bash
# Required
GEMINI_API_KEY=your-api-key-here

# Optional: Override default models
GEMINI_MODEL=gemini-2.5-flash
DEEP_RESEARCH_AGENT=gemini-2.5-pro-deep-research
```

Get your key from https://aistudio.google.com/apikey

## Usage

### VS Code (Recommended)

Add to `.vscode/mcp.json`:

```json
{
  "servers": {
    "deep-research": {
      "command": "uvx",
      "args": ["deep-research-mcp"],
      "env": {
        "GEMINI_API_KEY": "your-api-key"
      }
    }
  }
}
```

### Command Line

```bash
# After pip install
deep-research-mcp

# Or with uvx (no install needed)
uvx deep-research-mcp
```

## Architecture

- **Transport**: stdio (VS Code spawns as child process)
- **Tasks**: [MCP Tasks](https://spec.modelcontextprotocol.io/specification/draft/server/tasks/) (SEP-1732) with real-time progress
- **Framework**: [FastMCP](https://github.com/jlowin/fastmcp) 2.5+

## Module Structure

```
deep_research_mcp/
├── __init__.py     # Package exports
├── server.py       # MCP server (FastMCP tools)
├── config.py       # Configuration management
├── types.py        # Data types and exceptions
├── quick.py        # Quick research (grounded search)
├── deep.py         # Deep research (multi-step agent)
└── citations.py    # Citation extraction and URL resolution
```

## Development

```bash
uv sync --extra dev
uv run pytest
uv run mypy src/
uv run ruff check src/
```
