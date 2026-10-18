"""add subtitle_tracks table（字幕与本地化）。"""
from alembic import op
import sqlalchemy as sa

revision = "0009"
down_revision = "0008"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "subtitle_tracks",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("project_id", sa.Integer(), nullable=False),
        sa.Column("episode_id", sa.Integer(), nullable=False),
        sa.Column("language", sa.String(16), nullable=False),
        sa.Column("source_language", sa.String(16), nullable=True),
        sa.Column("status", sa.String(16), nullable=True),
        sa.Column("cues", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.UniqueConstraint("project_id", "episode_id", "language",
                            name="uq_subtitle_track"),
    )
    op.create_index("ix_subtitles_project", "subtitle_tracks", ["project_id"])


def downgrade() -> None:
    op.drop_index("ix_subtitles_project", table_name="subtitle_tracks")
    op.drop_table("subtitle_tracks")
