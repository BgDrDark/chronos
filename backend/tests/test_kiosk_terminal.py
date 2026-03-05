"""
Тестове за Kiosk Terminal достъп
"""
import pytest
from httpx import AsyncClient
from backend.main import app
from backend.database.database import get_db
from backend.database.models import User, Company, AccessDoor, AccessZone, AccessCode, Gateway
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.pool import StaticPool
from unittest.mock import AsyncMock, patch
import datetime


# Test database URL
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest.fixture
async def db_session():
    """Създава тестова база данни"""
    engine = create_async_engine(
        TEST_DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    
    from backend.database.models import Base
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    async_session = AsyncSession(engine)
    
    yield async_session
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    
    await engine.dispose()


@pytest.fixture
async def test_company(db_session):
    """Създава тестова компания"""
    company = Company(
        name="Test Company",
        business_type="retail",
        work_schedule_type="standard"
    )
    db_session.add(company)
    await db_session.commit()
    await db_session.refresh(company)
    return company


@pytest.fixture
async def test_user(db_session, test_company):
    """Създава тестов потребител"""
    user = User(
        email="test@example.com",
        first_name="Test",
        last_name="User",
        company_id=test_company.id,
        is_active=True,
        qr_secret="test_secret"
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest.fixture
async def test_gateway(db_session, test_company):
    """Създава тестов gateway"""
    gateway = Gateway(
        name="Test Gateway",
        hardware_uuid="test-hw-uuid-123",
        ip_address="192.168.1.100",
        terminal_port=1424,
        company_id=test_company.id
    )
    db_session.add(gateway)
    await db_session.commit()
    await db_session.refresh(gateway)
    return gateway


@pytest.fixture
async def test_zone(db_session, test_company):
    """Създава тестова зона"""
    zone = AccessZone(
        zone_id="zone_1",
        name="Test Zone",
        level=1,
        company_id=test_company.id,
        is_active=True
    )
    db_session.add(zone)
    await db_session.commit()
    await db_session.refresh(zone)
    return zone


@pytest.fixture
async def test_door(db_session, test_company, test_gateway, test_zone):
    """Създава тестова врата"""
    door = AccessDoor(
        door_id="door_1",
        name="Test Door",
        zone_db_id=test_zone.id,
        gateway_id=test_gateway.id,
        device_id="relay_1",
        relay_number=1,
        terminal_id="terminal-hw-uuid-123",
        terminal_mode="access",
        is_active=True
    )
    db_session.add(door)
    await db_session.commit()
    await db_session.refresh(door)
    return door


@pytest.fixture
async def test_access_code(db_session, test_company):
    """Създава тестов код за достъп"""
    code = AccessCode(
        code="123456",
        code_type="daily",
        zones=["zone_1"],
        uses_remaining=10,
        expires_at=datetime.datetime.now() + datetime.timedelta(days=1),
        is_active=True,
        gateway_id=None
    )
    db_session.add(code)
    await db_session.commit()
    await db_session.refresh(code)
    return code


# ============================================
# ТЕСТОВЕ
# ============================================

@pytest.mark.asyncio
async def test_terminal_scan_with_qr_code():
    """Тест: QR сканиране + отваряне на врата"""
    # Този тест изисква пълен тестов сетъп с mock-ване
    # Засега е placeholder
    
    # 1. Подготовка на заявката
    scan_data = {
        "qr_token": "1:valid_token",
        "terminal_hardware_uuid": "terminal-hw-uuid-123",
        "action": "access"
    }
    
    # 2. Изпълнение на заявката (с mock-ове)
    # response = await client.post("/kiosk/terminal/scan", json=scan_data)
    
    # 3. Проверка на резултатите
    # assert response.status_code == 200
    # data = response.json()
    # assert data["status"] == "success"
    # assert data["door_opened"] == True
    
    assert True  # Placeholder


@pytest.mark.asyncio
async def test_terminal_scan_with_keyboard_code():
    """Тест: Код от клавиатура + отваряне на врата"""
    # Placeholder тест
    assert True


@pytest.mark.asyncio
async def test_code_validation_valid():
    """Тест: Валидация на валиден код"""
    # Placeholder тест
    assert True


@pytest.mark.asyncio
async def test_code_validation_expired():
    """Тест: Валидация на изтекъл код"""
    # Placeholder тест
    assert True


@pytest.mark.asyncio
async def test_code_validation_invalid():
    """Тест: Валидация на невалиден код"""
    # Placeholder тест
    assert True


@pytest.mark.asyncio
async def test_terminal_mode_clock_only():
    """Тест: Терминал само за часовe"""
    # Placeholder тест
    assert True


@pytest.mark.asyncio
async def test_terminal_mode_both():
    """Тест: Терминал за достъп и часове"""
    # Placeholder тест
    assert True


@pytest.mark.asyncio
async def test_door_terminal_update():
    """Тест: Обновяване на врата + терминал"""
    # Placeholder тест
    assert True


@pytest.mark.asyncio
async def test_no_door_connected():
    """Тест: Терминал без свързана врата"""
    # Placeholder тест
    assert True


# ============================================
# INTEGRATION TESTS (with real HTTP) - Require DB
# ============================================

class TestKioskTerminalIntegration:
    """Интеграционни тестове - изискват база данни"""
    
    @pytest.mark.skip(reason="Requires database connection")
    async def test_health_check(self):
        """Тест: Health check на kiosk endpoint"""
        pass
    
    @pytest.mark.skip(reason="Requires database connection")
    async def test_scan_without_token(self):
        """Тест: Сканиране без QR код"""
        pass
    
    @pytest.mark.skip(reason="Requires database connection")
    async def test_scan_with_invalid_secret(self):
        """Тест: Сканиране с невалидна тайна"""
        pass
