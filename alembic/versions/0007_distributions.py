"""add distributions table（分发中心）。"""
from alembic import op
import sqlalchemy as sa

revision = "0007"
down_revision = "0006"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "distributions",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("project_id", sa.Integer(), nullable=False),
        sa.Column("channel_key", sa.String(32), nullable=False),
        sa.Column("channel_name", sa.String(64), nullable=False),
        sa.Column("status", sa.String(16), nullable=True),
        sa.Column("scheduled_at", sa.DateTime(), nullable=True),
        sa.Column("published_at", sa.DateTime(), nullable=True),
        sa.Column("external_url", sa.String(512), nullable=True),
        sa.Column("metrics", sa.JSON(), nullable=True),
        sa.Column("note", sa.String(512), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
    )
    op.create_index("ix_distributions_project", "distributions", ["project_id"])
    op.create_index("ix_distributions_channel", "distributions", ["channel_key"])


def downgrade() -> None:
    op.drop_index("ix_distributions_channel", table_name="distributions")
    op.drop_index("ix_distributions_project", table_name="distributions")
    op.drop_table("distributions")
