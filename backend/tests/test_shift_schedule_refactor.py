"""Integration tests for Shift & Schedule Refactor (plan items 1.1-3.3)"""
import asyncio

import httpx

BASE_URL = "http://localhost:14240"
GRAPHQL_URL = f"{BASE_URL}/graphql"
AUTH_URL = f"{BASE_URL}/auth/token"

TEST_EMAIL = "admin@example.com"
TEST_PASSWORD = "admin1234"


async def get_admin_session() -> tuple[httpx.AsyncClient, str, str, str]:
    """Login and return (client, token, csrf_token, session_cookie)"""
    client = httpx.AsyncClient()

    # Get CSRF cookie
    await client.get(f"{BASE_URL}/health")
    csrf_token = client.cookies.get("csrf_token", "")

    # Login
    response = await client.post(
        AUTH_URL,
        data={"username": TEST_EMAIL, "password": TEST_PASSWORD},
    )
    assert response.status_code == 200, f"Login failed: {response.text}"
    token = response.json()["access_token"]

    return client, token, csrf_token, ""


async def gql_query(client: httpx.AsyncClient, query: str, variables: dict = None, token: str = None) -> dict:
    """Execute GraphQL query with proper CSRF handling"""
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"

    # CSRF token is already in client.cookies from the /health request
    # httpx will automatically send cookies with subsequent requests

    response = await client.post(
        GRAPHQL_URL,
        json={"query": query, "variables": variables or {}},
        headers=headers,
    )
    assert response.status_code == 200, f"GraphQL error: {response.text}"
    return response.json()


