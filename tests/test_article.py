import datetime
import json
from pathlib import Path
from xml.etree import ElementTree as xml

import pytest

from pymed.article import PubMedArticle

FIXTURES = Path(__file__).resolve().parent / "fixtures"


def _load_article_xml():
    xml_text = (FIXTURES / "efetch_mixed.xml").read_text(encoding="utf-8")
    root = xml.fromstring(xml_text)
    return next(root.iter("PubmedArticle"))


def test_article_init_from_kwargs_sets_fields():
    article = PubMedArticle(
        pubmed_id="123456",
        title="Test Article Title",
        publication_date=datetime.date(2020, 12, 25),
    )

    data = article.toDict()
    assert data["pubmed_id"] == "123456"
    assert data["title"] == "Test Article Title"

    parsed = json.loads(article.toJSON())
    assert parsed["pubmed_id"] == "123456"
    assert parsed["publication_date"] == "2020-12-25"


def test_article_to_dict_uses_dataclass():
    article = PubMedArticle(
        pubmed_id="999",
        title="Dataclass Title",
        abstract="Testing",
    )

    data = article.to_dict()
    assert data["pubmed_id"] == "999"
    assert data["title"] == "Dataclass Title"
    assert data["abstract"] == "Testing"


def test_article_parses_expected_fields():
    article = PubMedArticle(xml_element=_load_article_xml())

    assert article.pubmed_id == "123456"
    assert article.title == "Test Article Title"
    assert (
        article.abstract
        == "Test abstract body.\nTest methods.\nTest results.\nTest conclusions."
    )
    assert article.keywords == ["alpha", "beta"]
    assert article.doi == "10.1000/test.doi"
    assert article.methods == "Test methods."
    assert article.results == "Test results."
    assert article.conclusions == "Test conclusions."
    assert article.copyrights == "Test copyright"
    assert article.publication_date is not None
    assert article.publication_date.year == 2020
    assert article.publication_date.month == 12
    assert article.publication_date.day == 25
    assert article.authors == [
        {
            "lastname": "Smith",
            "firstname": "Jane",
            "initials": "J",
            "affiliation": "Example University",
        }
    ]


def test_article_publication_date_missing_returns_none():
    xml_text = """
    <PubmedArticle>
      <MedlineCitation>
        <Article>
          <ArticleTitle>No Date</ArticleTitle>
        </Article>
      </MedlineCitation>
    </PubmedArticle>
    """
    element = xml.fromstring(xml_text)

    article = PubMedArticle(pubmed_id="1", title="No Date")
    assert article._extract_publication_date(element) is None


def test_article_publication_date_invalid_returns_none():
    xml_text = """
    <PubmedArticle>
      <MedlineCitation>
        <PubMedPubDate PubStatus="pubmed">
          <Year>BAD</Year>
          <Month>1</Month>
          <Day>1</Day>
        </PubMedPubDate>
      </MedlineCitation>
    </PubmedArticle>
    """
    element = xml.fromstring(xml_text)

    article = PubMedArticle(pubmed_id="1", title="Bad Date")
    assert article._extract_publication_date(element) is None


def test_article_camel_case_wrappers_work():
    element = _load_article_xml()
    article = PubMedArticle(pubmed_id="1", title="stub")

    with pytest.warns(DeprecationWarning):
        article._initializeFromXML(element)

    with pytest.warns(DeprecationWarning):
        assert article._extractPubMedId(element) == "123456"
    with pytest.warns(DeprecationWarning):
        assert article._extractTitle(element) == "Test Article Title"
    with pytest.warns(DeprecationWarning):
        assert article._extractKeywords(element) == ["alpha", "beta"]
    with pytest.warns(DeprecationWarning):
        assert article._extractJournal(element) == "Test Journal"
    with pytest.warns(DeprecationWarning):
        assert article._extractAbstract(element) is not None
    with pytest.warns(DeprecationWarning):
        assert article._extractConclusions(element) == "Test conclusions."
    with pytest.warns(DeprecationWarning):
        assert article._extractMethods(element) == "Test methods."
    with pytest.warns(DeprecationWarning):
        assert article._extractPublicationDate(element) is not None
    with pytest.warns(DeprecationWarning):
        assert article._extractAuthors(element)
    with pytest.warns(DeprecationWarning):
        assert article._extractResults(element) == "Test results."
    with pytest.warns(DeprecationWarning):
        assert article._extractCopyrights(element) == "Test copyright"
    with pytest.warns(DeprecationWarning):
        assert article._extractDoi(element) == "10.1000/test.doi"
