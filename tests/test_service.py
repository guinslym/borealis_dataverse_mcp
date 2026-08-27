import pytest

from borealis_toolkit.errors import BorealisUnsupportedFileError
from borealis_toolkit.service import BorealisService


class FakeClient:
    async def request_json(self, method, endpoint, *, params=None, accept=None):
        assert endpoint == "search"
        return {
            "status": "OK",
            "data": {
                "total_count": 1,
                "items": [{
                    "type": "dataset",
                    "name": "Example dataset",
                    "global_id": "doi:10.5683/SP3/EXAMPLE",
                    "authors": ["A. Researcher"],
                    "published_at": "2026-01-01",
                    "description": "Example",
                    "url": "https://example.test/dataset.xhtml",
                }],
            },
        }, False


async def test_search_returns_structured_results():
    service = BorealisService(client=FakeClient())
    result = await service.search_datasets("bees and pollination", institution="UBC")
    assert result.data["query"] == "bees AND pollination"
    assert result.data["scope"]["subtree"] == "ubc"
    assert result.data["results"][0]["doi_url"] == "https://doi.org/10.5683/SP3/EXAMPLE"


_SAMPLE_DDI_XML = """<?xml version='1.0' encoding='UTF-8'?>
<codeBook xmlns="ddi:codebook:2_5">
  <dataDscr>
    <var ID="v1" name="AGE" intrvl="contin">
      <labl level="variable">Age of respondent</labl>
      <qstn><qstnLit>How old are you?</qstnLit></qstn>
      <universe>All respondents</universe>
      <varFormat type="numeric" formatname="F2.0"/>
      <invalrng><item VALUE="99"/><item VALUE="98"/></invalrng>
      <sumStat type="min">18</sumStat>
      <sumStat type="max">95</sumStat>
      <sumStat type="mean">42.3</sumStat>
      <sumStat type="vald">1204</sumStat>
    </var>
    <var ID="v2" name="REGION">
      <labl level="variable">Geographic region</labl>
      <varFormat type="character"/>
      <catgry><catValu>1</catValu><labl level="category">Ontario</labl><catStat type="freq">450</catStat></catgry>
      <catgry><catValu>2</catValu><labl level="category">Quebec</labl><catStat type="freq">380</catStat></catgry>
    </var>
  </dataDscr>
</codeBook>
"""


class FakeDdiClient:
    def __init__(self, xml_text=_SAMPLE_DDI_XML):
        self.xml_text = xml_text

    async def request_text(self, method, endpoint, *, params=None, accept=None):
        assert endpoint == "access/datafile/12345/metadata/ddi"
        return self.xml_text, False


async def test_get_variable_metadata_parses_ddi_xml():
    service = BorealisService(client=FakeDdiClient())
    result = await service.get_variable_metadata("12345")
    assert result.data["file_id"] == "12345"
    assert result.data["variable_count"] == 2

    age = result.data["variables"][0]
    assert age["name"] == "AGE"
    assert age["type"] == "numeric"
    assert age["question_text"] == "How old are you?"
    assert age["universe"] == "All respondents"
    assert set(age["missing_values"]) == {"99", "98"}
    assert age["summary_stats"]["mean"] == 42.3
    assert age["summary_stats"]["valid_cases"] == 1204

    region = result.data["variables"][1]
    assert region["value_labels"] == {"1": "Ontario", "2": "Quebec"}
    assert region["summary_stats"]["freq"] == {"1": 450, "2": 380}


async def test_get_variable_metadata_respects_max_variables():
    service = BorealisService(client=FakeDdiClient())
    result = await service.get_variable_metadata("12345", max_variables=1)
    assert result.data["variable_count"] == 2
    assert len(result.data["variables"]) == 1
    assert result.warnings


class FakeUnsupportedFileClient:
    async def request_text(self, method, endpoint, *, params=None, accept=None):
        raise BorealisUnsupportedFileError("Borealis rejected the request: not a tabular file")


async def test_get_variable_metadata_reports_non_tabular_files_clearly():
    service = BorealisService(client=FakeUnsupportedFileClient())
    with pytest.raises(BorealisUnsupportedFileError, match="no DDI variable metadata"):
        await service.get_variable_metadata("999")


_SAMPLE_DATASET_METADATA = {
    "status": "OK",
    "data": {
        "title": "Canadian Election Study 2021",
        "author": [{"citation:authorName": "Stephenson, Laura B."}],
        "citation:dsDescription": {
            "citation:dsDescriptionValue": "x" * 150,
        },
        "citation:keyword": [
            {"citation:keywordValue": "Election"},
            {"citation:keywordValue": "Politics"},
            {"citation:keywordValue": "Voting"},
        ],
        "geospatial:geographicCoverage": {"geospatial:country": "Canada"},
        "socialscience:unitOfAnalysis": "Individual",
        "socialscience:universe": "Canadian citizens over 18",
        "socialscience:collectionMode": "Online survey",
        "socialscience:samplingProcedure": "Stratified random sample",
        "schema:license": "http://creativecommons.org/licenses/by-nc/4.0",
        "schema:version": "5.1",
    },
}


class FakeQualityClient:
    def __init__(self, metadata=_SAMPLE_DATASET_METADATA):
        self.metadata = metadata

    async def request_json(self, method, endpoint, *, params=None, accept=None):
        assert endpoint == "datasets/:persistentId/metadata"
        return self.metadata, False


async def test_assess_metadata_quality_scores_present_and_missing_fields():
    service = BorealisService(client=FakeQualityClient())
    result = await service.assess_metadata_quality("doi:10.5683/SP3/MMXTFC")
    data = result.data

    assert data["title"] == "Canadian Election Study 2021"
    assert "title" in data["present_fields"]
    assert "unit_of_analysis" in data["present_fields"]
    assert "date_of_collection" in data["missing_fields"]
    assert "sampling_procedure" in data["present_fields"]
    assert data["variable_metadata_present"] is None
    assert 0 <= data["score"] <= 100
    assert data["grade"] in {"A", "B", "C", "D", "F"}

    # High-priority recommendations must be listed before medium/low ones.
    priority_rank = {"high": 0, "medium": 1, "low": 2}
    priorities = [r["priority"] for r in data["recommendations"]]
    assert priorities == sorted(priorities, key=lambda p: priority_rank[p])


async def test_assess_metadata_quality_handles_sparse_metadata():
    sparse = {"status": "OK", "data": {"title": "Untitled dataset"}}
    service = BorealisService(client=FakeQualityClient(metadata=sparse))
    result = await service.assess_metadata_quality("doi:10.5683/SP3/SPARSE")
    assert result.data["grade"] == "F"
    assert result.data["missing_fields"]
    assert all(r["field"] in result.data["missing_fields"] for r in result.data["recommendations"])
