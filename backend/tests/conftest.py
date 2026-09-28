import sys
import os
import pytest

# Add backend directory to PYTHONPATH
backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from app.db.seed import seed_database
from app.core.database import engine, Base


@pytest.fixture(scope="function", autouse=True)
def setup_test_db():
    seed_database(reset=True)
