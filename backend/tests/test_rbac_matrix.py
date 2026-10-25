"""Role x permission matrix smoke tests (audit 23.10, R20)."""

import pytest
from backend.auth.rbac_service import (
    DEFAULT_PERMISSIONS,
    DEFAULT_ROLES,
    expand_role_permissions,
)


@pytest.mark.parametrize("role_name", sorted(DEFAULT_ROLES))
def test_role_permissions_are_known(role_name):
    unknown = set(DEFAULT_ROLES[role_name]["permissions"]) - set(DEFAULT_PERMISSIONS)
    assert unknown == set(), f"{role_name} сочи към непознати права: {sorted(unknown)}"


@pytest.mark.parametrize(
    ("role_name", "permission"),
    [
        ("employee", "timelogs:create_own"),
        ("employee", "timelogs:update_own"),
        ("manager", "leaves:approve"),
        ("manager", "users:read"),
        ("hr_manager", "users:manage_roles"),
        ("accountant", "payroll:create"),
        ("global_accountant", "payroll:export"),
        ("admin", "users:delete"),
        ("super_admin", "system:super_admin"),
    ],
)
def test_expected_role_has_permission(role_name, permission):
    assert permission in expand_role_permissions([role_name])


@pytest.mark.parametrize(
    ("role_name", "permission"),
    [
        ("employee", "users:delete"),
        ("employee", "system:super_admin"),
        ("employee", "payroll:create"),
        ("manager", "system:super_admin"),
        ("manager", "users:delete"),
        ("hr_manager", "system:super_admin"),
        ("accountant", "system:super_admin"),
        ("admin", "system:super_admin"),
        ("driver", "payroll:read"),
        ("viewer", "timelogs:create"),
    ],
)
def test_expected_role_lacks_permission(role_name, permission):
    assert permission not in expand_role_permissions([role_name])


def test_inheritance_is_transitive():
    employee = expand_role_permissions(["employee"])
    manager = expand_role_permissions(["manager"])
    hr_manager = expand_role_permissions(["hr_manager"])

    assert employee <= manager
    assert manager <= hr_manager


def test_unknown_role_grants_nothing():
    assert expand_role_permissions(["not_a_role"]) == set()
