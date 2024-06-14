from dynaconf import Dynaconf

from config.config import PostgresSQL

settings = Dynaconf(
    envvar_prefix=False,
    load_dotenv=True,
)

db_settings = PostgresSQL(url=settings.DATABASE_URL)
