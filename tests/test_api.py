import json
import logging
from pathlib import Path
from urllib.parse import parse_qs, urlparse

import pytest
import requests
import responses

from pymed.api import BASE_URL, PubMed
from pymed.article import PubMedArticle
from pymed.book import PubMedBookArticle

FIXTURES = Path(__file__).resolve().parent / "fixtures"


def _fixture_text(name: str) -> str:
    return (FIXTURES / name).read_text(encoding="utf-8")


def _fixture_json(name: str) -> dict:
    return json.loads(_fixture_text(name))


def _get_query_param(call, key: str) -> str | None:
    query = urlparse(call.request.url).query
    return parse_qs(query).get(key, [None])[0]


@responses.activate
def test_get_returns_json_by_default():
    responses.add(
        responses.GET,
        f"{BASE_URL}/entrez/eutils/esearch.fcgi",
        json=_fixture_json("esearch_single.json"),
        status=200,
    )

    pubmed = PubMed()
    response = pubmed._get(url="/entrez/eutils/esearch.fcgi", parameters={})

    assert isinstance(response, dict)
    assert response["esearchresult"]["idlist"] == ["123456"]
    assert _get_query_param(responses.calls[0], "retmode") == "json"


@responses.activate
def test_get_returns_text_when_xml_requested():
    responses.add(
        responses.GET,
        f"{BASE_URL}/entrez/eutils/efetch.fcgi",
        body=_fixture_text("efetch_mixed.xml"),
        status=200,
    )

    pubmed = PubMed()
    response = pubmed._get(
        url="/entrez/eutils/efetch.fcgi", parameters={}, output="xml"
    )

    assert isinstance(response, str)
    assert "<PubmedArticleSet>" in response
    assert _get_query_param(responses.calls[0], "retmode") == "xml"


@responses.activate
def test_get_total_results_count_returns_int():
    responses.add(
        responses.GET,
        f"{BASE_URL}/entrez/eutils/esearch.fcgi",
        json=_fixture_json("esearch_single.json"),
        status=200,
    )

    pubmed = PubMed()
    count = pubmed.get_total_results_count("occupational health[Title]")

    assert count == 1


def test_get_total_results_count_returns_zero_when_non_json(monkeypatch):
    pubmed = PubMed()

    def fake_get(*args, **kwargs):
        return "not-json"

    monkeypatch.setattr(pubmed, "_get", fake_get)

    count = pubmed.get_total_results_count("occupational health[Title]")

    assert count == 0


def test_get_total_results_count_deprecated_alias_warns(monkeypatch):
    pubmed = PubMed()

    def fake_get(*args, **kwargs):
        return "not-json"

    monkeypatch.setattr(pubmed, "_get", fake_get)

    with pytest.warns(DeprecationWarning):
        count = pubmed.getTotalResultsCount("occupational health[Title]")

    assert count == 0


@responses.activate
def test_get_article_ids_paginates_and_respects_max_results():
    responses.add(
        responses.GET,
        f"{BASE_URL}/entrez/eutils/esearch.fcgi",
        json=_fixture_json("esearch_paged_first.json"),
        status=200,
    )
    responses.add(
        responses.GET,
        f"{BASE_URL}/entrez/eutils/esearch.fcgi",
        json=_fixture_json("esearch_paged_second.json"),
        status=200,
    )

    pubmed = PubMed()
    ids = pubmed._get_article_ids("occupational health[Title]", max_results=3)

    assert ids == ["111", "222", "333"]
    assert len(responses.calls) == 2
    assert _get_query_param(responses.calls[1], "retstart") == "2"


@responses.activate
def test_get_article_ids_respects_max_results_minus_one():
    responses.add(
        responses.GET,
        f"{BASE_URL}/entrez/eutils/esearch.fcgi",
        json=_fixture_json("esearch_paged_first.json"),
        status=200,
    )
    responses.add(
        responses.GET,
        f"{BASE_URL}/entrez/eutils/esearch.fcgi",
        json=_fixture_json("esearch_paged_second.json"),
        status=200,
    )

    pubmed = PubMed()
    ids = pubmed._get_article_ids("occupational health[Title]", max_results=-1)

    assert ids == ["111", "222", "333"]
    assert len(responses.calls) == 2
    assert _get_query_param(responses.calls[0], "retmax") == "50000"


def test_get_articles_skips_empty_ids(monkeypatch):
    pubmed = PubMed()

    def fail_get(*args, **kwargs):
        raise AssertionError("_get should not be called for empty id lists")

    monkeypatch.setattr(pubmed, "_get", fail_get)

    assert list(pubmed._get_articles([])) == []


def test_get_total_results_count_warns_on_invalid_count(monkeypatch, caplog):
    pubmed = PubMed()

    def fake_get(*args, **kwargs):
        return {"esearchresult": {"count": "bad"}}

    monkeypatch.setattr(pubmed, "_get", fake_get)

    with caplog.at_level(logging.WARNING):
        count = pubmed.get_total_results_count("occupational health[Title]")

    assert count == 0
    assert "Failed to parse total result count" in caplog.text


def test_get_returns_empty_dict_on_bad_json(monkeypatch, caplog):
    pubmed = PubMed()

    class FakeResponse:
        def raise_for_status(self):
            return None

        def json(self):
            raise ValueError("bad json")

    class FakeSession:
        def get(self, *args, **kwargs):
            return FakeResponse()

    monkeypatch.setattr(pubmed, "_get_session", lambda: FakeSession())

    with caplog.at_level(logging.WARNING):
        response = pubmed._get(url="/entrez/eutils/esearch.fcgi", parameters={})

    assert response == {}
    assert "Failed to decode JSON response" in caplog.text


