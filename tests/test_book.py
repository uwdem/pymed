from pathlib import Path
from xml.etree import ElementTree as xml

import pytest

from pymed.book import PubMedBookArticle

FIXTURES = Path(__file__).resolve().parent / "fixtures"


def _load_book_xml():
    xml_text = (FIXTURES / "efetch_mixed.xml").read_text(encoding="utf-8")
    root = xml.fromstring(xml_text)
    return next(root.iter("PubmedBookArticle"))


def test_book_parses_expected_fields():
    book = PubMedBookArticle(xml_element=_load_book_xml())

    assert book.pubmed_id == "654321"
    assert book.title == "Test Book Title"
    assert book.abstract == "Book abstract."
    assert book.doi == "10.1000/book.doi"
    assert book.isbn == "9780123456789"
    assert book.language == "eng"
    assert book.publication_date == "2019"
    assert book.publication_type == "Book"
    assert book.publisher == "Test Publisher"
    assert book.publisher_location == "Test City"
    assert book.sections == [{"title": "Section One", "chapter": "1"}]
    assert book.authors == [
        {
            "collective": "Example Group",
            "lastname": "Doe",
            "firstname": "John",
            "initials": "J",
        }
    ]


def test_book_to_dict_and_json_include_expected_keys():
    book = PubMedBookArticle(xml_element=_load_book_xml())

    data = book.toDict()
    assert data["pubmed_id"] == "654321"
    assert data["title"] == "Test Book Title"
    assert data["isbn"] == "9780123456789"

    json_text = book.toJSON()
    assert '"pubmed_id"' in json_text
    assert '"isbn"' in json_text


def test_book_init_without_xml_sets_fields_to_none():
    book = PubMedBookArticle()

    data = book.toDict()
    assert data["pubmed_id"] is None
    assert data["title"] is None


def test_book_camel_case_wrappers_warn():
    book = PubMedBookArticle()
    element = _load_book_xml()

    with pytest.warns(DeprecationWarning):
        book._initializeFromXML(element)
    with pytest.warns(DeprecationWarning):
        assert book._extractPubMedId(element) == "654321"
    with pytest.warns(DeprecationWarning):
        assert book._extractTitle(element) == "Test Book Title"
    with pytest.warns(DeprecationWarning):
        assert book._extractAbstract(element) == "Book abstract."
    with pytest.warns(DeprecationWarning):
        assert book._extractCopyrights(element) == "Book copyright"
    with pytest.warns(DeprecationWarning):
        assert book._extractDoi(element) == "10.1000/book.doi"
    with pytest.warns(DeprecationWarning):
        assert book._extractIsbn(element) == "9780123456789"
    with pytest.warns(DeprecationWarning):
        assert book._extractLanguage(element) == "eng"
    with pytest.warns(DeprecationWarning):
        assert book._extractPublicationDate(element) == "2019"
    with pytest.warns(DeprecationWarning):
        assert book._extractPublicationType(element) == "Book"
    with pytest.warns(DeprecationWarning):
        assert book._extractPublisher(element) == "Test Publisher"
    with pytest.warns(DeprecationWarning):
        assert book._extractPublisherLocation(element) == "Test City"
    with pytest.warns(DeprecationWarning):
        assert book._extractAuthors(element)
    with pytest.warns(DeprecationWarning):
        assert book._extractSections(element)
