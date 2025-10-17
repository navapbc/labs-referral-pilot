import logging
from typing import List, Optional
from uuid import UUID

from sqlalchemy import ForeignKey, Text
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.db.models.base import Base, IdMixin, TimestampMixin

logger = logging.getLogger(__name__)


class SupportListing(Base, IdMixin, TimestampMixin):
    __tablename__ = "support_listing"

    name: Mapped[str] = mapped_column(
        nullable=False,
        unique=True,
        comment="name of the support listing; a human-readable identifier",
    )
    uri: Mapped[str] = mapped_column(
        nullable=False,
        comment="origin of the Support Listing; a file path or a website URL",
    )

    supports: Mapped[list["Support"]] = relationship(
        "Support", back_populates="support_listing", cascade="all, delete"
    )


class Support(Base, IdMixin, TimestampMixin):
    __tablename__ = "support"

    support_listing_id: Mapped[UUID] = mapped_column(
        ForeignKey("support_listing.id", ondelete="CASCADE")
    )
    support_listing: Mapped[SupportListing] = relationship(SupportListing)

    name: Mapped[str] = mapped_column(nullable=False, comment="The name for the support resource")

    addresses: Mapped[List[str]] = mapped_column(
        ARRAY(Text),
        nullable=False,
        comment="The address(es), as a list, of the support resource",
    )

    phone_numbers: Mapped[List[str]] = mapped_column(
        ARRAY(Text),
        nullable=False,
        comment="The phone number(s), as a list, of the support resource",
    )

    description: Mapped[Optional[str]] = mapped_column(
        nullable=True, comment="Description summarizing the resource"
    )

    website: Mapped[Optional[str]] = mapped_column(
        nullable=True, comment="The full URL for the resource"
    )

    email_addresses: Mapped[List[str]] = mapped_column(
        ARRAY(Text),
        nullable=False,
        comment="The email address(es) as a list to contact the resource",
    )


class LlmResponse(Base, IdMixin, TimestampMixin):
    __tablename__ = "llm_response"

    raw_text: Mapped[str] = mapped_column(
        nullable=False, comment="The raw string of the LLM query; may contain JSON string"
    )
