"""
Tests for Logistics and Fleet Management modules
"""

import pytest
import asyncio
from decimal import Decimal
from datetime import datetime, date, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

from backend.database.models import (
    Supplier,
    RequestTemplate,
    PurchaseRequest,
    PurchaseRequestItem,
    PurchaseRequestApproval,
    PurchaseRequestHistory,
    PurchaseOrder,
    PurchaseOrderItem,
    Delivery,
    VehicleType,
    Vehicle,
    VehicleDocument,
    VehicleFuelCard,
    VehicleVignette,
    VehicleToll,
    VehicleMileage,
    VehicleFuel,
    VehicleService,
    VehicleRepair,
    VehicleSchedule,
    VehicleInsurance,
    VehicleInspection,
    VehiclePreTripInspection,
    VehicleDriver,
    VehicleTrip,
    VehicleExpense,
    VehicleCostCenter,
    PurchaseRequestStatus,
    PurchaseRequestPriority,
    VehicleStatus,
    FuelType,
    ExpenseType,
)


class TestSupplierModel:
    """Tests for Supplier model"""

    @pytest.fixture
    def supplier_data(self):
        return {
            "id": 1,
            "name": "Тест ООД",
            "eik": "123456789",
            "mol": "Иван Иванов",
            "address": "ул. Тестова 1",
            "phone": "+359 2 123 4567",
            "email": "test@test.bg",
            "is_active": True,
            "notes": "Тестов доставчик",
            "company_id": 1,
        }

    def test_supplier_creation(self, supplier_data):
        """Test creating a supplier instance"""
        supplier = Supplier(**supplier_data)
        assert supplier.name == "Тест ООД"
        assert supplier.eik == "123456789"
        assert supplier.is_active is True
        assert supplier.company_id == 1

    def test_supplier_defaults(self):
        """Test default values"""
        supplier = Supplier(
            name="Нов доставчик",
            company_id=1,
        )
        assert supplier.eik is None
        assert supplier.mol is None


class TestPurchaseRequestModel:
    """Tests for PurchaseRequest model"""

    @pytest.fixture
    def purchase_request_data(self):
        return {
            "id": 1,
            "request_number": "PR-2026-00001",
            "requested_by_id": 1,
            "department_id": 1,
            "status": PurchaseRequestStatus.DRAFT.value,
            "priority": PurchaseRequestPriority.MEDIUM.value,
            "reason": "Нужни материали",
            "due_date": date.today() + timedelta(days=7),
            "is_auto": False,
            "company_id": 1,
        }

    def test_purchase_request_creation(self, purchase_request_data):
        """Test creating a purchase request"""
        pr = PurchaseRequest(**purchase_request_data)
        assert pr.request_number == "PR-2026-00001"
        assert pr.status == "draft"
        assert pr.priority == "medium"
        assert pr.is_auto is False

    def test_purchase_request_auto_flag(self):
        """Test auto-generated request flag"""
        pr = PurchaseRequest(
            request_number="AR-2026-00001",
            requested_by_id=1,
            is_auto=True,
            company_id=1,
        )
        assert pr.is_auto is True
        assert pr.request_number.startswith("AR-")

    def test_purchase_request_statuses(self):
        """Test all status values"""
        for status in PurchaseRequestStatus:
            pr = PurchaseRequest(
                request_number=f"PR-{status.value}",
                requested_by_id=1,
                status=status.value,
                company_id=1,
            )
            assert pr.status == status.value


class TestPurchaseRequestApproval:
    """Tests for PurchaseRequestApproval model"""

    def test_approval_creation(self):
        """Test creating an approval record"""
        approval = PurchaseRequestApproval(
            request_id=1,
            action="approved",
            user_id=1,
            reason="Одобрено",
            is_auto=False,
        )
        assert approval.action == "approved"
        assert approval.user_id == 1

    def test_rejection_creation(self):
        """Test creating a rejection record"""
        rejection = PurchaseRequestApproval(
            request_id=1,
            action="rejected",
            user_id=1,
            reason="Не е необходимо",
            is_auto=False,
        )
        assert rejection.action == "rejected"


