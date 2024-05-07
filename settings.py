from config.config import PostgresSQL, SQLite, Config

USER: str = "phonecontrol"  # CUCM End User username
USER_PWD: str = "phonecontrol"  # CUCM End User password
PAUSE: float = 1.5  # Pause in seconds between sending keypress
CHUNK_SIZE: int = 20  # Chunk size which split phones list (use for more control)

# default postgresql docker settings
cfg: Config = PostgresSQL(
    host="localhost",
    dbname="postgres",
    username="postgres",
    password="postgres"
)
