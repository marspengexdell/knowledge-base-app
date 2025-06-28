import importlib
import os
import sys
from pathlib import Path
import types

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))

# We reload the module to apply monkeypatches

def test_embedding_model_loads_local_path(monkeypatch, tmp_path):
    dummy = tmp_path / "dummy-model"
    dummy.mkdir()

    loaded = {}

    class DummyST:
        def __init__(self, path):
            loaded["path"] = str(path)
        def encode(self, texts, show_progress_bar=False, normalize_embeddings=True):
            return [[0.0]]

    fake_module = types.ModuleType("sentence_transformers")
    fake_module.SentenceTransformer = DummyST
    monkeypatch.setitem(sys.modules, "sentence_transformers", fake_module)
    monkeypatch.setenv("EMBEDDING_MODEL", str(dummy))

    module = importlib.reload(importlib.import_module("app.services.embedding"))
    assert module.embedding_model.model is not None
    assert loaded["path"] == str(dummy)