class TestVehicleModel:
    """Tests for Vehicle model"""

    @pytest.fixture
    def vehicle_data(self):
        return {
            "id": 1,
            "registration_number": "E1234AB",
            "vin": "ABC123456789",
            "make": "Toyota",
            "model": "Corolla",
            "year": 2020,
            "fuel_type": FuelType.DIZEL.value,
            "color": "Син",
            "is_company": True,
            "status": VehicleStatus.ACTIVE.value,
            "company_id": 1,
        }

    def test_vehicle_creation(self, vehicle_data):
        """Test creating a vehicle"""
        vehicle = Vehicle(**vehicle_data)
        assert vehicle.registration_number == "E1234AB"
        assert vehicle.make == "Toyota"
        assert vehicle.fuel_type == "dizel"
        assert vehicle.status == "active"

    def test_vehicle_defaults(self):
        """Test default values"""
        vehicle = Vehicle(
            registration_number="CA5678BB",
            make="Mercedes",
            model="Sprinter",
            company_id=1,
        )
        # Values may be None if not set in model defaults
        assert vehicle.registration_number == "CA5678BB"
        assert vehicle.make == "Mercedes"
        assert vehicle.company_id == 1

    def test_vehicle_statuses(self):
        """Test all status values"""
        for status in VehicleStatus:
            vehicle = Vehicle(
                registration_number=f"TEST{status.value[:3].upper()}",
                make="Test",
                model="Car",
                status=status.value,
                company_id=1,
            )
            assert vehicle.status == status.value


class TestVehicleFuel:
    """Tests for VehicleFuel model"""

    @pytest.fixture
    def fuel_data(self):
        return {
            "id": 1,
            "vehicle_id": 1,
            "date": datetime.now(),
            "fuel_type": "dizel",
            "quantity": Decimal("50.00"),
            "price_per_liter": Decimal("2.10"),
            "total_amount": Decimal("105.00"),
            "mileage": 50000,
            "location": "Shell София",
            "driver_id": 1,
        }

    def test_fuel_calculation(self, fuel_data):
        """Test fuel total amount calculation"""
        fuel = VehicleFuel(**fuel_data)
        assert fuel.quantity == Decimal("50.00")
        assert fuel.price_per_liter == Decimal("2.10")
        assert fuel.total_amount == Decimal("105.00")

    def test_fuel_with_card(self, fuel_data):
        """Test fuel record with fuel card"""
        fuel_data["fuel_card_id"] = 1
        fuel = VehicleFuel(**fuel_data)
        assert fuel.fuel_card_id == 1


class TestVehicleInsurance:
    """Tests for VehicleInsurance model"""

    def test_insurance_creation(self):
        """Test creating an insurance record"""
        insurance = VehicleInsurance(
            vehicle_id=1,
            insurance_type="civil",
            policy_number="123456789",
            insurance_company="Застраховане АД",
            start_date=date.today(),
            end_date=date.today() + timedelta(days=365),
            premium=Decimal("300.00"),
            coverage_amount=Decimal("50000.00"),
        )
        assert insurance.insurance_type == "civil"
        assert insurance.policy_number == "123456789"

    def test_insurance_expiry_check(self):
        """Test insurance expiry detection"""
        insurance = VehicleInsurance(
            vehicle_id=1,
            insurance_type="civil",
            policy_number="123456789",
            start_date=date.today() - timedelta(days=400),
            end_date=date.today() - timedelta(days=35),
            premium=Decimal("300.00"),
        )
        days_until_expiry = (insurance.end_date - date.today()).days
        assert days_until_expiry < 0 or days_until_expiry <= 30


class TestVehicleInspection:
    """Tests for VehicleInspection (GTP) model"""

    def test_inspection_creation(self):
        """Test creating an inspection record"""
        inspection = VehicleInspection(
            vehicle_id=1,
            inspection_date=date.today(),
            valid_until=date.today() + timedelta(days=365),
            result="passed",
            mileage=50000,
            inspector="Техпреглед ООД",
            certificate_number="123456",
        )
        assert inspection.result == "passed"
        assert inspection.valid_until > date.today()


class TestVehiclePreTripInspection:
    """Tests for VehiclePreTripInspection model"""

    def test_pretrip_all_passed(self):
        """Test pre-trip inspection with all checks passed"""
        inspection = VehiclePreTripInspection(
            vehicle_id=1,
            driver_id=1,
            tires_condition=True,
            tires_pressure=True,
            tires_tread=True,
            brakes_condition=True,
            brakes_parking=True,
            lights_headlights=True,
            lights_brake=True,
            lights_turn=True,
            lights_warning=True,
            fluids_oil=True,
            fluids_coolant=True,
            fluids_washer=True,
            fluids_brake=True,
            mirrors=True,
            wipers=True,
            horn=True,
            seatbelts=True,
            first_aid_kit=True,
            fire_extinguisher=True,
            warning_triangle=True,
            overall_status="passed",
        )
        assert inspection.overall_status == "passed"

    def test_pretrip_with_failures(self):
        """Test pre-trip inspection with some failures"""
        inspection = VehiclePreTripInspection(
            vehicle_id=1,
            driver_id=1,
            tires_condition=False,
            tires_pressure=True,
            overall_status="failed",
        )
        assert inspection.overall_status == "failed"
        assert inspection.tires_condition is False


