"""TDD Tests for RBAC Permission System

Tests PermissionGuardMiddleware, permission helpers, and PermissionService.
Validates that all mutations are properly protected with RBAC.
"""

import sys
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import pytest
from backend.auth.rbac_service import PermissionService
from backend.exceptions import PermissionDeniedException
from backend.chronos_graphql.permission_middleware import (
    COMPANY_SCOPED_OPERATIONS,
    PERMISSION_MAPPING,
    PermissionGuardMiddleware,
)
from backend.chronos_graphql.utils.permission_checker import (
    check_company_access,
    get_current_user,
    require_permission,
)


class TestPermissionMapping:
    """Test PERMISSION_MAPPING completeness and correctness"""

    def test_permission_mapping_has_time_tracking(self):
        """Verify time tracking mutations are mapped"""
        assert "clockIn" in PERMISSION_MAPPING
        assert PERMISSION_MAPPING["clockIn"] == "timelogs:create_own"
        assert "clockOut" in PERMISSION_MAPPING
        assert "adminClockIn" in PERMISSION_MAPPING

    def test_permission_mapping_has_payroll(self):
        """Verify payroll mutations are mapped"""
        assert "calculatePayroll" in PERMISSION_MAPPING
        assert PERMISSION_MAPPING["calculatePayroll"] == "payroll:create"
        assert "generatePayslip" in PERMISSION_MAPPING
        assert "addBonus" in PERMISSION_MAPPING

    def test_permission_mapping_has_leave(self):
        """Verify leave mutations are mapped"""
        assert "requestLeave" in PERMISSION_MAPPING
        assert PERMISSION_MAPPING["requestLeave"] == "leaves:create_own"
        assert "approveLeave" in PERMISSION_MAPPING
        assert "rejectLeave" in PERMISSION_MAPPING

    def test_permission_mapping_has_user_management(self):
        """Verify user management mutations are mapped"""
        assert "createUser" in PERMISSION_MAPPING
        assert PERMISSION_MAPPING["createUser"] == "users:create"
        assert "updateUser" in PERMISSION_MAPPING
        assert "deleteUser" in PERMISSION_MAPPING

    def test_permission_mapping_has_accounting(self):
        """Verify accounting mutations are mapped"""
        assert "createInvoice" in PERMISSION_MAPPING
        assert PERMISSION_MAPPING["createInvoice"] == "accounting:create"
        assert "updateInvoice" in PERMISSION_MAPPING
        assert "deleteInvoice" in PERMISSION_MAPPING

    def test_permission_mapping_count(self):
        """Verify we have 200+ mutations mapped"""
        assert len(PERMISSION_MAPPING) >= 200, f"Expected 200+ mappings, got {len(PERMISSION_MAPPING)}"


class TestCompanyScopedOperations:
    """Test COMPANY_SCOPED_OPERATIONS set"""

    def test_company_scoped_has_user_operations(self):
        """Verify user operations are company-scoped"""
        assert "createUser" in COMPANY_SCOPED_OPERATIONS
        assert "updateUser" in COMPANY_SCOPED_OPERATIONS

    def test_company_scoped_has_time_tracking(self):
        """Verify time tracking operations are company-scoped"""
        assert "clockIn" in COMPANY_SCOPED_OPERATIONS
        assert "clockOut" in COMPANY_SCOPED_OPERATIONS

    def test_company_scoped_has_payroll(self):
        """Verify payroll operations are company-scoped"""
        assert "calculatePayroll" in COMPANY_SCOPED_OPERATIONS
        assert "generatePayslip" in COMPANY_SCOPED_OPERATIONS


class TestPermissionGuardMiddleware:
    """Test PermissionGuardMiddleware"""

    @pytest.fixture
    def middleware(self):
        """Create middleware instance"""
        return PermissionGuardMiddleware()

    @pytest.fixture
    def mock_info(self):
        """Create mock Strawberry Info object"""
        info = MagicMock()
        info.operation.operation = "mutation"
        info.field_name = "createUser"
        info.context = {
            "current_user": MagicMock(
                id=1,
                company_id=10,
                role=MagicMock(name="user"),
            )
        }
        return info

    def test_middleware_instantiation(self, middleware):
        """Verify middleware can be instantiated"""
        assert middleware is not None

    @pytest.mark.asyncio
    async def test_middleware_skips_queries(self, middleware):
        """Verify middleware skips query operations"""
        mock_info = MagicMock()
        mock_info.operation.operation = "query"
        mock_info.field_name = "getUsers"

        # Should not raise exception
        async def next_resolver():
            return "result"

        result = await middleware.resolve(next_resolver, None, mock_info, [], {})
        assert result == "result"

    @pytest.mark.asyncio
    async def test_middleware_allows_super_admin(self, middleware):
        """Verify super_admin bypasses permission checks"""
        mock_info = MagicMock()
        mock_info.operation.operation = "mutation"
        mock_info.field_name = "createUser"
        mock_info.context = {
            "current_user": MagicMock(
                id=1,
                company_id=10,
                role=MagicMock(name="super_admin"),
            )
        }

        async def next_resolver():
            return "success"

        with patch.object(PermissionService, "check_permission", return_value=True):
            result = await middleware.resolve(next_resolver, None, mock_info, [], {})
            assert result == "success"


