import logging

from sqlalchemy.orm import Mapped, mapped_column

from src.db.models.base import Base, IdMixin, TimestampMixin

logger = logging.getLogger(__name__)


class SupportListing(Base, IdMixin, TimestampMixin):
    __tablename__ = "support_listing"

    name: Mapped[str]
    uri: Mapped[str] = mapped_column(
        comment="origin of the Support Listing for later reference and record keeping"
    )
