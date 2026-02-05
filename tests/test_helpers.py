from xml.etree import ElementTree as xml

from pymed.helpers import batches, getContent


def test_batches_handles_edges():
    assert list(batches([], 3)) == []
    assert list(batches([1, 2, 3], 1)) == [[1], [2], [3]]
    assert list(batches([1, 2, 3], 5)) == [[1, 2, 3]]


def test_get_content_returns_default_when_missing():
    element = xml.fromstring("<Root></Root>")
    assert getContent(element, path=".//Missing", default="fallback") == "fallback"


def test_get_content_returns_default_when_element_none():
    assert getContent(None, path=".//Missing", default="fallback") == "fallback"


def test_get_content_joins_multiple_nodes():
    element = xml.fromstring("<Root><Item>one</Item><Item>two</Item></Root>")
    assert getContent(element, path=".//Item", default="") == "one\ntwo"
    assert getContent(element, path=".//Item", default="", separator=", ") == "one, two"
