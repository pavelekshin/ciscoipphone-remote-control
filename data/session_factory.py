from sqlalchemy.exc import SQLAlchemyError, OperationalError
from contextlib import asynccontextmanager
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine, async_engine_from_config
from settings import cfg
from models.model_base import ModelBase

__async_factory = None


async def db_init():
    global __async_factory

    engine = async_engine_from_config(cfg.config, )

    try:
        async with engine.begin() as conn:
            await conn.run_sync(ModelBase.metadata.create_all)
    except Exception as ex:
        print(f"Oops: {ex}")
        exit()
    else:
        print(f"Successfully connected to DB :{engine.url}")

    __async_factory = async_sessionmaker(bind=engine, expire_on_commit=False)


@asynccontextmanager
async def async_get_session() -> AsyncSession:
    global __async_factory

    if __async_factory is None:
        await db_init()

    async_session = __async_factory()

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
