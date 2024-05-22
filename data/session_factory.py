from contextlib import asynccontextmanager

from sqlalchemy.exc import OperationalError, SQLAlchemyError
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_engine_from_config,
    async_sessionmaker,
)

from models.model import ModelBase
from settings import db_settings

__factory: AsyncEngine = None


async def db_init():
    global __factory

    engine = async_engine_from_config(
        db_settings.config,
    )

    try:
        async with engine.begin() as conn:
            await conn.run_sync(ModelBase.metadata.create_all)
    except Exception as ex:
        print(f"Oops: {ex}")
        exit()
    else:
        print(f"\nSuccessfully connected to DB: {engine.url}")

    __factory = async_sessionmaker(engine)


@asynccontextmanager
async def async_get_session() -> AsyncSession:
    global __factory

    if __factory is None:
        await db_init()

    async_session = __factory()

    try:
        yield async_session
    except SQLAlchemyError as err:
        await async_session.rollback()
        print(f"Oops! {err}")
    except OperationalError as err:
        await async_session.rollback()
        print(f"Oops! {err}")
    else:
        await async_session.commit()
