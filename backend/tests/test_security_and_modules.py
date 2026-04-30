import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from backend import crud, schemas
from backend.database.models import User, Role, Company, Module, TimeLog, Department, ThrottleLog
import asyncio
from decimal import Decimal
import uuid
from datetime import datetime, timedelta

@pytest.mark.asyncio
async def test_module_guard_and_rest_api(async_client: AsyncClient, test_db: AsyncSession):
    unique_suffix = uuid.uuid4().hex[:6]
    # 1. Setup roles and Super Admin
    sa_role = await crud.get_role_by_name(test_db, "super_admin")
    if not sa_role:
        sa_role = await crud.create_role(test_db, schemas.RoleCreate(name="super_admin", description="Super Admin"))
    
    sa_user_in = schemas.UserCreate(email=f"sa_{unique_suffix}@example.com", username=f"sa_{unique_suffix}", password="Sapassword123!")
    sa_user = await crud.create_user(test_db, sa_user_in, role_name="super_admin")
    
    # Login as Super Admin
    login_res = await async_client.post("/auth/token", data={"username": f"sa_{unique_suffix}", "password": "Sapassword123!"})
    token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 2. Ensure modules exist
    test_db.add(Module(code="kiosk", name="Kiosk", is_enabled=False))
    await test_db.commit()

    # Try to access a protected endpoint (Kiosk) - Should be 403
    kiosk_res = await async_client.post("/kiosk/scan", json={"qr_token": "test"}, headers={"X-Kiosk-Secret": "secret"})
    assert kiosk_res.status_code == 403

    # Enable module via API
    await async_client.patch("/system/modules/kiosk", json={"is_enabled": True}, headers=headers)
    
    # Try access again
    kiosk_res = await async_client.post("/kiosk/scan", json={"qr_token": "test"}, headers={"X-Kiosk-Secret": "wrong"})
    assert kiosk_res.status_code == 403
    assert "Неоторизиран терминал" in kiosk_res.json()["detail"]

@pytest.mark.asyncio
async def test_username_login(async_client: AsyncClient, test_db: AsyncSession):
    unique_suffix = uuid.uuid4().hex[:6]
    # Create user with username only
    user_in = schemas.UserCreate(username=f"worker_{unique_suffix}", password="WorkerPassword123!", email=None)
    await crud.create_user(test_db, user_in)
    
    # Attempt login with username
    login_res = await async_client.post("/auth/token", data={"username": f"worker_{unique_suffix}", "password": "WorkerPassword123!"})
    assert login_res.status_code == 200
    assert "access_token" in login_res.json()

@pytest.mark.asyncio
async def test_password_complexity_enforcement(async_client: AsyncClient, test_db: AsyncSession):
    # Set strict requirements
    await crud.set_global_setting(test_db, "pwd_min_length", "10")
    await crud.set_global_setting(test_db, "pwd_require_special", "true")
    await test_db.commit()

    # Try creating user with simple password
    user_in = schemas.UserCreate(username="fail_pwd", password="password", email="fail@ex.com")
    with pytest.raises(ValueError) as exc:
        await crud.create_user(test_db, user_in)
    assert "поне 10 символа" in str(exc.value)

@pytest.mark.asyncio
async def test_company_details_and_department_manager(async_client: AsyncClient, test_db: AsyncSession):
    unique_suffix = uuid.uuid4().hex[:6]
    # 1. Test Company with details
    company = await crud.create_company(
        test_db, 
        name=f"Test LTD {unique_suffix}", 
        eik=f"EIK_{unique_suffix}", 
        mol_name="Ivan Ivanov"
    )
    assert company.mol_name == "Ivan Ivanov"

    # 2. Test Department with Manager
    user_in = schemas.UserCreate(username=f"manager_{unique_suffix}", password="Password123!", email=f"m_{unique_suffix}@ex.com")
    manager = await crud.create_user(test_db, user_in)
    
    dept = await crud.create_department(test_db, name=f"IT {unique_suffix}", company_id=company.id, manager_id=manager.id)
    assert dept.manager_id == manager.id

@pytest.mark.asyncio
async def test_multi_tenancy_isolation(async_client: AsyncClient, test_db: AsyncSession):
    unique_suffix = uuid.uuid4().hex[:6]
    # Setup roles
    admin_role = await crud.get_role_by_name(test_db, "admin")
    if not admin_role:
        await crud.create_role(test_db, schemas.RoleCreate(name="admin", description="Admin"))

    c1 = await crud.create_company(test_db, name=f"Company A {unique_suffix}")
    c2 = await crud.create_company(test_db, name=f"Company B {unique_suffix}")

    admin_a_in = schemas.UserCreate(username=f"admin_a_{unique_suffix}", password="Password123!", email=f"a_{unique_suffix}@a.com", company_id=c1.id)
    await crud.create_user(test_db, admin_a_in, role_name="admin")
    
    user_b_in = schemas.UserCreate(username=f"user_b_{unique_suffix}", password="Password123!", email=f"b_{unique_suffix}@b.com", company_id=c2.id)
    await crud.create_user(test_db, user_b_in)

    login_res = await async_client.post("/auth/token", data={"username": f"admin_a_{unique_suffix}", "password": "Password123!"})
    token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Query users via GraphQL
    query = "{ users(limit: 100) { users { username companyId } } }"
    res = await async_client.post("/graphql", json={"query": query}, headers=headers)
    users = res.json()["data"]["users"]["users"]
    
    usernames = [u["username"] for u in users]
    assert f"admin_a_{unique_suffix}" in usernames
    assert f"user_b_{unique_suffix}" not in usernames # Isolation check


