import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch, AsyncMock

from backend.database.models import Company, AccessZone, AccessDoor, AccessCode, Gateway, AccessLog
from backend import crud, schemas

# Fixture to setup company and assign to admin
@pytest.fixture
async def setup_company(test_db: AsyncSession, create_admin_and_login):
    _, admin_user = create_admin_and_login
    
    # Create a company
    company = await crud.create_company(
        test_db, 
        name="Test Company Access", 
        eik="123456789", 
        vat_number="BG123456789"
    )
    
    # Assign admin to company
    admin_user.company_id = company.id
    test_db.add(admin_user)
    await test_db.commit()
    await test_db.refresh(admin_user)
    
    return company

@pytest.mark.asyncio
async def test_access_zone_lifecycle(client: TestClient, test_db: AsyncSession, create_admin_and_login, setup_company):
    _, token = create_admin_and_login
    headers = {"Authorization": f"Bearer {token}"}
    
    # 1. Create Zone
    create_query = """
        mutation CreateZone($input: AccessZoneInput!) {
            createAccessZone(input: $input) {
                id
                zoneId
                name
                level
                antiPassbackEnabled
            }
        }
    """
    create_vars = {
        "input": {
            "zoneId": "zone_test_1",
            "name": "Test Zone 1",
            "level": 1,
            "antiPassbackEnabled": True,
            "antiPassbackType": "soft"
        }
    }
    
    response = client.post("/graphql", json={"query": create_query, "variables": create_vars}, headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert "data" in data
    assert data["data"]["createAccessZone"]["zoneId"] == "zone_test_1"
    zone_id = data["data"]["createAccessZone"]["id"]
    
    # 2. List Zones
    list_query = """
        query {
            accessZones {
                id
                zoneId
                name
            }
        }
    """
    response = client.post("/graphql", json={"query": list_query}, headers=headers)
    assert response.status_code == 200
    zones = response.json()["data"]["accessZones"]
    assert len(zones) > 0
    assert any(z["id"] == zone_id for z in zones)
    
    # 3. Delete Zone
    delete_query = """
        mutation DeleteZone($id: Int!) {
            deleteAccessZone(id: $id)
        }
    """
    response = client.post("/graphql", json={"query": delete_query, "variables": {"id": zone_id}}, headers=headers)
    assert response.status_code == 200
    assert response.json()["data"]["deleteAccessZone"] is True

@pytest.mark.asyncio
async def test_access_door_lifecycle(client: TestClient, test_db: AsyncSession, create_admin_and_login, setup_company):
    _, token = create_admin_and_login
    headers = {"Authorization": f"Bearer {token}"}
    
    # Setup Zone and Gateway first
    company = setup_company
    zone = AccessZone(zone_id="zone_door", name="Zone Door", company_id=company.id)
    test_db.add(zone)
    
    gateway = Gateway(name="GW-DOOR", hardware_uuid="hw-door-123", company_id=company.id)
    test_db.add(gateway)
    await test_db.commit()
    await test_db.refresh(zone)
    await test_db.refresh(gateway)
    
    # 1. Create Door
    create_query = """
        mutation CreateDoor($input: AccessDoorInput!) {
            createAccessDoor(input: $input) {
                id
                doorId
                name
                relayNumber
            }
        }
    """
    create_vars = {
        "input": {
            "doorId": "door_test_1",
            "name": "Test Door 1",
            "zoneDbId": zone.id,
            "gatewayId": gateway.id,
            "deviceId": "sr201_1",
            "relayNumber": 1
        }
    }
    
    response = client.post("/graphql", json={"query": create_query, "variables": create_vars}, headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert "data" in data
    assert data["data"]["createAccessDoor"]["doorId"] == "door_test_1"
    door_id = data["data"]["createAccessDoor"]["id"]
    
    # 2. List Doors
    list_query = """
        query {
            accessDoors {
                id
                doorId
                name
            }
        }
    """
    response = client.post("/graphql", json={"query": list_query}, headers=headers)
    assert response.status_code == 200
    doors = response.json()["data"]["accessDoors"]
    assert len(doors) > 0
    
    # 3. Delete Door
    delete_query = """
        mutation DeleteDoor($id: Int!) {
            deleteAccessDoor(id: $id)
        }
    """
    response = client.post("/graphql", json={"query": delete_query, "variables": {"id": door_id}}, headers=headers)
    assert response.status_code == 200
    assert response.json()["data"]["deleteAccessDoor"] is True

@pytest.mark.asyncio
async def test_access_code_lifecycle(client: TestClient, test_db: AsyncSession, create_admin_and_login, setup_company):
    _, token = create_admin_and_login
    headers = {"Authorization": f"Bearer {token}"}
    
    # 1. Create Code
    create_query = """
        mutation CreateCode($input: AccessCodeInput!) {
            createAccessCode(input: $input) {
                id
                code
                codeType
                usesRemaining
            }
        }
    """
    create_vars = {
        "input": {
            "codeType": "one_time",
            "zones": ["zone_1"],
            "usesRemaining": 1,
            "expiresHours": 24
        }
    }
    
    response = client.post("/graphql", json={"query": create_query, "variables": create_vars}, headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert "data" in data
    code_obj = data["data"]["createAccessCode"]
    assert len(code_obj["code"]) > 0
    code_id = code_obj["id"]
    
    # 2. Revoke Code
    revoke_query = """
        mutation RevokeCode($id: Int!) {
            revokeAccessCode(id: $id)
        }
    """
    response = client.post("/graphql", json={"query": revoke_query, "variables": {"id": code_id}}, headers=headers)
    assert response.status_code == 200
    assert response.json()["data"]["revokeAccessCode"] is True
    
    # 3. Delete Code
    delete_query = """
        mutation DeleteCode($id: Int!) {
            deleteAccessCode(id: $id)
        }
    """
    response = client.post("/graphql", json={"query": delete_query, "variables": {"id": code_id}}, headers=headers)
    assert response.status_code == 200
    assert response.json()["data"]["deleteAccessCode"] is True

@pytest.mark.asyncio
async def test_remote_door_trigger(client: TestClient, test_db: AsyncSession, create_admin_and_login, setup_company):
    _, token = create_admin_and_login
    headers = {"Authorization": f"Bearer {token}"}
    
    # Setup infrastructure
    company = setup_company
    zone = AccessZone(zone_id="zone_remote", name="Zone Remote", company_id=company.id)
    test_db.add(zone)
    
    gateway = Gateway(
        name="GW-REMOTE", 
        hardware_uuid="hw-remote-123", 
        company_id=company.id,
        ip_address="192.168.1.50",
        terminal_port=8080
    )
    test_db.add(gateway)
    await test_db.commit()
    await test_db.refresh(zone)
    await test_db.refresh(gateway)
    
    door = AccessDoor(
        door_id="door_remote_1",
        name="Remote Door",
        zone_db_id=zone.id,
        gateway_id=gateway.id,
        device_id="sr201_1",
        relay_number=1
    )
    test_db.add(door)
    await test_db.commit()
    await test_db.refresh(door)
    
    # Mock aiohttp request
    trigger_query = """
        mutation TriggerDoor($id: Int!) {
            triggerDoorRemote(id: $id)
        }
    """
    
    with patch("aiohttp.ClientSession.post") as mock_post:
        # Mock context manager
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.__aenter__.return_value = mock_response
        mock_post.return_value = mock_response
        
        response = client.post(
            "/graphql", 
            json={"query": trigger_query, "variables": {"id": door.id}}, 
            headers=headers
        )
        
        assert response.status_code == 200
        assert response.json()["data"]["triggerDoorRemote"] is True
        
        # Verify URL called
        expected_url = "http://192.168.1.50:8080/access/doors/door_remote_1/trigger"
        mock_post.assert_called_once()
        args, kwargs = mock_post.call_args
        assert args[0] == expected_url

@pytest.mark.asyncio
async def test_sync_logs_endpoint(client: TestClient, test_db: AsyncSession, create_admin_and_login, setup_company):
    # Setup Gateway
    company = setup_company
    gateway = Gateway(name="GW-LOGS", hardware_uuid="hw-logs-123", company_id=company.id)
    test_db.add(gateway)
    await test_db.commit()
    await test_db.refresh(gateway)
    
    # Log Data
    log_data = [
        {
            "timestamp": datetime.utcnow().isoformat(),
            "user_id": "user_123",
            "action": "enter",
            "result": "granted",
            "zone_id": "zone_1",
            "method": "qr_scan"
        },
        {
            "timestamp": datetime.utcnow().isoformat(),
            "user_id": "user_456",
            "action": "exit",
            "result": "granted",
            "zone_id": "zone_1",
            "method": "qr_scan"
        }
    ]
    
    # Call Sync Endpoint
    response = client.post(f"/gateways/{gateway.id}/access/sync-logs", json=log_data)
    assert response.status_code == 200
    assert response.json()["count"] == 2
    
    # Verify DB
    logs = (await test_db.execute(select(AccessLog).where(AccessLog.gateway_id == gateway.id))).scalars().all()
    assert len(logs) == 2
    assert logs[0].user_id == "user_123"
    assert logs[1].user_id == "user_456"
