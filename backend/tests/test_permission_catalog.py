"""Guards for the RBAC permission catalog (Phase 1, audit 23.10)."""

from backend.auth.rbac_service import DEFAULT_PERMISSIONS, DEFAULT_ROLES
from backend.chronos_graphql.permission_middleware import (
    AUTH_ONLY_MUTATIONS,
    PERMISSION_MAPPING,
    PUBLIC_MUTATIONS,
)

REQUIRED_BY_MAPPING = {
    "behavioral:manage",
    "documents:create",
    "documents:delete",
    "fleet:fuel:read_own",
    "fleet:trips:create_own",
    "fleet:trips:read_own",
    "fleet:trips:update_own",
    "fleet:vehicles:read_own",
    "hr:manage_contracts",
    "integrations:manage",
    "inventory:create",
    "inventory:delete",
    "inventory:update",
    "kiosk:manage",
    "notifications:read",
    "shifts:create",
    "shifts:update_own",
    "timelogs:update_own",
}


def test_all_mapping_permissions_exist_in_catalog():
    missing = REQUIRED_BY_MAPPING - set(DEFAULT_PERMISSIONS)
    assert missing == set(), f"Липсват в каталога: {sorted(missing)}"


def test_employee_can_update_own_timelog():
    assert "timelogs:update_own" in DEFAULT_ROLES["employee"]["permissions"]


def test_employee_can_request_and_respond_to_swap():
    perms = set(DEFAULT_ROLES["employee"]["permissions"])
    assert {"shifts:create", "shifts:update_own"} <= perms


def test_hr_manager_gets_contracts_and_behavioral():
    perms = set(DEFAULT_ROLES["hr_manager"]["permissions"])
    assert {"hr:manage_contracts", "behavioral:manage"} <= perms


def test_admin_receives_every_catalog_permission():
    admin_perms = set(DEFAULT_ROLES["admin"]["permissions"])
    assert admin_perms == set(DEFAULT_PERMISSIONS)


def test_every_role_reference_exists():
    unknown = {
        perm
        for role in DEFAULT_ROLES.values()
        for perm in role["permissions"]
        if perm not in DEFAULT_PERMISSIONS
    }
    assert unknown == set(), f"Роли сочат към непознати permission-и: {sorted(unknown)}"


def _mutation_field_names() -> set[str]:
    """Извлича mutation полетата от реалната GraphQL схема."""
    from backend.chronos_graphql.schema import schema

    mutation_type = schema._schema.mutation_type
    assert mutation_type is not None
    return set(mutation_type.fields.keys())


def test_every_mutation_is_mapped_or_explicitly_public():
    fields = _mutation_field_names()
    unclassified = fields - set(PERMISSION_MAPPING) - AUTH_ONLY_MUTATIONS - PUBLIC_MUTATIONS
    assert unclassified == set(), (
        "Mutation-и без permission класификация: " + ", ".join(sorted(unclassified))
    )


def test_no_stale_mapping_entries():
    fields = _mutation_field_names()
    stale = set(PERMISSION_MAPPING) - fields
    assert stale == set(), "Остарели mapping ключове: " + ", ".join(sorted(stale))


def test_no_stale_auth_only_entries():
    fields = _mutation_field_names()
    stale = set(AUTH_ONLY_MUTATIONS) - fields
    assert stale == set(), "Остарели auth-only ключове: " + ", ".join(sorted(stale))


def test_mapping_targets_exist_in_catalog():
    missing = set(PERMISSION_MAPPING.values()) - set(DEFAULT_PERMISSIONS)
    assert missing == set(), f"Mapping сочи към липсващи permission-и: {sorted(missing)}"
