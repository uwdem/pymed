import datetime
import json
from dataclasses import asdict, dataclass, field
from xml.etree.ElementTree import Element

from .helpers import getContent


@dataclass(slots=True)
class PubMedArticle:
    """Data class that contains a PubMed article."""

    pubmed_id: str
    title: str
    abstract: str | None = None
    authors: list[dict] = field(default_factory=list)
    keywords: list[str] = field(default_factory=list)
    publication_date: datetime.date | None = None
    methods: str | None = None
    conclusions: str | None = None
    results: str | None = None
    copyrights: str | None = None
    doi: str | None = None

    def __init__(
        self,
        xml_element: Element | None = None,
        *args: list,
        **kwargs: dict,
    ) -> None:
        """Initialization of the object from XML or from parameters."""

        # If an XML element is provided, use it for initialization
        if xml_element is not None:
            self._initialize_from_XML(xml_element=xml_element)

        # If no XML element was provided, try to parse the input parameters
        else:
            for field in self.__slots__:
                self.__setattr__(field, kwargs.get(field))

    def to_dict(self) -> dict:
        """to_dict method using dataclasses.asdict."""
        return asdict(self)

    def _extract_pubmed_id(self, xml_element: Element) -> str:
        path = ".//ArticleId[@IdType='pubmed']"
        return getContent(element=xml_element, path=path)

    def _extract_title(self, xml_element: Element) -> str:
        path = ".//ArticleTitle"
        return getContent(element=xml_element, path=path)

    def _extract_keywords(self, xml_element: Element) -> list[str | None]:
        path = ".//Keyword"
        return [
            keyword.text for keyword in xml_element.findall(path) if keyword is not None
        ]

    def _extract_journal(self, xml_element: Element) -> str:
        path = ".//Journal/Title"
        return getContent(element=xml_element, path=path)

    def _extract_abstract(self, xml_element: Element) -> str:
        path = ".//AbstractText"
        return getContent(element=xml_element, path=path)

    def _extract_conclusions(self, xml_element: Element) -> str:
        path = ".//AbstractText[@Label='CONCLUSION']"
        return getContent(element=xml_element, path=path)

    def _extract_methods(self, xml_element: Element) -> str:
        path = ".//AbstractText[@Label='METHOD']"
        return getContent(element=xml_element, path=path)

    def _extractResults(self, xml_element: Element) -> str:
        path = ".//AbstractText[@Label='RESULTS']"
        return getContent(element=xml_element, path=path)

    def _extractCopyrights(self, xml_element: Element) -> str:
        path = ".//CopyrightInformation"
        return getContent(element=xml_element, path=path)

    def _extractDoi(self, xml_element: Element) -> str:
        path = ".//ArticleId[@IdType='doi']"
        return getContent(element=xml_element, path=path)

    def _extract_publication_date(self, xml_element: Element) -> datetime.datetime:
        """Get the publication date."""
        try:
            # Get the publication elements
            publication_date = xml_element.find(".//PubMedPubDate[@PubStatus='pubmed']")
            publication_year = int(getContent(publication_date, ".//Year", None))
            publication_month = int(getContent(publication_date, ".//Month", "1"))
            publication_day = int(getContent(publication_date, ".//Day", "1"))

            # Construct a datetime object from the info
            return datetime.date(
                year=publication_year, month=publication_month, day=publication_day
            )

        # Unable to parse the datetime
        except Exception as e:
            print(e)
            return None

    def _extractAuthors(self, xml_element: Element) -> list:
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

    def _initializeFromXML(self, xml_element: Element) -> None:
        """Helper method that parses an XML element into an article object."""

        # Parse the different fields of the article
        self.pubmed_id = self._extractPubMedId(xml_element)
        self.title = self._extractTitle(xml_element)
        self.keywords = self._extractKeywords(xml_element)
        self.journal = self._extractJournal(xml_element)
        self.abstract = self._extractAbstract(xml_element)
        self.conclusions = self._extractConclusions(xml_element)
        self.methods = self._extractMethods(xml_element)
        self.results = self._extractResults(xml_element)
        self.copyrights = self._extractCopyrights(xml_element)
        self.doi = self._extractDoi(xml_element)
        self.publication_date = self._extractPublicationDate(xml_element)
        self.authors = self._extractAuthors(xml_element)
        self.xml = xml_element

    def toDict(self) -> dict:
        """Helper method to convert the parsed information to a Python dict."""

        return {key: self.__getattribute__(key) for key in self.__slots__}

    def toJSON(self) -> str:
        """Helper method for debugging, dumps the object as JSON string."""

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
