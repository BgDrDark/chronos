import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from backend.main import app
from backend.database.models import User, Role, Company, Gateway, AccessZone, AccessDoor
from backend.database.database import get_db
from sqlalchemy import select, delete, insert

@pytest_asyncio.fixture
async def test_client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

@pytest.mark.asyncio
async def test_gateway_registration_flow(test_client):
    """Тест за автоматична регистрация и откриване"""
    hw_uuid = "test-unique-hwid-999"
    payload = {
        "hardware_uuid": hw_uuid,
        "ip_address": "127.0.0.1",
        "local_hostname": "test-box",
        "terminal_port": 1424,
        "web_port": 8889
    }
    
    # 1. Първоначална регистрация
    response = await test_client.post("/gateways/register", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["hardware_uuid"] == hw_uuid
    assert "api_key" in data
    gateway_id = data["id"]

    # 2. Повторна регистрация (трябва да разпознае устройството и да върне ID)
    response = await test_client.post("/gateways/register", json=payload)
    assert response.status_code == 400
    error_data = response.json()["detail"]
    assert error_data["id"] == gateway_id
    assert "api_key" in error_data

@pytest.mark.asyncio
async def test_gateway_config_sync(test_client):
    """Тест на конфигурационния ендпоинт за Fleet Sync"""
    # Регистрираме гейтуей
    reg_res = await test_client.post("/gateways/register", json={"hardware_uuid": "sync-test-uuid"})
    gw_id = reg_res.json()["id"]

    # Проверяваме празна конфигурация
    response = await test_client.get(f"/gateways/{gw_id}/config")
    assert response.status_code == 200
    data = response.json()
    assert data["gateway_id"] == gw_id
    assert "access_control" in data
    assert len(data["access_control"]["zones"]) == 0
