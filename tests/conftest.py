"""
Test setup. Environment variables must be set *before* the app is imported,
because app/config.py reads them at import time.
"""
import os
import tempfile

_db_file = os.path.join(tempfile.mkdtemp(), "test.db")
os.environ["DATABASE_URL"] = f"sqlite:///{_db_file}"
os.environ["LLM_PROVIDER"] = "mock"
os.environ["ASSEMBLYAI_API_KEY"] = "test-key"

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from app.main import app  # noqa: E402


@pytest.fixture(scope="session")
def client():
    # Using the client as a context manager runs the lifespan (create tables + seed roles).
    with TestClient(app) as c:
        yield c