def test_get_retries_on_server_error(monkeypatch):
    pubmed = PubMed(max_retries=1, backoff_factor=0)

    class ErrorResponse:
        status_code = 500

        def raise_for_status(self):
            raise requests.HTTPError("boom", response=self)

    class OkResponse:
        def raise_for_status(self):
            return None

        def json(self):
            return {"ok": True}

    class FakeSession:
        def __init__(self):
            self.calls = 0

        def get(self, *args, **kwargs):
            self.calls += 1
            if self.calls == 1:
                return ErrorResponse()
            return OkResponse()

    fake_session = FakeSession()
    monkeypatch.setattr(pubmed, "_get_session", lambda: fake_session)
    monkeypatch.setattr("pymed.api.time.sleep", lambda *_: None)

    response = pubmed._get(url="/entrez/eutils/esearch.fcgi", parameters={})

    assert response == {"ok": True}
    assert fake_session.calls == 2


def test_get_article_ids_returns_empty_on_non_dict(monkeypatch, caplog):
    pubmed = PubMed()

    def fake_get(*args, **kwargs):
        return "not-json"

    monkeypatch.setattr(pubmed, "_get", fake_get)

    with caplog.at_level(logging.WARNING):
        ids = pubmed._get_article_ids("occupational health[Title]", max_results=1)

    assert ids == []
    assert "Unexpected response type for esearch" in caplog.text


def test_get_article_ids_warns_on_bad_counts(monkeypatch, caplog):
    pubmed = PubMed()

    def fake_get(*args, **kwargs):
        return {"esearchresult": {"count": "bad", "retmax": "bad", "idlist": ["1"]}}

    monkeypatch.setattr(pubmed, "_get", fake_get)

    with caplog.at_level(logging.WARNING):
        ids = pubmed._get_article_ids("occupational health[Title]", max_results=1)

    assert ids == ["1"]
    assert "Failed to parse total result count" in caplog.text
    assert "Failed to parse retrieved count" in caplog.text


def test_get_article_ids_stops_on_non_dict_page(monkeypatch, caplog):
    pubmed = PubMed()
    responses_list = [
        {"esearchresult": {"count": "3", "retmax": "1", "idlist": ["1"]}},
        "not-json",
    ]

    def fake_get(*args, **kwargs):
        return responses_list.pop(0)

    monkeypatch.setattr(pubmed, "_get", fake_get)

    with caplog.at_level(logging.WARNING):
        ids = pubmed._get_article_ids("occupational health[Title]", max_results=3)

    assert ids == ["1"]
    assert "Unexpected response type for esearch" in caplog.text


def test_get_article_ids_stops_on_bad_page_count(monkeypatch, caplog):
    pubmed = PubMed()
    responses_list = [
        {"esearchresult": {"count": "3", "retmax": "1", "idlist": ["1"]}},
        {"esearchresult": {"count": "3", "retmax": "bad", "idlist": ["2"]}},
    ]

    def fake_get(*args, **kwargs):
        return responses_list.pop(0)

    monkeypatch.setattr(pubmed, "_get", fake_get)

    with caplog.at_level(logging.WARNING):
        ids = pubmed._get_article_ids("occupational health[Title]", max_results=3)

    assert ids == ["1", "2"]
    assert "Failed to parse retrieved count" in caplog.text


def test_get_article_ids_stops_on_zero_page_count(monkeypatch, caplog):
    pubmed = PubMed()
    responses_list = [
        {"esearchresult": {"count": "3", "retmax": "1", "idlist": ["1"]}},
        {"esearchresult": {"count": "3", "retmax": "0", "idlist": ["2"]}},
    ]

    def fake_get(*args, **kwargs):
        return responses_list.pop(0)

    monkeypatch.setattr(pubmed, "_get", fake_get)

    with caplog.at_level(logging.WARNING):
        ids = pubmed._get_article_ids("occupational health[Title]", max_results=3)

    assert ids == ["1", "2"]
    assert "Retrieved count was zero; stopping pagination" in caplog.text


@responses.activate
def test_get_waits_for_rate_limit_before_request(monkeypatch):
    responses.add(
        responses.GET,
        f"{BASE_URL}/entrez/eutils/esearch.fcgi",
        json=_fixture_json("esearch_single.json"),
        status=200,
    )

    pubmed = PubMed()
    calls = []

    def fake_exceeded(self):
        calls.append("tick")
        return len(calls) == 1

    monkeypatch.setattr(PubMed, "_exceeded_rate_limit", fake_exceeded)

    response = pubmed._get(url="/entrez/eutils/esearch.fcgi", parameters={})

    assert isinstance(response, dict)
    assert response["esearchresult"]["idlist"] == ["123456"]
    assert len(calls) >= 2


@responses.activate
def test_query_yields_article_and_book_types():
    responses.add(
        responses.GET,
        f"{BASE_URL}/entrez/eutils/esearch.fcgi",
        json=_fixture_json("esearch_single.json"),
        status=200,
    )
    responses.add(
        responses.GET,
        f"{BASE_URL}/entrez/eutils/efetch.fcgi",
        body=_fixture_text("efetch_mixed.xml"),
        status=200,
    )

    pubmed = PubMed()
    results = list(pubmed.query("occupational health[Title]", max_results=1))

    assert len(results) == 2
    assert any(isinstance(item, PubMedArticle) for item in results)
    assert any(isinstance(item, PubMedBookArticle) for item in results)


def test_query_rejects_empty_query():
    pubmed = PubMed()

    try:
        list(pubmed.query(""))
    except ValueError as exc:
        assert str(exc) == "The query string cannot be empty."
    else:
        raise AssertionError("Expected ValueError for empty query")
