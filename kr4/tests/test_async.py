import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app, memory_db, counter
from faker import Faker

fake = Faker()

@pytest.fixture(autouse=True)
def cleanup():
    global counter
    memory_db.clear()
    counter = 0
    yield
    memory_db.clear()
    counter = 0

@pytest.fixture
async def async_client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client

@pytest.mark.asyncio
async def test_async_create_user(async_client):
    user_data = {
        "username": fake.user_name(),
        "age": fake.random_int(min=19, max=99),
        "email": fake.email(),
        "password": fake.password(length=10) + "A1"
    }
    response = await async_client.post("/users", json=user_data)
    assert response.status_code == 201
    assert response.json()["username"] == user_data["username"]

@pytest.mark.asyncio
async def test_async_get_user(async_client):
    # Создаем
    user_data = {
        "username": "testuser",
        "age": 25,
        "email": "test@example.com",
        "password": "password123"
    }
    await async_client.post("/users", json=user_data)
    
    # Получаем
    response = await async_client.get("/users/1")
    assert response.status_code == 200

@pytest.mark.asyncio
async def test_async_get_nonexistent(async_client):
    response = await async_client.get("/users/999")
    assert response.status_code == 404

@pytest.mark.asyncio
async def test_async_delete_user(async_client):
    # Создаем
    await async_client.post("/users", json={
        "username": "deleteuser",
        "age": 25,
        "email": "delete@example.com",
        "password": "pass123"
    })
    
    # Удаляем
    response = await async_client.delete("/users/1")
    assert response.status_code == 204
    
    # Проверяем
    get_response = await async_client.get("/users/1")
    assert get_response.status_code == 404

@pytest.mark.asyncio
async def test_async_double_delete(async_client):
    await async_client.post("/users", json={
        "username": "doubleuser",
        "age": 25,
        "email": "double@example.com",
        "password": "pass123"
    })
    
    await async_client.delete("/users/1")
    response = await async_client.delete("/users/1")
    assert response.status_code == 404

@pytest.mark.asyncio
async def test_async_validate_negative(async_client):
    response = await async_client.get("/validate/-5")
    assert response.status_code == 422

@pytest.mark.asyncio
async def test_async_register(async_client):
    response = await async_client.post("/register", json={
        "username": "fakertest",
        "age": 25,
        "email": "faker@example.com",
        "password": "FakerPass123"
    })
    assert response.status_code == 201