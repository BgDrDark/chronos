"""
Tests for user creation functionality.
Covers all fields from CreateUserForm in frontend and UserCreatePydantic in backend.
"""

import pytest
from datetime import date, timedelta
from decimal import Decimal
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession


@pytest.mark.asyncio
async def test_create_user_minimal_fields(client: TestClient, test_db: AsyncSession, create_admin_and_login):
    """Test creating a user with only required fields (email, password)."""
    _, token = create_admin_and_login
    
    query = """
        mutation CreateUser($email: String!, $password: String!) {
            createUser(userInput: {email: $email, password: $password}) {
                id
                email
                isActive
                role {
                    name
                }
            }
        }
    """
    variables = {
        "email": "minimal@example.com",
        "password": "securepass123"
    }
    headers = {"Authorization": f"Bearer {token}"}
    response = client.post("/graphql", json={"query": query, "variables": variables}, headers=headers)
    
    assert response.status_code == 200
    data = response.json()["data"]["createUser"]
    assert data["email"] == "minimal@example.com"
    assert data["isActive"] is True
    assert data["role"]["name"] == "user"  # Default role
    assert data["id"] is not None


@pytest.mark.asyncio
async def test_create_user_with_name_fields(client: TestClient, test_db: AsyncSession, create_admin_and_login):
    """Test creating a user with name fields (firstName, lastName)."""
    _, token = create_admin_and_login
    
    query = """
        mutation CreateUser(
            $email: String!
            $password: String!
            $firstName: String!
            $lastName: String!
        ) {
            createUser(userInput: {
                email: $email
                password: $password
                firstName: $firstName
                lastName: $lastName
            }) {
                id
                email
                firstName
                lastName
            }
        }
    """
    variables = {
        "email": "john@example.com",
        "password": "securepass123",
        "firstName": "John",
        "lastName": "Doe"
    }
    headers = {"Authorization": f"Bearer {token}"}
    response = client.post("/graphql", json={"query": query, "variables": variables}, headers=headers)
    
    assert response.status_code == 200
    data = response.json()["data"]["createUser"]
    assert data["email"] == "john@example.com"
    assert data["firstName"] == "John"
    assert data["lastName"] == "Doe"


@pytest.mark.asyncio
async def test_create_user_with_username(client: TestClient, test_db: AsyncSession, create_admin_and_login):
    """Test creating a user with username instead of email."""
    _, token = create_admin_and_login
    
    query = """
        mutation CreateUser(
            $username: String!
            $password: String!
            $firstName: String!
        ) {
            createUser(userInput: {
                username: $username
                password: $password
                firstName: $firstName
            }) {
                id
                username
                firstName
            }
        }
    """
    variables = {
        "username": "johndoe",
        "password": "securepass123",
        "firstName": "John"
    }
    headers = {"Authorization": f"Bearer {token}"}
    response = client.post("/graphql", json={"query": query, "variables": variables}, headers=headers)
    
    assert response.status_code == 200
    data = response.json()["data"]["createUser"]
    assert data["username"] == "johndoe"
    assert data["firstName"] == "John"


@pytest.mark.asyncio
async def test_create_user_with_personal_info(client: TestClient, test_db: AsyncSession, create_admin_and_login):
    """Test creating a user with personal information (phone, address, EGN, birthDate, IBAN)."""
    _, token = create_admin_and_login
    
    query = """
        mutation CreateUser(
            $email: String!
            $password: String!
            $phoneNumber: String
            $address: String
            $egn: String
            $birthDate: Date
            $iban: String
        ) {
            createUser(userInput: {
                email: $email
                password: $password
                phoneNumber: $phoneNumber
                address: $address
                egn: $egn
                birthDate: $birthDate
                iban: $iban
            }) {
                id
                email
                phoneNumber
                address
                egn
                birthDate
                iban
            }
        }
    """
    variables = {
        "email": "personal@example.com",
        "password": "securepass123",
        "phoneNumber": "+359888123456",
        "address": "Sofia, Bulgaria",
        "egn": "1234567890",
        "birthDate": "1990-01-15",
        "iban": "BG80BNBG96611020345678"
    }
    headers = {"Authorization": f"Bearer {token}"}
    response = client.post("/graphql", json={"query": query, "variables": variables}, headers=headers)
    
    assert response.status_code == 200
    data = response.json()["data"]["createUser"]
    assert data["email"] == "personal@example.com"
    assert data["phoneNumber"] == "+359888123456"
    assert data["address"] == "Sofia, Bulgaria"
    assert data["egn"] == "1234567890"
    assert data["birthDate"] == "1990-01-15"
    assert data["iban"] == "BG80BNBG96611020345678"


