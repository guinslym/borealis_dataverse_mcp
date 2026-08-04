from __future__ import annotations

from collections import Counter
import csv
import io
import json
from typing import Any

from .client import BorealisClient
from .errors import BorealisUnsupportedFileError
from .institutions import normalize_institution
from .models import Provenance, ToolkitResult
from .utils import human_size, normalize_boolean_query, normalize_identifier, utc_now_iso

_TEXT_EXTENSIONS = {
    ".txt", ".csv", ".tsv", ".dat", ".sps", ".r", ".py", ".json", ".md",
    ".readme", ".do", ".sas", ".sql", ".xml", ".log", ".sh", ".yaml", ".yml",
    ".ini", ".cfg", ".conf",
}


class BorealisService:
    """Host-neutral research functions shared by MCP and REST transports."""

    def __init__(self, client: BorealisClient | None = None) -> None:
        self.client = client or BorealisClient()

    async def search_datasets(
        self,
        query: str,
        *,
        institution: str | None = None,
        country: str | None = None,
        province: str | None = None,
        city: str | None = None,
        result_type: str = "dataset",
        per_page: int = 10,
        start: int = 0,
        sort: str = "relevance",
        date_from: str | None = None,
        date_to: str | None = None,
    ) -> ToolkitResult:
        per_page = max(1, min(int(per_page), 100))
        start = max(0, int(start))
        query = normalize_boolean_query(query.strip() or "*")
        params: list[tuple[str, Any]] = [("q", query), ("type", result_type), ("per_page", per_page), ("start", start)]
        if sort != "relevance":
            params += [("sort", sort), ("order", "desc" if sort == "date" else "asc")]
        subtree = normalize_institution(institution)
        if subtree:
            params.append(("subtree", subtree))
        if country:
            params.append(("fq", f"country:{country}"))
        if province:
            params.append(("fq", f"state:{province}"))
        if city:
            params.append(("fq", f"city:{city}"))
        if date_from or date_to:
            lower = date_from or "*"
            upper = date_to or "*"
            params.append(("fq", f"publicationDate:[{lower} TO {upper}]"))

        payload, used_auth = await self.client.request_json("GET", "search", params=params)
        search_data = payload.get("data", {})
        raw_items = search_data.get("items", [])
        items: list[dict[str, Any]] = []
        for item in raw_items:
            global_id = item.get("global_id", "")
            doi_url = ""
            if global_id:
                doi_url = global_id if str(global_id).startswith("http") else f"https://doi.org/{str(global_id).replace('doi:', '')}"
            items.append({
                "type": item.get("type"),
                "title": item.get("name", "Untitled"),
                "persistent_id": global_id or None,
                "doi_url": doi_url or item.get("url"),
                "authors": item.get("authors", []),
                "published_at": item.get("published_at"),
                "description": item.get("description"),
                "source_url": item.get("url"),
                "institution": item.get("publisher"),
            })
        total = int(search_data.get("total_count", len(items)))
        next_start = start + len(items) if start + len(items) < total else None
        data = {
            "query": query,
            "scope": {"institution": institution, "subtree": subtree, "country": country, "province": province, "city": city, "result_type": result_type},
            "total_matches": total,
            "start": start,
            "returned": len(items),
            "next_start": next_start,
            "results": items,
        }
        return ToolkitResult(data, Provenance("GET /api/search", utc_now_iso(), used_auth, dict(params)))

    async def get_dataset_metadata(self, identifier: str) -> ToolkitResult:
        normalized, persistent = normalize_identifier(identifier)
        if persistent:
            endpoint = "datasets/:persistentId/metadata"
            params = {"persistentId": normalized}
        else:
            endpoint = f"datasets/{normalized}/metadata"
            params = None
        payload, used_auth = await self.client.request_json("GET", endpoint, params=params, accept="application/ld+json")
        metadata = payload.get("data", payload)
        return ToolkitResult(metadata, Provenance(f"GET /api/{endpoint}", utc_now_iso(), used_auth, params or {}))

    async def list_dataset_files(
        self,
        identifier: str,
        *,
        limit: int = 20,
        offset: int = 0,
        file_type: str | None = None,
        version: str = ":latest-published",
    ) -> ToolkitResult:
        normalized, persistent = normalize_identifier(identifier)
        limit = max(1, min(int(limit), 1000))
        offset = max(0, int(offset))
        if persistent:
            endpoint = f"datasets/:persistentId/versions/{version}/files"
            params = {"persistentId": normalized, "limit": limit, "offset": offset}
        else:
            endpoint = f"datasets/{normalized}/versions/{version}/files"
            params = {"limit": limit, "offset": offset}
        payload, used_auth = await self.client.request_json("GET", endpoint, params=params)
        raw_files = payload.get("data", [])
        results: list[dict[str, Any]] = []
        for entry in raw_files:
            data_file = entry.get("dataFile", {})
            filename = data_file.get("filename", entry.get("label", "Unnamed file"))
            friendly = data_file.get("friendlyType", "Unknown")
            if file_type and file_type.lower() not in f"{filename} {friendly}".lower():
                continue
            results.append({
                "file_id": data_file.get("id"),
                "filename": filename,
                "description": entry.get("description"),
                "friendly_type": friendly,
                "content_type": data_file.get("contentType"),
                "size_bytes": data_file.get("filesize", 0),
                "size_display": human_size(int(data_file.get("filesize", 0))),
                "restricted": bool(entry.get("restricted", False)),
                "md5": data_file.get("md5"),
                "download_url": f"https://borealisdata.ca/api/access/datafile/{data_file.get('id')}",
            })
        total = int(payload.get("totalCount", len(raw_files)))
        return ToolkitResult(
            {"identifier": normalized, "version": version, "total_files": total, "offset": offset, "returned": len(results), "files": results},
            Provenance(f"GET /api/{endpoint}", utc_now_iso(), used_auth, params),
        )

    async def get_dataset_file(
        self,
        file_id: str,
        *,
        filename: str = "file.txt",
        start_line: int = 1,
        max_lines: int = 100,
    ) -> ToolkitResult:
        start_line = max(1, int(start_line))
        max_lines = max(1, min(int(max_lines), 2000))
        suffix = "." + filename.lower().rsplit(".", 1)[-1] if "." in filename else ""
        if suffix and suffix not in _TEXT_EXTENSIONS and suffix != ".docx":
            raise BorealisUnsupportedFileError(f"{filename} is not a supported text format.")
        raw, content_type, used_auth = await self.client.download_limited(str(file_id))
        if suffix == ".docx":
            try:
                from docx import Document
            except ImportError as exc:
                raise BorealisUnsupportedFileError("Install the 'docx' optional dependency to read Word files.") from exc
            doc = Document(io.BytesIO(raw))
            text = "\n".join(p.text for p in doc.paragraphs)
            encoding = "docx"
        else:
            try:
                text = raw.decode("utf-8-sig")
                encoding = "utf-8"
            except UnicodeDecodeError:
                text = raw.decode("latin-1")
                encoding = "latin-1"
        lines = text.splitlines()
        selected = lines[start_line - 1:start_line - 1 + max_lines]
        end_line = start_line + len(selected) - 1
        return ToolkitResult(
            {"file_id": str(file_id), "filename": filename, "content_type": content_type, "encoding": encoding, "start_line": start_line, "end_line": end_line, "total_lines": len(lines), "truncated": end_line < len(lines), "content": "\n".join(selected)},
            Provenance(f"GET /api/access/datafile/{file_id}", utc_now_iso(), used_auth, {"start_line": start_line, "max_lines": max_lines}),
        )

    async def profile_tabular_file(
        self,
        file_id: str,
        *,
        filename: str = "table.csv",
        delimiter: str | None = None,
        max_rows: int = 100_000,
    ) -> ToolkitResult:
        max_rows = max(1, min(int(max_rows), 250_000))
        raw, content_type, used_auth = await self.client.download_limited(str(file_id))
        try:
            text = raw.decode("utf-8-sig")
            encoding = "utf-8"
        except UnicodeDecodeError:
            text = raw.decode("latin-1")
            encoding = "latin-1"
        if delimiter in {"tab", "\\t"}:
            delimiter = "\t"
        if not delimiter:
            try:
                delimiter = csv.Sniffer().sniff(text[:65536], delimiters=",\t;|").delimiter
            except csv.Error:
                delimiter = "\t" if filename.lower().endswith(".tsv") else ","
        reader = csv.DictReader(io.StringIO(text), delimiter=delimiter)
        if not reader.fieldnames:
            raise ValueError("No header row could be detected.")
        columns = [name or f"column_{index + 1}" for index, name in enumerate(reader.fieldnames)]
        missing = Counter()
        distinct: dict[str, set[str]] = {name: set() for name in columns}
        common: dict[str, Counter[str]] = {name: Counter() for name in columns}
        numeric: dict[str, list[float]] = {name: [] for name in columns}
        rows = 0
        for row in reader:
            if rows >= max_rows:
                break
            rows += 1
            for name in columns:
                value = str(row.get(name, "") or "").strip()
                if value.lower() in {"", "na", "n/a", "null", "none"}:
                    missing[name] += 1
                    continue
                if len(distinct[name]) < 100_000:
                    distinct[name].add(value)
                common[name][value] += 1
                try:
                    numeric[name].append(float(value))
                except ValueError:
                    pass
        profiles = []
        for name in columns:
            non_missing = rows - missing[name]
            numeric_values = numeric[name]
            inferred = "number" if non_missing and len(numeric_values) / non_missing >= 0.95 else "text"
            profile: dict[str, Any] = {
                "name": name,
                "inferred_type": inferred,
                "missing": missing[name],
                "distinct_in_profile": len(distinct[name]),
                "most_common": [{"value": value, "count": count} for value, count in common[name].most_common(5)],
            }
            if numeric_values:
                profile["numeric_min"] = min(numeric_values)
                profile["numeric_max"] = max(numeric_values)
            profiles.append(profile)
        warnings = ["Profile statistics describe rows read from the file; they do not prove that one row equals one person, sample, or observation."]
        if rows >= max_rows:
            warnings.append(f"Profiling stopped at max_rows={max_rows:,}.")
        return ToolkitResult(
            {"file_id": str(file_id), "filename": filename, "content_type": content_type, "encoding": encoding, "delimiter": delimiter, "rows_profiled": rows, "columns": profiles},
            Provenance(f"GET /api/access/datafile/{file_id}", utc_now_iso(), used_auth, {"max_rows": max_rows}),
            warnings,
        )

    def server_status(self) -> ToolkitResult:
        settings = self.client.settings
        return ToolkitResult(
            {"name": "Borealis Research Toolkit", "version": "0.3.0", "api_base_url": settings.api_base_url, "authentication_configured": settings.authentication_configured, "max_file_bytes": settings.max_file_bytes, "capabilities": ["search", "metadata", "file_listing", "text_file_reading", "tabular_profiling", "stdio_mcp", "streamable_http_mcp", "rest_api"]},
            Provenance("local", utc_now_iso(), False, {}),
        )
