# env vars have to be set before importing the app
import os
import tempfile

_db_file = os.path.join(tempfile.mkdtemp(), "test.db")
os.environ["DATABASE_URL"] = f"sqlite:///{_db_file}"
os.environ["LLM_PROVIDER"] = "mock"
os.environ["ASSEMBLYAI_API_KEY"] = "test-key"
os.environ["HR_API_KEY"] = ""  # turn off HR key check

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from app.main import app  # noqa: E402


@pytest.fixture(scope="session")
def client():
    # "with" runs startup (tables + seed roles)
    with TestClient(app) as c:
        yield c
