import pytest
from datetime import date, timedelta
from httpx import AsyncClient, ASGITransport
from backend.main import app

@pytest.mark.anyio
async def test_export_payroll_xlsx_permissions(client, regular_user):
    """Проверка дали обикновен потребител има достъп до Excel експорт."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        # Логин като обикновен потребител
        response = await ac.post(
            "/auth/token",
            data={"username": "user@example.com", "password": "userpassword"}
        )
        token = response.json()["access_token"]
        
        # Опит за достъп
        start = date.today().isoformat()
        end = date.today().isoformat()
        response = await ac.get(
            f"/export/payroll/xlsx?start_date={start}&end_date={end}",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 403

@pytest.mark.anyio
async def test_export_payroll_xlsx_admin(create_admin_and_login):
    """Проверка дали администратор може да свали Excel файл."""
    admin, token = await create_admin_and_login
    
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        start = (date.today() - timedelta(days=30)).isoformat()
        end = date.today().isoformat()
        
        response = await ac.get(
            f"/export/payroll/xlsx?start_date={start}&end_date={end}",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 200
        assert response.headers["content-type"] == "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        assert response.content.startswith(b"PK") # Стандартно за Excel/Zip файлове
