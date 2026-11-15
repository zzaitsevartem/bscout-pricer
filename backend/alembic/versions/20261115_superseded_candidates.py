"""Preserve obsolete matcher proposals separately from human decisions."""

from alembic import op

revision = "20261115_superseded_candidates"
down_revision = "20261113_device_tracking"
branch_labels = None
depends_on = None


def upgrade():
    op.drop_constraint(
        op.f("ck_match_candidates_status_allowed"), "match_candidates", type_="check"
    )
    op.create_check_constraint(
        "status_allowed",
        "match_candidates",
        "status IN ('pending', 'approved', 'rejected', 'superseded')",
    )


def downgrade():
    op.execute("UPDATE match_candidates SET status = 'pending' WHERE status = 'superseded'")
    op.drop_constraint(
        op.f("ck_match_candidates_status_allowed"), "match_candidates", type_="check"
    )
    op.create_check_constraint(
        "status_allowed", "match_candidates", "status IN ('pending', 'approved', 'rejected')"
    )
