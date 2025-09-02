import uuid
from typing import List, Optional

from sqlalchemy import ForeignKey, Text
from sqlalchemy.dialects.postgresql import ARRAY, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.src.db.models.support_listing_model import SupportListing
from src.db.models.base import Base, IdMixin, TimestampMixin


class Support(Base, IdMixin, TimestampMixin):
    __tablename__ = "support"

    support_listing_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(SupportListing.support_listings.id, ondelete="CASCADE"),
        nullable=False,
        comment="Foreign Key relationship to the Support Listing Table",
    )

    name: Mapped[str] = mapped_column(
        Text, nullable=False, unique=True, comment="Human usable name for the support"
    )

    addresses: Mapped[List[str]] = mapped_column(
        ARRAY(Text),
        nullable=False,
        server_default="{}",
        comment="The address(es), as a list, of the the support resource(s)",
    )

    phone_numbers: Mapped[List[str]] = mapped_column(
        ARRAY(Text),
        nullable=False,
        server_default="{}",
        comment="The phone number(s), as a list, of the the support resource(s)",
    )

    description: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True, commment="Description summarizing the resource"
    )

    website: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True, comment="The full URL for the specific resource"
    )

    email_addresses: Mapped[List[str]] = mapped_column(
        ARRAY(Text),
        nullable=False,
        server_default="{}",
        comment="The email address(es) as a list to contact the referral resource",
    )
