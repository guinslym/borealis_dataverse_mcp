# Architecture

The toolkit separates Borealis-specific research logic from the protocol used to expose it.

```text
Claude web / remote MCP clients ── Streamable HTTP MCP ┐
Claude Desktop / local clients ── stdio MCP            ├── BorealisService ── BorealisClient ── Borealis API
Other applications ────────────── REST API             ┘
```

## Modules

- `client.py`: HTTP, authentication fallback, errors, and bounded file downloads.
- `service.py`: dataset search, metadata, file listing, text retrieval, and tabular profiling.
- `mcp_server.py`: MCP tool definitions and stdio/Streamable HTTP entry points.
- `rest_api.py`: optional REST routes for integrations that do not support MCP.
- `institutions.py`: institution aliases and Borealis subtree identifiers.

The service layer returns structured `ToolkitResult` values containing `data`, `provenance`, and `warnings`. Transport layers do not duplicate Borealis logic.
