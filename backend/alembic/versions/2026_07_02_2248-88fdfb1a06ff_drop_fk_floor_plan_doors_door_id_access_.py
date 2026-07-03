"""drop FK floor_plan_doors.door_id -> access_doors.id

Revision ID: 88fdfb1a06ff
Revises: de4ab07c6a35
Create Date: 2026-07-02 22:48:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "88fdfb1a06ff"
down_revision: Union[str, None] = "de4ab07c6a35"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.drop_constraint(
        "fk_floor_plan_doors_door_id_access_doors",
        "floor_plan_doors",
        type_="foreignkey",
    )


def downgrade() -> None:
    op.create_foreign_key(
        "fk_floor_plan_doors_door_id_access_doors",
        "floor_plan_doors",
        "access_doors",
        ["door_id"],
        ["id"],
    )
