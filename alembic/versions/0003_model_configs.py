"""add model_configs table（G2 模型配置持久化；明文存储，API 不回传明文）。"""
from alembic import op
import sqlalchemy as sa

revision = "0003"
down_revision = "0002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "model_configs",
        sa.Column("kind", sa.String(32), primary_key=True),
        sa.Column("model", sa.String(128), nullable=True),
        sa.Column("api_url", sa.String(256), nullable=True),
        sa.Column("api_key", sa.String(512), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
    )


def downgrade() -> None:
    op.drop_table("model_configs")
