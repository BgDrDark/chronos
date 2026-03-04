import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from backend import crud, schemas
from backend.database.models import User, Role, Company, Module, TimeLog, Department
import asyncio
from decimal import Decimal
import uuid

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