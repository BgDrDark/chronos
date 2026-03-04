import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession
import datetime

@pytest.mark.asyncio
async def test_add_bonus(client: TestClient, test_db: AsyncSession, create_admin_and_login):
    admin_user, token = create_admin_and_login
    
    query = """
        mutation AddBonus($userId: Int!, $amount: Float!, $date: Date!, $description: String) {
            addBonus(input: { userId: $userId, amount: $amount, date: $date, description: $description }) {
                id
                amount
                date
                description
            }
        }
    """
    variables = {
        "userId": admin_user.id,
        "amount": 100.50,
        "date": "2026-01-01",
        "description": "Test Bonus"
    }
    headers = {"Authorization": f"Bearer {token}"}
    response = client.post("/graphql", json={"query": query, "variables": variables}, headers=headers)
    
    assert response.status_code == 200
    data = response.json()["data"]["addBonus"]
    assert data["amount"] == 100.5
    assert data["date"] == "2026-01-01"
    assert data["description"] == "Test Bonus"

@pytest.mark.asyncio
async def test_set_monthly_work_days(client: TestClient, test_db: AsyncSession, create_admin_and_login):
    _, token = create_admin_and_login
    
    query = """
        mutation SetMonthlyWorkDays($year: Int!, $month: Int!, $daysCount: Int!) {
            setMonthlyWorkDays(input: { year: $year, month: $month, daysCount: $daysCount }) {
                id
                year
                month
                daysCount
            }
        }
    """
    variables = {
        "year": 2026,
        "month": 1,
        "daysCount": 21
    }
    headers = {"Authorization": f"Bearer {token}"}
    response = client.post("/graphql", json={"query": query, "variables": variables}, headers=headers)
    
    assert response.status_code == 200
    data = response.json()["data"]["setMonthlyWorkDays"]
    assert data["year"] == 2026
    assert data["month"] == 1
    assert data["daysCount"] == 21

@pytest.mark.asyncio
async def test_my_daily_stats(client: TestClient, test_db: AsyncSession, create_admin_and_login):
    _, token = create_admin_and_login
    
    query = """
        query MyDailyStats($startDate: Date!, $endDate: Date!) {
            myDailyStats(startDate: $startDate, endDate: $endDate) {
                date
                totalWorkedHours
                regularHours
                overtimeHours
                shiftName
            }
        }
    """
    # Test for a 3-day range
    today = datetime.date.today()
    start_date = today - datetime.timedelta(days=2)
    variables = {
        "startDate": start_date.isoformat(),
        "endDate": today.isoformat()
    }
    headers = {"Authorization": f"Bearer {token}"}
    response = client.post("/graphql", json={"query": query, "variables": variables}, headers=headers)
    
    assert response.status_code == 200
    data = response.json()["data"]["myDailyStats"]
    assert len(data) == 3
    for stat in data:
        assert "totalWorkedHours" in stat
        assert "regularHours" in stat
        assert "overtimeHours" in stat
