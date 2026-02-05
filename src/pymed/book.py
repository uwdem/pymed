import datetime
import json
import warnings
from xml.etree.ElementTree import Element

from .helpers import getContent


class PubMedBookArticle:
    """Data class that contains a PubMed article."""

    __slots__ = (
        "pubmed_id",
        "title",
        "abstract",
        "publication_date",
        "authors",
        "copyrights",
        "doi",
        "isbn",
        "language",
        "publication_type",
        "sections",
        "publisher",
        "publisher_location",
    )

    def __init__(
        self,
        xml_element: Element | None = None,
        *args: object,
        **kwargs: object,
    ) -> None:
        """Initialization of the object from XML or from parameters."""

        # If an XML element is provided, use it for initialization
        if xml_element is not None:
            self._initializeFromXML(xml_element=xml_element)

        # If no XML element was provided, try to parse the input parameters
        else:
            for field in self.__slots__:
                self.__setattr__(field, kwargs.get(field))

    def _extractPubMedId(self, xml_element: Element) -> str | None:
        self._warn_deprecated("_extractPubMedId", "_extract_pubmed_id")
        return self._extract_pubmed_id(xml_element)

    def _extract_pubmed_id(self, xml_element: Element) -> str | None:
        path = ".//ArticleId[@IdType='pubmed']"
        return getContent(element=xml_element, path=path)

    def _extractTitle(self, xml_element: Element) -> str | None:
        self._warn_deprecated("_extractTitle", "_extract_title")
        return self._extract_title(xml_element)

    def _extract_title(self, xml_element: Element) -> str | None:
        path = ".//BookTitle"
        return getContent(element=xml_element, path=path)

    def _extractAbstract(self, xml_element: Element) -> str | None:
        self._warn_deprecated("_extractAbstract", "_extract_abstract")
        return self._extract_abstract(xml_element)

    def _extract_abstract(self, xml_element: Element) -> str | None:
        path = ".//AbstractText"
        return getContent(element=xml_element, path=path)

    def _extractCopyrights(self, xml_element: Element) -> str | None:
        self._warn_deprecated("_extractCopyrights", "_extract_copyrights")
        return self._extract_copyrights(xml_element)

    def _extract_copyrights(self, xml_element: Element) -> str | None:
        path = ".//CopyrightInformation"
        return getContent(element=xml_element, path=path)

    def _extractDoi(self, xml_element: Element) -> str | None:
        self._warn_deprecated("_extractDoi", "_extract_doi")
        return self._extract_doi(xml_element)

    def _extract_doi(self, xml_element: Element) -> str | None:
        path = ".//ArticleId[@IdType='doi']"
        return getContent(element=xml_element, path=path)

    def _extractIsbn(self, xml_element: Element) -> str | None:
        self._warn_deprecated("_extractIsbn", "_extract_isbn")
        return self._extract_isbn(xml_element)

    def _extract_isbn(self, xml_element: Element) -> str | None:
        path = ".//Isbn"
        return getContent(element=xml_element, path=path)

    def _extractLanguage(self, xml_element: Element) -> str | None:
        self._warn_deprecated("_extractLanguage", "_extract_language")
        return self._extract_language(xml_element)

    def _extract_language(self, xml_element: Element) -> str | None:
        path = ".//Language"
        return getContent(element=xml_element, path=path)

    def _extractPublicationType(self, xml_element: Element) -> str | None:
        self._warn_deprecated("_extractPublicationType", "_extract_publication_type")
        return self._extract_publication_type(xml_element)

    def _extract_publication_type(self, xml_element: Element) -> str | None:
        path = ".//PublicationType"
        return getContent(element=xml_element, path=path)

    def _extractPublicationDate(self, xml_element: Element) -> str | None:
        self._warn_deprecated("_extractPublicationDate", "_extract_publication_date")
        return self._extract_publication_date(xml_element)

    def _extract_publication_date(self, xml_element: Element) -> str | None:
        path = ".//PubDate/Year"
        return getContent(element=xml_element, path=path)

    def _extractPublisher(self, xml_element: Element) -> str | None:
        self._warn_deprecated("_extractPublisher", "_extract_publisher")
        return self._extract_publisher(xml_element)

    def _extract_publisher(self, xml_element: Element) -> str | None:
        path = ".//Publisher/PublisherName"
        return getContent(element=xml_element, path=path)

    def _extractPublisherLocation(self, xml_element: Element) -> str | None:
        self._warn_deprecated(
            "_extractPublisherLocation", "_extract_publisher_location"
        )
        return self._extract_publisher_location(xml_element)

    def _extract_publisher_location(self, xml_element: Element) -> str | None:
        path = ".//Publisher/PublisherLocation"
        return getContent(element=xml_element, path=path)

    def _extractAuthors(self, xml_element: Element) -> list[dict[str, str | None]]:
        self._warn_deprecated("_extractAuthors", "_extract_authors")
        return self._extract_authors(xml_element)

    def _extract_authors(self, xml_element: Element) -> list[dict[str, str | None]]:
        return [
            {
                "collective": getContent(author, path=".//CollectiveName"),
                "lastname": getContent(element=author, path=".//LastName"),
                "firstname": getContent(element=author, path=".//ForeName"),
                "initials": getContent(element=author, path=".//Initials"),
            }
            for author in xml_element.findall(".//Author")
        ]

    def _extractSections(self, xml_element: Element) -> list[dict[str, str | None]]:
        self._warn_deprecated("_extractSections", "_extract_sections")
        return self._extract_sections(xml_element)

    def _extract_sections(self, xml_element: Element) -> list[dict[str, str | None]]:
        return [
            {
                "title": getContent(section, path=".//SectionTitle"),
                "chapter": getContent(element=section, path=".//LocationLabel"),
            }
            for section in xml_element.findall(".//Section")
        ]

    def _initializeFromXML(self, xml_element: Element) -> None:
        self._warn_deprecated("_initializeFromXML", "_initialize_from_xml")
        return self._initialize_from_xml(xml_element)

    def _initialize_from_xml(self, xml_element: Element) -> None:
        """Helper method that parses an XML element into an article object."""

        # Parse the different fields of the article
        self.pubmed_id = self._extract_pubmed_id(xml_element)
        self.title = self._extract_title(xml_element)
        self.abstract = self._extract_abstract(xml_element)
        self.copyrights = self._extract_copyrights(xml_element)
        self.doi = self._extract_doi(xml_element)
        self.isbn = self._extract_isbn(xml_element)
        self.language = self._extract_language(xml_element)
        self.publication_date = self._extract_publication_date(xml_element)
        self.authors = self._extract_authors(xml_element)
        self.publication_type = self._extract_publication_type(xml_element)
        self.publisher = self._extract_publisher(xml_element)
        self.publisher_location = self._extract_publisher_location(xml_element)
        self.sections = self._extract_sections(xml_element)

    @staticmethod
    def _warn_deprecated(old_name: str, new_name: str) -> None:
        warnings.warn(
            f"{old_name} is deprecated; use {new_name} instead.",
            DeprecationWarning,
            stacklevel=2,
        )

    def toDict(self) -> dict[str, object | None]:
        """Return a dict representation of the book article."""

        return {
            key: (self.__getattribute__(key) if hasattr(self, key) else None)
            for key in self.__slots__
        }

    def toJSON(self) -> str:
        """Return a JSON string representation of the book article."""

        return json.dumps(
            {
                key: (value if not isinstance(value, datetime.date) else str(value))
                for key, value in self.toDict().items()
            },
            sort_keys=True,
            indent=4,
        )
