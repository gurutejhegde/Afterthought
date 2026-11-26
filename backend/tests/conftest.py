import asyncio
import os
import pytest

os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///./test_afterthought.db"
os.environ["FORCE_OFFLINE_AI"] = "true"

from app.db.database import engine  # noqa: E402


@pytest.fixture(scope="session", autouse=True)
def cleanup_test_db():
    if os.path.exists("test_afterthought.db"):
        os.remove("test_afterthought.db")
    yield
    asyncio.run(engine.dispose())
    if os.path.exists("test_afterthought.db"):
        os.remove("test_afterthought.db")
