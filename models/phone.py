import datetime
import enum

from sqlalchemy import DateTime, Enum, Index, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

# noinspection PyPackageRequirements
from models.model_base import ModelBase


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
            f"Phone(id={self.id!r}, ip_address={self.ip_address!r}, status={self.status!r}, error={self.error!r}, "
            f"created={self.created!r}, updated={self.updated!r})"
        )
