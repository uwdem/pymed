import datetime
import itertools
import xml.etree.ElementTree as xml
from collections.abc import Generator
from dataclasses import dataclass, field
from typing import Any

import requests

from .article import PubMedArticle
from .book import PubMedBookArticle
from .helpers import batches

# Base url for all queries
BASE_URL = "https://eutils.ncbi.nlm.nih.gov"


@dataclass
class PubMed:
    """
    Wrapper for the PubMed API.

    This class provides a simple interface to query PubMed using the
    Entrez Programming Utilities (E-utilities). It allows users to search
    for articles, retrieve article details, and handle rate limiting.

    Attributes:
        __init__(tool: str, email: str):
            Initializes the PubMed class with the tool name and email.
            The tool name and email are requested by PMC (PubMed Central)
            but not strictly required.
        tool (str): Name of the tool executing the query, requested by PMC.
        email (str): Email of the user of the tool, requested by PMC.
        parameters (dict): Default parameters for queries, including 'db'
        set to 'pubmed'.
        _rate_limit (int): Maximum number of requests allowed per second.
        _requests_made (list): List to keep track of request timestamps
            for rate limiting.

    Methods:
        query(query: str, max_results: int = 100):
            Executes a query against PubMed and retrieves articles.
        get_total_results_count(query: str) -> int:
            Returns the total number of results for a given query.
        _get(url: str, parameters: dict, output: str = "json") -> dict | str:
            Makes a request to PubMed and returns the response.
        _get_articles(article_ids: list) -> list:
            Retrieves articles based on a list of article IDs.
        _get_article_ids(query: str, max_results: int) -> list:
            Retrieves article IDs for a given query, respecting the
            maximum results limit.
        _exceeded_rate_limit() -> bool:
            Checks if the rate limit has been exceeded based on the
            number of requests made in the last second.

    Note:
        - The `tool` and `email` parameters are not strictly required
          but are kindly requested by PMC (PubMed Central).
        - The class handles rate limiting by tracking the timestamps of
          requests made.
        - The `query` method automatically retrieves article IDs and
          their details in batches.
        - The `get_total_results_count` method allows users to check how many
          results match a specific query without retrieving
          the articles themselves.
        - The class supports both JSON and XML responses, with JSON
          as the default format.
        - The `PubMedArticle` and `PubMedBookArticle` classes are used to
        represent the articles retrieved from PubMed.

    """

    tool: str = "my_tool"
    email: str = "my_email@example.com"
    # Keep track of the rate limit
    _rate_limit: int = 3
    _requests_made: list[float] = field(default_factory=list)
    parameters: dict[str, Any] = field(
        default_factory=lambda: {
            "tool": "my_tool",
            "email": "my_email@example.com",
            "db": "pubmed",
        }
    )

    def __post_init__(self):
        self.parameters["tool"] = self.tool
        self.parameters["email"] = self.email

    def query(self, query: str, max_results: int = 100):
        """
        Executes a query against PubMed and retrieves articles.

        Args:
            query (str): The query string.
            max_results (int): Maximum number of results to retrieve.

        Returns:
            Iterator of articles.
        """
        if query == "":
            raise ValueError("The query string cannot be empty.")

        # Retrieve the article IDs for the query
        article_ids = self._get_article_ids(query=query, max_results=max_results)

        # Get the articles themselves
        articles = [
            self._get_articles(article_ids=batch) for batch in batches(article_ids, 250)
        ]

        # Chain the batches back together and return the list
        return itertools.chain.from_iterable(articles)

    def get_total_results_count(self, query: str) -> int:
        """
        Return the total number of results that match the query.

        Parameters
        ----------
            - query String, the query to send to PubMed

        Returns
        -------
            - total_results_count   Int, total number of results for the query in PubMed

        """
        # Get the default parameters
        parameters = self.parameters.copy()

        # Add specific query parameters
        parameters["term"] = query
        parameters["retmax"] = 1

        # Make the request (request a single article ID for this search)
        response = self._get(url="/entrez/eutils/esearch.fcgi", parameters=parameters)

        # Get from the returned meta data the total number
        # of available results for the query
        if isinstance(response, dict):
            return int(response.get("esearchresult", {}).get("count"))
        else:
            return 0

    def _exceeded_rate_limit(self) -> bool:
        """
        Helper method to check if we've exceeded the rate limit.

        Returns:
            - exceeded      Bool, Whether or not the rate limit is exceeded.

        """
        # Remove requests from the list that are longer than 1 second ago
        self._requests_made = [
            requestTime
            for requestTime in self._requests_made
            if requestTime > datetime.datetime.now() - datetime.timedelta(seconds=1)
        ]

        # Return whether we've made more requests in the last second,
        # than the rate limit
        return len(self._requests_made) > self._rate_limit

    def _get(
        self, url: str, parameters: dict[str, Any], output: str = "json"
    ) -> dict[str, Any] | str:
        """
        Generic helper method that makes a request to PubMed.

        Parameters
        ----------
            - url           Str, last part of the URL that is requested (will
                            be combined with the base url)
            - parameters    Dict, parameters to use for the request
            - output        Str, type of output that is requested (defaults to
                            JSON but can be used to retrieve XML)

        Returns
        -------
            - response      Dict / str, if the response is valid JSON it will
                            be parsed before returning, otherwise a string is
                            returned

        """
        # Make sure the rate limit is not exceeded
        while self._exceeded_rate_limit():
            pass

        # Set the response mode
        parameters["retmode"] = output

        # Make the request to PubMed
        response: requests.Response = requests.get(
            f"{BASE_URL}{url}", params=parameters
        )

        # Check for any errors
        response.raise_for_status()

        # Add this request to the list of requests made
        self._requests_made.append(datetime.datetime.now())

        # Return the response
        if output == "json":
            return response.json()
        return response.text

    def _get_articles(self, article_ids: list) -> Generator:
        """
        Helper method that batches a list of article IDs and retrieves the content.

        Parameters
        ----------
            - article_ids   List, article IDs.

        Returns
        -------
            - articles      List, article objects.

        """
        # Get the default parameters
        parameters = self.parameters.copy()
        parameters["id"] = article_ids

        # Make the request
        response = self._get(
            url="/entrez/eutils/efetch.fcgi", parameters=parameters, output="xml"
        )

        # Parse as XML
        root = xml.fromstring(response)

        # Loop over the articles and construct article objects
        for article in root.iter("PubmedArticle"):
            yield PubMedArticle(xml_element=article)
        for book in root.iter("PubmedBookArticle"):
            yield PubMedBookArticle(xml_element=book)

    def _get_article_ids(self, query: str, max_results: int) -> list:
        """
        Helper method to retrieve the article IDs for a query.

        Parameters
        ----------
            - query         Str, query to be executed against the PubMed database.
            - max_results   Int, the maximum number of results to retrieve.

        Returns
        -------
            - article_ids   List, article IDs as a list.

        """
        # Create a placeholder for the retrieved IDs
        article_ids = []

        # Get the default parameters
        parameters = self.parameters.copy()

        # Add specific query parameters
        parameters["term"] = query
        parameters["retmax"] = 50000

        # Calculate a cut off point based on the max_results parameter
        if max_results < parameters["retmax"]:
            parameters["retmax"] = max_results

        # Make the first request to PubMed
        response = self._get(url="/entrez/eutils/esearch.fcgi", parameters=parameters)

        # Add the retrieved IDs to the list
        if isinstance(response, dict):
            article_ids += response.get("esearchresult", {}).get("idlist", [])
            # Get information from the response
            total_result_count = int(response.get("esearchresult", {}).get("count"))
            retrieved_count = int(response.get("esearchresult", {}).get("retmax"))

        # If no max is provided (-1) we'll try to retrieve everything
        if max_results == -1:
            max_results = total_result_count

        # If not all articles are retrieved,
        # continue to make requests until we have everything
        while retrieved_count < total_result_count and retrieved_count < max_results:
            # Calculate a cut off point based on the max_results parameter
            if (max_results - retrieved_count) < parameters["retmax"]:
                parameters["retmax"] = max_results - retrieved_count

            # Start the collection from the number of already retrieved articles
            parameters["retstart"] = retrieved_count

            # Make a new request
            response = self._get(
                url="/entrez/eutils/esearch.fcgi", parameters=parameters
            )

            if isinstance(response, dict):
                # Add the retrieved IDs to the list
                article_ids += response.get("esearchresult", {}).get("idlist", [])
                # Get information from the response
                retrieved_count += int(response.get("esearchresult", {}).get("retmax"))

        # Return the response
        return article_ids
