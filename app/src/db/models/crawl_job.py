import logging

from sqlalchemy.orm import Mapped, mapped_column

from src.db.models.base import Base, IdMixin, TimestampMixin

logger = logging.getLogger(__name__)


class CrawlJob(Base, IdMixin, TimestampMixin):
    __tablename__ = "crawl_job"

    prompt_name: Mapped[str] = mapped_column(
        nullable=False,
        comment="Name of the prompt to use for this crawl job",
    )

    domain: Mapped[str] = mapped_column(
        nullable=False,
        comment="Domain to crawl",
    )

    crawling_interval: Mapped[int] = mapped_column(
        nullable=False,
        comment="Crawling interval in hours (positive integer)",
    )
