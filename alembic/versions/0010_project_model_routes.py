"""add project_model_routes table（项目级模型路由）。"""
from alembic import op
import sqlalchemy as sa

revision = "0010"
down_revision = "0009"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "project_model_routes",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("project_id", sa.Integer(), nullable=False),
        sa.Column("kind", sa.String(16), nullable=False),
        sa.Column("model", sa.String(128), nullable=True),
        sa.Column("api_url", sa.String(256), nullable=True),
        sa.Column("enabled", sa.Boolean(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.UniqueConstraint("project_id", "kind", name="uq_project_model_kind"),
    )
    op.create_index("ix_project_model_project", "project_model_routes", ["project_id"])


def downgrade() -> None:
    op.drop_index("ix_project_model_project", table_name="project_model_routes")
    op.drop_table("project_model_routes")
