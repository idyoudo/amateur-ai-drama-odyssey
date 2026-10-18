"""add hit analysis fields（summary/score/grade/analysis_meta）。"""
from alembic import op
import sqlalchemy as sa

revision = "0015"
down_revision = "0014"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("hit_cases", sa.Column("summary", sa.String(4000), nullable=True))
    op.add_column("hit_cases", sa.Column("score", sa.Integer(), nullable=True))
    op.add_column("hit_cases", sa.Column("grade", sa.String(4), nullable=True))
    op.add_column("hit_cases", sa.Column("analysis_meta", sa.JSON(), nullable=True))


def downgrade() -> None:
    op.drop_column("hit_cases", "analysis_meta")
    op.drop_column("hit_cases", "grade")
    op.drop_column("hit_cases", "score")
    op.drop_column("hit_cases", "summary")
