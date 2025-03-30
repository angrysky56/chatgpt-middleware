#!/usr/bin/env python3
"""
Example client script for interacting with the ChatGPT Middleware API.
"""

import requests
import os
import json
from dotenv import load_dotenv

# Load API key from .env file
load_dotenv()
API_KEY = os.getenv("API_KEY")

# Base URL for the API
BASE_URL = "http://localhost:8000"

# Headers for authentication
HEADERS = {
    "X-API-Key": API_KEY,
    "Content-Type": "application/json"
}

def run_cli_command(command):
    """Execute a CLI command through the middleware."""
    response = requests.post(
        f"{BASE_URL}/cli",
        params={"command": command},
        headers=HEADERS
    )
    
    if response.status_code == 200:
        return response.json()["output"]
    else:
        return f"Error: {response.status_code} - {response.text}"

def read_file(file_path):
    """Read a file through the middleware."""
    response = requests.get(
        f"{BASE_URL}/read-file",
        params={"path": file_path},
        headers=HEADERS
    )
    
    if response.status_code == 200:
        return response.json()["content"]
    else:
        return f"Error: {response.status_code} - {response.text}"

def write_file(file_path, content):
    """Write content to a file through the middleware."""
    response = requests.post(
        f"{BASE_URL}/write-file",
        json={"path": file_path, "content": content},
        headers=HEADERS
    )
    
    if response.status_code == 200:
        return f"Successfully wrote to {file_path}"
    else:
        return f"Error: {response.status_code} - {response.text}"

def create_item(name, description):
    """Create a new item in the database."""
    response = requests.post(
        f"{BASE_URL}/items",
        json={"name": name, "description": description},
        headers=HEADERS
    )
    
    if response.status_code == 200:
        return response.json()
    else:
        return f"Error: {response.status_code} - {response.text}"

def get_item(item_id):
    """Retrieve an item from the database by ID."""
    response = requests.get(
        f"{BASE_URL}/items/{item_id}",
        headers=HEADERS
    )
    
    if response.status_code == 200:
        return response.json()
    else:
        return f"Error: {response.status_code} - {response.text}"

if __name__ == "__main__":
    # Example usage
    print("1. Running CLI command 'ls -la':")
    print(run_cli_command("ls -la"))
    
    print("\n2. Writing to a test file:")
    write_file("test_output.txt", "This is a test file created by the middleware client.")
    
    print("\n3. Reading the test file:")
    print(read_file("test_output.txt"))
    
    print("\n4. Creating an item in the database:")
    item = create_item("Test Item", "This is a test item created by the middleware client.")
    print(json.dumps(item, indent=2) if isinstance(item, dict) else item)
    
    if isinstance(item, dict) and "id" in item:
        print(f"\n5. Retrieving the item with ID {item['id']}:")
        retrieved_item = get_item(item["id"])
        print(json.dumps(retrieved_item, indent=2) if isinstance(retrieved_item, dict) else retrieved_item)
