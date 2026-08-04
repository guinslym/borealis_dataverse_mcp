# Changelog

## 0.3.0 — Borealis Research Toolkit refactor

- Split Borealis API access, research logic, transports, configuration, and institution mappings into modules.
- Added structured results with provenance and warnings.
- Added stdio MCP and Streamable HTTP MCP entry points.
- Added an optional FastAPI REST interface.
- Added bounded streaming file downloads and partial line retrieval.
- Added CSV/TSV profiling with explicit interpretation warnings.
- Added Docker, Compose, environment template, GitHub Actions, and architecture documentation.
- Kept `borealis_server.py` as a backward-compatible local entry point.

## 0.2.0

- Added dataset-only defaults, pagination, date filters, diagnostics, and initial tabular profiling.
