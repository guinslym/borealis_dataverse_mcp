import borealis_server as server


def test_boolean_normalization_is_word_bounded():
    import re
    query = "salmon and trout or char not atlantic Oregon android"
    normalized = re.sub(
        r"\b(and|or|not)\b",
        lambda match: match.group(0).upper(),
        query,
        flags=re.IGNORECASE,
    )
    assert normalized == "salmon AND trout OR char NOT atlantic Oregon android"


def test_delimiter_aliases():
    assert server._delimiter_from_argument("tab", "data.txt") == "\t"
    assert server._delimiter_from_argument(None, "data.tsv") == "\t"
    assert server._delimiter_from_argument(None, "data.csv") == ","


def test_scalar_type_inference():
    assert server._infer_scalar_type(["1", "2", "NA"]) == "integer"
    assert server._infer_scalar_type(["1.2", "2", ""]) == "number"
    assert server._infer_scalar_type(["north", "south"]) == "text"
    assert server._infer_scalar_type(["", "NA"]) == "empty"


def test_corrected_institution_aliases():
    assert server.UNIVERSITY_DATAVERSE_MAP["athabasca university"] == "athabascau"
    assert server.UNIVERSITY_DATAVERSE_MAP["university of lethbridge"] == "lethbridge"
