"""add logistics and fleet modules

Revision ID: add_logistics_fleet_modules
Revises: 9d439ebc0ec1
Create Date: 2026-03-10 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'add_logistics_fleet_modules'
down_revision: Union[str, Sequence[str], None] = '9d439ebc0ec1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    
    # ==================== SUPPLIER UPDATES ====================
    # Add new columns to existing suppliers table
    op.add_column('suppliers', sa.Column('mol', sa.String(length=255), nullable=True))
    op.add_column('suppliers', sa.Column('is_active', sa.Boolean(), nullable=True, server_default='true'))
    op.add_column('suppliers', sa.Column('notes', sa.Text(), nullable=True))
    op.add_column('suppliers', sa.Column('created_at', sa.DateTime(), nullable=True))
    op.add_column('suppliers', sa.Column('updated_at', sa.DateTime(), nullable=True))
    
    # ==================== INGREDIENT AUTO-REORDER ====================
    op.add_column('ingredients', sa.Column('min_quantity', sa.Numeric(precision=12, scale=3), nullable=True))
    op.add_column('ingredients', sa.Column('reorder_quantity', sa.Numeric(precision=12, scale=3), nullable=True))
    op.add_column('ingredients', sa.Column('is_auto_reorder', sa.Boolean(), nullable=True, server_default='false'))
    op.add_column('ingredients', sa.Column('preferred_supplier_id', sa.Integer(), nullable=True))
    op.create_foreign_key('fk_ingredient_preferred_supplier', 'ingredients', 'suppliers', ['preferred_supplier_id'], ['id'])

    # ==================== LOGISTICS MODELS ====================
    
    # Request Templates
    op.create_table('request_templates',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('items', sa.JSON(), nullable=True),
        sa.Column('default_department_id', sa.Integer(), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('company_id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['company_id'], ['companies.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['default_department_id'], ['departments.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_request_templates_id'), 'request_templates', ['id'], unique=False)
    
    # Purchase Requests
    op.create_table('purchase_requests',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('request_number', sa.String(length=50), nullable=False),
        sa.Column('requested_by_id', sa.Integer(), nullable=False),
        sa.Column('department_id', sa.Integer(), nullable=True),
        sa.Column('status', sa.String(length=20), nullable=True, server_default='draft'),
        sa.Column('priority', sa.String(length=20), nullable=True, server_default='medium'),
        sa.Column('reason', sa.Text(), nullable=True),
        sa.Column('due_date', sa.Date(), nullable=True),
        sa.Column('approved_by_id', sa.Integer(), nullable=True),
        sa.Column('approved_at', sa.DateTime(), nullable=True),
        sa.Column('is_auto', sa.Boolean(), nullable=True, server_default='false'),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('company_id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['company_id'], ['companies.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['requested_by_id'], ['users.id'], ),
        sa.ForeignKeyConstraint(['department_id'], ['departments.id'], ),
        sa.ForeignKeyConstraint(['approved_by_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('request_number')
    )
    op.create_index(op.f('ix_purchase_requests_id'), 'purchase_requests', ['id'], unique=False)
    op.create_index(op.f('ix_purchase_requests_request_number'), 'purchase_requests', ['request_number'], unique=True)
    
    # Purchase Request Items
    op.create_table('purchase_request_items',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('purchase_request_id', sa.Integer(), nullable=False),
        sa.Column('item_name', sa.String(length=255), nullable=False),
        sa.Column('quantity', sa.Numeric(precision=12, scale=3), nullable=False),
        sa.Column('unit', sa.String(length=20), nullable=True),
        sa.Column('notes', sa.String(length=500), nullable=True),
        sa.ForeignKeyConstraint(['purchase_request_id'], ['purchase_requests.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_purchase_request_items_id'), 'purchase_request_items', ['id'], unique=False)
    
    # Purchase Request Approvals
    op.create_table('purchase_request_approvals',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('request_id', sa.Integer(), nullable=False),
        sa.Column('action', sa.String(length=20), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('action_date', sa.DateTime(), nullable=True),
        sa.Column('reason', sa.Text(), nullable=True),
        sa.Column('is_auto', sa.Boolean(), nullable=True, server_default='false'),
        sa.ForeignKeyConstraint(['request_id'], ['purchase_requests.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_purchase_request_approvals_id'), 'purchase_request_approvals', ['id'], unique=False)
    
    # Purchase Request History
    op.create_table('purchase_request_history',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('request_id', sa.Integer(), nullable=False),
        sa.Column('field_name', sa.String(length=100), nullable=False),
        sa.Column('old_value', sa.Text(), nullable=True),
        sa.Column('new_value', sa.Text(), nullable=True),
        sa.Column('changed_by_id', sa.Integer(), nullable=False),
        sa.Column('changed_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['request_id'], ['purchase_requests.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['changed_by_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_purchase_request_history_id'), 'purchase_request_history', ['id'], unique=False)
    
    # Purchase Orders
    op.create_table('purchase_orders',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('order_number', sa.String(length=50), nullable=False),
        sa.Column('supplier_id', sa.Integer(), nullable=False),
        sa.Column('purchase_request_id', sa.Integer(), nullable=True),
        sa.Column('status', sa.String(length=20), nullable=True, server_default='draft'),
        sa.Column('order_date', sa.Date(), nullable=True),
        sa.Column('expected_date', sa.Date(), nullable=True),
        sa.Column('received_date', sa.Date(), nullable=True),
        sa.Column('total_amount', sa.Numeric(precision=12, scale=2), nullable=True, server_default='0'),
        sa.Column('vat_amount', sa.Numeric(precision=12, scale=2), nullable=True, server_default='0'),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('company_id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['company_id'], ['companies.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['supplier_id'], ['suppliers.id'], ),
        sa.ForeignKeyConstraint(['purchase_request_id'], ['purchase_requests.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('order_number')
    )
    op.create_index(op.f('ix_purchase_orders_id'), 'purchase_orders', ['id'], unique=False)
    op.create_index(op.f('ix_purchase_orders_order_number'), 'purchase_orders', ['order_number'], unique=True)
    
    # Purchase Order Items
    op.create_table('purchase_order_items',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('purchase_order_id', sa.Integer(), nullable=False),
        sa.Column('item_name', sa.String(length=255), nullable=False),
        sa.Column('quantity', sa.Numeric(precision=12, scale=3), nullable=False),
        sa.Column('received_quantity', sa.Numeric(precision=12, scale=3), nullable=True, server_default='0'),
        sa.Column('unit_price', sa.Numeric(precision=12, scale=2), nullable=True, server_default='0'),
        sa.Column('vat_rate', sa.Numeric(precision=5, scale=2), nullable=True, server_default='20'),
        sa.Column('unit', sa.String(length=20), nullable=True),
        sa.ForeignKeyConstraint(['purchase_order_id'], ['purchase_orders.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_purchase_order_items_id'), 'purchase_order_items', ['id'], unique=False)
    
    # ==================== FLEET MODELS ====================
    
    # Vehicle Types
    op.create_table('vehicle_types',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('code', sa.String(length=20), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_vehicle_types_id'), 'vehicle_types', ['id'], unique=False)
    
    # Vehicles
    op.create_table('vehicles',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('registration_number', sa.String(length=20), nullable=False),
        sa.Column('vin', sa.String(length=50), nullable=True),
        sa.Column('make', sa.String(length=100), nullable=False),
        sa.Column('model', sa.String(length=100), nullable=False),
        sa.Column('year', sa.Integer(), nullable=True),
        sa.Column('vehicle_type_id', sa.Integer(), nullable=True),
        sa.Column('fuel_type', sa.String(length=20), nullable=True, server_default='dizel'),
        sa.Column('engine_number', sa.String(length=100), nullable=True),
        sa.Column('chassis_number', sa.String(length=100), nullable=True),
        sa.Column('color', sa.String(length=50), nullable=True),
        sa.Column('initial_mileage', sa.Integer(), nullable=True, server_default='0'),
        sa.Column('is_company', sa.Boolean(), nullable=True, server_default='true'),
        sa.Column('owner_name', sa.String(length=255), nullable=True),
        sa.Column('status', sa.String(length=20), nullable=True, server_default='active'),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('company_id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['company_id'], ['companies.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['vehicle_type_id'], ['vehicle_types.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('registration_number')
    )
    op.create_index(op.f('ix_vehicles_id'), 'vehicles', ['id'], unique=False)
    op.create_index(op.f('ix_vehicles_registration_number'), 'vehicles', ['registration_number'], unique=True)
    
    # Vehicle Documents
    op.create_table('vehicle_documents',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('vehicle_id', sa.Integer(), nullable=False),
        sa.Column('document_type', sa.String(length=20), nullable=False),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('file_url', sa.String(length=500), nullable=True),
        sa.Column('issue_date', sa.Date(), nullable=True),
        sa.Column('expiry_date', sa.Date(), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['vehicle_id'], ['vehicles.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_vehicle_documents_id'), 'vehicle_documents', ['id'], unique=False)
    
    # Vehicle Fuel Cards
    op.create_table('vehicle_fuel_cards',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('vehicle_id', sa.Integer(), nullable=False),
        sa.Column('card_number', sa.String(length=50), nullable=False),
        sa.Column('provider', sa.String(length=255), nullable=True),
        sa.Column('pin', sa.String(length=10), nullable=True),
        sa.Column('limit', sa.Numeric(precision=12, scale=2), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True, server_default='true'),
        sa.Column('expiry_date', sa.Date(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['vehicle_id'], ['vehicles.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_vehicle_fuel_cards_id'), 'vehicle_fuel_cards', ['id'], unique=False)
    
    # Vehicle Vignettes
    op.create_table('vehicle_vignettes',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('vehicle_id', sa.Integer(), nullable=False),
        sa.Column('vignette_type', sa.String(length=20), nullable=False),
        sa.Column('purchase_date', sa.Date(), nullable=True),
        sa.Column('valid_from', sa.Date(), nullable=True),
        sa.Column('valid_until', sa.Date(), nullable=True),
        sa.Column('price', sa.Numeric(precision=12, scale=2), nullable=True),
        sa.Column('provider', sa.String(length=255), nullable=True),
        sa.Column('document_url', sa.String(length=500), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['vehicle_id'], ['vehicles.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_vehicle_vignettes_id'), 'vehicle_vignettes', ['id'], unique=False)
    
    # Vehicle Tolls
    op.create_table('vehicle_tolls',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('vehicle_id', sa.Integer(), nullable=False),
        sa.Column('route', sa.String(length=255), nullable=True),
        sa.Column('toll_amount', sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column('toll_date', sa.DateTime(), nullable=True),
        sa.Column('section', sa.String(length=100), nullable=True),
        sa.Column('document_url', sa.String(length=500), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['vehicle_id'], ['vehicles.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_vehicle_tolls_id'), 'vehicle_tolls', ['id'], unique=False)
    
    # Vehicle Mileage
    op.create_table('vehicle_mileage',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('vehicle_id', sa.Integer(), nullable=False),
        sa.Column('date', sa.Date(), nullable=False),
        sa.Column('mileage', sa.Integer(), nullable=False),
        sa.Column('source', sa.String(length=20), nullable=True, server_default='manual'),
        sa.Column('notes', sa.String(length=500), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['vehicle_id'], ['vehicles.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_vehicle_mileage_id'), 'vehicle_mileage', ['id'], unique=False)
    
    # Vehicle Fuel
    op.create_table('vehicle_fuel',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('vehicle_id', sa.Integer(), nullable=False),
        sa.Column('date', sa.DateTime(), nullable=False),
        sa.Column('fuel_type', sa.String(length=20), nullable=True),
        sa.Column('quantity', sa.Numeric(precision=12, scale=3), nullable=False),
        sa.Column('price_per_liter', sa.Numeric(precision=12, scale=4), nullable=False),
        sa.Column('total_amount', sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column('mileage', sa.Integer(), nullable=True),
        sa.Column('location', sa.String(length=255), nullable=True),
        sa.Column('invoice_number', sa.String(length=50), nullable=True),
        sa.Column('fuel_card_id', sa.Integer(), nullable=True),
        sa.Column('driver_id', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['vehicle_id'], ['vehicles.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['fuel_card_id'], ['vehicle_fuel_cards.id'], ),
        sa.ForeignKeyConstraint(['driver_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_vehicle_fuel_id'), 'vehicle_fuel', ['id'], unique=False)
    
    # Vehicle Services
    op.create_table('vehicle_services',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('address', sa.String(length=500), nullable=True),
        sa.Column('phone', sa.String(length=50), nullable=True),
        sa.Column('email', sa.String(length=255), nullable=True),
        sa.Column('contact_person', sa.String(length=255), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_vehicle_services_id'), 'vehicle_services', ['id'], unique=False)
    
    # Vehicle Repairs
    op.create_table('vehicle_repairs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('vehicle_id', sa.Integer(), nullable=False),
        sa.Column('repair_date', sa.DateTime(), nullable=False),
        sa.Column('repair_type', sa.String(length=20), nullable=True, server_default='unscheduled'),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('parts', sa.JSON(), nullable=True),
        sa.Column('labor_hours', sa.Numeric(precision=8, scale=2), nullable=True),
        sa.Column('labor_cost', sa.Numeric(precision=12, scale=2), nullable=True, server_default='0'),
        sa.Column('parts_cost', sa.Numeric(precision=12, scale=2), nullable=True, server_default='0'),
        sa.Column('total_cost', sa.Numeric(precision=12, scale=2), nullable=True, server_default='0'),
        sa.Column('mileage', sa.Integer(), nullable=True),
        sa.Column('vehicle_service_id', sa.Integer(), nullable=True),
        sa.Column('warranty_months', sa.Integer(), nullable=True),
        sa.Column('next_service_km', sa.Integer(), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['vehicle_id'], ['vehicles.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['vehicle_service_id'], ['vehicle_services.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_vehicle_repairs_id'), 'vehicle_repairs', ['id'], unique=False)
    
    # Vehicle Schedules
    op.create_table('vehicle_schedules',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('vehicle_id', sa.Integer(), nullable=False),
        sa.Column('schedule_type', sa.String(length=20), nullable=False),
        sa.Column('interval_km', sa.Integer(), nullable=True),
        sa.Column('interval_months', sa.Integer(), nullable=True),
        sa.Column('last_service_date', sa.Date(), nullable=True),
        sa.Column('last_service_km', sa.Integer(), nullable=True),
        sa.Column('next_service_date', sa.Date(), nullable=True),
        sa.Column('next_service_km', sa.Integer(), nullable=True),
        sa.Column('vehicle_service_id', sa.Integer(), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['vehicle_id'], ['vehicles.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['vehicle_service_id'], ['vehicle_services.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_vehicle_schedules_id'), 'vehicle_schedules', ['id'], unique=False)
    
    # Vehicle Insurances
    op.create_table('vehicle_insurances',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('vehicle_id', sa.Integer(), nullable=False),
        sa.Column('insurance_type', sa.String(length=20), nullable=False),
        sa.Column('policy_number', sa.String(length=50), nullable=False),
        sa.Column('insurance_company', sa.String(length=255), nullable=True),
        sa.Column('start_date', sa.Date(), nullable=False),
        sa.Column('end_date', sa.Date(), nullable=False),
        sa.Column('premium', sa.Numeric(precision=12, scale=2), nullable=True),
        sa.Column('coverage_amount', sa.Numeric(precision=12, scale=2), nullable=True),
        sa.Column('payment_type', sa.String(length=20), nullable=True, server_default='annual'),
        sa.Column('document_url', sa.String(length=500), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['vehicle_id'], ['vehicles.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_vehicle_insurances_id'), 'vehicle_insurances', ['id'], unique=False)
    
    # Vehicle Inspections (GTP)
    op.create_table('vehicle_inspections',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('vehicle_id', sa.Integer(), nullable=False),
        sa.Column('inspection_date', sa.Date(), nullable=False),
        sa.Column('valid_until', sa.Date(), nullable=False),
        sa.Column('result', sa.String(length=20), nullable=True, server_default='pending'),
        sa.Column('mileage', sa.Integer(), nullable=True),
        sa.Column('inspector', sa.String(length=255), nullable=True),
        sa.Column('certificate_number', sa.String(length=50), nullable=True),
        sa.Column('next_inspection_date', sa.Date(), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['vehicle_id'], ['vehicles.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_vehicle_inspections_id'), 'vehicle_inspections', ['id'], unique=False)
    
    # Vehicle Pre-Trip Inspections
    op.create_table('vehicle_pretrip_inspections',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('vehicle_id', sa.Integer(), nullable=False),
        sa.Column('driver_id', sa.Integer(), nullable=False),
        sa.Column('inspection_date', sa.DateTime(), nullable=True),
        sa.Column('tires_condition', sa.Boolean(), nullable=True, server_default='false'),
        sa.Column('tires_pressure', sa.Boolean(), nullable=True, server_default='false'),
        sa.Column('tires_tread', sa.Boolean(), nullable=True, server_default='false'),
        sa.Column('brakes_condition', sa.Boolean(), nullable=True, server_default='false'),
        sa.Column('brakes_parking', sa.Boolean(), nullable=True, server_default='false'),
        sa.Column('lights_headlights', sa.Boolean(), nullable=True, server_default='false'),
        sa.Column('lights_brake', sa.Boolean(), nullable=True, server_default='false'),
        sa.Column('lights_turn', sa.Boolean(), nullable=True, server_default='false'),
        sa.Column('lights_warning', sa.Boolean(), nullable=True, server_default='false'),
        sa.Column('fluids_oil', sa.Boolean(), nullable=True, server_default='false'),
        sa.Column('fluids_coolant', sa.Boolean(), nullable=True, server_default='false'),
        sa.Column('fluids_washer', sa.Boolean(), nullable=True, server_default='false'),
        sa.Column('fluids_brake', sa.Boolean(), nullable=True, server_default='false'),
        sa.Column('mirrors', sa.Boolean(), nullable=True, server_default='false'),
        sa.Column('wipers', sa.Boolean(), nullable=True, server_default='false'),
        sa.Column('horn', sa.Boolean(), nullable=True, server_default='false'),
        sa.Column('seatbelts', sa.Boolean(), nullable=True, server_default='false'),
        sa.Column('first_aid_kit', sa.Boolean(), nullable=True, server_default='false'),
        sa.Column('fire_extinguisher', sa.Boolean(), nullable=True, server_default='false'),
        sa.Column('warning_triangle', sa.Boolean(), nullable=True, server_default='false'),
        sa.Column('overall_status', sa.String(length=20), nullable=True, server_default='failed'),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('photos', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['vehicle_id'], ['vehicles.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['driver_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_vehicle_pretrip_inspections_id'), 'vehicle_pretrip_inspections', ['id'], unique=False)
    
    # Vehicle Drivers
    op.create_table('vehicle_drivers',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('vehicle_id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('assigned_from', sa.Date(), nullable=False),
        sa.Column('assigned_to', sa.Date(), nullable=True),
        sa.Column('is_primary', sa.Boolean(), nullable=True, server_default='false'),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['vehicle_id'], ['vehicles.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_vehicle_drivers_id'), 'vehicle_drivers', ['id'], unique=False)
    
    # Deliveries
    op.create_table('deliveries',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('delivery_number', sa.String(length=50), nullable=False),
        sa.Column('purchase_order_id', sa.Integer(), nullable=True),
        sa.Column('vehicle_id', sa.Integer(), nullable=True),
        sa.Column('driver_id', sa.Integer(), nullable=True),
        sa.Column('status', sa.String(length=20), nullable=True, server_default='pending'),
        sa.Column('shipped_date', sa.DateTime(), nullable=True),
        sa.Column('delivery_date', sa.DateTime(), nullable=True),
        sa.Column('tracking_number', sa.String(length=100), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('company_id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['company_id'], ['companies.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['purchase_order_id'], ['purchase_orders.id'], ),
        sa.ForeignKeyConstraint(['vehicle_id'], ['vehicles.id'], ),
        sa.ForeignKeyConstraint(['driver_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('delivery_number')
    )
    op.create_index(op.f('ix_deliveries_id'), 'deliveries', ['id'], unique=False)
    op.create_index(op.f('ix_deliveries_delivery_number'), 'deliveries', ['delivery_number'], unique=True)
    
    # Vehicle Trips
    op.create_table('vehicle_trips',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('vehicle_id', sa.Integer(), nullable=False),
        sa.Column('driver_id', sa.Integer(), nullable=False),
        sa.Column('delivery_id', sa.Integer(), nullable=True),
        sa.Column('start_address', sa.String(length=500), nullable=True),
        sa.Column('end_address', sa.String(length=500), nullable=True),
        sa.Column('start_time', sa.DateTime(), nullable=True),
        sa.Column('end_time', sa.DateTime(), nullable=True),
        sa.Column('distance_km', sa.Integer(), nullable=True),
        sa.Column('purpose', sa.String(length=255), nullable=True),
        sa.Column('expenses', sa.Numeric(precision=12, scale=2), nullable=True, server_default='0'),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['vehicle_id'], ['vehicles.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['driver_id'], ['users.id'], ),
        sa.ForeignKeyConstraint(['delivery_id'], ['deliveries.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_vehicle_trips_id'), 'vehicle_trips', ['id'], unique=False)
    
    # Vehicle Cost Centers
    op.create_table('vehicle_cost_centers',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('department_id', sa.Integer(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True, server_default='true'),
        sa.Column('company_id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['company_id'], ['companies.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['department_id'], ['departments.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_vehicle_cost_centers_id'), 'vehicle_cost_centers', ['id'], unique=False)
    
    # Vehicle Expenses
    op.create_table('vehicle_expenses',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('vehicle_id', sa.Integer(), nullable=False),
        sa.Column('expense_type', sa.String(length=20), nullable=False),
        sa.Column('expense_date', sa.Date(), nullable=False),
        sa.Column('amount', sa.Numeric(precision=12, scale=2), nullable=True, server_default='0'),
        sa.Column('vat_amount', sa.Numeric(precision=12, scale=2), nullable=True, server_default='0'),
        sa.Column('total_amount', sa.Numeric(precision=12, scale=2), nullable=True, server_default='0'),
        sa.Column('description', sa.String(length=500), nullable=True),
        sa.Column('reference_id', sa.Integer(), nullable=True),
        sa.Column('reference_type', sa.String(length=50), nullable=True),
        sa.Column('is_deductible', sa.Boolean(), nullable=True, server_default='true'),
        sa.Column('cost_center_id', sa.Integer(), nullable=True),
        sa.Column('company_id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['vehicle_id'], ['vehicles.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['cost_center_id'], ['vehicle_cost_centers.id'], ),
        sa.ForeignKeyConstraint(['company_id'], ['companies.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_vehicle_expenses_id'), 'vehicle_expenses', ['id'], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    # Drop fleet tables
    op.drop_table('vehicle_expenses')
    op.drop_table('vehicle_cost_centers')
    op.drop_table('vehicle_trips')
    op.drop_table('deliveries')
    op.drop_table('vehicle_drivers')
    op.drop_table('vehicle_pretrip_inspections')
    op.drop_table('vehicle_inspections')
    op.drop_table('vehicle_insurances')
    op.drop_table('vehicle_schedules')
    op.drop_table('vehicle_repairs')
    op.drop_table('vehicle_services')
    op.drop_table('vehicle_fuel')
    op.drop_table('vehicle_mileage')
    op.drop_table('vehicle_tolls')
    op.drop_table('vehicle_vignettes')
    op.drop_table('vehicle_fuel_cards')
    op.drop_table('vehicle_documents')
    op.drop_table('vehicles')
    op.drop_table('vehicle_types')
    
    # Drop logistics tables
    op.drop_table('purchase_order_items')
    op.drop_table('purchase_orders')
    op.drop_table('purchase_request_history')
    op.drop_table('purchase_request_approvals')
    op.drop_table('purchase_request_items')
    op.drop_table('purchase_requests')
    op.drop_table('request_templates')
    
    # Drop ingredient columns
    op.drop_constraint('fk_ingredient_preferred_supplier', 'ingredients')
    op.drop_column('ingredients', 'preferred_supplier_id')
    op.drop_column('ingredients', 'is_auto_reorder')
    op.drop_column('ingredients', 'reorder_quantity')
    op.drop_column('ingredients', 'min_quantity')
    
    # Drop supplier columns
    op.drop_column('suppliers', 'updated_at')
    op.drop_column('suppliers', 'created_at')
    op.drop_column('suppliers', 'notes')
    op.drop_column('suppliers', 'is_active')
    op.drop_column('suppliers', 'mol')
