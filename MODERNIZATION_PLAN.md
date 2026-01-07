# PyMed Modernization Plan

## Phase 1: Foundation (Critical)

### 1. Configure `pyproject.toml`
- Migrate all metadata from `setup.py` to PEP 621 format
- Define `requires-python = ">=3.9"`
- Configure build backend (hatchling, setuptools, or flit)
- Add dependency groups:
  - `[project.dependencies]` - requests
  - `[project.optional-dependencies.dev]` - pytest, ruff, mypy, pre-commit
  - `[project.optional-dependencies.test]` - pytest, pytest-cov, responses
- Use dynamic versioning from `pymed/__init__.py` or `__version__` attribute
- Add proper classifiers for Python 3.9, 3.10, 3.11, 3.12, 3.13
- Configure project URLs (homepage, repository, documentation)

### 2. Add Test Suite
- Create `tests/` directory structure:
  ```
  tests/
  ├── __init__.py
  ├── conftest.py          # Shared fixtures, mock responses
  ├── test_api.py          # PubMed class tests
  ├── test_article.py      # PubMedArticle tests
  ├── test_book.py         # PubMedBookArticle tests
  └── test_helpers.py      # Helper function tests
  ```
- Use `responses` or `pytest-httpserver` to mock PubMed API
- Add sample XML responses as fixtures
- Test edge cases: empty results, malformed XML, rate limiting
- Configure pytest in `pyproject.toml`:
  ```toml
  [tool.pytest.ini_options]
  testpaths = ["tests"]
  addopts = "-v --cov=pymed --cov-report=term-missing"
  ```

### 3. Fix Critical Code Issues
- **Rate limiting** (`api.py:185-186`): Replace busy-wait with:
  ```python
  while self._exceededRateLimit():
      time.sleep(0.1)  # or exponential backoff
  ```
- **TypeVar misuse** (`article.py`, `book.py`): Replace with:
  ```python
  from xml.etree.ElementTree import Element
  ```
- **Old-style classes**: Remove `(object)` from class definitions
- **Mutable default**: Move `_requestsMade = []` to `__init__`

### 4. Set Up CI/CD
- Create `.github/workflows/ci.yml`:
  - Trigger on push/PR to main branches
  - Matrix test: Python 3.9, 3.10, 3.11, 3.12, 3.13
  - Steps: checkout, setup-python, install deps, lint, type-check, test
- Create `.github/workflows/publish.yml`:
  - Trigger on GitHub release
  - Build with `python -m build`
  - Publish to PyPI with trusted publishing (OIDC)
- Add status badges to README

---

## Phase 2: Code Quality

### 5. Add Code Quality Tools
- **Ruff configuration** in `pyproject.toml`:
  ```toml
  [tool.ruff]
  line-length = 88
  target-version = "py39"

  [tool.ruff.lint]
  select = ["E", "F", "W", "I", "UP", "B", "C4", "SIM"]
  ```
- **Mypy configuration**:
  ```toml
  [tool.mypy]
  python_version = "3.9"
  strict = true
  warn_return_any = true
  ```
- **Pre-commit hooks** (`.pre-commit-config.yaml`):
  - ruff (lint + format)
  - mypy
  - check-yaml, check-toml
  - trailing-whitespace, end-of-file-fixer
- Add `py.typed` marker file in `pymed/` for PEP 561

### 6. Update Dependencies
- Runtime: `requests>=2.28.0,<3.0`
- Dev dependencies:
  ```
  pytest>=7.0
  pytest-cov>=4.0
  responses>=0.23
  mypy>=1.0
  ruff>=0.1
  pre-commit>=3.0
  types-requests  # for mypy
  ```
- Consider adding `httpx` as optional async alternative

### 7. Code Cleanup
- **Naming convention**: Deprecate camelCase methods, add snake_case aliases
  ```python
  def get_total_results_count(self, ...):
      ...

  # Deprecated alias
  getTotalResultsCount = get_total_results_count
  ```
