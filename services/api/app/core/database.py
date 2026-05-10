from collections.abc import AsyncIterator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from app.core.config import get_settings


class Base(DeclarativeBase):
    pass


_session_factory: async_sessionmaker[AsyncSession] | None = None


def get_session_factory() -> async_sessionmaker[AsyncSession] | None:
    global _session_factory
    if _session_factory is not None:
        return _session_factory

    database_url = get_settings().async_database_url
    if not database_url:
        return None

    engine = create_async_engine(database_url, pool_pre_ping=True)
    _session_factory = async_sessionmaker(engine, expire_on_commit=False)
    return _session_factory


async def get_db_session() -> AsyncIterator[AsyncSession | None]:
    session_factory = get_session_factory()
    if session_factory is None:
        yield None
        return

    async with session_factory() as session:
        yield session

