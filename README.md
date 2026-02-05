> Status: This project is actively being modernized; see `MODERNIZATION_PLAN.md` for the roadmap.

# PyMed - PubMed Access through Python
PyMed is a Python library that provides access to PubMed through the PubMed API.

## Why this library?
The PubMed API is not very well documented and querying it in a performant way is too complicated and time consuming for researchers. This wrapper provides access to the API in a consistent, readable and performant way.

## Requirements
- Python 3.10+

## Installation
```bash
pip install pymed
```

If you use uv:
```bash
uv add pymed
```

## Features
This library takes care of the following for you:

- Querying the PubMed database (with the standard PubMed query language)
- Batching of requests for better performance
- Parsing and cleaning of the retrieved articles

## Quickstart
In essence you only need to import the `PubMed` class, instantiate it, and use it to query:

```python
from pymed import PubMed
pubmed = PubMed(tool="MyTool", email="my@email.address")
results = pubmed.query("Some query", max_results=10)
for article in results:
    print(article.pubmed_id, article.title)
```

## Configuration
- `tool` and `email` are strongly recommended by NCBI for identification.
- `timeout` (seconds) controls request timeouts; default is 30.
- `max_retries` and `backoff_factor` control retries for 5xx errors.
- `max_results` limits results; set `-1` to request all available IDs.

```python
from pymed import PubMed

pubmed = PubMed(tool="MyTool", email="my@email.address", timeout=20, max_retries=2)
results = pubmed.query("cancer[Title]", max_results=-1)
```

## Examples
For full working examples see `examples/`.

## Development (uv)
Common project commands using uv:

Type checking is done with `ty`.

```bash
uv sync --group dev
uv run pytest -v --cov=pymed --cov-report=term-missing
ruff check .
ty check
uv build
```

## Notes on the API
The original documentation of the PubMed API can be found here: [PubMed Central](https://www.ncbi.nlm.nih.gov/pmc/tools/developers/). PubMed Central kindly requests you to:

> - Do not make concurrent requests, even at off-peak times; and
> - Include two parameters that help to identify your service or application to our servers
>   * _tool_ should be the name of the application, as a string value with no internal spaces, and
>   * _email_ should be the e-mail address of the maintainer of the tool, and should be a valid e-mail address.

## Notice of Non-Affiliation and Disclaimer 
The author of this library is not affiliated, associated, authorized, endorsed by, or in any way officially connected with PubMed, or any of its subsidiaries or its affiliates. The official PubMed website can be found at https://www.ncbi.nlm.nih.gov/pubmed/.
