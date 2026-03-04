import pytest
from datetime import datetime, timedelta
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession
from backend.database.models import TimeLog

@pytest.mark.asyncio
async def test_update_user_payroll(client: TestClient, test_db: AsyncSession, create_admin_and_login, regular_user):
    _, admin_token = create_admin_and_login
    
    query = """
        mutation UpdateUserPayroll($userId: Int!, $hourlyRate: Decimal!, $overtimeMultiplier: Decimal!, $standardHoursPerDay: Int!) {
            updateUserPayroll(userId: $userId, hourlyRate: $hourlyRate, overtimeMultiplier: $overtimeMultiplier, standardHoursPerDay: $standardHoursPerDay) {
                id
                hourlyRate
                overtimeMultiplier
                standardHoursPerDay
            }
        }
    """
    variables = {
        "userId": regular_user.id,
        "hourlyRate": "20.00",
        "overtimeMultiplier": "1.0",
        "standardHoursPerDay": 8
    }
    headers = {"Authorization": f"Bearer {admin_token}"}
    response = client.post("/graphql", json={"query": query, "variables": variables}, headers=headers)
    assert response.status_code == 200
    data = response.json()["data"]["updateUserPayroll"]
    assert data["hourlyRate"] == "20.00"
    assert data["overtimeMultiplier"] == "1.0"
    assert data["standardHoursPerDay"] == 8

@pytest.mark.asyncio
async def test_generate_payslip(client: TestClient, test_db: AsyncSession, create_admin_and_login, regular_user):
    _, admin_token = create_admin_and_login
    
    # 1. Setup Payroll Config
    setup_query = """
        mutation UpdateUserPayroll($userId: Int!, $hourlyRate: Decimal!, $overtimeMultiplier: Decimal!, $standardHoursPerDay: Int!) {
            updateUserPayroll(userId: $userId, hourlyRate: $hourlyRate, overtimeMultiplier: $overtimeMultiplier, standardHoursPerDay: $standardHoursPerDay) {
                id
            }
        }
    """
    client.post("/graphql", json={"query": setup_query, "variables": {
        "userId": regular_user.id,
        "hourlyRate": "10.00",
        "overtimeMultiplier": "1.0",
        "standardHoursPerDay": 8
    }}, headers={"Authorization": f"Bearer {admin_token}"})
    
    # 2. Insert TimeLogs directly into DB
    today = datetime.utcnow().date()
    start_of_month = datetime(today.year, today.month, 1)
    
    # Day 1: 8 hours (Regular)
    log1 = TimeLog(
        user_id=regular_user.id,
        start_time=start_of_month + timedelta(hours=9),
        end_time=start_of_month + timedelta(hours=17)
    )
    # Day 2: 10 hours (8 Regular + 2 Overtime)
    log2 = TimeLog(
        user_id=regular_user.id,
        start_time=start_of_month + timedelta(days=1, hours=9),
        end_time=start_of_month + timedelta(days=1, hours=19)
    )
    
    test_db.add(log1)
    test_db.add(log2)
    await test_db.commit()
    
    # 3. Generate Payslip
    query = """
        mutation GeneratePayslip($userId: Int!, $startDate: Date!, $endDate: Date!) {
            generatePayslip(userId: $userId, startDate: $startDate, endDate: $endDate) {
                totalRegularHours
                totalOvertimeHours
                regularAmount
                overtimeAmount
                totalAmount
            }
        }
    """
    
    end_of_month = start_of_month + timedelta(days=28) # Ensure coverage
    
    variables = {
        "userId": regular_user.id,
        "startDate": start_of_month.strftime("%Y-%m-%d"),
        "endDate": end_of_month.strftime("%Y-%m-%d")
    }
    
    response = client.post("/graphql", json={"query": query, "variables": variables}, headers={"Authorization": f"Bearer {admin_token}"})
    
    assert response.status_code == 200
    if "errors" in response.json():
        print(response.json()["errors"])
    
    data = response.json()["data"]["generatePayslip"]
    
    # Expected:
    # Regular Hours: 8 (Day 1) + 8 (Day 2) = 16
    # Overtime Hours: 0 (Day 1) + 2 (Day 2) = 2
    # Rate: 10
    # Overtime Rate: 10 * 1.5 = 15
    # Regular Amount: 16 * 10 = 160
    # Overtime Amount: 2 * 15 = 30
    # Total: 190
    
    assert float(data["totalRegularHours"]) == 16.0
    assert float(data["totalOvertimeHours"]) == 2.0
    assert float(data["regularAmount"]) == 160.0
    assert float(data["overtimeAmount"]) == 30.0
    assert float(data["totalAmount"]) == 190.0