@pytest.mark.asyncio
async def test_create_user_with_role(client: TestClient, test_db: AsyncSession, create_admin_and_login):
    """Test creating a user with a specific role."""
    _, token = create_admin_and_login
    
    # First create a new role
    role_query = """
        mutation CreateRole($name: String!, $description: String) {
            createRole(roleInput: {name: $name, description: $description}) {
                id
                name
            }
        }
    """
    role_variables = {"name": "manager", "description": "Manager role"}
    headers = {"Authorization": f"Bearer {token}"}
    role_response = client.post("/graphql", json={"query": role_query, "variables": role_variables}, headers=headers)
    role_id = role_response.json()["data"]["createRole"]["id"]
    
    # Now create user with that role
    query = """
        mutation CreateUser(
            $email: String!
            $password: String!
            $roleId: Int!
        ) {
            createUser(userInput: {
                email: $email
                password: $password
                roleId: $roleId
            }) {
                id
                email
                role {
                    id
                    name
                }
            }
        }
    """
    variables = {
        "email": "manager@example.com",
        "password": "securepass123",
        "roleId": int(role_id)
    }
    response = client.post("/graphql", json={"query": query, "variables": variables}, headers=headers)
    
    assert response.status_code == 200
    data = response.json()["data"]["createUser"]
    assert data["email"] == "manager@example.com"
    assert data["role"]["name"] == "manager"
    assert data["role"]["id"] == role_id


@pytest.mark.asyncio
async def test_create_user_with_company_department_position(client: TestClient, test_db: AsyncSession, create_admin_and_login):
    """Test creating a user with company, department, and position."""
    _, token = create_admin_and_login
    headers = {"Authorization": f"Bearer {token}"}
    
    # Create a company first
    company_query = """
        mutation CreateCompany($name: String!) {
            createCompany(companyInput: {name: $name}) {
                id
                name
            }
        }
    """
    company_response = client.post(
        "/graphql", 
        json={"query": company_query, "variables": {"name": "Test Company"}}, 
        headers=headers
    )
    company_id = company_response.json()["data"]["createCompany"]["id"]
    
    # Create a department
    dept_query = """
        mutation CreateDepartment($name: String!, $companyId: Int!) {
            createDepartment(departmentInput: {name: $name, companyId: $companyId}) {
                id
                name
            }
        }
    """
    dept_response = client.post(
        "/graphql",
        json={"query": dept_query, "variables": {"name": "IT Department", "companyId": company_id}},
        headers=headers
    )
    department_id = dept_response.json()["data"]["createDepartment"]["id"]
    
    # Create a position
    position_query = """
        mutation CreatePosition($title: String!, $departmentId: Int!) {
            createPosition(positionInput: {title: $title, departmentId: $departmentId}) {
                id
                title
            }
        }
    """
    position_response = client.post(
        "/graphql",
        json={"query": position_query, "variables": {"title": "Software Engineer", "departmentId": department_id}},
        headers=headers
    )
    position_id = position_response.json()["data"]["createPosition"]["id"]
    
    # Now create user with these relations
    user_query = """
        mutation CreateUser(
            $email: String!
            $password: String!
            $companyId: Int
            $departmentId: Int
            $positionId: Int
        ) {
            createUser(userInput: {
                email: $email
                password: $password
                companyId: $companyId
                departmentId: $departmentId
                positionId: $positionId
            }) {
                id
                email
                company {
                    id
                    name
                }
                department {
                    id
                    name
                }
                position {
                    id
                    title
                }
            }
        }
    """
    variables = {
        "email": "employee@example.com",
        "password": "securepass123",
        "companyId": company_id,
        "departmentId": department_id,
        "positionId": position_id
    }
    response = client.post("/graphql", json={"query": user_query, "variables": variables}, headers=headers)
    
    assert response.status_code == 200
    data = response.json()["data"]["createUser"]
    assert data["email"] == "employee@example.com"
    assert data["company"]["id"] == company_id
    assert data["department"]["id"] == department_id
    assert data["position"]["id"] == position_id


