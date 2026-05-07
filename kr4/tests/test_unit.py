import pytest
from fastapi.testclient import TestClient
from app.main import app, memory_db, counter

client = TestClient(app)

@pytest.fixture(autouse=True)
def cleanup():
    global counter
    memory_db.clear()
    counter = 0
    yield
    memory_db.clear()
    counter = 0

# ===== Тесты =====

def test_create_user():
    response = client.post("/users", json={
        "username": "testuser",
        "age": 25,
        "email": "test@example.com",
        "password": "password123"
    })
    assert response.status_code == 201
    assert response.json()["username"] == "testuser"

def test_get_existing_user():
    client.post("/users", json={
        "username": "getuser",
        "age": 30,
        "email": "get@example.com",
        "password": "pass123"
    })
    response = client.get("/users/1")
    assert response.status_code == 200
    assert response.json()["username"] == "getuser"

def test_get_nonexistent_user():
    response = client.get("/users/999")
    assert response.status_code == 404

def test_delete_existing_user():
    client.post("/users", json={
        "username": "deleteuser",
        "age": 20,
        "email": "del@example.com",
        "password": "pass123"
    })
    response = client.delete("/users/1")
    assert response.status_code == 204
    
    get_response = client.get("/users/1")
    assert get_response.status_code == 404

def test_delete_nonexistent_user():
    response = client.delete("/users/999")
    assert response.status_code == 404

def test_double_delete():
    client.post("/users", json={
        "username": "doubleuser",
        "age": 25,
        "email": "double@example.com",
        "password": "pass123"
    })
    response1 = client.delete("/users/1")
    assert response1.status_code == 204
    
    response2 = client.delete("/users/1")
    assert response2.status_code == 404

def test_custom_exception_a():
    response = client.get("/validate/-5")
    assert response.status_code == 422
    assert "отрицательным" in response.json()["message"]

def test_custom_exception_b():
    response = client.get("/resource/999")
    assert response.status_code == 404

def test_register_valid():
    response = client.post("/register", json={
        "username": "newuser",
        "age": 25,
        "email": "user@example.com",
        "password": "SecurePass123"
    })
    assert response.status_code == 201
    assert response.json()["success"] is True

def test_register_invalid_age():
    response = client.post("/register", json={
        "username": "young",
        "age": 16,
        "email": "young@example.com",
        "password": "Pass123"
    })
    assert response.status_code == 422