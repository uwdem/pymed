import importlib
import importlib.metadata

import pymed.version as version_module


def test_version_falls_back_when_metadata_missing(monkeypatch):
    def raise_not_found(*args, **kwargs):
        raise importlib.metadata.PackageNotFoundError("pymed")

    monkeypatch.setattr(importlib.metadata, "version", raise_not_found)

    reloaded = importlib.reload(version_module)
    assert reloaded.__version__ == "0.8.9"

    importlib.reload(version_module)
