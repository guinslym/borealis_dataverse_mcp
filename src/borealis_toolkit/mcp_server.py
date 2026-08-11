from __future__ import annotations

import os
from typing import Literal

from mcp.server.fastmcp import FastMCP

from .service import BorealisService

mcp = FastMCP(
    "Borealis Research Toolkit",
    instructions=(
        "Search and inspect research datasets in Borealis Dataverse. "
        "Treat institution filters as publishing-collection filters and geographic filters as places the data describes. "
        "Always preserve DOI URLs and provenance returned by tools."
    ),
)
service = BorealisService()


@mcp.tool()
async def search_datasets(
    query: str,
    institution: str | None = None,
    country: str | None = None,
    province: str | None = None,
    city: str | None = None,
    result_type: Literal["dataset", "dataverse", "file"] = "dataset",
    per_page: int = 10,
    start: int = 0,
    sort: Literal["relevance", "date", "name"] = "relevance",
    date_from: str | None = None,
    date_to: str | None = None,
) -> dict:
    """Search Borealis. Dataset-only is the default. Returns structured results and provenance.

    Borealis combines bare terms with OR, so a multi-word title matches thousands of unrelated
    records. Wrap a known survey or dataset title in double quotes to search it as a phrase:
    '"Canadian Community Health Survey"' returns the survey itself, while the unquoted words
    return unrelated health records. Add unquoted terms such as a year alongside a quoted phrase
    to rank matching cycles first. Prefer the default relevance sort when the title is known,
    because sorting by date discards relevance entirely.
    """
    result = await service.search_datasets(
        query,
        institution=institution,
        country=country,
        province=province,
        city=city,
        result_type=result_type,
        per_page=per_page,
        start=start,
        sort=sort,
        date_from=date_from,
        date_to=date_to,
    )
    return result.to_dict()


@mcp.tool()
async def get_dataset_metadata(identifier: str) -> dict:
    """Get complete deposited metadata for a dataset by DOI URL, DOI, or numeric dataset ID."""
    return (await service.get_dataset_metadata(identifier)).to_dict()


@mcp.tool()
async def list_dataset_files(
    identifier: str,
    limit: int = 20,
    offset: int = 0,
    file_type: str | None = None,
    version: str = ":latest-published",
) -> dict:
    """List files in a dataset version, including file IDs, sizes, access status, and checksums."""
    return (await service.list_dataset_files(identifier, limit=limit, offset=offset, file_type=file_type, version=version)).to_dict()


@mcp.tool()
async def get_dataset_file(
    file_id: str,
    filename: str = "file.txt",
    start_line: int = 1,
    max_lines: int = 100,
) -> dict:
    """Read a safe range from a small text or Word file. Binary formats return a clear error."""
    return (await service.get_dataset_file(file_id, filename=filename, start_line=start_line, max_lines=max_lines)).to_dict()


@mcp.tool()
async def profile_tabular_file(
    file_id: str,
    filename: str = "table.csv",
    delimiter: str | None = None,
    max_rows: int = 100000,
) -> dict:
    """Profile CSV/TSV columns, missing values, distinct values, common values, and numeric ranges."""
    return (await service.profile_tabular_file(file_id, filename=filename, delimiter=delimiter, max_rows=max_rows)).to_dict()


@mcp.tool()
def get_server_status() -> dict:
    """Return toolkit version, limits, API target, authentication state, and capabilities."""
    return service.server_status().to_dict()


def main() -> None:
    """Run the local stdio MCP transport, suitable for Claude Desktop and other local hosts."""
    mcp.run(transport="stdio")


def _split_env_list(name: str) -> list[str]:
    return [item.strip() for item in os.getenv(name, "").split(",") if item.strip()]


def main_http() -> None:
    """Run Streamable HTTP MCP for Claude web, ChatGPT, and other remote MCP clients."""
    # FastMCP reads FASTMCP_HOST and FASTMCP_PORT through pydantic-settings, which silently
    # fails to resolve them on current releases, so bind explicitly instead.
    mcp.settings.host = os.getenv("MCP_HOST", "127.0.0.1")
    mcp.settings.port = int(os.getenv("MCP_PORT", "8000"))

    # DNS rebinding protection trusts only localhost by default, so a tunnel or proxy hostname
    # must be named explicitly before a remote client can reach the endpoint.
    allowed_hosts = _split_env_list("MCP_ALLOWED_HOSTS")
    security = mcp.settings.transport_security
    if allowed_hosts and security is not None:
        allowed_origins = _split_env_list("MCP_ALLOWED_ORIGINS") or [f"https://{host}" for host in allowed_hosts]
        security.allowed_hosts = [*security.allowed_hosts, *allowed_hosts]
        security.allowed_origins = [*security.allowed_origins, *allowed_origins]

    mcp.run(transport="streamable-http")


if __name__ == "__main__":
    main()