class TestShiftRefactor:
    """Tests for shift & schedule refactor"""

    async def test_1_create_shift_with_all_params(self, client, token, csrf_token):
        """Test 1.1: Create shift with custom tolerance/break/pay_multiplier + overnight"""
        query = """
        mutation CreateShift($name: String!, $startTime: Time!, $endTime: Time!, 
                           $toleranceMinutes: Int, $breakDurationMinutes: Int,
                           $payMultiplier: Decimal, $shiftType: String, $overnight: Boolean) {
            createShift(name: $name, startTime: $startTime, endTime: $endTime,
                       toleranceMinutes: $toleranceMinutes, breakDurationMinutes: $breakDurationMinutes,
                       payMultiplier: $payMultiplier, shiftType: $shiftType, overnight: $overnight) {
                id name startTime endTime toleranceMinutes breakDurationMinutes 
                payMultiplier shiftType overnight
            }
        }
        """
        result = await gql_query(client, query, {
            "name": "Нощна смяна тест",
            "startTime": "22:00:00",
            "endTime": "06:00:00",
            "toleranceMinutes": 30,
            "breakDurationMinutes": 45,
            "payMultiplier": "1.5",
            "shiftType": "regular",
            "overnight": True,
        }, token, csrf_token)

        assert "errors" not in result, f"GraphQL errors: {result.get('errors')}"
        shift = result["data"]["createShift"]
        assert shift["name"] == "Нощна смяна тест"
        assert shift["toleranceMinutes"] == 30
        assert shift["breakDurationMinutes"] == 45
        assert shift["payMultiplier"] == "1.5"
        assert shift["overnight"] is True
        self.test_shift_id = shift["id"]
        print("✅ Test 1.1 PASSED: Create shift with all params")

    async def test_1b_create_shift_without_overnight_fails(self, client, token, csrf_token):
        """Test 2.1: Create shift end < start without overnight should fail"""
        query = """
        mutation CreateShift($name: String!, $startTime: Time!, $endTime: Time!) {
            createShift(name: $name, startTime: $startTime, endTime: $endTime) { id }
        }
        """
        result = await gql_query(client, query, {
            "name": "Invalid shift",
            "startTime": "22:00:00",
            "endTime": "06:00:00",
        }, token, csrf_token)

        assert "errors" in result, "Should have failed without overnight=True"
        print("✅ Test 2.1 PASSED: Shift validation (end < start without overnight)")

    async def test_2_update_shift_with_overnight(self, client, token, csrf_token):
        """Test update shift with overnight field"""
        query = """
        query Shifts { shifts { id name } }
        """
        result = await gql_query(client, query, token=token, csrf_token=csrf_token)
        assert "errors" not in result
        shifts = result["data"]["shifts"]
        assert len(shifts) > 0
        shift_id = shifts[0]["id"]

        update_query = """
        mutation UpdateShift($id: Int!, $name: String!, $startTime: Time!, $endTime: Time!, $overnight: Boolean) {
            updateShift(id: $id, name: $name, startTime: $startTime, endTime: $endTime, overnight: $overnight) {
                id name overnight
            }
        }
        """
        result = await gql_query(client, update_query, {
            "id": shift_id,
            "name": "Updated Shift",
            "startTime": "08:00:00",
            "endTime": "16:00:00",
            "overnight": False,
        }, token, csrf_token)

        assert "errors" not in result, f"Update failed: {result.get('errors')}"
        assert result["data"]["updateShift"]["name"] == "Updated Shift"
        assert result["data"]["updateShift"]["overnight"] is False
        print("✅ Test 2 PASSED: Update shift with overnight")

    async def test_3_shifts_query_company_filter(self, client, token, csrf_token):
        """Test 4.1: Shifts query filters by company_id"""
        query = """
        query Shifts { shifts { id name } }
        """
        result = await gql_query(client, query, token=token, csrf_token=csrf_token)
        assert "errors" not in result
        shifts = result["data"]["shifts"]
        assert len(shifts) > 0
        print(f"✅ Test 4.1 PASSED: Got {len(shifts)} shifts (company filtered)")

    async def test_4_create_schedule_template(self, client, token, csrf_token):
        """Create a schedule template for testing"""
        query = """
        query Shifts { shifts { id } }
        """
        result = await gql_query(client, query, token=token, csrf_token=csrf_token)
        shifts = result["data"]["shifts"]
        shift_id = shifts[0]["id"]

        create_query = """
        mutation CreateTemplate($name: String!, $description: String, $items: [ScheduleTemplateItemInput!]!) {
            createScheduleTemplate(name: $name, description: $description, items: $items) {
                id name items { dayIndex shiftId }
            }
        }
        """
        result = await gql_query(client, create_query, {
            "name": "Test Template 5-day",
            "description": "Test template for refactor tests",
            "items": [
                {"dayIndex": 0, "shiftId": shift_id},
                {"dayIndex": 1, "shiftId": shift_id},
                {"dayIndex": 2, "shiftId": shift_id},
                {"dayIndex": 3, "shiftId": shift_id},
                {"dayIndex": 4, "shiftId": shift_id},
                {"dayIndex": 5, "shiftId": None},
                {"dayIndex": 6, "shiftId": None},
            ],
        }, token, csrf_token)

        assert "errors" not in result, f"Create template failed: {result.get('errors')}"
        template = result["data"]["createScheduleTemplate"]
        assert template["name"] == "Test Template 5-day"
        assert len(template["items"]) == 7
        self.template_id = template["id"]
        print(f"✅ Test: Created template ID={self.template_id}")

    async def test_5_update_schedule_template(self, client, token, csrf_token):
        """Test 2.2: Update schedule template"""
        if not hasattr(self, "template_id"):
            await self.test_4_create_schedule_template(client, token, csrf_token)

        query = """
        query Shifts { shifts { id } }
        """
        result = await gql_query(client, query, token=token, csrf_token=csrf_token)
        shift_id = result["data"]["shifts"][0]["id"]

        update_query = """
        mutation UpdateTemplate($id: Int!, $name: String, $items: [ScheduleTemplateItemInput!]) {
            updateScheduleTemplate(id: $id, name: $name, items: $items) {
                id name items { dayIndex shiftId }
            }
        }
        """
        result = await gql_query(client, update_query, {
            "id": self.template_id,
            "name": "Updated Template",
            "items": [
                {"dayIndex": 0, "shiftId": shift_id},
                {"dayIndex": 1, "shiftId": None},
                {"dayIndex": 2, "shiftId": shift_id},
                {"dayIndex": 3, "shiftId": None},
                {"dayIndex": 4, "shiftId": shift_id},
            ],
        }, token, csrf_token)

        assert "errors" not in result, f"Update template failed: {result.get('errors')}"
        template = result["data"]["updateScheduleTemplate"]
        assert template["name"] == "Updated Template"
        assert len(template["items"]) == 5
        print("✅ Test 2.2 PASSED: Update schedule template")

    async def test_6_template_preview(self, client, token, csrf_token):
        """Test 2.4: Template preview query"""
        if not hasattr(self, "template_id"):
            await self.test_4_create_schedule_template(client, token, csrf_token)

        query = """
        query TemplatePreview($templateId: Int!, $startDate: Date!, $endDate: Date!) {
            templatePreview(templateId: $templateId, startDate: $startDate, endDate: $endDate) {
                date shiftId shiftName dayIndex
            }
        }
        """
        result = await gql_query(client, query, {
            "templateId": self.template_id,
            "startDate": "2026-06-01",
            "endDate": "2026-06-07",
        }, token, csrf_token)

        assert "errors" not in result, f"Template preview failed: {result.get('errors')}"
        preview = result["data"]["templatePreview"]
        assert len(preview) == 7
        assert preview[0]["shiftName"] is not None
        print(f"✅ Test 2.4 PASSED: Template preview returned {len(preview)} items")

    async def test_7_set_work_schedule_unique_constraint(self, client, token, csrf_token):
        """Test 1.3: Unique constraint on work_schedules (user_id + date)"""
        query = """
        query Users { users { id } }
        """
        result = await gql_query(client, query, token=token, csrf_token=csrf_token)
        users = result["data"]["users"]
        user_id = users[0]["id"]

        query = """
        query Shifts { shifts { id } }
        """
        result = await gql_query(client, query, token=token, csrf_token=csrf_token)
        shift_id = result["data"]["shifts"][0]["id"]

        set_query = """
        mutation SetSchedule($userId: Int!, $shiftId: Int!, $date: Date!) {
            setWorkSchedule(userId: $userId, shiftId: $shiftId, date: $date) {
                id userId shiftId date
            }
        }
        """
        result1 = await gql_query(client, set_query, {
            "userId": user_id,
            "shiftId": shift_id,
            "date": "2026-06-15",
        }, token, csrf_token)
        assert "errors" not in result1, f"First set failed: {result1.get('errors')}"

        result2 = await gql_query(client, set_query, {
            "userId": user_id,
            "shiftId": shift_id,
            "date": "2026-06-15",
        }, token, csrf_token)
        assert "errors" not in result2, f"Second set failed: {result2.get('errors')}"

        verify_query = """
        query Schedules($userId: Int!, $startDate: Date!, $endDate: Date!) {
            workSchedules(userId: $userId, startDate: $startDate, endDate: $endDate) {
                id userId shiftId date
            }
        }
        """
        result3 = await gql_query(client, verify_query, {
            "userId": user_id,
            "startDate": "2026-06-15",
            "endDate": "2026-06-15",
        }, token, csrf_token)
        schedules = result3["data"]["workSchedules"]
        assert len(schedules) == 1, f"Expected 1 schedule, got {len(schedules)}"
        print("✅ Test 1.3 PASSED: Unique constraint works (no duplicates)")

    async def test_8_bulk_delete_schedules(self, client, token, csrf_token):
        """Test 2.3: Bulk delete schedules"""
        query = """
        query Users { users { id } }
        """
        result = await gql_query(client, query, token=token, csrf_token=csrf_token)
        users = result["data"]["users"][:3]

        query = """
        query Shifts { shifts { id } }
        """
        result = await gql_query(client, query, token=token, csrf_token=csrf_token)
        shift_id = result["data"]["shifts"][0]["id"]

        set_query = """
        mutation SetSchedule($userId: Int!, $shiftId: Int!, $date: Date!) {
            setWorkSchedule(userId: $userId, shiftId: $shiftId, date: $date) { id }
        }
        """
        for user in users:
            for day in ["2026-07-01", "2026-07-02", "2026-07-03"]:
                await gql_query(client, set_query, {
                    "userId": user["id"],
                    "shiftId": shift_id,
                    "date": day,
                }, token, csrf_token)

        verify_query = """
        query Schedules($startDate: Date!, $endDate: Date!) {
            workSchedules(startDate: $startDate, endDate: $endDate) { id }
        }
        """
        result = await gql_query(client, verify_query, {
            "startDate": "2026-07-01",
            "endDate": "2026-07-03",
        }, token, csrf_token)
        before_count = len(result["data"]["workSchedules"])
        assert before_count >= 9, f"Expected >= 9 schedules, got {before_count}"

        delete_query = """
        mutation BulkDelete($userIds: [Int!]!, $startDate: Date!, $endDate: Date!) {
            bulkDeleteSchedules(userIds: $userIds, startDate: $startDate, endDate: $endDate)
        }
        """
        result = await gql_query(client, delete_query, {
            "userIds": [u["id"] for u in users],
            "startDate": "2026-07-01",
            "endDate": "2026-07-03",
        }, token, csrf_token)
        assert "errors" not in result, f"Bulk delete failed: {result.get('errors')}"
        deleted = result["data"]["bulkDeleteSchedules"]
        assert deleted >= 9, f"Expected >= 9 deleted, got {deleted}"

        result = await gql_query(client, verify_query, {
            "startDate": "2026-07-01",
            "endDate": "2026-07-03",
        }, token, csrf_token)
        after_count = len(result["data"]["workSchedules"])
        assert after_count == 0, f"Expected 0 schedules, got {after_count}"
        print(f"✅ Test 2.3 PASSED: Bulk deleted {deleted} schedules")

    async def test_9_audit_log_exists(self, client, token, csrf_token):
        """Test 3.2: Audit log table exists"""
        from backend.database.database import AsyncSessionLocal
        from sqlalchemy import text

        async with AsyncSessionLocal() as db:
            result = await db.execute(text("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_name = 'schedule_audit_logs'
                )
            """))
            exists = result.scalar()
            assert exists, "schedule_audit_logs table does not exist"
            print("✅ Test 3.2 PASSED: Audit log table exists")


def run_tests():
    """Run all tests"""
    import sys
    sys.path.insert(0, "/home/niki/PycharmProjects/WorkingTime")

    test = TestShiftRefactor()
    loop = asyncio.new_event_loop()

    tests = [
        ("1.1 Create shift with all params", test.test_1_create_shift_with_all_params),
        ("1.1b Shift validation (end < start)", test.test_1b_create_shift_without_overnight_fails),
        ("2 Update shift with overnight", test.test_2_update_shift_with_overnight),
        ("4.1 Shifts company filter", test.test_3_shifts_query_company_filter),
        ("4 Create schedule template", test.test_4_create_schedule_template),
        ("2.2 Update schedule template", test.test_5_update_schedule_template),
        ("2.4 Template preview", test.test_6_template_preview),
        ("1.3 Unique constraint", test.test_7_set_work_schedule_unique_constraint),
        ("2.3 Bulk delete schedules", test.test_8_bulk_delete_schedules),
        ("3.2 Audit log table", test.test_9_audit_log_exists),
    ]

    client, token, csrf_token, _ = loop.run_until_complete(get_admin_session())
    passed = 0
    failed = 0

    for name, test_func in tests:
        try:
            loop.run_until_complete(test_func(client, token, csrf_token))
            passed += 1
        except Exception as e:
            print(f"❌ {name} FAILED: {e}")
            import traceback
            traceback.print_exc()
            failed += 1

    loop.run_until_complete(client.aclose())

    print(f"\n{'='*50}")
    print(f"Results: {passed} passed, {failed} failed, {passed+failed} total")
    print(f"{'='*50}")

    return failed == 0


if __name__ == "__main__":
    success = run_tests()
    exit(0 if success else 1)
