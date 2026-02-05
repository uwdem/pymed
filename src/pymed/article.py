import datetime
import json
import logging
import warnings
from dataclasses import asdict, dataclass, field
from xml.etree.ElementTree import Element

from .helpers import getContent

logger = logging.getLogger(__name__)


@dataclass(slots=True)
class PubMedArticle:
    """Data class that contains a PubMed article."""

    pubmed_id: str
    title: str
    abstract: str | None = None
    authors: list[dict[str, str | None]] = field(default_factory=list)
    keywords: list[str | None] = field(default_factory=list)
    journal: str | None = None
    publication_date: datetime.date | None = None
    methods: str | None = None
    conclusions: str | None = None
    results: str | None = None
    copyrights: str | None = None
    doi: str | None = None
    xml: Element | None = None

    def __init__(
        self,
        xml_element: Element | None = None,
        *args: object,
        **kwargs: object,
    ) -> None:
        """Initialization of the object from XML or from parameters."""

        # If an XML element is provided, use it for initialization
        if xml_element is not None:
            self._initialize_from_xml(xml_element=xml_element)

        # If no XML element was provided, try to parse the input parameters
        else:
            for field in self.__slots__:
                self.__setattr__(field, kwargs.get(field))

    def to_dict(self) -> dict[str, object]:
        """Return a dict representation of the article."""
        data = asdict(self)
        data.pop("xml", None)
        return data

    def _extract_pubmed_id(self, xml_element: Element) -> str:
        path = ".//ArticleId[@IdType='pubmed']"
        return getContent(element=xml_element, path=path, default="") or ""

    def _extract_title(self, xml_element: Element) -> str:
        path = ".//ArticleTitle"
        return getContent(element=xml_element, path=path, default="") or ""

    def _extract_keywords(self, xml_element: Element) -> list[str | None]:
        path = ".//Keyword"
        return [
            keyword.text for keyword in xml_element.findall(path) if keyword is not None
        ]

    def _extract_journal(self, xml_element: Element) -> str | None:
        path = ".//Journal/Title"
        return getContent(element=xml_element, path=path)

    def _extract_abstract(self, xml_element: Element) -> str | None:
        path = ".//AbstractText"
        return getContent(element=xml_element, path=path)

    def _extract_conclusions(self, xml_element: Element) -> str | None:
        path = ".//AbstractText[@Label='CONCLUSION']"
        return getContent(element=xml_element, path=path)

    def _extract_methods(self, xml_element: Element) -> str | None:
        path = ".//AbstractText[@Label='METHOD']"
        return getContent(element=xml_element, path=path)

    def _extractResults(self, xml_element: Element) -> str | None:
        self._warn_deprecated("_extractResults", "_extract_results")
        return self._extract_results(xml_element)

    def _extractCopyrights(self, xml_element: Element) -> str | None:
        self._warn_deprecated("_extractCopyrights", "_extract_copyrights")
        return self._extract_copyrights(xml_element)

    def _extractDoi(self, xml_element: Element) -> str | None:
        self._warn_deprecated("_extractDoi", "_extract_doi")
        return self._extract_doi(xml_element)

    def _extract_publication_date(self, xml_element: Element) -> datetime.date | None:
        """Get the publication date."""
        try:
            # Get the publication elements
            publication_date = xml_element.find(".//PubMedPubDate[@PubStatus='pubmed']")
            if publication_date is None:
                return None
            publication_year = int(getContent(publication_date, ".//Year", "") or "")
            publication_month = int(
                getContent(publication_date, ".//Month", "1") or "1"
            )
            publication_day = int(getContent(publication_date, ".//Day", "1") or "1")

            # Construct a datetime object from the info
            return datetime.date(
                year=publication_year, month=publication_month, day=publication_day
            )

        # Unable to parse the datetime
        except (TypeError, ValueError):
            logger.warning("Failed to parse publication date", exc_info=True)
            return None

    def _extract_authors(self, xml_element: Element) -> list[dict[str, str | None]]:
        return [
            {
                "lastname": getContent(author, ".//LastName", None),
                "firstname": getContent(author, ".//ForeName", None),
                "initials": getContent(author, ".//Initials", None),
                "affiliation": getContent(
                    author, ".//AffiliationInfo/Affiliation", None
                ),
            }
            for author in xml_element.findall(".//Author")
        ]

    def _extract_results(self, xml_element: Element) -> str | None:
        path = ".//AbstractText[@Label='RESULTS']"
        return getContent(element=xml_element, path=path)

    def _extract_copyrights(self, xml_element: Element) -> str | None:
        path = ".//CopyrightInformation"
        return getContent(element=xml_element, path=path)

    def _extract_doi(self, xml_element: Element) -> str | None:
        path = ".//ArticleId[@IdType='doi']"
        return getContent(element=xml_element, path=path)

    def _initialize_from_xml(self, xml_element: Element) -> None:
        """Helper method that parses an XML element into an article object."""

        # Parse the different fields of the article
        self.pubmed_id = self._extract_pubmed_id(xml_element)
        self.title = self._extract_title(xml_element)
        self.keywords = self._extract_keywords(xml_element)
        self.journal = self._extract_journal(xml_element)
        self.abstract = self._extract_abstract(xml_element)
        self.conclusions = self._extract_conclusions(xml_element)
        self.methods = self._extract_methods(xml_element)
        self.results = self._extract_results(xml_element)
        self.copyrights = self._extract_copyrights(xml_element)
        self.doi = self._extract_doi(xml_element)
        self.publication_date = self._extract_publication_date(xml_element)
        self.authors = self._extract_authors(xml_element)
        self.xml = xml_element

    def _initializeFromXML(self, xml_element: Element) -> None:
        self._warn_deprecated("_initializeFromXML", "_initialize_from_xml")
        return self._initialize_from_xml(xml_element)

    def _extractPubMedId(self, xml_element: Element) -> str:
        self._warn_deprecated("_extractPubMedId", "_extract_pubmed_id")
        return self._extract_pubmed_id(xml_element)

    def _extractTitle(self, xml_element: Element) -> str:
        self._warn_deprecated("_extractTitle", "_extract_title")
        return self._extract_title(xml_element)

    def _extractKeywords(self, xml_element: Element) -> list[str | None]:
        self._warn_deprecated("_extractKeywords", "_extract_keywords")
        return self._extract_keywords(xml_element)

    def _extractJournal(self, xml_element: Element) -> str | None:
        self._warn_deprecated("_extractJournal", "_extract_journal")
        return self._extract_journal(xml_element)

    def _extractAbstract(self, xml_element: Element) -> str | None:
        self._warn_deprecated("_extractAbstract", "_extract_abstract")
        return self._extract_abstract(xml_element)

    def _extractConclusions(self, xml_element: Element) -> str | None:
        self._warn_deprecated("_extractConclusions", "_extract_conclusions")
        return self._extract_conclusions(xml_element)

    def _extractMethods(self, xml_element: Element) -> str | None:
        self._warn_deprecated("_extractMethods", "_extract_methods")
        return self._extract_methods(xml_element)

    def _extractPublicationDate(self, xml_element: Element) -> datetime.date | None:
        self._warn_deprecated("_extractPublicationDate", "_extract_publication_date")
        return self._extract_publication_date(xml_element)

    def _extractAuthors(self, xml_element: Element) -> list[dict[str, str | None]]:
        self._warn_deprecated("_extractAuthors", "_extract_authors")
        return self._extract_authors(xml_element)

    @staticmethod
    def _warn_deprecated(old_name: str, new_name: str) -> None:
        warnings.warn(
            f"{old_name} is deprecated; use {new_name} instead.",
            DeprecationWarning,
            stacklevel=2,
        )

    def toDict(self) -> dict[str, object]:
        """Return a dict representation of the article (legacy alias)."""

        return {key: self.__getattribute__(key) for key in self.__slots__}

    def toJSON(self) -> str:
        """Return a JSON string representation of the article."""

        return json.dumps(
            {
                key: (
                    value
                    if not isinstance(value, (datetime.date, Element))
                    else str(value)
                )
                for key, value in self.toDict().items()
            },
            sort_keys=True,
            indent=4,
        )
