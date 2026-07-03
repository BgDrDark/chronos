"""restore FK floor_plan_doors.door_id -> access_doors.id

Revision ID: a1b2c3d4e5f6
Revises: 88fdfb1a06ff
Create Date: 2026-07-02 23:30:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "0b4ffe30ad6f"
down_revision: Union[str, None] = "88fdfb1a06ff"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_foreign_key(
        "fk_floor_plan_doors_door_id_access_doors",
        "floor_plan_doors",
        "access_doors",
        ["door_id"],
        ["id"],
    )


def downgrade() -> None:
    op.drop_constraint(
        "fk_floor_plan_doors_door_id_access_doors",
        "floor_plan_doors",
        type_="foreignkey",
    )
