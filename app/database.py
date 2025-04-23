import os
from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlmodel import SQLModel
from sqlmodel.ext.asyncio.session import AsyncSession

# TODO: We want to use PostgreSQL in production, but for now we are using SQLite

# Use test.db for tests, dev.db otherwise to prevent wiping my data when running tests
is_testing = "PYTEST_VERSION" in os.environ
DATABASE_URL = f"sqlite+aiosqlite:///./{'test.db' if is_testing else 'dev.db'}"

_engine = create_async_engine(DATABASE_URL, echo=True)
_async_session = async_sessionmaker(
    _engine, class_=AsyncSession, expire_on_commit=False
)


async def init_db():
    async with _engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)


async def get_db_session() -> AsyncGenerator[AsyncSession]:
    async with _async_session() as session:
        yield session


__all__ = [
    "AsyncSession",
    "create_async_engine",
    "get_db_session",
    "init_db",
]