- **Logging**: Replace all `print()` with `logging`:
  ```python
  import logging
  logger = logging.getLogger(__name__)
  logger.warning("Rate limit exceeded, waiting...")
  ```
- **Exception handling**: Replace bare `except Exception` with specific exceptions
- **Remove dead code**: Delete empty `src/` directory, unused imports
- **Import organization**: Follow PEP 8 (stdlib, third-party, local)

---

## Phase 3: Documentation

### 8. Improve Documentation
- **README.md updates**:
  - Add installation section (`pip install pymed`)
  - Add Python version badge
  - Update usage examples
  - Add "Development" section for contributors
  - Remove or update deprecation notice (if taking over maintenance)
- **Docstring standardization**: Use Google style consistently
  ```python
  def query(self, query: str, max_results: int = 100) -> Iterator[PubMedArticle]:
      """Execute a PubMed query and return results.

      Args:
          query: PubMed search query string.
          max_results: Maximum number of results to return.

      Yields:
          PubMedArticle objects matching the query.

      Raises:
          RequestException: If the API request fails.
      """
  ```
- **Remove outdated references**: Delete "GraphQL" mentions in comments
- **Create CHANGELOG.md**: Follow Keep a Changelog format

### 9. Enhance Type Annotations
- Add return types to all public methods
- Use `Self` type (Python 3.11+) or `TypeVar` for method chaining
- Proper Optional/Union syntax: `str | None` instead of `Optional[str]`
- Add overloads where return type depends on input
- Create `py.typed` marker for downstream type checking

---

## Phase 4: Enhancements (Optional)

### 10. Modernize Data Models
- Convert to dataclasses:
  ```python
  from dataclasses import dataclass, field

  @dataclass
  class PubMedArticle:
      pubmed_id: str
      title: str
      abstract: str | None = None
      authors: list[dict] = field(default_factory=list)
      # ... etc
  ```
- Benefits: automatic `__init__`, `__repr__`, `__eq__`, easier serialization
- Alternative: Pydantic for validation and JSON serialization
- Keep `toDict()` for backwards compatibility

### 11. Improve API Design
- **Configurable parameters**:
  ```python
  class PubMed:
      def __init__(
          self,
          tool: str = "my_tool",
          email: str = "my_email@example.com",
          batch_size: int = 250,
          rate_limit: int = 10,
          timeout: int = 30,
      ):
  ```
- **Session reuse**: Use `requests.Session()` for connection pooling
- **Retry logic**: Add `urllib3.Retry` or `tenacity` for transient failures
- **Async support**: Consider `httpx` async client for better performance
  ```python
  async def query_async(self, query: str) -> AsyncIterator[PubMedArticle]:
      ...
  ```

### 12. Additional Enhancements
- **Context manager support**:
  ```python
  with PubMed(tool="my_tool", email="...") as pubmed:
      articles = pubmed.query("cancer")
  ```
- **Better error types**: Create custom exceptions (`PubMedAPIError`, `RateLimitError`)
- **Caching**: Optional response caching with `requests-cache`
- **Progress callbacks**: For long-running queries

---

## Files Summary