@pytest.mark.asyncio
async def test_create_user_with_employment_contract(client: TestClient, test_db: AsyncSession, create_admin_and_login):
    """Test creating a user with employment contract details."""
    _, token = create_admin_and_login
    
    query = """
        mutation CreateUser(
            $email: String!
            $password: String!
            $contractType: String
            $contractStartDate: Date
            $contractEndDate: Date
            $baseSalary: Decimal
            $workHoursPerWeek: Int
            $probationMonths: Int
            $salaryCalculationType: String
            $salaryInstallmentsCount: Int
            $monthlyAdvanceAmount: Decimal
        ) {
            createUser(userInput: {
                email: $email
                password: $password
                contractType: $contractType
                contractStartDate: $contractStartDate
                contractEndDate: $contractEndDate
                baseSalary: $baseSalary
                workHoursPerWeek: $workHoursPerWeek
                probationMonths: $probationMonths
                salaryCalculationType: $salaryCalculationType
                salaryInstallmentsCount: $salaryInstallmentsCount
                monthlyAdvanceAmount: $monthlyAdvanceAmount
            }) {
                id
                email
            }
        }
    """
    variables = {
        "email": "contract@example.com",
        "password": "securepass123",
        "contractType": "permanent",
        "contractStartDate": "2024-01-01",
        "contractEndDate": None,
        "baseSalary": "5000.00",
        "workHoursPerWeek": 40,
        "probationMonths": 6,
        "salaryCalculationType": "monthly",
        "salaryInstallmentsCount": 1,
        "monthlyAdvanceAmount": "1000.00"
    }
    headers = {"Authorization": f"Bearer {token}"}
    response = client.post("/graphql", json={"query": query, "variables": variables}, headers=headers)
    
    assert response.status_code == 200
    # Contract fields are stored but may not be returned in User type directly
    # The test verifies the mutation succeeds
    assert "errors" not in response.json()


@pytest.mark.asyncio
async def test_create_user_with_tax_and_insurance(client: TestClient, test_db: AsyncSession, create_admin_and_login):
    """Test creating a user with tax and insurance settings.
    
    Note: These fields may not be returned directly in the User type.
    This test verifies the mutation accepts these fields.
    """
    _, token = create_admin_and_login
    
    query = """
        mutation CreateUser(
            $email: String!
            $password: String!
            $taxResident: Boolean
            $insuranceContributor: Boolean
            $hasIncomeTax: Boolean
        ) {
            createUser(userInput: {
                email: $email
                password: $password
                taxResident: $taxResident
                insuranceContributor: $insuranceContributor
                hasIncomeTax: $hasIncomeTax
            }) {
                id
                email
            }
        }
    """
    variables = {
        "email": "tax@example.com",
        "password": "securepass123",
        "taxResident": True,
        "insuranceContributor": True,
        "hasIncomeTax": True
    }
    headers = {"Authorization": f"Bearer {token}"}
    response = client.post("/graphql", json={"query": query, "variables": variables}, headers=headers)
    
    assert response.status_code == 200
    assert "errors" not in response.json()


