import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession

@pytest.mark.asyncio
async def test_create_role(client: TestClient, test_db: AsyncSession, create_admin_and_login):
    _, token = create_admin_and_login
    query = """
        mutation CreateRole($name: String!, $description: String) {
            createRole(roleInput: {name: $name, description: $description}) {
                id
                name
                description
            }
        }
    """
    variables = {"name": "editor", "description": "Editor role"}
    headers = {"Authorization": f"Bearer {token}"}
    response = client.post("/graphql", json={"query": query, "variables": variables}, headers=headers)
    assert response.status_code == 200
    data = response.json()["data"]["createRole"]
    assert data["name"] == "editor"
    assert data["description"] == "Editor role"
    assert data["id"] is not None

@pytest.mark.asyncio
async def test_create_user(client: TestClient, test_db: AsyncSession, create_admin_and_login):
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
    variables = {"email": "test@example.com", "password": "testpassword"}
    headers = {"Authorization": f"Bearer {token}"}
    response = client.post("/graphql", json={"query": query, "variables": variables}, headers=headers)
    assert response.status_code == 200
    data = response.json()["data"]["createUser"]
    assert data["email"] == "test@example.com"
    assert data["isActive"] is True
    assert data["role"]["name"] == "user"
    assert data["id"] is not None

@pytest.mark.asyncio
async def test_get_users(client: TestClient, test_db: AsyncSession, create_admin_and_login):
    _, token = create_admin_and_login
    query = """
        query {
            users {
                id
                email
                role {
                    name
                }
            }
        }
    """
    headers = {"Authorization": f"Bearer {token}"}
    response = client.post("/graphql", json={"query": query}, headers=headers)
    assert response.status_code == 200
    data = response.json()["data"]["users"]
    assert len(data) >= 1 # Admin user
    admin_user_data = next((user for user in data if user["email"] == "admin@example.com"), None)
    assert admin_user_data is not None
    assert admin_user_data["role"]["name"] == "admin"

@pytest.mark.asyncio
async def test_me_query(client: TestClient, create_admin_and_login, admin_user_data):
    _, token = create_admin_and_login
    query = """
        query Me {
            me {
                id
                email
                role {
                    name
                }
            }
        }
    """
    headers = {"Authorization": f"Bearer {token}"}
    response = client.post("/graphql", json={"query": query}, headers=headers)
    assert response.status_code == 200
    data = response.json()["data"]
    assert "me" in data
    assert data["me"]["email"] == admin_user_data["email"]
    assert data["me"]["role"]["name"] == "admin"

@pytest.mark.asyncio
async def test_update_user(client: TestClient, test_db: AsyncSession, create_admin_and_login, regular_user):
    admin_user, admin_token = create_admin_and_login
    user_to_update = regular_user

    # Test update email and is_active
    update_query = """
        mutation UpdateUser($id: Int!, $email: EmailStr, $isActive: Boolean) {
            updateUser(userInput: {id: $id, email: $email, isActive: $isActive}) {
                id
                email
                isActive
            }
        }
    """
    update_variables = {
        "id": user_to_update.id,
        "email": "updated_user@example.com",
        "isActive": False
    }
    headers = {"Authorization": f"Bearer {admin_token}"}
    response = client.post("/graphql", json={"query": update_query, "variables": update_variables}, headers=headers)
    assert response.status_code == 200
    updated_data = response.json()["data"]["updateUser"]
    assert updated_data["id"] == user_to_update.id
    assert updated_data["email"] == "updated_user@example.com"
    assert updated_data["isActive"] is False

    # Test update password
    update_password_query = """
        mutation UpdateUser($id: Int!, $password: String!) {
            updateUser(userInput: {id: $id, password: $password}) {
                id
                email
            }
        }
    """
    update_password_variables = {
        "id": user_to_update.id,
        "password": "new_user_password"
    }
    response = client.post("/graphql", json={"query": update_password_query, "variables": update_password_variables}, headers=headers)
    assert response.status_code == 200
    
    # Verify new password by trying to log in
    login_response = client.post(
        "/auth/token",
        data={"username": "updated_user@example.com", "password": "new_user_password"}
    )
    assert login_response.status_code == 200

    # Test unauthorized update
    unauth_token = login_response.json()["access_token"]
    response = client.post("/graphql", json={"query": update_query, "variables": update_variables}, headers={"Authorization": f"Bearer {unauth_token}"})
    assert response.status_code == 200
    assert response.json()["errors"][0]["message"] == "Operation not permitted for this user role"

@pytest.mark.asyncio
async def test_delete_user(client: TestClient, test_db: AsyncSession, create_admin_and_login, regular_user):
    admin_user, admin_token = create_admin_and_login
    user_to_delete = regular_user

    # Test unauthorized delete
    login_response = client.post(
        "/auth/token",
        data={"username": user_to_delete.email, "password": "userpassword"}
    )
    unauth_token = login_response.json()["access_token"]

    delete_query = """
        mutation DeleteUser($id: Int!) {
            deleteUser(id: $id)
        }
    """
    delete_variables = {"id": user_to_delete.id}
    response = client.post("/graphql", json={"query": delete_query, "variables": delete_variables}, headers={"Authorization": f"Bearer {unauth_token}"})
    assert response.status_code == 200
    assert response.json()["errors"][0]["message"] == "Operation not permitted for this user role"

    # Test authorized delete
    response = client.post("/graphql", json={"query": delete_query, "variables": delete_variables}, headers={"Authorization": f"Bearer {admin_token}"})
    assert response.status_code == 200
    assert response.json()["data"]["deleteUser"] is True

    # Verify user is deleted
    get_user_query = """
        query User($id: Int!) {
            user(id: $id) {
                id
            }
        }
    """
    get_user_variables = {"id": user_to_delete.id}
    response = client.post("/graphql", json={"query": get_user_query, "variables": get_user_variables}, headers={"Authorization": f"Bearer {admin_token}"})
    assert response.status_code == 200
    assert response.json()["data"]["user"] is None