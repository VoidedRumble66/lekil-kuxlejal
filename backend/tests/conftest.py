from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient

from app.main import create_app


@pytest.fixture
def database_url(tmp_path):
    return f"sqlite:///{(tmp_path / 'test.db').as_posix()}"


@pytest.fixture
def application(database_url):
    return create_app(database_url)


@pytest.fixture
def client(application) -> Generator[TestClient, None, None]:
    with TestClient(application) as test_client:
        yield test_client
