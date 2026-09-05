"""create dataset insights table

Revision ID: a6f0c4d9e8b1
Revises: 922b17a3c6f4
Create Date: 2026-09-03

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "a6f0c4d9e8b1"
down_revision: Union[str, Sequence[str], None] = "922b17a3c6f4"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "dataset_insights",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("dataset_id", sa.Integer(), nullable=False),
        sa.Column("analysis_id", sa.Integer(), nullable=False),
        sa.Column("provider", sa.String(length=50), nullable=False),
        sa.Column("model", sa.String(length=100), nullable=True),
        sa.Column("summary", sa.Text(), nullable=False),
        sa.Column(
            "insights",
            sa.JSON().with_variant(postgresql.JSONB(astext_type=sa.Text()), "postgresql"),
            nullable=False,
        ),
        sa.Column(
            "recommendations",
            sa.JSON().with_variant(postgresql.JSONB(astext_type=sa.Text()), "postgresql"),
            nullable=False,
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["dataset_id"], ["datasets.id"]),
        sa.ForeignKeyConstraint(["analysis_id"], ["dataset_analyses.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_dataset_insights_dataset_id"), "dataset_insights", ["dataset_id"], unique=False)
    op.create_index(op.f("ix_dataset_insights_analysis_id"), "dataset_insights", ["analysis_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_dataset_insights_analysis_id"), table_name="dataset_insights")
    op.drop_index(op.f("ix_dataset_insights_dataset_id"), table_name="dataset_insights")
    op.drop_table("dataset_insights")