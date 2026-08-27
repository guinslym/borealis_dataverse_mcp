from __future__ import annotations

from typing import Any

# Each spec scores one DDI-relevant field out of a Dataverse dataset's exported
# metadata. `match` substrings are checked against metadata's top-level keys
# (case-insensitively) rather than one fixed key name, because different
# Dataverse installs prefix fields with different metadata-block namespaces
# (e.g. 'citation:', 'socialscience:', 'geospatial:') depending on which
# blocks they enable.
_FIELD_SPECS: list[dict[str, Any]] = [
    {"key": "title", "weight": 5, "category": "discovery", "match": ["title"]},
    {"key": "author", "weight": 5, "category": "discovery", "match": ["author"]},
    {"key": "description", "weight": 10, "category": "discovery", "match": ["dsdescription"], "min_length": 100},
    {"key": "keywords", "weight": 8, "category": "discovery", "match": ["keyword"], "min_count": 3},
    {"key": "related_publications", "weight": 5, "category": "discovery", "match": ["publication"]},
    {"key": "date_of_collection", "weight": 7, "category": "coverage", "match": ["dateofcollection"]},
    {"key": "geographic_coverage", "weight": 7, "category": "coverage", "match": ["geographiccoverage", "geographicunit"]},
    {"key": "unit_of_analysis", "weight": 8, "category": "coverage", "match": ["unitofanalysis"]},
    {"key": "universe", "weight": 8, "category": "coverage", "match": ["universe"]},
    {"key": "time_period_covered", "weight": 7, "category": "coverage", "match": ["timeperiodcovered"]},
    {"key": "data_collection_method", "weight": 8, "category": "methodology", "match": ["collectionmode", "typeofdatacollection", "researchinstrument"]},
    {"key": "sampling_procedure", "weight": 7, "category": "methodology", "match": ["samplingprocedure"]},
    {"key": "license", "weight": 6, "category": "access", "match": ["license"]},
    {"key": "file_format_documented", "weight": 5, "category": "access", "match": ["kindofdata"]},
]

VARIABLE_METADATA_WEIGHT = 10
VARIABLE_METADATA_CATEGORY = "access"

_RECOMMENDATIONS: dict[str, str] = {
    "title": "Add a descriptive title. It is the primary field used for discovery and citation.",
    "author": "Add at least one author with name and affiliation.",
    "description": "Write a fuller abstract/description (aim for 100+ characters) so reusers understand what the data measures.",
    "keywords": "Add at least 3 keyword/subject terms so the dataset surfaces in topic search.",
    "related_publications": "Link to related publications (DOIs preferred). Increases discoverability and citation.",
    "date_of_collection": "Record the date(s) data collection took place. Distinct from the publication date, this tells reusers how current the data is.",
    "geographic_coverage": "Document the geographic coverage (country/region/unit) the data describes.",
    "unit_of_analysis": "Add the unit of analysis (e.g. 'Individual respondents'). This is a core DDI field required for informed reuse.",
    "universe": "Describe the universe/population studied — who was eligible to be observed, surveyed, or sampled.",
    "time_period_covered": "Note the time period the data covers, which may differ from the collection date.",
    "data_collection_method": "Document the data collection method (survey, interview, administrative records, etc.).",
    "sampling_procedure": "Document the sampling procedure. Without this, users cannot assess representativeness.",
    "license": "Add a license (e.g. CC-BY) so reusers know their rights.",
    "file_format_documented": "Note the original file format(s) contributed (e.g. SPSS, Stata), not just the archival .tab conversion.",
    "variable_metadata": "Add variable-level DDI documentation (labels, value labels, question text) — the richest reuse signal in a dataset.",
}

_PRIORITY_ORDER = {"high": 0, "medium": 1, "low": 2}


def _priority_for_weight(weight: int) -> str:
    if weight >= 7:
        return "high"
    if weight >= 5:
        return "medium"
    return "low"


def _stringify(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return value
    if isinstance(value, (int, float, bool)):
        return str(value)
    if isinstance(value, dict):
        return " ".join(_stringify(v) for v in value.values())
    if isinstance(value, list):
        return " ".join(_stringify(v) for v in value)
    return str(value)


def _count_entries(value: Any) -> int:
    if isinstance(value, list):
        return len(value)
    return 0 if value in (None, "", {}) else 1


def recommendation_for(field_key: str) -> str:
    return _RECOMMENDATIONS[field_key]


def sort_recommendations(recommendations: list[dict[str, str]]) -> list[dict[str, str]]:
    return sorted(recommendations, key=lambda r: _PRIORITY_ORDER[r["priority"]])


def assess_dataverse_metadata(metadata: dict[str, Any]) -> dict[str, Any]:
    """Score a Dataverse dataset's exported metadata against a DDI-informed
    completeness rubric. Field presence is judged by top-level key name only,
    so nested parent-collection metadata (schema:isPartOf, @context, ...)
    never gets mistaken for the dataset's own fields.
    """
    keys_lower = {key.lower(): key for key in metadata}
    breakdown: dict[str, dict[str, Any]] = {}
    present: list[str] = []
    missing: list[str] = []
    recommendations: list[dict[str, str]] = []
    earned = 0
    max_total = 0

    for spec in _FIELD_SPECS:
        category = breakdown.setdefault(spec["category"], {"score": 0, "max": 0, "fields": []})
        category["max"] += spec["weight"]
        category["fields"].append(spec["key"])
        max_total += spec["weight"]

        matched_key = next((keys_lower[k] for k in keys_lower if any(sub in k for sub in spec["match"])), None)
        value = metadata.get(matched_key) if matched_key else None
        present_ok = matched_key is not None and value not in (None, "", [], {})
        if present_ok and "min_length" in spec:
            present_ok = len(_stringify(value)) >= spec["min_length"]
        if present_ok and "min_count" in spec:
            present_ok = _count_entries(value) >= spec["min_count"]

        if present_ok:
            present.append(spec["key"])
            category["score"] += spec["weight"]
            earned += spec["weight"]
        else:
            missing.append(spec["key"])
            recommendations.append({
                "priority": _priority_for_weight(spec["weight"]),
                "field": spec["key"],
                "message": recommendation_for(spec["key"]),
            })

    return {
        "breakdown": breakdown,
        "present_fields": present,
        "missing_fields": missing,
        "recommendations": sort_recommendations(recommendations),
        "earned": earned,
        "max_total": max_total,
    }


def grade_for_score(score: int) -> str:
    if score >= 90:
        return "A"
    if score >= 75:
        return "B"
    if score >= 60:
        return "C"
    if score >= 45:
        return "D"
    return "F"
