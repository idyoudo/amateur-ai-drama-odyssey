"""initial schema: jobs / intents / outbox（对齐 film/jobs/db.py 模型）。"""
from alembic import op
import sqlalchemy as sa

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "jobs",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("project_id", sa.String(64), nullable=False),
        sa.Column("episode_id", sa.Integer(), nullable=True),
        sa.Column("shot_id", sa.Integer(), nullable=True),
        sa.Column("type", sa.String(32), nullable=False),
        sa.Column("status", sa.String(32), nullable=False),
        sa.Column("progress", sa.Integer(), nullable=True),
        sa.Column("error_code", sa.String(64), nullable=True),
        sa.Column("error_class", sa.String(32), nullable=True),
        sa.Column("attempts", sa.Integer(), nullable=True),
        sa.Column("attempt_limit", sa.Integer(), nullable=True),
        sa.Column("available_at", sa.Integer(), nullable=True),
        sa.Column("locked_until", sa.Integer(), nullable=True),
        sa.Column("lease_epoch", sa.Integer(), nullable=True),
        sa.Column("priority", sa.Integer(), nullable=True),
        sa.Column("idempotency_key", sa.String(512), nullable=False),
        sa.Column("provider_task_id", sa.String(128), nullable=True),
        sa.Column("checkpoint", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.UniqueConstraint("project_id", "idempotency_key", name="uq_jobs_idem"),
    )
    op.create_index("ix_jobs_status_available", "jobs", ["status", "available_at"])

    op.create_table(
        "intents",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("job_id", sa.Integer(), nullable=False),
        sa.Column("provider", sa.String(64), nullable=False),
        sa.Column("fingerprint", sa.String(64), nullable=False),
        sa.Column("client_op_id", sa.String(128), nullable=True),
        sa.Column("request_id", sa.String(128), nullable=False),
        sa.Column("payload_frozen", sa.JSON(), nullable=True),
        sa.Column("status", sa.String(32), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
    )

    op.create_table(
        "outbox",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("job_id", sa.Integer(), nullable=True),
        sa.Column("topic", sa.String(64), nullable=False),
        sa.Column("payload", sa.JSON(), nullable=True),
        sa.Column("idempotency_key", sa.String(512), nullable=False),
        sa.Column("version", sa.Integer(), nullable=True),
        sa.Column("status", sa.String(32), nullable=False),
        sa.Column("attempt_count", sa.Integer(), nullable=True),
        sa.Column("next_attempt_at", sa.DateTime(), nullable=True),
        sa.Column("claimed_at", sa.DateTime(), nullable=True),
        sa.Column("sent_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.UniqueConstraint("idempotency_key", name="uq_outbox_idem"),
    )


def downgrade() -> None:
    op.drop_table("outbox")
    op.drop_table("intents")
    op.drop_index("ix_jobs_status_available", table_name="jobs")
    op.drop_table("jobs")
