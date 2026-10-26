"""Create subjects, quarters, and topics.

Revision ID: 0001_initial
Revises:
Create Date: 2026-10-25
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "0001_initial"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "subjects",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name"),
    )
    op.create_table(
        "quarters",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("school_year", sa.String(length=20), nullable=False),
        sa.Column("number", sa.Integer(), nullable=False),
        sa.Column("starts_at", sa.Date(), nullable=True),
        sa.Column("ends_at", sa.Date(), nullable=True),
        sa.CheckConstraint("number >= 1 AND number <= 4", name="ck_quarters_number_1_to_4"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("school_year", "number", name="uq_quarters_school_year_number"),
    )
    op.create_index("ix_quarters_school_year", "quarters", ["school_year"], unique=False)

    op.create_table(
        "topics",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("subject_id", sa.Integer(), nullable=False),
        sa.Column("quarter_id", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(length=200), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("status", sa.String(length=20), server_default="draft", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint("status IN ('draft', 'published', 'archived')", name="ck_topics_status"),
        sa.ForeignKeyConstraint(["quarter_id"], ["quarters.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["subject_id"], ["subjects.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_topics_subject_quarter", "topics", ["subject_id", "quarter_id"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_topics_subject_quarter", table_name="topics")
    op.drop_table("topics")
    op.drop_index("ix_quarters_school_year", table_name="quarters")
    op.drop_table("quarters")
    op.drop_table("subjects")
