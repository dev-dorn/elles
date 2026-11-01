import os

# Must be set before catalog_app is imported: Settings reads it once, at import time,
# and an environment variable takes priority over any value in .env.
os.environ["JWT_SECRET_KEY"] = "test-secret-key-for-unit-tests-only-0123456789"

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from catalog_app.main import app  # noqa: E402
from catalog_app.presentation.api.products import get_product_repo  # noqa: E402
from tests.fakes import FakeProductRepository  # noqa: E402
from tests.helpers import auth  # noqa: E402


@pytest.fixture
def repo() -> FakeProductRepository:
    return FakeProductRepository()


@pytest.fixture
def client(repo):
    """API client wired to the in-memory repository.

    TestClient is deliberately not used as a context manager, so the app's lifespan
    (which creates MongoDB indexes) never runs and no database is needed.
    """
    app.dependency_overrides[get_product_repo] = lambda: repo
    yield TestClient(app)
    app.dependency_overrides.clear()


@pytest.fixture
def admin():
    return auth()
