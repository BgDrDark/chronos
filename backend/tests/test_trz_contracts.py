"""
Comprehensive tests for TRZ (Labor Law) Employment Contracts.

Tests cover:
- Contract creation (draft state)
- Contract signing
- Contract linking to users
- Contract status transitions
- Annex creation and signing
- Permission checks
- Error handling
"""

import pytest
from datetime import date, datetime
from decimal import Decimal
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from backend.main import app
from backend.database.database import get_db
from backend.database.models import (
    EmploymentContract, User, Company, Role, 
    ContractAnnex, Position, Department
)
from backend import crud
from backend.schemas import RoleCreate, UserCreate

import backend.auth.security as security_module
import uuid

_original_encrypt = security_module.encrypt_data
_original_decrypt = security_module.decrypt_data

def plaintext_encrypt(value):
    if value is None:
        return None
    return value

def plaintext_decrypt(value):
    if value is None:
        return None
    return value

security_module.encrypt_data = plaintext_encrypt
security_module.decrypt_data = plaintext_decrypt
crud.encrypt_data = plaintext_encrypt
crud.decrypt_data = plaintext_decrypt


@pytest.fixture
async def test_company(test_db: AsyncSession) -> Company:
    """Create a test company with unique EIK."""
    unique_suffix = uuid.uuid4().hex[:6]
    company = Company(
        name=f"Test Company {unique_suffix}",
        eik=f"123456{unique_suffix}",
        bulstat=f"BG{unique_suffix}56789"
    )
    test_db.add(company)
    await test_db.commit()
    await test_db.refresh(company)
    return company


@pytest.fixture
async def test_role(test_db: AsyncSession) -> Role:
    """Create admin role."""
    role = await crud.get_role_by_name(test_db, "admin")
    if not role:
        role = await crud.create_role(test_db, RoleCreate(name="admin", description="Admin"))
    return role


@pytest.fixture
async def test_user(test_db: AsyncSession, test_company: Company, test_role: Role) -> User:
    """Create a test user for linking contracts."""
    unique_id = uuid.uuid4().hex[:6]
    user = await crud.create_user(
        test_db,
        UserCreate(
            email=f"employee_{unique_id}@test.com",
            password="testpassword123",
            first_name="Иван",
            last_name="Иванов",
            egn="1234567890"
        ),
        role_name="employee"
    )
    user.company_id = test_company.id
    await test_db.commit()
    await test_db.refresh(user)
    return user


@pytest.fixture
async def admin_user(test_db: AsyncSession, test_company: Company, test_role: Role) -> User:
    """Create admin user for testing."""
    unique_id = uuid.uuid4().hex[:6]
    admin = await crud.create_user(
        test_db,
        UserCreate(
            email=f"admin_{unique_id}@test.com",
            password="adminpassword123",
            first_name="Админ",
            last_name="Админов",
            egn="0000000000"
        ),
        role_name="admin"
    )
    admin.company_id = test_company.id
    await test_db.commit()
    await test_db.refresh(admin)
    return admin


@pytest.fixture
async def auth_headers(async_client: AsyncClient, admin_user: User) -> dict:
    """Get auth headers for admin user."""
    response = await async_client.post(
        "/auth/token",
        data={"username": admin_user.email, "password": "adminpassword123"}
    )
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


