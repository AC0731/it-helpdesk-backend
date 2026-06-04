import os

import pytest
from fastapi.testclient import TestClient

os.environ["DATABASE_URL"] = "sqlite:///./test_supportops.db"
os.environ["ALLOWED_ORIGINS"] = "http://localhost:5173"

from app.db.database import Base, engine  # noqa: E402
from app.main import app  # noqa: E402


def reset_database() -> None:
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)


@pytest.fixture(autouse=True)
def clean_database():
    reset_database()
    yield
    reset_database()


@pytest.fixture
def client():
    with TestClient(app) as test_client:
        yield test_client