| Action | File | Notes |
|--------|------|-------|
| **Modify** | `pyproject.toml` | Full PEP 621 configuration |
| **Modify** | `pymed/__init__.py` | Update exports, add `__version__` |
| **Modify** | `pymed/api.py` | Rate limit fix, logging, types |
| **Modify** | `pymed/article.py` | Type fixes, dataclass conversion |
| **Modify** | `pymed/book.py` | Type fixes, dataclass conversion |
| **Modify** | `pymed/helpers.py` | Type annotations |
| **Modify** | `README.md` | Installation, badges, examples |
| **Delete** | `setup.py` | Replaced by pyproject.toml |
| **Delete** | `build.py` | Replaced by CI/CD |
| **Delete** | `requirements.txt` | Merged into pyproject.toml |
| **Delete** | `src/` | Empty, unused |
| **Create** | `tests/conftest.py` | Fixtures, mock responses |
| **Create** | `tests/test_api.py` | PubMed class tests |
| **Create** | `tests/test_article.py` | Article tests |
| **Create** | `tests/test_book.py` | Book tests |
| **Create** | `.github/workflows/ci.yml` | Test/lint workflow |
| **Create** | `.github/workflows/publish.yml` | PyPI publishing |
| **Create** | `.pre-commit-config.yaml` | Git hooks |
| **Create** | `CHANGELOG.md` | Release notes |
| **Create** | `pymed/py.typed` | PEP 561 marker |

---

## Implementation Order

1. `pyproject.toml` configuration
2. Critical bug fixes (rate limiting, types)
3. Test suite setup
4. CI/CD workflows
5. Code quality tools (ruff, mypy, pre-commit)
6. Code cleanup (logging, naming, exceptions)
7. Documentation updates
8. Optional enhancements

---

# Technology Comparisons

## Dataclasses vs Pydantic

### Dataclasses (stdlib)

**Pros:**
- Zero dependencies (built into Python 3.7+)
- Lightweight, minimal overhead
- Simple and Pythonic
- Fast instantiation (no validation cost)
- Easy to understand for contributors

**Cons:**
- No runtime validation (types are hints only)
- Manual serialization to dict/JSON
- No automatic type coercion
- Limited nested model support

**Example:**
```python
from dataclasses import dataclass, field, asdict

@dataclass
class PubMedArticle:
    pubmed_id: str
    title: str
    abstract: str | None = None
    authors: list[dict] = field(default_factory=list)

    def to_dict(self) -> dict:
        return asdict(self)

# No validation - this "works" even though it's wrong
article = PubMedArticle(pubmed_id=12345, title=None)  # No error!
```

---

### Pydantic

**Pros:**
- Runtime validation (catches bad data immediately)
- Automatic type coercion (`"123"` → `123`)
- Built-in JSON/dict serialization
- Excellent for API responses and external data
- Rich error messages
- Nested model support
- Aliases, validators, computed fields

**Cons:**
- External dependency (~2MB)
- Slower instantiation (validation overhead)
- Steeper learning curve
- Can be overkill for simple internal models
- v1 to v2 migration was breaking

**Example:**
```python
from pydantic import BaseModel, Field

class PubMedArticle(BaseModel):
    pubmed_id: str
    title: str
    abstract: str | None = None
    authors: list[dict] = Field(default_factory=list)

    model_config = {"extra": "ignore"}  # Ignore unknown fields

# Validation happens automatically
article = PubMedArticle(pubmed_id=12345, title=None)  # ValidationError!

# Type coercion
article = PubMedArticle(pubmed_id="12345", title="Test")  # Works, coerces int→str
```

---

### For PyMed Specifically

| Factor | Dataclass | Pydantic |
|--------|-----------|----------|
| **Dependency** | None | +1 dependency |
| **XML parsing** | Manual validation needed | Auto-validates parsed data |
| **Performance** | Faster for many articles | Slight overhead per article |
| **Serialization** | Need `asdict()` | Built-in `.model_dump()` |
| **Error handling** | Silent failures | Explicit validation errors |
| **Backwards compat** | Easier to maintain `toDict()` | Can alias to `toDict()` |

### Recommendation

**For PyMed, dataclasses are suggested** because:

1. **Minimal dependencies** - PyMed currently only needs `requests`
2. **Performance** - Queries can return hundreds of articles
3. **Simplicity** - Lower barrier for contributors
4. **Source data is XML** - You're already manually parsing, validation happens there

However, **Pydantic makes sense if**:
- You want to catch malformed PubMed responses automatically
- You plan to add JSON API endpoints
- You want strict guarantees about data types

---