class TestPermissionHelpers:
    """Test permission helper functions"""

    @pytest.fixture
    def mock_info(self):
        """Create mock Info object"""
        info = MagicMock()
        info.context = {
            "current_user": MagicMock(
                id=1,
                company_id=10,
                role=MagicMock(name="user"),
            )
        }
        return info

    @pytest.mark.asyncio
    async def test_get_current_user(self, mock_info):
        """Verify get_current_user extracts user from context"""
        user = get_current_user(mock_info)
        assert user.id == 1
        assert user.company_id == 10

    @pytest.mark.asyncio
    async def test_require_permission_success(self, mock_info):
        """Verify require_permission succeeds when user has permission"""
        with patch.object(PermissionService, "check_permission", return_value=True):
            # Should not raise exception
            await require_permission(mock_info, "users:create")

    @pytest.mark.asyncio
    async def test_require_permission_denied(self, mock_info):
        """Verify require_permission raises when user lacks permission"""
        with patch.object(PermissionService, "check_permission", return_value=False):
            with pytest.raises(PermissionDeniedException):
                await require_permission(mock_info, "users:delete")

    @pytest.mark.asyncio
    async def test_check_company_access_same_company(self, mock_info):
        """Verify check_company_access succeeds for same company"""
        mock_db = AsyncMock()
        user = mock_info.context["current_user"]

        with patch.object(PermissionService, "verify_company_access", return_value=True):
            # Should not raise exception
            await check_company_access(mock_db, user, "User", 1)

    @pytest.mark.asyncio
    async def test_check_company_access_different_company(self, mock_info):
        """Verify check_company_access fails for different company"""
        mock_db = AsyncMock()
        user = mock_info.context["current_user"]

        with patch.object(PermissionService, "verify_company_access", return_value=False):
            with pytest.raises(PermissionDeniedException):
                await check_company_access(mock_db, user, "User", 999)


class TestPermissionService:
    """Test PermissionService methods"""

    @pytest.fixture
    def service(self):
        """Create PermissionService instance"""
        return PermissionService()

    @pytest.mark.asyncio
    async def test_verify_company_access_super_admin(self, service):
        """Verify super_admin has access to all companies"""
        mock_db = AsyncMock()
        mock_user = MagicMock(id=1, role=MagicMock(name="super_admin"))

        result = await service.verify_company_access(mock_db, mock_user, 999)
        assert result is True

    @pytest.mark.asyncio
    async def test_verify_company_access_same_company(self, service):
        """Verify user has access to own company"""
        mock_db = AsyncMock()
        mock_user = MagicMock(id=1, company_id=10, role=MagicMock(name="user"))

        result = await service.verify_company_access(mock_db, mock_user, 10)
        assert result is True

    @pytest.mark.asyncio
    async def test_verify_company_access_different_company(self, service):
        """Verify user cannot access different company"""
        mock_db = AsyncMock()
        mock_user = MagicMock(id=1, company_id=10, role=MagicMock(name="user"))

        result = await service.verify_company_access(mock_db, mock_user, 999)
        assert result is False


class TestIntegration:
    """Integration tests for permission system"""

    @pytest.mark.asyncio
    async def test_full_permission_flow(self):
        """Test complete permission check flow"""
        # Setup
        mock_info = MagicMock()
        mock_info.operation.operation = "mutation"
        mock_info.field_name = "createUser"
        mock_info.context = {
            "current_user": MagicMock(
                id=1,
                company_id=10,
                role=MagicMock(name="admin"),
            )
        }

        middleware = PermissionGuardMiddleware()

        async def next_resolver():
            return {"id": 1, "name": "Test User"}

        # Mock permission check
        with patch.object(PermissionService, "check_permission", return_value=True):
            with patch.object(PermissionService, "verify_company_access", return_value=True):
                result = await middleware.resolve(
                    next_resolver, None, mock_info, [], {"input": {"company_id": 10}}
                )
                assert result["id"] == 1

    @pytest.mark.asyncio
    async def test_permission_denied_flow(self):
        """Test permission denied flow"""
        mock_info = MagicMock()
        mock_info.operation.operation = "mutation"
        mock_info.field_name = "deleteUser"
        mock_info.context = {
            "current_user": MagicMock(
                id=1,
                company_id=10,
                role=MagicMock(name="user"),
            )
        }

        middleware = PermissionGuardMiddleware()

        async def next_resolver():
            return "success"

        # Mock permission denied
        with patch.object(PermissionService, "check_permission", return_value=False):
            with pytest.raises(PermissionDeniedException):
                await middleware.resolve(next_resolver, None, mock_info, [], {})
