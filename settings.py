from dynaconf import Dynaconf

from config.config import Config, PostgresSQL

settings = Dynaconf(
    envvar_prefix="ENV",
    load_dotenv=True,
)

cfg: Config = PostgresSQL(
    host=settings.DB_HOST,
    dbname=settings.DB_NAME,
    username=settings.DB_USERNAME,
    password=settings.DB_PASSWORD,
)
