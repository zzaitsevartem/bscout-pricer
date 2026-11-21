import sqlalchemy as sa
from alembic import op

revision = "20261121_payment_periods"
down_revision = "20261115_superseded_candidates"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("payments", sa.Column("upgrade_days", sa.Integer(), nullable=True))
    op.execute("UPDATE subscriptions SET auto_renew = false WHERE auto_renew = true")


def downgrade() -> None:
    op.drop_column("payments", "upgrade_days")
