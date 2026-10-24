"""Structural RBAC tests (audit 23.10, Phase 2)."""

from unittest.mock import AsyncMock, MagicMock

from backend.auth.rbac_service import PermissionService
from backend.chronos_graphql.permission_middleware import (
    extract_target_company_id,
)


def test_extract_company_id_from_snake_case_kwarg():
    assert extract_target_company_id({"company_id": 7}) == 7


def test_extract_company_id_from_input_dict():
    assert extract_target_company_id({"input": {"company_id": 9}}) == 9


def test_extract_company_id_from_user_input_dict():
    assert extract_target_company_id({"user_input": {"company_id": 11}}) == 11


def test_extract_company_id_from_camel_case_user_input_dict():
    assert extract_target_company_id({"userInput": {"company_id": 13}}) == 13


def test_extract_company_id_returns_none_when_absent():
    assert extract_target_company_id({}) is None


def test_extract_company_id_prefers_explicit_kwarg():
    assert extract_target_company_id({"company_id": 1, "input": {"company_id": 2}}) == 1


async def test_log_permission_decision_uses_dedicated_writer(monkeypatch):
    db = MagicMock()
    db.commit = AsyncMock()
    db.add = MagicMock()
    writer = AsyncMock()
    monkeypatch.setattr(
        "backend.auth.audit_writer.write_permission_audit", writer
    )
    service = PermissionService(db)

    await service.log_permission_decision(
        user_id=1,
        permission="users:update",
        decision=False,
        resource_type="mutation",
        resource_id=2,
        context={"ip_address": "127.0.0.1", "user_agent": "pytest"},
    )

    writer.assert_awaited_once_with(
        user_id=1,
        permission="users:update",
        decision=False,
        resource_type="mutation",
        resource_id=2,
        ip_address="127.0.0.1",
        user_agent="pytest",
    )
    db.commit.assert_not_awaited()
    db.add.assert_not_called()
