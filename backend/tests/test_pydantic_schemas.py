"""TDD Tests for Pydantic Schema Conversions

Tests the @sp.type(schemas.Xxx) pattern and from_pydantic() conversions.
Red-Green-Refactor approach: validate schema → GraphQL type conversion.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from datetime import date, datetime
from decimal import Decimal

import pytest
from backend import schemas
from backend.graphql import types


class TestCompanySchema:
    """Test Company Pydantic schema and GraphQL conversion"""

    def test_company_schema_creation(self):
        """RED: Create Company schema with minimal fields"""
        company = schemas.Company(
            id=1,
            name="Test Company",
            eik="123456789",
            bulstat="123456789",
            address="123 Test St",
            mol_name="Ivan Ivanov",
        )
        
        assert company.id == 1
        assert company.name == "Test Company"
        assert company.eik == "123456789"

    def test_company_from_pydantic(self):
        """GREEN: Convert Company schema to GraphQL type"""
        company = schemas.Company(
            id=1,
            name="Test Company",
            eik="123456789",
            bulstat="123456789",
            vat_number="BG123456789",
            address="123 Test St",
            mol_name="Ivan Ivanov",
        )
        
        gql_company = types.Company.from_pydantic(company)
        
        assert gql_company.id == 1
        assert gql_company.name == "Test Company"
        assert gql_company.eik == "123456789"
        assert gql_company.bulstat == "123456789"
        assert gql_company.vat_number == "BG123456789"
        assert gql_company.address == "123 Test St"
        assert gql_company.mol_name == "Ivan Ivanov"

    def test_company_with_optional_fields_none(self):
        """EDGE: Company with optional fields as None"""
        company = schemas.Company(
            id=2,
            name="Minimal Company",
        )
        
        gql_company = types.Company.from_pydantic(company)
        
        assert gql_company.id == 2
        assert gql_company.name == "Minimal Company"
        assert gql_company.eik is None
        assert gql_company.address is None


class TestUserSchema:
    """Test User Pydantic schema and GraphQL conversion"""

    def test_user_schema_creation(self):
        """RED: Create User schema with required fields"""
        role = schemas.Role(id=1, name="user")
        user = schemas.User(
            id=1,
            email="test@example.com",
            is_active=True,
            role_id=1,
            role=role,
        )
        
        assert user.id == 1
        assert user.email == "test@example.com"
        assert user.is_active is True

    def test_user_from_pydantic(self):
        """GREEN: Convert User schema to GraphQL type"""
        role = schemas.Role(id=1, name="user")
        user = schemas.User(
            id=1,
            email="test@example.com",
            is_active=True,
            role_id=1,
            role=role,
            first_name="John",
            last_name="Doe",
            phone_number="+359888123456",
        )
        
        gql_user = types.User.from_pydantic(user)
        
        assert gql_user.id == 1
        assert gql_user.email == "test@example.com"
        assert gql_user.is_active is True
        assert gql_user.first_name == "John"
        assert gql_user.last_name == "Doe"
        assert gql_user.phone_number == "+359888123456"

    def test_user_with_department_and_position(self):
        """GREEN: User with nested department and position IDs"""
        role = schemas.Role(id=2, name="manager")
        user = schemas.User(
            id=2,
            email="manager@example.com",
            is_active=True,
            role_id=2,
            role=role,
            company_id=1,
            department_id=5,
            position_id=3,
        )
        
        gql_user = types.User.from_pydantic(user)
        
        assert gql_user.department_id == 5
        assert gql_user.position_id == 3


class TestInvoiceSchema:
    """Test Invoice Pydantic schema with Decimal fields"""

    def test_invoice_schema_with_decimals(self):
        """RED: Create Invoice with Decimal amounts"""
        invoice = schemas.Invoice(
            id=1,
            number="INV-2024-001",
            type="outgoing",
            date=date(2024, 1, 15),
            due_date=date(2024, 2, 15),
            subtotal=Decimal("1000.00"),
            vat_amount=Decimal("200.00"),
            total=Decimal("1200.00"),
            company_id=1,
            created_at=datetime.now(),
        )
        
        assert invoice.total == Decimal("1200.00")
        assert invoice.vat_amount == Decimal("200.00")

    def test_invoice_from_pydantic(self):
        """GREEN: Convert Invoice schema to GraphQL type"""
        invoice = schemas.Invoice(
            id=1,
            number="INV-2024-001",
            type="outgoing",
            date=date(2024, 1, 15),
            due_date=date(2024, 2, 15),
            subtotal=Decimal("1000.00"),
            vat_amount=Decimal("200.00"),
            total=Decimal("1200.00"),
            company_id=1,
            status="draft",
            created_at=datetime.now(),
        )
        
        gql_invoice = types.Invoice.from_pydantic(invoice)
        
        assert gql_invoice.id == 1
        assert gql_invoice.number == "INV-2024-001"
        assert gql_invoice.type == "outgoing"
        assert gql_invoice.status == "draft"
        assert gql_invoice.total == Decimal("1200.00")

    def test_invoice_with_optional_notes(self):
        """EDGE: Invoice with optional notes field"""
        invoice = schemas.Invoice(
            id=2,
            number="INV-2024-002",
            type="incoming",
            date=date(2024, 1, 20),
            due_date=date(2024, 2, 20),
            subtotal=Decimal("500.00"),
            vat_amount=Decimal("100.00"),
            total=Decimal("600.00"),
            company_id=1,
            notes="Test invoice with notes",
            created_at=datetime.now(),
        )
        
        gql_invoice = types.Invoice.from_pydantic(invoice)
        
        assert gql_invoice.notes == "Test invoice with notes"


class TestVehicleSchema:
    """Test Vehicle Pydantic schema with nested types"""

    def test_vehicle_schema_creation(self):
        """RED: Create Vehicle schema"""
        vehicle = schemas.Vehicle(
            id=1,
            registration_number="CA1234AB",
            make="Toyota",
            model="Corolla",
            year=2022,
            vin="1HGBH41JXMN109186",
            fuel_type="dizel",
            status="active",
            company_id=1,
        )
        
        assert vehicle.registration_number == "CA1234AB"
        assert vehicle.make == "Toyota"
        assert vehicle.status == "active"

    def test_vehicle_from_pydantic(self):
        """GREEN: Convert Vehicle schema to GraphQL type"""
        vehicle = schemas.Vehicle(
            id=1,
            registration_number="CA1234AB",
            make="Toyota",
            model="Corolla",
            year=2022,
            vin="1HGBH41JXMN109186",
            fuel_type="dizel",
            status="active",
            company_id=1,
            initial_mileage=50000,
            color="бял",
        )
        
        gql_vehicle = types.Vehicle.from_pydantic(vehicle)
        
        assert gql_vehicle.id == 1
        assert gql_vehicle.registration_number == "CA1234AB"
        assert gql_vehicle.make == "Toyota"
        assert gql_vehicle.model == "Corolla"
        assert gql_vehicle.year == 2022
        assert gql_vehicle.fuel_type == "dizel"
        assert gql_vehicle.status == "active"
        assert gql_vehicle.initial_mileage == 50000
        assert gql_vehicle.color == "бял"


class TestRecipeSchema:
    """Test Recipe Pydantic schema with nested ingredients"""

    def test_recipe_schema_creation(self):
        """RED: Create Recipe schema"""
        recipe = schemas.Recipe(
            id=1,
            name="Chocolate Cake",
            description="Delicious chocolate cake",
            yield_quantity=Decimal("8.0"),
            yield_unit="br",
            shelf_life_days=7,
            portions=8,
            company_id=1,
        )
        
        assert recipe.name == "Chocolate Cake"
        assert recipe.portions == 8

    def test_recipe_from_pydantic(self):
        """GREEN: Convert Recipe schema to GraphQL type"""
        recipe = schemas.Recipe(
            id=1,
            name="Chocolate Cake",
            description="Delicious chocolate cake",
            yield_quantity=Decimal("8.0"),
            yield_unit="br",
            shelf_life_days=7,
            portions=8,
            company_id=1,
            cost_price=Decimal("15.50"),
            markup_percentage=Decimal("30.00"),
            selling_price=Decimal("20.15"),
        )
        
        gql_recipe = types.Recipe.from_pydantic(recipe)
        
        assert gql_recipe.id == 1
        assert gql_recipe.name == "Chocolate Cake"
        assert gql_recipe.yield_quantity == Decimal("8.0")
        assert gql_recipe.yield_unit == "br"
        assert gql_recipe.shelf_life_days == 7
        assert gql_recipe.portions == 8
        assert gql_recipe.cost_price == Decimal("15.50")
        assert gql_recipe.selling_price == Decimal("20.15")


class TestTimeLogSchema:
    """Test TimeLog Pydantic schema with datetime fields"""

    def test_timelog_schema_creation(self):
        """RED: Create TimeLog schema"""
        now = datetime.now()
        timelog = schemas.TimeLog(
            id=1,
            user_id=1,
            start_time=now,
            end_time=None,
            is_manual=False,
            break_duration_minutes=0,
            type="work",
        )
        
        assert timelog.user_id == 1
        assert timelog.type == "work"
        assert timelog.end_time is None

    def test_timelog_from_pydantic(self):
        """GREEN: Convert TimeLog schema to GraphQL type"""
        start = datetime(2024, 1, 15, 9, 0, 0)
        end = datetime(2024, 1, 15, 17, 30, 0)
        
        timelog = schemas.TimeLog(
            id=1,
            user_id=1,
            start_time=start,
            end_time=end,
            is_manual=False,
            break_duration_minutes=30,
            type="work",
            notes="Full work day",
        )
        
        gql_timelog = types.TimeLog.from_pydantic(timelog)
        
        assert gql_timelog.id == 1
        assert gql_timelog.user_id == 1
        assert gql_timelog.start_time == start
        assert gql_timelog.end_time == end
        assert gql_timelog.is_manual is False
        assert gql_timelog.break_duration_minutes == 30
        assert gql_timelog.type == "work"
        assert gql_timelog.notes == "Full work day"


class TestAccessControlSchema:
    """Test Access Control Pydantic schemas"""

    def test_access_zone_schema(self):
        """RED: Create AccessZone schema"""
        zone = schemas.AccessZone(
            id=1,
            zone_id="main_building",
            name="Main Building",
            level=1,
            company_id=1,
            is_active=True,
        )
        
        assert zone.name == "Main Building"
        assert zone.is_active is True

    def test_access_zone_from_pydantic(self):
        """GREEN: Convert AccessZone to GraphQL type"""
        zone = schemas.AccessZone(
            id=1,
            zone_id="main_building",
            name="Main Building",
            level=1,
            description="Main office building",
            company_id=1,
            is_active=True,
            anti_passback_enabled=True,
            anti_passback_type="hard",
        )
        
        gql_zone = types.AccessZone.from_pydantic(zone)
        
        assert gql_zone.id == 1
        assert gql_zone.zone_id == "main_building"
        assert gql_zone.name == "Main Building"
        assert gql_zone.level == 1
        assert gql_zone.description == "Main office building"
        assert gql_zone.is_active is True
        assert gql_zone.anti_passback_enabled is True

    def test_access_door_schema(self):
        """RED: Create AccessDoor schema"""
        door = schemas.AccessDoor(
            id=1,
            door_id="main_entrance",
            name="Main Entrance",
            zone_db_id=1,
            gateway_id=1,
            device_id="DEV001",
            is_active=True,
        )
        
        assert door.name == "Main Entrance"
        assert door.device_id == "DEV001"

    def test_access_door_from_pydantic(self):
        """GREEN: Convert AccessDoor to GraphQL type"""
        door = schemas.AccessDoor(
            id=1,
            door_id="main_entrance",
            name="Main Entrance",
            zone_db_id=1,
            gateway_id=1,
            device_id="DEV001",
            relay_number=1,
            terminal_mode="access",
            is_active=True,
            is_online=True,
            description="Ground floor entrance",
        )
        
        gql_door = types.AccessDoor.from_pydantic(door)
        
        assert gql_door.id == 1
        assert gql_door.door_id == "main_entrance"
        assert gql_door.name == "Main Entrance"
        assert gql_door.zone_db_id == 1
        assert gql_door.gateway_id == 1
        assert gql_door.device_id == "DEV001"
        assert gql_door.description == "Ground floor entrance"


class TestPayrollSchema:
    """Test Payroll Pydantic schema with complex calculations"""

    def test_payroll_schema_creation(self):
        """RED: Create Payroll schema"""
        payroll = schemas.Payroll(
            id=1,
            hourly_rate=Decimal("25.00"),
            monthly_salary=Decimal("4000.00"),
            user_id=1,
        )
        
        assert payroll.hourly_rate == Decimal("25.00")
        assert payroll.monthly_salary == Decimal("4000.00")

    def test_payroll_from_pydantic(self):
        """GREEN: Convert Payroll schema to GraphQL type"""
        payroll = schemas.Payroll(
            id=1,
            hourly_rate=Decimal("25.00"),
            monthly_salary=Decimal("4000.00"),
            overtime_multiplier=Decimal("1.5"),
            standard_hours_per_day=8,
            currency="BGN",
            annual_leave_days=20,
            tax_percent=Decimal("10.00"),
            health_insurance_percent=Decimal("13.78"),
            has_tax_deduction=True,
            has_health_insurance=True,
            user_id=1,
        )
        
        gql_payroll = types.Payroll.from_pydantic(payroll)
        
        assert gql_payroll.id == 1
        assert gql_payroll.hourly_rate == Decimal("25.00")
        assert gql_payroll.monthly_salary == Decimal("4000.00")
        assert gql_payroll.overtime_multiplier == Decimal("1.5")
        assert gql_payroll.standard_hours_per_day == 8
        assert gql_payroll.currency == "BGN"
        assert gql_payroll.annual_leave_days == 20
        assert gql_payroll.tax_percent == Decimal("10.00")


class TestContractSchema:
    """Test Employment Contract Pydantic schema"""

    def test_contract_schema_creation(self):
        """RED: Create EmploymentContract schema"""
        contract = schemas.EmploymentContract(
            id=1,
            user_id=1,
            company_id=1,
            contract_type="permanent",
            contract_number="EMP-2024-001",
            start_date=date(2024, 1, 1),
            end_date=None,
            is_active=True,
            created_at=datetime.now(),
        )
        
        assert contract.contract_number == "EMP-2024-001"
        assert contract.contract_type == "permanent"
        assert contract.end_date is None

    def test_contract_from_pydantic(self):
        """GREEN: Convert EmploymentContract to GraphQL type"""
        contract = schemas.EmploymentContract(
            id=1,
            user_id=1,
            company_id=1,
            contract_type="fixed_term",
            contract_number="EMP-2024-001",
            start_date=date(2024, 1, 1),
            end_date=date(2025, 12, 31),
            base_salary=Decimal("2500.00"),
            work_hours_per_week=40,
            probation_months=3,
            is_active=True,
            status="active",
            created_at=datetime.now(),
        )
        
        gql_contract = types.EmploymentContract.from_pydantic(contract)
        
        assert gql_contract.id == 1
        assert gql_contract.user_id == 1
        assert gql_contract.company_id == 1
        assert gql_contract.contract_number == "EMP-2024-001"
        assert gql_contract.start_date == date(2024, 1, 1)
        assert gql_contract.end_date == date(2025, 12, 31)
        assert gql_contract.contract_type == "fixed_term"
        assert gql_contract.base_salary == Decimal("2500.00")
        assert gql_contract.work_hours_per_week == 40


class TestNotificationSchema:
    """Test Notification Pydantic schema"""

    def test_notification_schema_creation(self):
        """RED: Create Notification schema"""
        notification = schemas.Notification(
            id=1,
            user_id=1,
            message="This is a test message",
            is_read=False,
            created_at=datetime.now(),
        )
        
        assert notification.message == "This is a test message"
        assert notification.is_read is False

    def test_notification_from_pydantic(self):
        """GREEN: Convert Notification to GraphQL type"""
        now = datetime.now()
        notification = schemas.Notification(
            id=1,
            user_id=1,
            message="This is a test message",
            is_read=False,
            created_at=now,
        )
        
        gql_notification = types.Notification.from_pydantic(notification)
        
        assert gql_notification.id == 1
        assert gql_notification.user_id == 1
        assert gql_notification.message == "This is a test message"
        assert gql_notification.is_read is False
        assert gql_notification.created_at == now


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
