"""model providers：同一模型类型多提供商 + 单一生效。"""
from alembic import op
import sqlalchemy as sa

revision = "0016"
down_revision = "0015"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "model_providers",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("kind", sa.String(32), nullable=False),
        sa.Column("name", sa.String(64), nullable=False),
        sa.Column("model", sa.String(128), nullable=True),
        sa.Column("api_url", sa.String(256), nullable=True),
        sa.Column("api_key", sa.String(512), nullable=True),
        sa.Column("active", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.UniqueConstraint("kind", "name", name="uq_model_provider_name"),
    )
    op.create_index("ix_model_provider_kind", "model_providers", ["kind"])
    conn = op.get_bind()
    rows = conn.execute(sa.text(
        "SELECT kind, model, api_url, api_key FROM model_configs")).fetchall()
    for kind, model, api_url, api_key in rows:
        if not (model or api_url or api_key):
            continue
        conn.execute(sa.text(
            "INSERT INTO model_providers (kind, name, model, api_url, api_key, active) "
            "VALUES (:kind, :name, :model, :api_url, :api_key, :active)"),
            {"kind": kind, "name": "默认配置", "model": model or "",
             "api_url": api_url or "", "api_key": api_key or "", "active": True})


def downgrade() -> None:
    op.drop_index("ix_model_provider_kind", table_name="model_providers")
    op.drop_table("model_providers")