@pytest.mark.asyncio
async def test_create_user_with_trz_rates(client: TestClient, test_db: AsyncSession, create_admin_and_login):
    """Test creating a user with TRZ (night/overtime/holiday) rates.
    
    Note: TRZ fields (nightWorkRate, overtimeRate, holidayRate, workClass, dangerousWork)
    are in the UserCreatePydantic input but may not be stored in create_user mutation.
    This test verifies the mutation accepts these fields without error.
    """
    _, token = create_admin_and_login
    
    query = """
        mutation CreateUser(
            $email: String!
            $password: String!
            $nightWorkRate: Decimal
            $overtimeRate: Decimal
            $holidayRate: Decimal
            $workClass: String
            $dangerousWork: Boolean
        ) {
            createUser(userInput: {
                email: $email
                password: $password
                nightWorkRate: $nightWorkRate
                overtimeRate: $overtimeRate
                holidayRate: $holidayRate
                workClass: $workClass
                dangerousWork: $dangerousWork
            }) {
                id
                email
            }
        }
    """
    variables = {
        "email": "trz@example.com",
        "password": "securepass123",
        "nightWorkRate": "0.50",
        "overtimeRate": "1.50",
        "holidayRate": "2.00",
        "workClass": "normal",
        "dangerousWork": False
    }
    headers = {"Authorization": f"Bearer {token}"}
    response = client.post("/graphql", json={"query": query, "variables": variables}, headers=headers)
    
    assert response.status_code == 200
    # Verify mutation accepts the fields without error
    assert "errors" not in response.json()


@pytest.mark.asyncio
async def test_create_user_with_password_force_change(client: TestClient, test_db: AsyncSession, create_admin_and_login):
    """Test creating a user with password force change flag."""
    _, token = create_admin_and_login
    
    query = """
        mutation CreateUser(
            $email: String!
            $password: String!
            $passwordForceChange: Boolean!
        ) {
            createUser(userInput: {
                email: $email
                password: $password
                passwordForceChange: $passwordForceChange
            }) {
                id
                email
                passwordForceChange
            }
        }
    """
    variables = {
        "email": "force@example.com",
        "password": "securepass123",
        "passwordForceChange": True
    }
    headers = {"Authorization": f"Bearer {token}"}
    response = client.post("/graphql", json={"query": query, "variables": variables}, headers=headers)
    
    assert response.status_code == 200
    data = response.json()["data"]["createUser"]
    assert data["email"] == "force@example.com"
    assert data["passwordForceChange"] is True


