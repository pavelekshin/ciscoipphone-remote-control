from dynaconf import Dynaconf

from config.config import PostgresSQL

settings = Dynaconf(
    envvar_prefix="ENV",
    load_dotenv=True,
)

db_settings = PostgresSQL(url=settings.DATABASE_URL)
