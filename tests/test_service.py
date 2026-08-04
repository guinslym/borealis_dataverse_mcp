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