@pytest.mark.asyncio
async def test_create_user_with_all_fields(client: TestClient, test_db: AsyncSession, create_admin_and_login):
    """Test creating a user with all available fields.
    
    Note: Many fields (contract, tax, TRZ) are stored but may not be returned 
    directly in the User type. This test verifies the mutation accepts all fields.
    """
    _, token = create_admin_and_login
    headers = {"Authorization": f"Bearer {token}"}
    
    # Create supporting entities first
    company_response = client.post(
        "/graphql",
        json={"query": """mutation CreateCompany($name: String!) { createCompany(companyInput: {name: $name}) { id } }""", "variables": {"name": "Full Test Company"}},
        headers=headers
    )
    company_id = company_response.json()["data"]["createCompany"]["id"]
    
    dept_response = client.post(
        "/graphql",
        json={"query": """mutation CreateDepartment($name: String!, $companyId: Int!) { createDepartment(departmentInput: {name: $name, companyId: $companyId}) { id } }""", "variables": {"name": "Full Test Dept", "companyId": company_id}},
        headers=headers
    )
    department_id = dept_response.json()["data"]["createDepartment"]["id"]
    
    position_response = client.post(
        "/graphql",
        json={"query": """mutation CreatePosition($title: String!, $departmentId: Int!) { createPosition(positionInput: {title: $title, departmentId: $departmentId}) { id } }""", "variables": {"title": "Senior Engineer", "departmentId": department_id}},
        headers=headers
    )
    position_id = position_response.json()["data"]["createPosition"]["id"]
    
    # Create user with all fields
    query = """
        mutation CreateUser(
            $email: String!
            $username: String
            $password: String!
            $firstName: String!
            $lastName: String!
            $phoneNumber: String
            $address: String
            $egn: String
            $birthDate: Date
            $iban: String
            $companyId: Int
            $departmentId: Int
            $positionId: Int
            $passwordForceChange: Boolean
            $contractType: String
            $contractStartDate: Date
            $baseSalary: Decimal
            $workHoursPerWeek: Int
            $probationMonths: Int
            $salaryCalculationType: String
            $salaryInstallmentsCount: Int
            $monthlyAdvanceAmount: Decimal
            $taxResident: Boolean
            $insuranceContributor: Boolean
            $hasIncomeTax: Boolean
            $nightWorkRate: Decimal
            $overtimeRate: Decimal
            $holidayRate: Decimal
            $workClass: String
            $dangerousWork: Boolean
        ) {
            createUser(userInput: {
                email: $email
                username: $username
                password: $password
                firstName: $firstName
                lastName: $lastName
                phoneNumber: $phoneNumber
                address: $address
                egn: $egn
                birthDate: $birthDate
                iban: $iban
                companyId: $companyId
                departmentId: $departmentId
                positionId: $positionId
                passwordForceChange: $passwordForceChange
                contractType: $contractType
                contractStartDate: $contractStartDate
                baseSalary: $baseSalary
                workHoursPerWeek: $workHoursPerWeek
                probationMonths: $probationMonths
                salaryCalculationType: $salaryCalculationType
                salaryInstallmentsCount: $salaryInstallmentsCount
                monthlyAdvanceAmount: $monthlyAdvanceAmount
                taxResident: $taxResident
                insuranceContributor: $insuranceContributor
                hasIncomeTax: $hasIncomeTax
                nightWorkRate: $nightWorkRate
                overtimeRate: $overtimeRate
                holidayRate: $holidayRate
                workClass: $workClass
                dangerousWork: $dangerousWork
            }) {
                id
                email
                username
                firstName
                lastName
                phoneNumber
                address
                egn
                birthDate
                iban
                company { id name }
                department { id name }
                position { id title }
                passwordForceChange
            }
        }
    """
    variables = {
        "email": "fulltest@example.com",
        "username": "fulltestuser",
        "password": "securepass123",
        "firstName": "Full",
        "lastName": "Test",
        "phoneNumber": "+359888999888",
        "address": "Sofia, Bulgaria",
        "egn": "1234567890",
        "birthDate": "1990-05-15",
        "iban": "BG80BNBG96611020345678",
        "companyId": company_id,
        "departmentId": department_id,
        "positionId": position_id,
        "passwordForceChange": True,
        "contractType": "permanent",
        "contractStartDate": "2024-01-01",
        "baseSalary": "7500.00",
        "workHoursPerWeek": 40,
        "probationMonths": 6,
        "salaryCalculationType": "monthly",
        "salaryInstallmentsCount": 1,
        "monthlyAdvanceAmount": "1500.00",
        "taxResident": True,
        "insuranceContributor": True,
        "hasIncomeTax": True,
        "nightWorkRate": "0.50",
        "overtimeRate": "1.50",
        "holidayRate": "2.00",
        "workClass": "normal",
        "dangerousWork": False
    }
    response = client.post("/graphql", json={"query": query, "variables": variables}, headers=headers)
    
    assert response.status_code == 200
    assert "errors" not in response.json()
    data = response.json()["data"]["createUser"]
    
    # Verify basic fields
    assert data["email"] == "fulltest@example.com"
    assert data["username"] == "fulltestuser"
    assert data["firstName"] == "Full"
    assert data["lastName"] == "Test"
    assert data["phoneNumber"] == "+359888999888"
    assert data["address"] == "Sofia, Bulgaria"
    assert data["egn"] == "1234567890"
    assert data["birthDate"] == "1990-05-15"
    assert data["iban"] == "BG80BNBG96611020345678"
    assert data["company"]["id"] == company_id
    assert data["department"]["id"] == department_id
    assert data["position"]["id"] == position_id
    assert data["passwordForceChange"] is True


