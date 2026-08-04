from borealis_toolkit.institutions import normalize_institution
from borealis_toolkit.utils import normalize_boolean_query, normalize_identifier


def test_boolean_query_normalization():
    assert normalize_boolean_query("salmon and trout not atlantic") == "salmon AND trout NOT atlantic"


def test_identifier_normalization():
    assert normalize_identifier("https://doi.org/10.5683/SP3/ABC") == ("doi:10.5683/SP3/ABC", True)
    assert normalize_identifier("123") == ("123", False)


def test_institution_alias():
    assert normalize_institution("U of T") == "toronto"
    assert normalize_institution("UBC") == "ubc"