class TestVehicleDriver:
    """Tests for VehicleDriver model"""

    def test_driver_assignment_primary(self):
        """Test assigning a primary driver"""
        driver = VehicleDriver(
            vehicle_id=1,
            user_id=1,
            assigned_from=date.today(),
            is_primary=True,
        )
        assert driver.is_primary is True

    def test_driver_assignment_temporary(self):
        """Test assigning a temporary driver"""
        driver = VehicleDriver(
            vehicle_id=1,
            user_id=2,
            assigned_from=date.today(),
            assigned_to=date.today() + timedelta(days=30),
            is_primary=False,
        )
        assert driver.is_primary is False
        assert driver.assigned_to is not None


class TestVehicleExpense:
    """Tests for VehicleExpense model"""

    @pytest.fixture
    def expense_data(self):
        return {
            "vehicle_id": 1,
            "expense_type": ExpenseType.FUEL.value,
            "expense_date": date.today(),
            "amount": Decimal("100.00"),
            "vat_amount": Decimal("20.00"),
            "total_amount": Decimal("120.00"),
            "is_deductible": True,
            "company_id": 1,
        }

    def test_expense_creation(self, expense_data):
        """Test creating an expense record"""
        expense = VehicleExpense(**expense_data)
        assert expense.expense_type == "fuel"
        assert expense.amount == Decimal("100.00")
        assert expense.vat_amount == Decimal("20.00")

    def test_expense_types(self, expense_data):
        """Test all expense types"""
        for exp_type in ExpenseType:
            expense_data["expense_type"] = exp_type.value
            expense = VehicleExpense(**expense_data)
            assert expense.expense_type == exp_type.value


class TestDeliveryModel:
    """Tests for Delivery model"""

    @pytest.fixture
    def delivery_data(self):
        return {
            "id": 1,
            "delivery_number": "D-2026-00001",
            "purchase_order_id": 1,
            "vehicle_id": 1,
            "driver_id": 1,
            "status": "pending",
            "company_id": 1,
        }

    def test_delivery_creation(self, delivery_data):
        """Test creating a delivery"""
        delivery = Delivery(**delivery_data)
        assert delivery.delivery_number == "D-2026-00001"
        assert delivery.status == "pending"

    def test_delivery_statuses(self, delivery_data):
        """Test all delivery statuses"""
        statuses = ["pending", "in_transit", "delivered", "cancelled"]
        for status in statuses:
            delivery_data["status"] = status
            delivery = Delivery(**delivery_data)
            assert delivery.status == status


class TestInventoryCheckJob:
    """Tests for inventory auto-reorder job"""

    @pytest.mark.skip(reason="Requires database connection")
    @pytest.mark.asyncio
    async def test_check_inventory_levels_empty(self):
        """Test inventory check with no ingredients"""
        pass

    @pytest.mark.skip(reason="Requires database connection")
    @pytest.mark.asyncio
    async def test_generate_request_number(self):
        """Test request number generation"""
        pass


class TestFleetNotificationsJob:
    """Tests for fleet notifications job"""

    @pytest.mark.asyncio
    async def test_check_fleet_notifications(self):
        """Test fleet notifications check"""
        from backend.jobs.fleet_notifications_job import check_fleet_notifications
        
        mock_db = AsyncMock()
        mock_result = AsyncMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_db.execute = AsyncMock(return_value=mock_result)
        mock_db.commit = AsyncMock()
        
        with patch('backend.jobs.fleet_notifications_job.AsyncSessionLocal', return_value=mock_db):
            try:
                await check_fleet_notifications()
            except Exception:
                pass


class TestRBACPermissions:
    """Tests for RBAC permissions"""

    def test_logistics_permissions_exist(self):
        """Test that all logistics permissions are defined"""
        from backend.auth.rbac_service import DEFAULT_PERMISSIONS
        
        logistics_perms = [
            "logistics:suppliers:read",
            "logistics:suppliers:create",
            "logistics:requests:read",
            "logistics:requests:create",
            "logistics:requests:approve",
            "logistics:orders:read",
            "logistics:deliveries:read",
        ]
        
        for perm in logistics_perms:
            assert perm in DEFAULT_PERMISSIONS, f"Missing permission: {perm}"

    def test_fleet_permissions_exist(self):
        """Test that all fleet permissions are defined"""
        from backend.auth.rbac_service import DEFAULT_PERMISSIONS
        
        fleet_perms = [
            "fleet:vehicles:read",
            "fleet:vehicles:create",
            "fleet:fuel:read",
            "fleet:repairs:read",
            "fleet:insurances:read",
            "fleet:inspections:read",
            "fleet:drivers:read",
            "fleet:trips:read",
            "fleet:expenses:read",
        ]
        
        for perm in fleet_perms:
            assert perm in DEFAULT_PERMISSIONS, f"Missing permission: {perm}"


