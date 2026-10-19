"""Add canonical source record fields to events."""

from alembic import op
import sqlalchemy as sa


revision = "20260615_source_record_fields"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("events", sa.Column("end_date", sa.DateTime(), nullable=True))
    op.add_column("events", sa.Column("duration", sa.Unicode(length=128), nullable=True))
    op.add_column("events", sa.Column("source_key", sa.UnicodeText(), nullable=True))
    op.create_index("ix_events_source_key", "events", ["source_key"])


def downgrade():
    op.drop_index("ix_events_source_key", table_name="events")
    op.drop_column("events", "source_key")
    op.drop_column("events", "duration")
    op.drop_column("events", "end_date")