"""add reviews table（审核/协作中心）。"""
from alembic import op
import sqlalchemy as sa

revision = "0008"
down_revision = "0007"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "reviews",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("project_id", sa.Integer(), nullable=False),
        sa.Column("target_type", sa.String(16), nullable=True),
        sa.Column("target_ref", sa.String(64), nullable=True),
        sa.Column("title", sa.String(128), nullable=False),
        sa.Column("status", sa.String(16), nullable=True),
        sa.Column("reviewer", sa.String(64), nullable=True),
        sa.Column("comment", sa.String(1024), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
    )
    op.create_index("ix_reviews_project", "reviews", ["project_id"])


def downgrade() -> None:
    op.drop_index("ix_reviews_project", table_name="reviews")
    op.drop_table("reviews")
