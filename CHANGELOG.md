# Changelog

## Unreleased

- Added `get_variable_metadata`, which parses a tabular file's DDI codebook XML into variable labels, value labels, question text, universe, type, and summary statistics.
- Added `assess_metadata_quality`, which scores a dataset's DDI metadata completeness (0-100, letter grade) against a 15-field rubric and returns prioritized recommendations for missing fields.
- Added a `tabular` flag to `list_dataset_files` output.

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
