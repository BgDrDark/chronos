"""Add Enhanced Payroll System

Revision ID: enhanced_payroll_system
Revises: google_calendar_integration
Create Date: 2026-02-05 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers
revision = 'enhanced_payroll_system'
down_revision = 'google_calendar_integration'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create payroll_payment_schedules table
    op.create_table('payroll_payment_schedules',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('company_id', sa.Integer(), nullable=False),
        sa.Column('payment_day', sa.Integer(), nullable=False),
        sa.Column('payment_month_offset', sa.Integer(), nullable=True),
        sa.Column('active', sa.Boolean(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['company_id'], ['companies.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_payroll_payment_schedules_id'), 'payroll_payment_schedules', ['id'], unique=False)
    
    # Create payroll_deductions table
    op.create_table('payroll_deductions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('company_id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('deduction_type', sa.String(length=50), nullable=False),
        sa.Column('amount', sa.Numeric(precision=10, scale=2), nullable=True),
        sa.Column('percentage', sa.Numeric(precision=5, scale=2), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True),
        sa.Column('apply_to_all', sa.Boolean(), nullable=True),
        sa.Column('employee_ids', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['company_id'], ['companies.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_payroll_deductions_id'), 'payroll_deductions', ['id'], unique=False)
    
    # Create sick_leave_records table
    op.create_table('sick_leave_records',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('start_date', sa.Date(), nullable=False),
        sa.Column('end_date', sa.Date(), nullable=False),
        sa.Column('sick_leave_type', sa.String(length=50), nullable=False),
        sa.Column('is_paid_by_noi', sa.Boolean(), nullable=True),
        sa.Column('employer_payment_percentage', sa.Numeric(precision=5, scale=2), nullable=True),
        sa.Column('daily_amount', sa.Numeric(precision=10, scale=2), nullable=True),
        sa.Column('total_days', sa.Integer(), nullable=False),
        sa.Column('noi_payment_days', sa.Integer(), nullable=True),
        sa.Column('employer_payment_days', sa.Integer(), nullable=True),
        sa.Column('medical_document_number', sa.String(length=100), nullable=True),
        sa.Column('status', sa.String(length=20), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_sick_leave_records_id'), 'sick_leave_records', ['id'], unique=False)
    op.create_index('ix_sick_leave_records_dates', 'sick_leave_records', ['user_id', 'start_date', 'end_date'], unique=False)
    
    # Create noi_payment_days table
    op.create_table('noi_payment_days',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('year', sa.Integer(), nullable=False),
        sa.Column('total_noi_days_available', sa.Integer(), nullable=True),
        sa.Column('noi_days_used', sa.Integer(), nullable=True),
        sa.Column('noi_days_remaining', sa.Integer(), nullable=False),
        sa.Column('employer_payment_percentage', sa.Numeric(precision=5, scale=2), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id', 'year')
    )
    op.create_index(op.f('ix_noi_payment_days_id'), 'noi_payment_days', ['id'], unique=False)
    
    # Create employment_contracts table
    op.create_table('employment_contracts',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('company_id', sa.Integer(), nullable=False),
        sa.Column('contract_type', sa.String(length=50), nullable=False),
        sa.Column('start_date', sa.Date(), nullable=False),
        sa.Column('end_date', sa.Date(), nullable=True),
        sa.Column('base_salary', sa.Numeric(precision=10, scale=2), nullable=True),
        sa.Column('work_hours_per_week', sa.Integer(), nullable=True),
        sa.Column('probation_months', sa.Integer(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True),
        sa.Column('salary_calculation_type', sa.String(length=20), nullable=True),
        sa.Column('tax_resident', sa.Boolean(), nullable=True),
        sa.Column('insurance_contributor', sa.Boolean(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['company_id'], ['companies.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_employment_contracts_id'), 'employment_contracts', ['id'], unique=False)
    
    # Create payroll_periods table
    op.create_table('payroll_periods',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('company_id', sa.Integer(), nullable=False),
        sa.Column('start_date', sa.Date(), nullable=False),
        sa.Column('end_date', sa.Date(), nullable=False),
        sa.Column('status', sa.String(length=20), nullable=True),
        sa.Column('processing_date', sa.DateTime(), nullable=True),
        sa.Column('payment_date', sa.Date(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['company_id'], ['companies.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_payroll_periods_id'), 'payroll_periods', ['id'], unique=False)
    
    # Create payments table
    op.create_table('payments',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('payslip_id', sa.Integer(), nullable=False),
        sa.Column('amount', sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column('payment_date', sa.DateTime(), nullable=True),
        sa.Column('payment_method', sa.String(length=50), nullable=True),
        sa.Column('status', sa.String(length=20), nullable=True),
        sa.Column('reference', sa.String(length=255), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['payslip_id'], ['payslips.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_payments_id'), 'payments', ['id'], unique=False)


def downgrade() -> None:
    # Drop Enhanced Payroll tables
    op.drop_index(op.f('ix_payments_id'), table_name='payments')
    op.drop_table('payments')
    
    op.drop_index(op.f('ix_payroll_periods_id'), table_name='payroll_periods')
    op.drop_table('payroll_periods')
    
    op.drop_index(op.f('ix_employment_contracts_id'), table_name='employment_contracts')
    op.drop_table('employment_contracts')
    
    op.drop_index(op.f('ix_noi_payment_days_id'), table_name='noi_payment_days')
    op.drop_index('ix_sick_leave_records_dates', table_name='sick_leave_records')
    op.drop_index(op.f('ix_sick_leave_records_id'), table_name='sick_leave_records')
    op.drop_table('noi_payment_days')
    
    op.drop_index('ix_sick_leave_records_dates', table_name='sick_leave_records')
    op.drop_index(op.f('ix_sick_leave_records_id'), table_name='sick_leave_records')
    op.drop_table('sick_leave_records')
    
    op.drop_index(op.f('ix_payroll_deductions_id'), table_name='payroll_deductions')
    op.drop_table('payroll_deductions')
    
    op.drop_index(op.f('ix_payroll_payment_schedules_id'), table_name='payroll_payment_schedules')
    op.drop_table('payroll_payment_schedules')