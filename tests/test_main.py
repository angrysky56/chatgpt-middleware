import os
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

# Import the FastAPI app and database models
from main import app, Base, Item

# Create a test database in memory
TEST_DB_URL = "sqlite:///:memory:"
engine = create_engine(
    TEST_DB_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create the test database tables
Base.metadata.create_all(bind=engine)

# Mock environment variables for testing
os.environ["API_KEY"] = "test_api_key"

# Create a test client
client = TestClient(app)

def test_api_key_validation():
    """Test that API requests require a valid API key"""
    # Request without API key should fail
    response = client.get("/items/1")
    assert response.status_code == 403

    # Request with invalid API key should fail
    response = client.get("/items/1", headers={"X-API-Key": "invalid_key"})
    assert response.status_code == 403

    # Request with valid API key should work (though it might return 404 for non-existent item)
    response = client.get("/items/1", headers={"X-API-Key": "test_api_key"})
    assert response.status_code == 404  # Item doesn't exist yet

def test_database_operations():
    """Test basic database CRUD operations"""
    # API key for all requests
    headers = {"X-API-Key": "test_api_key"}
    
    # Create an item
    response = client.post(
        "/items",
        headers=headers,
        json={"name": "Test Item", "description": "This is a test item"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Test Item"
    assert data["description"] == "This is a test item"
    assert "id" in data
    
    # Read the created item
    item_id = data["id"]
    response = client.get(f"/items/{item_id}", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Test Item"
    assert data["description"] == "This is a test item"

def test_file_operations(tmp_path):
    """Test file read/write operations using a temporary directory"""
    # API key for all requests
    headers = {"X-API-Key": "test_api_key"}
    
    # Create a temporary file
    test_file = tmp_path / "test.txt"
    test_content = "This is a test file."
    test_file.write_text(test_content)
    
    # Test reading the file
    response = client.get(
        "/read-file",
        headers=headers,
        params={"path": str(test_file)}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["content"] == test_content
    
    # Test writing to a new file
    new_file = tmp_path / "new.txt"
    new_content = "This is a new test file."
    response = client.post(
        "/write-file",
        headers=headers,
        json={"path": str(new_file), "content": new_content}
    )
    assert response.status_code == 200
    assert new_file.read_text() == new_content

# Note: Testing the CLI endpoint would need special handling
# since it runs actual system commands, which may not be desirable in tests.
