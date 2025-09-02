import logging

from sqlalchemy.orm import Mapped, mapped_column

from src.db.models.base import Base, IdMixin, TimestampMixin

logger = logging.getLogger(__name__)


class SupportListing(Base, IdMixin, TimestampMixin):
    __tablename__ = "support_listing"

    name: Mapped[str] = mapped_column(nullable=False, unique=True)
    uri: Mapped[str] = mapped_column(
        comment="origin of the Support Listing; a file path or a website URL"
    )
