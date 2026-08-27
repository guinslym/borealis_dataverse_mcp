from __future__ import annotations

from typing import Any
from xml.etree import ElementTree as ET

_STAT_KEY_MAP = {
    "min": "min",
    "max": "max",
    "mean": "mean",
    "medn": "median",
    "stdev": "stddev",
    "mode": "mode",
    "vald": "valid_cases",
    "invd": "invalid_cases",
}


def _local_name(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def _child(elem: ET.Element | None, name: str) -> ET.Element | None:
    if elem is None:
        return None
    for node in elem:
        if _local_name(node.tag) == name:
            return node
    return None


def _children(elem: ET.Element, name: str) -> list[ET.Element]:
    return [node for node in elem if _local_name(node.tag) == name]


def _text(elem: ET.Element | None) -> str | None:
    if elem is None:
        return None
    value = "".join(elem.itertext()).strip()
    return value or None


def _number(text: str) -> Any:
    try:
        as_float = float(text)
    except ValueError:
        return text
    return int(as_float) if as_float.is_integer() else as_float


def parse_ddi_variables(
    xml_text: str,
    *,
    include_summary_stats: bool = True,
    max_variables: int = 50,
) -> tuple[list[dict[str, Any]], int]:
    """Parse a DDI codebook XML document into variable dicts.

    Returns (variables, total_variable_count). Namespaces are stripped before
    matching tag names so this works across the DDI codebook namespace URIs
    different Dataverse installs declare (e.g. 'ddi:codebook:2_5' vs.
    'http://www.icpsr.umich.edu/DDI'), without hard-coding one of them.
    """
    root = ET.fromstring(xml_text)
    data_dscr = next((elem for elem in root.iter() if _local_name(elem.tag) == "dataDscr"), None)
    if data_dscr is None:
        return [], 0

    var_elements = _children(data_dscr, "var")
    total = len(var_elements)
    variables = [_parse_variable(var, include_summary_stats=include_summary_stats) for var in var_elements[:max_variables]]
    return variables, total


def _parse_variable(var: ET.Element, *, include_summary_stats: bool) -> dict[str, Any]:
    var_format = _child(var, "varFormat")
    qstn = _child(var, "qstn")

    missing_values: list[str] = []
    invalrng = _child(var, "invalrng")
    if invalrng is not None:
        for item in _children(invalrng, "item"):
            value = item.get("VALUE") or item.get("value")
            if value is not None:
                missing_values.append(value)

    value_labels: dict[str, str] = {}
    freq: dict[str, int] = {}
    for catgry in _children(var, "catgry"):
        value = _text(_child(catgry, "catValu"))
        label = _text(_child(catgry, "labl"))
        if value is None:
            continue
        if label is not None:
            value_labels[value] = label
        if catgry.get("missing", "").lower() in {"y", "yes", "true"}:
            missing_values.append(value)
        if include_summary_stats:
            for cat_stat in _children(catgry, "catStat"):
                if cat_stat.get("type") != "freq":
                    continue
                text = _text(cat_stat)
                if text is not None:
                    try:
                        freq[value] = int(float(text))
                    except ValueError:
                        pass

    entry: dict[str, Any] = {
        "id": var.get("ID") or var.get("id"),
        "name": var.get("name"),
        "label": _text(_child(var, "labl")),
        "type": (var_format.get("type") if var_format is not None else None),
        "format": (var_format.get("formatname") if var_format is not None else None),
        "question_text": _text(_child(qstn, "qstnLit")) if qstn is not None else None,
        "universe": _text(_child(var, "universe")),
        "missing_values": list(dict.fromkeys(missing_values)),
        "value_labels": value_labels,
    }

    if include_summary_stats:
        stats: dict[str, Any] = {}
        for sum_stat in _children(var, "sumStat"):
            stat_type = sum_stat.get("type")
            text = _text(sum_stat)
            if not stat_type or text is None:
                continue
            stats[_STAT_KEY_MAP.get(stat_type, stat_type)] = _number(text)
        if freq:
            stats["freq"] = freq
        entry["summary_stats"] = stats

    return entry
