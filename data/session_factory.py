import sqlalchemy as sa
import sqlalchemy.orm as orm
from asyncio import current_task
from sqlalchemy.exc import SQLAlchemyError, OperationalError
from sqlalchemy.orm import Session
from contextlib import contextmanager, asynccontextmanager
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, async_scoped_session, create_async_engine

from settings import DB_USER, DB_PASSWORD, DB_HOST, DB_NAME
from db import db_folder
from models.model_base import ModelBase

__factory = None
__async_factory = None


def global_init():
    global __factory

    # full_file = db_folder.get_db_path('phonedb.sqlite')  # sqlite3
    # url = 'sqlite:///' + full_file  # sqlite3

    url = f"postgresql+psycopg://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:5432/{DB_NAME}"  # postgresql

    engine = sa.create_engine(url, echo=False, pool_size=20, )
    ModelBase.metadata.create_all(engine, checkfirst=True, )

    __factory = orm.sessionmaker(bind=engine, expire_on_commit=False)


@contextmanager
def get_session() -> Session:
    global __factory

    if __factory is None:
        global_init()

    session = orm.scoped_session(__factory)

    try:
        yield session
    except SQLAlchemyError as err:
        session.rollback()
        print(f"Oops! {err}")
    except OperationalError as err:
        session.rollback()
        print(f"Oops! {err}")
    finally:
        session.remove()


async def async_global_init():
    global __async_factory

    # full_file = db_folder.get_db_path('phonedb.sqlite')  # sqlite3
    # url = 'sqlite+aiosqlite:///' + full_file  # sqlite3
    # engine = create_async_engine(url, echo=False, )  # sqlite3

    url = f"postgresql+asyncpg://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:5432/{DB_NAME}"  # postgresql
    engine = create_async_engine(url, echo=False, pool_size=20)  # poll = NullPool, #postgresql

    async with engine.begin() as conn:
        await conn.run_sync(ModelBase.metadata.create_all)

    __async_factory = async_sessionmaker(bind=engine, expire_on_commit=False)


@asynccontextmanager
async def async_get_session() -> AsyncSession:
    global __async_factory

    if __async_factory is None:
        await async_global_init()

    async_session = async_scoped_session(__async_factory, scopefunc=current_task)

    try:
        yield async_session
    except SQLAlchemyError as err:
        await async_session.rollback()
        print(f"Oops! {err}")
    except OperationalError as err:
        await async_session.rollback()
        print(f"Oops! {err}")
    finally:
        await async_session.remove()
