import pytest
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from datetime import datetime, timedelta, date
from backend.main import app
from backend import crud, schemas
from backend.auth import jwt_utils, security
from backend.database.models import User, UserSession, AuthKey, LeaveRequest, LeaveBalance, GlobalSetting

# --- MOCKS ---
# Mock OCR to avoid needing tesseract installed during tests
from unittest.mock import MagicMock
import sys
sys.modules['pytesseract'] = MagicMock()
sys.modules['pdf2image'] = MagicMock()

@pytest.fixture
async def admin_token(test_db: AsyncSession):
    # Ensure admin user exists
    user = await crud.get_user_by_email(test_db, "admin@example.com")
    if not user:
        role = await crud.get_role_by_name(test_db, "admin")
        if not role:
            role = await crud.create_role(test_db, schemas.RoleCreate(name="admin", description="Admin"))
        
        user = User(
            email="admin@example.com",
            hashed_password=security.hash_password("admin1234"),
            role_id=role.id,
            first_name="Admin",
            last_name="User",
            is_active=True
        )
        test_db.add(user)
        await test_db.commit()
    
    # Generate tokens
    access, _ = await jwt_utils.create_tokens(test_db, user.id, user.email)
    return access

@pytest.fixture
async def regular_user_token(test_db: AsyncSession):
    email = "testuser@example.com"
    user = await crud.get_user_by_email(test_db, email)
    if not user:
        role = await crud.get_role_by_name(test_db, "user")
        if not role:
            role = await crud.create_role(test_db, schemas.RoleCreate(name="user", description="User"))
            
        user = User(
            email=email,
            hashed_password=security.hash_password("user1234"),
            role_id=role.id,
            first_name="Test",
            last_name="User",
            is_active=True
        )
        test_db.add(user)
        await test_db.commit()
    
    access, refresh = await jwt_utils.create_tokens(test_db, user.id, user.email)
    return access, refresh, user

@pytest.mark.asyncio
async def test_auth_flow_and_sessions(test_db: AsyncSession):
    """
    Test Phase 12: Authlib integration, Refresh Tokens, Whitelist in DB.
    """
    # Ensure admin exists
    admin_user = await crud.get_user_by_email(test_db, "admin@example.com")
    if not admin_user:
        role = await crud.get_role_by_name(test_db, "admin")
        if not role:
            role = await crud.create_role(test_db, schemas.RoleCreate(name="admin", description="Admin"))
        admin_user = User(
            email="admin@example.com",
            hashed_password=security.hash_password("admin1234"),
            role_id=role.id,
            is_active=True
        )
        test_db.add(admin_user)
        await test_db.commit()

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        # 1. Login
        login_data = {"username": "admin@example.com", "password": "admin1234"}
        response = await ac.post("/auth/token", data=login_data)
        assert response.status_code == 200
        tokens = response.json()
        assert "access_token" in tokens
        assert "refresh_token" in tokens
        
        # Verify Session created in DB
        refresh_token = tokens["refresh_token"]
        # Determine JTI from token (need to decode or check DB)
        # We can just check if ANY session exists for admin
        admin_user = await crud.get_user_by_email(test_db, "admin@example.com")
        stmt = select(UserSession).where(UserSession.user_id == admin_user.id).where(UserSession.is_active == True)
        result = await test_db.execute(stmt)
        session = result.scalars().first()
        assert session is not None, "User Session should be created in DB upon login"

        # 2. Refresh Token Flow
        # Use cookie for refresh
        ac.cookies.set("refresh_token", refresh_token)
        refresh_response = await ac.post("/auth/refresh")
        assert refresh_response.status_code == 200, f"Refresh failed: {refresh_response.text}"
        new_tokens = refresh_response.json()
        assert new_tokens["access_token"] != tokens["access_token"]
        
        # Verify OLD session is invalidated (Rotation)
        await test_db.refresh(session)
        assert session.is_active == False, "Old session should be invalidated after refresh"
        
        # Verify NEW session exists
        result = await test_db.execute(select(UserSession).where(UserSession.user_id == admin_user.id).where(UserSession.is_active == True))
        new_session = result.scalars().first()
        assert new_session is not None
        assert new_session.id != session.id

        # 3. Logout
        ac.cookies.set("refresh_token", new_tokens["refresh_token"])
        logout_res = await ac.post("/auth/logout")
        assert logout_res.status_code == 200
        
        await test_db.refresh(new_session)
        assert new_session.is_active == False, "Session should be invalidated after logout"