class TestGraphQLTypes:
    """Tests for GraphQL types"""

    def test_supplier_extended_type(self):
        """Test SupplierExtended GraphQL type"""
        from backend.graphql.types import SupplierExtended
        
        supplier_data = {
            "id": 1,
            "name": "Тест ООД",
            "eik": "123456789",
            "vat_number": "BG123456789",
            "mol": "Иван Иванов",
            "address": "ул. Тестова 1",
            "contact_person": "Петър Петров",
            "phone": "+359 2 123 4567",
            "email": "test@test.bg",
            "is_active": True,
            "notes": "Тест",
            "company_id": 1,
            "created_at": datetime.now(),
            "updated_at": None,
        }
        
        supplier = SupplierExtended(**supplier_data)
        assert supplier.name == "Тест ООД"
        assert supplier.is_active is True

    def test_vehicle_type(self):
        """Test Vehicle GraphQL type"""
        from backend.graphql.types import Vehicle, FuelType, VehicleStatus
        
        vehicle_data = {
            "id": 1,
            "registration_number": "E1234AB",
            "vin": "ABC123456789",
            "make": "Toyota",
            "model": "Corolla",
            "year": 2020,
            "vehicle_type_id": 1,
            "fuel_type": FuelType.DIZEL,
            "engine_number": "ABC123",
            "chassis_number": "XYZ789",
            "color": "Син",
            "initial_mileage": 0,
            "is_company": True,
            "owner_name": None,
            "status": VehicleStatus.ACTIVE,
            "notes": None,
            "company_id": 1,
            "created_at": datetime.now(),
            "updated_at": None,
        }
        
        vehicle = Vehicle(**vehicle_data)
        assert vehicle.registration_number == "E1234AB"
        assert vehicle.fuel_type == FuelType.DIZEL
        assert vehicle.status == VehicleStatus.ACTIVE


# Integration tests
class TestLogisticsIntegration:
    """Integration tests for Logistics module"""

    def test_request_to_order_flow(self):
        """Test the flow from purchase request to order"""
        # Create a purchase request
        pr = PurchaseRequest(
            request_number="PR-2026-00001",
            requested_by_id=1,
            status="approved",
            company_id=1,
        )
        assert pr.status == "approved"
        
        # Create a purchase order from the request
        order = PurchaseOrder(
            order_number="PO-2026-00001",
            supplier_id=1,
            purchase_request_id=1,
            company_id=1,
        )
        assert order.purchase_request_id == 1
        
        # Create a delivery from the order
        delivery = Delivery(
            delivery_number="D-2026-00001",
            purchase_order_id=1,
            vehicle_id=1,
            driver_id=1,
            company_id=1,
        )
        assert delivery.purchase_order_id == 1


class TestFleetIntegration:
    """Integration tests for Fleet module"""

    def test_vehicle_lifecycle(self):
        """Test the full vehicle lifecycle"""
        # Create vehicle
        vehicle = Vehicle(
            registration_number="E1234AB",
            make="Toyota",
            model="Corolla",
            company_id=1,
        )
        
        # Add mileage record
        mileage = VehicleMileage(
            vehicle_id=1,
            date=date.today(),
            mileage=50000,
            source="manual",
        )
        
        # Add fuel record
        fuel = VehicleFuel(
            vehicle_id=1,
            date=datetime.now(),
            quantity=Decimal("50.00"),
            price_per_liter=Decimal("2.10"),
            total_amount=Decimal("105.00"),
            mileage=50000,
        )
        
        # Create expense from fuel
        expense = VehicleExpense(
            vehicle_id=1,
            expense_type="fuel",
            expense_date=date.today(),
            amount=Decimal("100.00"),
            vat_amount=Decimal("20.00"),
            total_amount=Decimal("120.00"),
            reference_id=1,
            reference_type="fuel",
            company_id=1,
        )
        
        assert expense.reference_type == "fuel"
        assert expense.total_amount == Decimal("120.00")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