class TestContractCreation:
    """Tests for contract creation."""

    @pytest.mark.asyncio
    async def test_create_contract_requires_auth(
        self, 
        async_client: AsyncClient,
        test_company: Company
    ):
        """Test that creating contract requires authentication."""
        response = await async_client.post(
            "/graphql",
            json={
                "query": """
                    mutation CreateContract($input: EmploymentContractCreateInput!) {
                        createEmploymentContract(input: $input) {
                            id
                            employeeName
                            status
                        }
                    }
                """,
                "variables": {
                    "input": {
                        "employeeName": "Тест Тестов",
                        "employeeEgn": "1234567890",
                        "companyId": test_company.id,
                        "contractType": "full_time",
                        "startDate": "2024-01-15"
                    }
                }
            }
        )
        assert response.status_code == 200
        # Should require auth
        data = response.json()
        assert "errors" in data or data.get("data", {}).get("createEmploymentContract") is None

    @pytest.mark.asyncio
    async def test_create_contract_with_valid_data(
        self,
        async_client: AsyncClient,
        auth_headers: dict,
        test_company: Company
    ):
        """Test creating a contract with all valid fields."""
        response = await async_client.post(
            "/graphql",
            json={
                "query": """
                    mutation CreateContract($input: EmploymentContractCreateInput!) {
                        createEmploymentContract(input: $input) {
                            id
                            employeeName
                            employeeEgn
                            contractType
                            startDate
                            status
                            companyId
                        }
                    }
                """,
                "variables": {
                    "input": {
                        "employeeName": "Петър Петров",
                        "employeeEgn": "7501010010",
                        "companyId": test_company.id,
                        "contractType": "full_time",
                        "contractNumber": "TRZ-2024-001",
                        "startDate": "2024-02-01",
                        "endDate": "2025-02-01",
                        "baseSalary": 1500.00,
                        "workHoursPerWeek": 40
                    }
                }
            },
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        if "errors" in data:
            print(f"GraphQL errors: {data['errors']}")
        assert "errors" not in data
        
        contract = data["data"]["createEmploymentContract"]
        assert contract["employeeName"] == "Петър Петров"
        assert contract["employeeEgn"] == "7501010010"
        assert contract["contractType"] == "full_time"
        assert contract["status"] == "draft"
        assert contract["companyId"] == test_company.id

    @pytest.mark.asyncio
    async def test_create_contract_minimal_data(
        self,
        async_client: AsyncClient,
        auth_headers: dict,
        test_company: Company
    ):
        """Test creating contract with only required fields."""
        response = await async_client.post(
            "/graphql",
            json={
                "query": """
                    mutation CreateContract($input: EmploymentContractCreateInput!) {
                        createEmploymentContract(input: $input) {
                            id
                            status
                        }
                    }
                """,
                "variables": {
                    "input": {
                        "employeeName": "Минимални Данни",
                        "employeeEgn": "8012120011",
                        "companyId": test_company.id,
                        "contractType": "part_time",
                        "startDate": "2024-03-01"
                    }
                }
            },
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "errors" not in data
        assert data["data"]["createEmploymentContract"]["status"] == "draft"

    @pytest.mark.asyncio
    async def test_create_contract_without_employee_name_fails(
        self,
        async_client: AsyncClient,
        auth_headers: dict,
        test_company: Company
    ):
        """Test that contract without employee name fails."""
        response = await async_client.post(
            "/graphql",
            json={
                "query": """
                    mutation CreateContract($input: EmploymentContractCreateInput!) {
                        createEmploymentContract(input: $input) {
                            id
                        }
                    }
                """,
                "variables": {
                    "input": {
                        "employeeEgn": "7501010010",
                        "companyId": test_company.id,
                        "contractType": "full_time",
                        "startDate": "2024-01-15"
                    }
                }
            },
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        # Should fail validation
        assert "errors" in data or data.get("data", {}).get("createEmploymentContract") is None


class TestContractSigning:
    """Tests for contract signing."""

    @pytest.fixture
    async def draft_contract(
        self,
        test_db: AsyncSession,
        test_company: Company
    ) -> EmploymentContract:
        """Create a draft contract for signing tests."""
        contract = EmploymentContract(
            employee_name="Чернова Чернова",
            employee_egn="9001010010",
            company_id=test_company.id,
            user_id=0,
            contract_type="full_time",
            start_date=date(2024, 1, 15),
            status="draft"
        )
        test_db.add(contract)
        await test_db.commit()
        await test_db.refresh(contract)
        return contract

    @pytest.mark.asyncio
    async def test_sign_draft_contract(
        self,
        async_client: AsyncClient,
        auth_headers: dict,
        draft_contract: EmploymentContract
    ):
        """Test signing a draft contract."""
        response = await async_client.post(
            "/graphql",
            json={
                "query": """
                    mutation SignContract($id: Int!) {
                        signEmploymentContract(id: $id) {
                            id
                            status
                            signedAt
                        }
                    }
                """,
                "variables": {"id": draft_contract.id}
            },
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "errors" not in data
        
        result = data["data"]["signEmploymentContract"]
        assert result["status"] == "signed"
        assert result["signedAt"] is not None

    @pytest.mark.asyncio
    async def test_sign_already_signed_contract_fails(
        self,
        async_client: AsyncClient,
        auth_headers: dict,
        test_db: AsyncSession,
        draft_contract: EmploymentContract
    ):
        """Test that signing already signed contract fails."""
        # First sign
        draft_contract.status = "signed"
        draft_contract.signed_at = datetime.now()
        await test_db.commit()
        
        response = await async_client.post(
            "/graphql",
            json={
                "query": """
                    mutation SignContract($id: Int!) {
                        signEmploymentContract(id: $id) {
                            status
                        }
                    }
                """,
                "variables": {"id": draft_contract.id}
            },
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        # Should return error about already signed
        assert "errors" in data

    @pytest.mark.asyncio
    async def test_sign_nonexistent_contract(
        self,
        async_client: AsyncClient,
        auth_headers: dict
    ):
        """Test signing a non-existent contract returns error."""
        response = await async_client.post(
            "/graphql",
            json={
                "query": """
                    mutation SignContract($id: Int!) {
                        signEmploymentContract(id: $id) {
                            status
                        }
                    }
                """,
                "variables": {"id": 999999}
            },
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "errors" in data


class TestContractLinking:
    """Tests for linking contracts to users."""

    @pytest.fixture
    async def signed_contract(
        self,
        test_db: AsyncSession,
        test_company: Company
    ) -> EmploymentContract:
        """Create a signed contract for linking tests."""
        contract = EmploymentContract(
            employee_name="Подписан Подписан",
            employee_egn="8505050010",
            company_id=test_company.id,
            user_id=0,
            contract_type="full_time",
            start_date=date(2024, 1, 1),
            status="signed",
            signed_at=datetime.now()
        )
        test_db.add(contract)
        await test_db.commit()
        await test_db.refresh(contract)
        return contract

    @pytest.mark.asyncio
    async def test_link_signed_contract_to_user(
        self,
        async_client: AsyncClient,
        auth_headers: dict,
        signed_contract: EmploymentContract,
        test_user: User
    ):
        """Test linking a signed contract to a user."""
        response = await async_client.post(
            "/graphql",
            json={
                "query": """
                    mutation LinkContract($contractId: Int!, $userId: Int!) {
                        linkEmploymentContractToUser(contractId: $contractId, userId: $userId) {
                            id
                            status
                            userId
                        }
                    }
                """,
                "variables": {
                    "contractId": signed_contract.id,
                    "userId": test_user.id
                }
            },
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "errors" not in data
        
        result = data["data"]["linkEmploymentContractToUser"]
        assert result["status"] == "linked"
        assert result["userId"] == test_user.id

    @pytest.mark.asyncio
    async def test_link_draft_contract_fails(
        self,
        async_client: AsyncClient,
        auth_headers: dict,
        draft_contract: EmploymentContract,
        test_user: User
    ):
        """Test that linking a draft (unsigned) contract fails."""
        response = await async_client.post(
            "/graphql",
            json={
                "query": """
                    mutation LinkContract($contractId: Int!, $userId: Int!) {
                        linkEmploymentContractToUser(contractId: $contractId, userId: $userId) {
                            status
                        }
                    }
                """,
                "variables": {
                    "contractId": draft_contract.id,
                    "userId": test_user.id
                }
            },
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "errors" in data

    @pytest.mark.asyncio
    async def test_link_to_nonexistent_user_fails(
        self,
        async_client: AsyncClient,
        auth_headers: dict,
        signed_contract: EmploymentContract
    ):
        """Test linking to non-existent user fails."""
        response = await async_client.post(
            "/graphql",
            json={
                "query": """
                    mutation LinkContract($contractId: Int!, $userId: Int!) {
                        linkEmploymentContractToUser(contractId: $contractId, userId: $userId) {
                            status
                        }
                    }
                """,
                "variables": {
                    "contractId": signed_contract.id,
                    "userId": 999999
                }
            },
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "errors" in data


class TestContractQueries:
    """Tests for contract queries."""

    @pytest.fixture
    async def multiple_contracts(
        self,
        test_db: AsyncSession,
        test_company: Company
    ):
        """Create multiple contracts with different statuses."""
        contracts = [
            EmploymentContract(
                employee_name="Чернова 1",
                employee_egn="9001010010",
                company_id=test_company.id,
                user_id=0,
                contract_type="full_time",
                start_date=date(2024, 1, 1),
                status="draft"
            ),
            EmploymentContract(
                employee_name="Подписан 1",
                employee_egn="9001010011",
                company_id=test_company.id,
                user_id=1,
                contract_type="part_time",
                start_date=date(2024, 2, 1),
                status="signed",
                signed_at=datetime.now()
            ),
            EmploymentContract(
                employee_name="Свързан 1",
                employee_egn="9001010012",
                company_id=test_company.id,
                user_id=2,
                contract_type="full_time",
                start_date=date(2024, 3, 1),
                status="linked"
            ),
        ]
        for contract in contracts:
            test_db.add(contract)
        await test_db.commit()
        return contracts

    @pytest.mark.asyncio
    async def test_get_all_contracts(
        self,
        async_client: AsyncClient,
        auth_headers: dict,
        multiple_contracts: list
    ):
        """Test fetching all contracts."""
        response = await async_client.post(
            "/graphql",
            json={
                "query": """
                    query GetContracts {
                        employmentContracts {
                            id
                            employeeName
                            status
                        }
                    }
                """
            },
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "errors" not in data
        
        contracts = data["data"]["employmentContracts"]
        assert len(contracts) >= 3

    @pytest.mark.asyncio
    async def test_filter_contracts_by_status(
        self,
        async_client: AsyncClient,
        auth_headers: dict,
        multiple_contracts: list
    ):
        """Test filtering contracts by status."""
        response = await async_client.post(
            "/graphql",
            json={
                "query": """
                    query GetContractsByStatus($status: String!) {
                        employmentContracts(status: $status) {
                            id
                            employeeName
                            status
                        }
                    }
                """,
                "variables": {"status": "draft"}
            },
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "errors" not in data
        
        contracts = data["data"]["employmentContracts"]
        for contract in contracts:
            assert contract["status"] == "draft"

    @pytest.mark.asyncio
    async def test_get_single_contract(
        self,
        async_client: AsyncClient,
        auth_headers: dict,
        multiple_contracts: list
    ):
        """Test fetching a single contract by ID."""
        contract_id = multiple_contracts[0].id
        
        response = await async_client.post(
            "/graphql",
            json={
                "query": """
                    query GetContract($id: Int!) {
                        employmentContract(id: $id) {
                            id
                            employeeName
                            employeeEgn
                            status
                            annexes {
                                id
                            }
                        }
                    }
                """,
                "variables": {"id": contract_id}
            },
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "errors" not in data
        
        contract = data["data"]["employmentContract"]
        assert contract["id"] == contract_id
        assert "annexes" in contract


class TestContractAnnexes:
    """Tests for contract annex functionality."""

    @pytest.fixture
    async def contract_with_annexes(
        self,
        test_db: AsyncSession,
        test_company: Company
    ):
        """Create a contract with annexes."""
        contract = EmploymentContract(
            employee_name="Анекс Тестов",
            employee_egn="8010100010",
            company_id=test_company.id,
            user_id=1,
            contract_type="full_time",
            start_date=date(2024, 1, 1),
            status="linked"
        )
        test_db.add(contract)
        await test_db.commit()
        await test_db.refresh(contract)
        
        # Add annexes
        annex1 = ContractAnnex(
            contract_id=contract.id,
            annex_number="А-001",
            effective_date=date(2024, 4, 1),
            base_salary=2000.00,
            change_type="salary_increase",
            status="signed",
            is_signed=True,
            signed_at=datetime.now()
        )
        annex2 = ContractAnnex(
            contract_id=contract.id,
            annex_number="А-002",
            effective_date=date(2024, 7, 1),
            base_salary=2200.00,
            change_type="salary_increase",
            status="draft",
            is_signed=False
        )
        test_db.add_all([annex1, annex2])
        await test_db.commit()
        
        return contract

    @pytest.mark.asyncio
    async def test_get_contract_with_annexes(
        self,
        async_client: AsyncClient,
        auth_headers: dict,
        contract_with_annexes: EmploymentContract
    ):
        """Test fetching contract with its annexes."""
        response = await async_client.post(
            "/graphql",
            json={
                "query": """
                    query GetContractWithAnnexes($id: Int!) {
                        employmentContract(id: $id) {
                            id
                            employeeName
                            annexes {
                                id
                                annexNumber
                                effectiveDate
                                baseSalary
                                status
                                isSigned
                                changeType
                            }
                        }
                    }
                """,
                "variables": {"id": contract_with_annexes.id}
            },
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "errors" not in data
        
        contract = data["data"]["employmentContract"]
        assert len(contract["annexes"]) == 2

    @pytest.mark.asyncio
    async def test_annexes_ordered_by_date(
        self,
        async_client: AsyncClient,
        auth_headers: dict,
        contract_with_annexes: EmploymentContract
    ):
        """Test that annexes are returned ordered by effective date descending."""
        response = await async_client.post(
            "/graphql",
            json={
                "query": """
                    query GetContractWithAnnexes($id: Int!) {
                        employmentContract(id: $id) {
                            annexes {
                                effectiveDate
                            }
                        }
                    }
                """,
                "variables": {"id": contract_with_annexes.id}
            },
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        annexes = data["data"]["employmentContract"]["annexes"]
        # Most recent first
        dates = [a["effectiveDate"] for a in annexes]
        assert dates == sorted(dates, reverse=True)


class TestContractPermissions:
    """Tests for contract permissions."""

    @pytest.mark.asyncio
    async def test_non_admin_cannot_create_contract(
        self,
        async_client: AsyncClient,
        test_db: AsyncSession,
        test_company: Company
    ):
        """Test that non-admin users cannot create contracts."""
        # Create employee role and user
        employee_role = await crud.get_role_by_name(test_db, "employee")
        if not employee_role:
            employee_role = await crud.create_role(
                test_db, 
                RoleCreate(name="employee", description="Employee")
            )
        
        employee = await crud.create_user(
            test_db,
            UserCreate(
                email="employee@test.com",
                password="emppassword123",
                first_name="Служител",
                last_name="Служителов",
                egn="9010100010"
            ),
            role_name="employee"
        )
        
        # Login as employee
        response = await async_client.post(
            "/auth/token",
            data={"username": employee.email, "password": "emppassword123"}
        )
        token = response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        # Try to create contract
        response = await async_client.post(
            "/graphql",
            json={
                "query": """
                    mutation CreateContract($input: EmploymentContractCreateInput!) {
                        createEmploymentContract(input: $input) {
                            id
                        }
                    }
                """,
                "variables": {
                    "input": {
                        "employeeName": "Тест",
                        "employeeEgn": "9010100010",
                        "companyId": test_company.id,
                        "contractType": "full_time",
                        "startDate": "2024-01-15"
                    }
                }
            },
            headers=headers
        )
        
        assert response.status_code == 200
        data = response.json()
        # Should fail with permission error
        assert "errors" in data


class TestContractStatusFlow:
    """Tests for the complete contract status flow."""

    @pytest.mark.asyncio
    async def test_full_contract_lifecycle(
        self,
        async_client: AsyncClient,
        auth_headers: dict,
        test_db: AsyncSession,
        test_company: Company,
        test_user: User
    ):
        """Test complete contract lifecycle: create -> sign -> link."""
        # Step 1: Create contract
        create_response = await async_client.post(
            "/graphql",
            json={
                "query": """
                    mutation CreateContract($input: EmploymentContractCreateInput!) {
                        createEmploymentContract(input: $input) {
                            id
                            status
                        }
                    }
                """,
                "variables": {
                    "input": {
                        "employeeName": "Пълен Живот",
                        "employeeEgn": "7510100010",
                        "companyId": test_company.id,
                        "contractType": "full_time",
                        "startDate": "2024-01-01",
                        "baseSalary": 1000.00
                    }
                }
            },
            headers=auth_headers
        )
        
        assert create_response.status_code == 200
        create_data = create_response.json()
        assert "errors" not in create_data
        assert create_data["data"]["createEmploymentContract"]["status"] == "draft"
        
        contract_id = create_data["data"]["createEmploymentContract"]["id"]
        
        # Step 2: Sign contract
        sign_response = await async_client.post(
            "/graphql",
            json={
                "query": """
                    mutation SignContract($id: Int!) {
                        signEmploymentContract(id: $id) {
                            status
                            signedAt
                        }
                    }
                """,
                "variables": {"id": contract_id}
            },
            headers=auth_headers
        )
        
        assert sign_response.status_code == 200
        sign_data = sign_response.json()
        assert "errors" not in sign_data
        assert sign_data["data"]["signEmploymentContract"]["status"] == "signed"
        assert sign_data["data"]["signEmploymentContract"]["signedAt"] is not None
        
        # Step 3: Link to user
        link_response = await async_client.post(
            "/graphql",
            json={
                "query": """
                    mutation LinkContract($contractId: Int!, $userId: Int!) {
                        linkEmploymentContractToUser(contractId: $contractId, userId: $userId) {
                            status
                            userId
                        }
                    }
                """,
                "variables": {
                    "contractId": contract_id,
                    "userId": test_user.id
                }
            },
            headers=auth_headers
        )
        
        assert link_response.status_code == 200
        link_data = link_response.json()
        assert "errors" not in link_data
        assert link_data["data"]["linkEmploymentContractToUser"]["status"] == "linked"
        assert link_data["data"]["linkEmploymentContractToUser"]["userId"] == test_user.id
        
        # Verify in database
        result = await test_db.execute(
            select(EmploymentContract).where(EmploymentContract.id == contract_id)
        )
        contract = result.scalar_one()
        assert contract.status == "linked"
        assert contract.user_id == test_user.id