## Pydantic Example for PyMed

```python
from datetime import datetime
from pydantic import BaseModel, Field, field_validator, computed_field
from xml.etree.ElementTree import Element

class Author(BaseModel):
    lastname: str
    firstname: str
    initials: str = ""
    affiliation: str = ""

class PubMedArticle(BaseModel):
    """Pydantic model for a PubMed article."""

    pubmed_id: str
    title: str
    abstract: str = ""
    keywords: list[str] = Field(default_factory=list)
    journal: str = ""
    publication_date: datetime | None = None
    authors: list[Author] = Field(default_factory=list)
    methods: str = ""
    conclusions: str = ""
    results: str = ""
    copyrights: str = ""
    doi: str = ""
    xml: str = Field(default="", repr=False)  # Exclude from repr

    model_config = {
        "extra": "ignore",           # Ignore unknown fields from XML
        "str_strip_whitespace": True # Auto-strip whitespace
    }

    # Validators
    @field_validator("pubmed_id")
    @classmethod
    def validate_pubmed_id(cls, v: str) -> str:
        if not v.isdigit():
            raise ValueError(f"pubmed_id must be numeric, got: {v}")
        return v

    @field_validator("publication_date", mode="before")
    @classmethod
    def parse_date(cls, v):
        if isinstance(v, str):
            # Handle various date formats from PubMed
            for fmt in ["%Y-%m-%d", "%Y-%m", "%Y"]:
                try:
                    return datetime.strptime(v, fmt)
                except ValueError:
                    continue
        return v

    # Computed field
    @computed_field
    @property
    def author_string(self) -> str:
        return ", ".join(
            f"{a.firstname} {a.lastname}" for a in self.authors
        )

    # Factory method from XML
    @classmethod
    def from_xml(cls, xml_element: Element) -> "PubMedArticle":
        """Parse a PubMed XML element into an article."""

        # Extract fields from XML
        pubmed_id = xml_element.findtext(".//PMID", default="")
        title = xml_element.findtext(".//ArticleTitle", default="")

        # Parse authors
        authors = []
        for author_elem in xml_element.findall(".//Author"):
            authors.append(Author(
                lastname=author_elem.findtext("LastName", default=""),
                firstname=author_elem.findtext("ForeName", default=""),
                initials=author_elem.findtext("Initials", default=""),
                affiliation=author_elem.findtext(".//Affiliation", default="")
            ))

        # Pydantic validates everything automatically here
        return cls(
            pubmed_id=pubmed_id,
            title=title,
            authors=authors,
            # ... other fields
        )

    # Backwards compatibility with existing API
    def toDict(self) -> dict:
        """Legacy method for backwards compatibility."""
        return self.model_dump(exclude={"xml"})

    def toJSON(self) -> str:
        """Serialize to JSON string."""
        return self.model_dump_json(exclude={"xml"}, indent=2)


# Usage examples
if __name__ == "__main__":
    # Direct instantiation with validation
    article = PubMedArticle(
        pubmed_id="12345678",
        title="Example Article",
        authors=[
            Author(lastname="Smith", firstname="John"),
            Author(lastname="Doe", firstname="Jane", affiliation="MIT")
        ]
    )

    print(article.author_string)  # "John Smith, Jane Doe"
    print(article.model_dump())   # Dict output

    # Validation error example
    try:
        bad_article = PubMedArticle(
            pubmed_id="not-a-number",  # ValidationError!
            title="Test"
        )
    except Exception as e:
        print(f"Validation failed: {e}")

    # Type coercion (int -> str)
    article2 = PubMedArticle(
        pubmed_id=12345678,  # Coerced to "12345678"
        title="Another Article"
    )
```

### Key Pydantic Features