@pytest.mark.asyncio
async def test_geolocation_enforcement(test_db: AsyncSession, regular_user_token):
    access_token, _, user = regular_user_token
    
    headers = {"Authorization": f"Bearer {access_token}"}
    
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        # 1. Configure Office Location
        await crud.set_global_setting(test_db, "office_latitude", "42.6977") # Sofia
        await crud.set_global_setting(test_db, "office_longitude", "23.3219")
        await crud.set_global_setting(test_db, "office_radius", "100") # 100 meters
        
        # 2. Clock In - Success (Inside radius)
        mutation_success = """
            mutation {
                clockIn(latitude: 42.69775, longitude: 23.32195) {
                    id
                    startTime
                }
            }
        """
        res = await ac.post("/graphql", json={"query": mutation_success}, headers=headers)
        assert res.status_code == 200
        data = res.json()
        assert "data" in data and data["data"].get("clockIn") is not None
        
        # Clock Out
        await ac.post("/graphql", json={"query": "mutation { clockOut { id } }"}, headers=headers)

        # 3. Clock In - Fail (Outside radius)
        mutation_fail = """
            mutation {
                clockIn(latitude: 42.1354, longitude: 24.7453) {
                    id
                }
            }
        """
        res_fail = await ac.post("/graphql", json={"query": mutation_fail}, headers=headers)
        data_fail = res_fail.json()
        assert data_fail["data"].get("clockIn") is None
        assert "errors" in data_fail
        assert "извън офис зоната" in data_fail["errors"][0]["message"]

@pytest.mark.asyncio
async def test_leave_management_flow(test_db: AsyncSession, regular_user_token):
    access_token, _, user = regular_user_token
    headers = {"Authorization": f"Bearer {access_token}"}
    
    # Ensure balance
    balance = await crud.get_leave_balance(test_db, user.id, 2026)
    balance.total_days = 20
    balance.used_days = 0
    test_db.add(balance)
    await test_db.commit()

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        # 1. Request Leave
        req_mut = """
            mutation {
                requestLeave(leaveInput: {
                    startDate: "2026-06-01",
                    endDate: "2026-06-05",
                    leaveType: "paid_leave",
                    reason: "Summer vacation"
                }) {
                    id
                    status
                }
            }
        """
        res = await ac.post("/graphql", json={"query": req_mut}, headers=headers)
        data = res.json()
        assert "data" in data and data["data"].get("requestLeave") is not None
        req_id = data["data"]["requestLeave"]["id"]
        assert data["data"]["requestLeave"]["status"] == "pending"

        # 2. Approve (As Admin)
        await crud.update_leave_request_status(test_db, int(req_id), "approved")
        
        # Verify Balance Deducted
        await test_db.refresh(balance)
        assert balance.used_days == 5
        
        # 3. Cancel (As User)
        cancel_mut = f"""
            mutation {{
                cancelLeaveRequest(requestId: {req_id}) {{
                    id
                    status
                }}
            }}
        """
        res_cancel = await ac.post("/graphql", json={"query": cancel_mut}, headers=headers)
        data_cancel = res_cancel.json()
        assert data_cancel["data"]["cancelLeaveRequest"]["status"] == "cancelled"
        
        # Verify Balance Refunded
        await test_db.refresh(balance)
        assert balance.used_days == 0
