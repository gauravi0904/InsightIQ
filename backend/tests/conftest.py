import pytest
from pathlib import Path
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.app.main import app
from backend.app.core.config import settings
from backend.app.core.database import Base, get_db

# Use test SQLite database
TEST_DB_PATH = settings.PROJECT_ROOT / "data" / "test_insightiq.sqlite3"
TEST_DATABASE_URL = f"sqlite:///{TEST_DB_PATH}"

test_engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture(scope="session", autouse=True)
def setup_test_db():
    Base.metadata.drop_all(bind=test_engine)
    Base.metadata.create_all(bind=test_engine)
    app.dependency_overrides[get_db] = override_get_db
    yield
    Base.metadata.drop_all(bind=test_engine)
    if TEST_DB_PATH.exists():
        TEST_DB_PATH.unlink(missing_ok=True)


@pytest.fixture
def client():
    with TestClient(app) as c:
        yield c


@pytest.fixture
def sample_csv_path():
    return settings.PROJECT_ROOT / "sample_data" / "customers.csv"


@pytest.fixture
def sample_sales_csv_path():
    return settings.PROJECT_ROOT / "sample_data" / "sales.csv"


@pytest.fixture
def sample_employee_csv_path():
    return settings.PROJECT_ROOT / "sample_data" / "employee_data.csv"
