"""add novels table（小说 TXT 导入与改编来源）。"""
from alembic import op
import sqlalchemy as sa

revision = "0005"
down_revision = "0004"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "novels",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("filename", sa.String(256), nullable=True),
        sa.Column("title", sa.String(128), nullable=True),
        sa.Column("author", sa.String(128), nullable=True),
        sa.Column("chapters", sa.Integer(), nullable=True),
        sa.Column("char_count", sa.Integer(), nullable=True),
        sa.Column("encoding", sa.String(32), nullable=True),
        sa.Column("text", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
    )


def downgrade() -> None:
    op.drop_table("novels")
