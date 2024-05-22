from typing import Any

from db.db_folder import get_db_path


class SQLAlchemyConfig:
    """Base config, uses staging SQLAlchemy Engine."""

    __test__ = False

    ECHO: bool = False
    ENGINE_OPTIONS: dict[str, Any] = {}
    DATABASE_URL: str = None

    @property
    def sa_database_uri(self) -> str:
        if self.__class__ is SQLite or PostgresSQL:
            return self.DATABASE_URL
        else:
            raise NotImplementedError("This DB not implemented!")

    @property
    def sa_engine_options(self) -> dict[str, Any]:
        return self.ENGINE_OPTIONS

    @property
    def sa_echo(self) -> bool:
        return self.ECHO

    @property
    def config(self) -> dict[str, Any]:
        cfg = {"sqlalchemy.url": self.sa_database_uri, "sqlalchemy.echo": self.sa_echo}
        for k, v in self.sa_engine_options.items():
            cfg[f"sqlalchemy.{k}"] = v
        return cfg


class PostgresSQL(SQLAlchemyConfig):
    """Uses for PostgresSQL database server."""

    ECHO: bool = False
    ENGINE_OPTIONS: dict[str, Any] = {
        "pool_size": 10,
        "pool_pre_ping": True,
    }

    def __init__(self, url):
        self.DATABASE_URL = url


class SQLite(SQLAlchemyConfig):
    """Uses for SQLite database server."""

    ECHO: bool = True
    DB_NAME: str = "phonedb.sqlite"
    ENGINE_OPTIONS: dict[str, Any] = {
        "pool_pre_ping": True,
    }

    def __init__(self, db_name: str):
        if db_name.strip():
            self.DB_NAME = db_name
        self.DATABASE_URL = f"sqlite+aiosqlite:///{get_db_path(self.DB_NAME)}"
