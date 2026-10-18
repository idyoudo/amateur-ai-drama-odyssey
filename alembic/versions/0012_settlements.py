"""add settlements table（商业化结算台账）。"""
from alembic import op
import sqlalchemy as sa

revision = "0012"
down_revision = "0011"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "settlements",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("project_id", sa.Integer(), nullable=False),
        sa.Column("channel_key", sa.String(32), nullable=False),
        sa.Column("channel_name", sa.String(64), nullable=False),
        sa.Column("revenue_type", sa.String(16), nullable=True),
        sa.Column("amount", sa.Float(), nullable=True),
        sa.Column("currency", sa.String(8), nullable=True),
        sa.Column("period", sa.String(7), nullable=True),
        sa.Column("note", sa.String(512), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
    )
    op.create_index("ix_settlements_project", "settlements", ["project_id"])
    op.create_index("ix_settlements_channel", "settlements", ["channel_key"])


def downgrade() -> None:
    op.drop_index("ix_settlements_channel", table_name="settlements")
    op.drop_index("ix_settlements_project", table_name="settlements")
    op.drop_table("settlements")
