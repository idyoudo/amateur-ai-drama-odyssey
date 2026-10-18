"""add hit_cases table（爆款案例库）。"""
from alembic import op
import sqlalchemy as sa

revision = "0014"
down_revision = "0013"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "hit_cases",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("title", sa.String(128), nullable=False),
        sa.Column("platform", sa.String(64), nullable=True),
        sa.Column("genre", sa.String(64), nullable=True),
        sa.Column("heat_note", sa.String(512), nullable=True),
        sa.Column("play_count", sa.Integer(), nullable=True),
        sa.Column("verified", sa.Boolean(), nullable=True),
        sa.Column("formula", sa.String(32), nullable=True),
        sa.Column("hook_type", sa.String(32), nullable=True),
        sa.Column("cliffhanger_type", sa.String(32), nullable=True),
        sa.Column("structure", sa.JSON(), nullable=True),
        sa.Column("visual", sa.String(512), nullable=True),
        sa.Column("why_text", sa.String(1024), nullable=True),
        sa.Column("source_note", sa.String(512), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
    )


def downgrade() -> None:
    op.drop_table("hit_cases")
