from sqlalchemy.orm import DeclarativeBase
from sqlalchemy import MetaData

# metadata_base = MetaData(schema='main')
metadata_base = MetaData()

naming_convention = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_`%(constraint_name)s`",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s"
}


class ModelBase(DeclarativeBase):
    metadata = metadata_base
    metadata.naming_convention = naming_convention
    pass
