"""SQLAlchemy models for the first ClassSignal release."""

from datetime import date, datetime

from sqlalchemy import CheckConstraint, Date, DateTime, ForeignKey, Index, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class Subject(Base):
    __tablename__ = "subjects"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100), unique=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)


class Quarter(Base):
    __tablename__ = "quarters"
    __table_args__ = (
        UniqueConstraint("school_year", "number", name="uq_quarters_school_year_number"),
        CheckConstraint("number >= 1 AND number <= 4", name="ck_quarters_number_1_to_4"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    school_year: Mapped[str] = mapped_column(String(20), index=True)
    number: Mapped[int]
    starts_at: Mapped[date | None] = mapped_column(Date, nullable=True)
    ends_at: Mapped[date | None] = mapped_column(Date, nullable=True)


class Topic(Base):
    __tablename__ = "topics"
    __table_args__ = (
        CheckConstraint("status IN ('draft', 'published', 'archived')", name="ck_topics_status"),
        Index("ix_topics_subject_quarter", "subject_id", "quarter_id"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    subject_id: Mapped[int] = mapped_column(ForeignKey("subjects.id", ondelete="RESTRICT"))
    quarter_id: Mapped[int] = mapped_column(ForeignKey("quarters.id", ondelete="RESTRICT"))
    title: Mapped[str] = mapped_column(String(200))
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="draft", server_default="draft")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
