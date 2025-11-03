import logging
from datetime import datetime

from sqlalchemy.orm import Mapped, mapped_column

from src.db.models.base import Base, IdMixin, TimestampMixin

logger = logging.getLogger(__name__)


class CrawlJob(Base, IdMixin, TimestampMixin):
    __tablename__ = "crawl_job"

    prompt_name: Mapped[str | None] = mapped_column(
        nullable=True,
        comment="Name of the prompt to use for this crawl job (optional if using scraper function)",
    )

    domain: Mapped[str] = mapped_column(
        nullable=False,
        unique=True,
        comment="Domain to crawl",
    )

    crawling_interval: Mapped[int] = mapped_column(
        nullable=False,
        comment="Crawling interval in hours (positive integer)",
    )

    last_crawled_at: Mapped[datetime | None] = mapped_column(
        nullable=True,
        default=None,
        comment="Timestamp of the last successful crawl",
    )