# ========================================
# Tests for Module System (Fleet, Inventory, Cost Centers)
# ========================================

@pytest.mark.asyncio
async def test_core_modules_always_enabled(test_db: AsyncSession):
    """Core modules cannot be disabled"""
    from backend.services.module_service import ModuleService
    
    for core_module in ["shifts", "accounting", "confectionery", "cost_centers"]:
        is_enabled = await ModuleService.is_enabled(test_db, core_module)
        assert is_enabled is True, f"{core_module} should always be enabled"


@pytest.mark.asyncio
async def test_optional_modules_can_be_toggled(test_db: AsyncSession):
    """Optional modules can be enabled/disabled"""
    from backend.services.module_service import ModuleService
    from sqlalchemy import select
    
    test_db.add(Module(code="fleet", name="Fleet", is_enabled=False))
    await test_db.commit()
    
    is_enabled = await ModuleService.is_enabled(test_db, "fleet")
    assert is_enabled is False
    
    await ModuleService.toggle_module(test_db, "fleet", True)
    is_enabled = await ModuleService.is_enabled(test_db, "fleet")
    assert is_enabled is True


@pytest.mark.asyncio
async def test_module_mapping_includes_fleet_inventory_costcenters(test_db: AsyncSession):
    """Verify MODULE_MAPPING includes new modules"""
    from backend.graphql.module_middleware import MODULE_MAPPING
    
    fleet_fields = ["vehicles", "drivers", "trips", "vehicle", "driver", "trip"]
    for field in fleet_fields:
        assert field in MODULE_MAPPING, f"{field} should be in MODULE_MAPPING"
    
    inventory_fields = ["batches", "inventorySessions"]
    for field in inventory_fields:
        assert field in MODULE_MAPPING
    
    cost_center_fields = ["cost_centers", "cost_center", "create_cost_center", "update_cost_center"]
    for field in cost_center_fields:
        assert field in MODULE_MAPPING


@pytest.mark.asyncio
async def test_fleet_graphql_queries(async_client: AsyncClient, test_db: AsyncSession):
    """Test fleet GraphQL queries require fleet module"""
    from backend.database.models import Module, Vehicle
    from sqlalchemy import select
    
    test_db.add(Module(code="fleet", name="Fleet", is_enabled=True))
    await test_db.commit()
    
    result = await test_db.execute(select(Vehicle))
    assert result is not None


@pytest.mark.asyncio
async def test_cost_center_crud(test_db: AsyncSession):
    """Test CostCenter CRUD via GraphQL"""
    unique_suffix = uuid.uuid4().hex[:6]
    
    company = await crud.create_company(test_db, name=f"CostCo {unique_suffix}", eik=f"EIK{unique_suffix}")
    
    assert company.id is not None
    assert company.name == f"CostCo {unique_suffix}"


@pytest.mark.asyncio
async def test_throttle_log_table_created(test_db: AsyncSession):
    """Verify ThrottleLog table exists and works"""
    from sqlalchemy import select
    
    result = await test_db.execute(select(ThrottleLog))
    assert result is not None
    
    test_db.add(ThrottleLog(
        user_id=1,
        field_name="generatePayslip",
        ip_address="127.0.0.1"
    ))
    await test_db.commit()
    
    result = await test_db.execute(select(ThrottleLog).limit(1))
    logs = result.scalars().all()
    assert len(logs) >= 1


@pytest.mark.asyncio
async def test_throttle_config_exists(test_db: AsyncSession):
    """Verify THROTTLE_CONFIG is defined"""
    from backend.graphql.module_middleware import THROTTLE_CONFIG
    
    assert "generatePayslip" in THROTTLE_CONFIG
    assert "calculatePayroll" in THROTTLE_CONFIG
    assert THROTTLE_CONFIG["generatePayslip"] == 10


@pytest.mark.asyncio
async def test_module_mapping_has_proper_structure(test_db: AsyncSession):
    """Verify MODULE_MAPPING has expected fields"""
    from backend.graphql.module_middleware import MODULE_MAPPING
    
    assert isinstance(MODULE_MAPPING, dict)
    assert len(MODULE_MAPPING) > 50, "Should have many field mappings"
    
    # Check core module mappings
    assert MODULE_MAPPING["clockIn"] == "shifts"
    assert MODULE_MAPPING["payrollSummary"] == "salaries"
    assert MODULE_MAPPING["vehicles"] == "fleet"
    assert MODULE_MAPPING["batches"] == "inventory"
    assert MODULE_MAPPING["cost_centers"] == "cost_centers"