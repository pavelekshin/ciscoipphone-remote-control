import datetime
import enum

from sqlalchemy import DateTime, Enum, Index, Integer, MetaData, String
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

DB_NAMING_CONVENTION = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_`%(constraint_name)s`",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}

metadata_base = MetaData()


class ModelBase(DeclarativeBase):
    metadata = metadata_base
    metadata.naming_convention = DB_NAMING_CONVENTION


class StatusEnum(str, enum.Enum):
    SUCCESS = "Success"
    ERROR = "Error"
    CANCEL = "Canceled"
    IN_PROGRESS = "In progress"


class Phone(ModelBase):
    __tablename__ = "phones"
    __table_args__ = (
        Index(None, "id"),  # create index
        Index(None, "ip_address"),  # create index
        # {"schema": "main"},  # set table schema
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    ip_address: Mapped[str] = mapped_column(String(30), nullable=False, unique=True)
    status: Mapped[Enum] = mapped_column(Enum(StatusEnum), nullable=True)
    error: Mapped[str] = mapped_column(String(4096), nullable=True)
    created: Mapped[datetime] = mapped_column(DateTime, default=datetime.datetime.now)
    updated: Mapped[datetime] = mapped_column(DateTime, nullable=True)

    def __repr__(self) -> str:
        return (
            f"Phone(id={self.id!r}, ip_address={self.ip_address!r},"
            f" status={self.status!r}, error={self.error!r}, "
            f"created={self.created!r}, updated={self.updated!r})"
        )
