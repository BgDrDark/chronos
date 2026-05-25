"""Add company_id to shifts and unique constraint to work_schedules

Revision ID: shift_company_schedule_uc
Revises: ba_001_behavioral_analysis
Create Date: 2026-05-16

"""
import sqlalchemy as sa

from alembic import op

revision = "shift_company_schedule_uc"
down_revision = "ba_001_behavioral_analysis"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 1. Add company_id to shifts
    op.add_column("shifts",
        sa.Column("company_id", sa.Integer(), sa.ForeignKey("companies.id"), nullable=True))
    op.create_index("ix_shifts_company_id", "shifts", ["company_id"])

    # Assign existing shifts to first company
    op.execute("""
        UPDATE shifts SET company_id = (SELECT id FROM companies LIMIT 1)
        WHERE company_id IS NULL
    """)

    # 2. Add unique constraint to work_schedules (user_id, date)
    # First remove duplicates (keep latest by id)
    op.execute("""
        DELETE FROM work_schedules
        WHERE id NOT IN (
            SELECT MAX(id) FROM work_schedules
            GROUP BY user_id, date
        )
    """)
    op.create_unique_constraint("uq_user_date_schedule", "work_schedules", ["user_id", "date"])


def downgrade() -> None:
    op.drop_constraint("uq_user_date_schedule", "work_schedules", type_="unique")
    op.drop_index("ix_shifts_company_id", table_name="shifts")
    op.drop_column("shifts", "company_id")