@pytest.mark.asyncio
async def test_create_user_invalid_email(client: TestClient, test_db: AsyncSession, create_admin_and_login):
    """Test that creating a user with invalid email fails."""
    _, token = create_admin_and_login
    
    query = """
        mutation CreateUser($email: String!, $password: String!) {
            createUser(userInput: {email: $email, password: $password}) {
                id
                email
            }
        }
    """
    variables = {
        "email": "not-an-email",
        "password": "securepass123"
    }
    headers = {"Authorization": f"Bearer {token}"}
    response = client.post("/graphql", json={"query": query, "variables": variables}, headers=headers)
    
    assert response.status_code == 200
    assert "errors" in response.json()
    assert "email" in response.json()["errors"][0]["message"].lower()


@pytest.mark.asyncio
async def test_create_user_short_password(client: TestClient, test_db: AsyncSession, create_admin_and_login):
    """Test that creating a user with short password fails."""
    _, token = create_admin_and_login
    
    query = """
        mutation CreateUser($email: String!, $password: String!) {
            createUser(userInput: {email: $email, password: $password}) {
                id
                email
            }
        }
    """
    variables = {
        "email": "shortpass@example.com",
        "password": "short"  # Less than 8 characters
    }
    headers = {"Authorization": f"Bearer {token}"}
    response = client.post("/graphql", json={"query": query, "variables": variables}, headers=headers)
    
    assert response.status_code == 200
    assert "errors" in response.json()


@pytest.mark.asyncio
async def test_create_user_duplicate_email(client: TestClient, test_db: AsyncSession, create_admin_and_login):
    """Test that creating a user with duplicate email fails."""
    _, token = create_admin_and_login
    
    # First create a user
    query = """
        mutation CreateUser($email: String!, $password: String!) {
            createUser(userInput: {email: $email, password: $password}) {
                id
                email
            }
        }
    """
    variables = {"email": "duplicate@example.com", "password": "securepass123"}
    headers = {"Authorization": f"Bearer {token}"}
    response1 = client.post("/graphql", json={"query": query, "variables": variables}, headers=headers)
    assert response1.status_code == 200
    assert "errors" not in response1.json()
    
    # Try to create another user with the same email
    variables2 = {"email": "duplicate@example.com", "password": "anotherpass123"}
    response2 = client.post("/graphql", json={"query": query, "variables": variables2}, headers=headers)
    
    assert response2.status_code == 200
    assert "errors" in response2.json()


@pytest.mark.asyncio
async def test_create_user_without_auth(client: TestClient, test_db: AsyncSession):
    """Test that creating a user without authentication fails."""
    query = """
        mutation CreateUser($email: String!, $password: String!) {
            createUser(userInput: {email: $email, password: $password}) {
                id
                email
            }
        }
    """
    variables = {"email": "unauth@example.com", "password": "securepass123"}
    response = client.post("/graphql", json={"query": query, "variables": variables})
    
    assert response.status_code == 200
    assert "errors" in response.json()


@pytest.mark.asyncio
async def test_create_user_contract_end_date(client: TestClient, test_db: AsyncSession, create_admin_and_login):
    """Test creating a user with contract end date (for fixed-term contracts)."""
    _, token = create_admin_and_login
    
    query = """
        mutation CreateUser(
            $email: String!
            $password: String!
            $contractType: String!
            $contractStartDate: Date!
            $contractEndDate: Date!
        ) {
            createUser(userInput: {
                email: $email
                password: $password
                contractType: $contractType
                contractStartDate: $contractStartDate
                contractEndDate: $contractEndDate
            }) {
                id
                email
            }
        }
    """
    variables = {
        "email": "fixedterm@example.com",
        "password": "securepass123",
        "contractType": "fixed_term",
        "contractStartDate": "2024-01-01",
        "contractEndDate": "2024-12-31"
    }
    headers = {"Authorization": f"Bearer {token}"}
    response = client.post("/graphql", json={"query": query, "variables": variables}, headers=headers)
    
    assert response.status_code == 200
    assert "errors" not in response.json()
