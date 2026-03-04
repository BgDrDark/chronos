"""add_company_details

Revision ID: c6f40e20fe4e
Revises: b2143731f014
Create Date: 2026-02-08 23:48:40.614134

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c6f40e20fe4e'
down_revision: Union[str, Sequence[str], None] = 'b2143731f014'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('companies', sa.Column('eik', sa.String(), nullable=True))
    op.create_index(op.f('ix_companies_eik'), 'companies', ['eik'], unique=True)
    op.add_column('companies', sa.Column('bulstat', sa.String(), nullable=True))
    op.create_index(op.f('ix_companies_bulstat'), 'companies', ['bulstat'], unique=True)
    op.add_column('companies', sa.Column('vat_number', sa.String(), nullable=True))
    op.create_index(op.f('ix_companies_vat_number'), 'companies', ['vat_number'], unique=True)
    op.add_column('companies', sa.Column('address', sa.String(), nullable=True))
    op.add_column('companies', sa.Column('mol_name', sa.String(), nullable=True))


def downgrade() -> None:
    op.drop_column('companies', 'mol_name')
    op.drop_column('companies', 'address')
    op.drop_index(op.f('ix_companies_vat_number'), table_name='companies')
    op.drop_column('companies', 'vat_number')
    op.drop_index(op.f('ix_companies_bulstat'), table_name='companies')
    op.drop_column('companies', 'bulstat')
    op.drop_index(op.f('ix_companies_eik'), table_name='companies')
    op.drop_column('companies', 'eik')