| Feature | Benefit |
|---------|---------|
| `field_validator` | Custom validation logic |
| `mode="before"` | Transform data before validation |
| `computed_field` | Derived properties included in serialization |
| `model_config` | Global settings (extra fields, whitespace) |
| `model_dump()` | Dict serialization with exclude/include |
| `model_dump_json()` | Direct JSON serialization |
| Nested models | `Author` as a separate validated model |
| Type coercion | `int` → `str` automatic conversion |

---

## Requests vs HTTPX

### Requests

**Pros:**
- Battle-tested, extremely stable (10+ years)
- Huge ecosystem (requests-cache, requests-oauthlib, etc.)
- Simple, intuitive API
- Already a dependency in PyMed
- More tutorials/Stack Overflow answers
- Slightly smaller install size

**Cons:**
- Sync only (no async support)
- No HTTP/2 support
- Slower for many concurrent requests
- Less actively developed (maintenance mode)

```python
import requests

with requests.Session() as session:
    response = session.get(
        "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi",
        params={"db": "pubmed", "term": "cancer"}
    )
    data = response.text
```

---

### HTTPX

**Pros:**
- Async and sync support in one library
- HTTP/2 support
- Modern, actively developed
- requests-compatible API (easy migration)
- Better timeout handling
- Built-in connection pooling
- Type hints throughout

**Cons:**
- Newer (less battle-tested)
- Additional dependency if you're already using requests
- Slightly larger (~adds httpcore, h11, anyio)
- Fewer third-party extensions

```python
import httpx

# Sync (drop-in replacement for requests)
with httpx.Client() as client:
    response = client.get(
        "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi",
        params={"db": "pubmed", "term": "cancer"}
    )

# Async
async with httpx.AsyncClient() as client:
    response = await client.get(...)
```

---

### For PyMed Specifically

| Factor | Requests | HTTPX |
|--------|----------|-------|
| **Migration effort** | None (already used) | ~30 min (API is similar) |
| **Async queries** | Not possible | Ready when needed |
| **Concurrent fetches** | Threads/multiprocessing | Native async |
| **Dependencies** | +0 | +1 (httpx) |
| **Future-proofing** | Limited | Better |
| **PubMed rate limits** | Works fine | Works fine |

### Performance Comparison

For **sequential requests** (current PyMed behavior):
- Nearly identical performance
- Requests might be marginally faster

For **concurrent requests** (fetching multiple batches):
```python
# HTTPX async - much faster for many requests
async def fetch_all_batches(queries: list[str]) -> list[Response]:
    async with httpx.AsyncClient() as client:
        tasks = [client.get(url) for url in queries]
        return await asyncio.gather(*tasks)
```

---

### Recommendation

**Stick with requests** if:
- You want minimal changes
- You don't need async
- You value stability over features
- You want to keep dependencies minimal

**Switch to HTTPX** if:
- You plan to add async support (Phase 4 of your plan)
- You want better concurrent batch fetching
- You're doing a major rewrite anyway
- You want HTTP/2 or modern features

### Suggestion for PyMed

**Start with requests, design for HTTPX migration:**

```python
# pymed/api.py
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from requests import Session
    # or: from httpx import Client as Session

class PubMed:
    def __init__(self, ...):
        self._session: Session | None = None

    def _get_session(self) -> Session:
        if self._session is None:
            import requests
            self._session = requests.Session()
        return self._session
```

This way you can swap to HTTPX later with minimal code changes. The APIs are nearly identical:

```python
# requests
session.get(url, params=params, timeout=30)

# httpx (identical!)
client.get(url, params=params, timeout=30)
```

### If You Go HTTPX

Migration is straightforward:

```python
# Before (requests)
import requests
response = requests.get(url, params=params)

# After (httpx sync)
import httpx
response = httpx.get(url, params=params)

# After (httpx async)
async with httpx.AsyncClient() as client:
    response = await client.get(url, params=params)
```

**Bottom line:** For a library focused on simplicity and minimal dependencies, **requests is fine**. Switch to HTTPX when/if you implement async support in Phase 4.
