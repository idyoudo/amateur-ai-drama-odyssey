"""add projects table（M1 立项）。"""
from alembic import op
import sqlalchemy as sa

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "projects",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("title", sa.String(128), nullable=False),
        sa.Column("logline", sa.String(512), nullable=False),
        sa.Column("platform", sa.String(64), nullable=True),
        sa.Column("rating", sa.String(16), nullable=True),
        sa.Column("genre", sa.String(64), nullable=True),
        sa.Column("style", sa.String(32), nullable=True),
        sa.Column("episodes", sa.Integer(), nullable=True),
        sa.Column("minutes", sa.Integer(), nullable=True),
        sa.Column("delivery_spec", sa.JSON(), nullable=True),
        sa.Column("pilot_mode", sa.Boolean(), nullable=True),
        sa.Column("status", sa.String(32), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
    )


def downgrade() -> None:
    op.drop_table("projects")
