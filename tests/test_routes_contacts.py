import pytest
from httpx import AsyncClient
from fastapi import status
from datetime import datetime, timedelta

from main import app
from src.entity.model import User


@pytest.fixture
async def test_user():
    return User(id=1, username="test_user", email="test@example.com", password="hashed_password", confirmed=True)


@pytest.fixture
async def test_contact():
    return {
        "first_name": "John",
        "last_name": "Doe",
        "email": "john.doe@example.com",
        "phone": "123456789",
        "born_date": str(datetime.now().date())
    }


@pytest.mark.asyncio
async def test_get_contacts(test_user):
    async with AsyncClient(app=app, base_url="http://testserver") as client:
        response = await client.get(
            "/contacts/",
            headers={"Authorization": f"Bearer test_user_token"}
        )
    assert response.status_code == status.HTTP_200_OK
    assert isinstance(response.json(), list)


@pytest.mark.asyncio
async def test_get_contact(test_user, test_contact):
    contact_id = 1
    async with AsyncClient(app=app, base_url="http://testserver") as client:
        response = await client.get(
            f"/contacts/{contact_id}",
            headers={"Authorization": f"Bearer test_user_token"}
        )
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["email"] == test_contact["email"]


@pytest.mark.asyncio
async def test_create_contact(test_user, test_contact):
    async with AsyncClient(app=app, base_url="http://testserver") as client:
        response = await client.post(
            "/contacts/",
            json=test_contact,
            headers={"Authorization": f"Bearer test_user_token"}
        )
    assert response.status_code == status.HTTP_201_CREATED
    assert response.json()["email"] == test_contact["email"]


@pytest.mark.asyncio
async def test_update_contact(test_user, test_contact):
    contact_id = 1
    updated_contact = test_contact.copy()
    updated_contact["first_name"] = "Updated John"

    async with AsyncClient(app=app, base_url="http://testserver") as client:
        response = await client.put(
            f"/contacts/{contact_id}",
            json=updated_contact,
            headers={"Authorization": f"Bearer test_user_token"}
        )
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["first_name"] == updated_contact["first_name"]


@pytest.mark.asyncio
async def test_delete_contact(test_user):
    contact_id = 1
    async with AsyncClient(app=app, base_url="http://testserver") as client:
        response = await client.delete(
            f"/contacts/{contact_id}",
            headers={"Authorization": f"Bearer test_user_token"}
        )
    assert response.status_code == status.HTTP_204_NO_CONTENT


@pytest.mark.asyncio
async def test_search_contacts(test_user):
    query = "John"
    async with AsyncClient(app=app, base_url="http://testserver") as client:
        response = await client.get(
            f"/contacts/search?query={query}",
            headers={"Authorization": f"Bearer test_user_token"}
        )
    assert response.status_code == status.HTTP_200_OK
    assert len(response.json()) > 0
    assert "John" in response.json()[0]["first_name"]


@pytest.mark.asyncio
async def test_get_upcoming_birthdays(test_user):
    async with AsyncClient(app=app, base_url="http://testserver") as client:
        response = await client.get(
            "/contacts/birthdays",
            headers={"Authorization": f"Bearer test_user_token"}
        )
    assert response.status_code == status.HTTP_200_OK
    assert isinstance(response.json(), list)
