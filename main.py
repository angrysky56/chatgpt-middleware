import os
import json
from enum import Enum
from typing import Dict, Any, List, Optional
from fastapi import FastAPI, HTTPException, Request, Depends, Header, Body
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.security import APIKeyHeader
from subprocess import Popen, PIPE
from dotenv import load_dotenv
from pydantic import BaseModel, Field
from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.orm import sessionmaker, declarative_base

# Load environment variables
load_dotenv()

class SecurityLevel(str, Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    
# Configuration
class Config:
    # API Authentication
    API_KEY = os.getenv("API_KEY", "default_middleware_key")
    SECURITY_LEVEL = os.getenv("SECURITY_LEVEL", SecurityLevel.MEDIUM)
    
    # Command whitelist for high security
    ALLOWED_COMMANDS = [
        "ls", "dir", "pwd", "echo", "cat", "head", "tail", 
        "grep", "find", "wc", "date", "ps", "df"
    ]
    
    # Path restrictions for security levels
    # These can be overridden by ALLOWED_PATHS in the .env file
    DEFAULT_ALLOWED_PATHS = [
        "/home/ty/Repositories/ai_workspace"
    ]
    
    # Get allowed paths from environment variable if defined
    ALLOWED_PATHS = os.getenv("ALLOWED_PATHS", None)
    if ALLOWED_PATHS:
        # Split by comma and strip whitespace
        ALLOWED_PATHS = [path.strip() for path in ALLOWED_PATHS.split(",")]
    else:
        ALLOWED_PATHS = DEFAULT_ALLOWED_PATHS
    
    @classmethod
    def is_command_allowed(cls, command):
        """Check if a command is allowed based on security level"""
        if cls.SECURITY_LEVEL == SecurityLevel.LOW:
            return True
            
        command_parts = command.strip().split()
        base_command = command_parts[0]
        
        if cls.SECURITY_LEVEL == SecurityLevel.MEDIUM:
            # Block dangerous commands in medium security
            dangerous_commands = ["rm", "rmdir", "mv", "dd", "mkfs", ">", "sudo", "su"]
            return base_command not in dangerous_commands
            
        # High security - only allow whitelisted commands
        return base_command in cls.ALLOWED_COMMANDS
    
    @classmethod
    def is_path_allowed(cls, path):
        """Check if a file path is allowed based on security level"""
        if cls.SECURITY_LEVEL == SecurityLevel.LOW:
            return True
            
        # For medium and high security, check path restrictions
        for allowed_path in cls.ALLOWED_PATHS:
            if path.startswith(allowed_path):
                return True
                
        return False

# API key authentication
api_key_header = APIKeyHeader(name="X-API-Key")

def verify_api_key(api_key: str = Depends(api_key_header)):
    if api_key != Config.API_KEY:
        raise HTTPException(status_code=403, detail="Invalid API Key")

app = FastAPI()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Update this in production to specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add global authentication
app.dependency_overrides[api_key_header] = lambda: Config.API_KEY

# Database Setup
engine = create_engine('sqlite:///localdb.sqlite3')
SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()

class Item(Base):
    __tablename__ = 'items'
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    description = Column(String)

Base.metadata.create_all(bind=engine)

class ItemSchema(BaseModel):
    name: str
    description: str

# Request models
class CommandRequest(BaseModel):
    command: str = Field(..., description="CLI command to execute")

class FileReadRequest(BaseModel):
    path: str = Field(..., description="Path to the file to read")

class FileWriteRequest(BaseModel):
    path: str = Field(..., description="Path where to write the file")
    content: str = Field(..., description="Content to write to the file")

# Unified API endpoint for all operations
class ApiRequest(BaseModel):
    operation: str = Field(..., description="Operation to perform: cli, read_file, write_file, create_item, get_item")
    params: Dict[str, Any] = Field(default={}, description="Parameters for the operation")

@app.post("/api")
async def unified_api(request: ApiRequest, api_key: str = Depends(api_key_header)):
    # Validate API key
    if api_key != Config.API_KEY:
        raise HTTPException(status_code=403, detail="Invalid API Key")
        
    try:
        # Route to appropriate handler based on operation
        if request.operation == "cli":
            return await run_cli(request.params.get("command", ""))
        elif request.operation == "read_file":
            return await read_file(request.params.get("path", ""))
        elif request.operation == "write_file":
            return await write_file(FileWriteRequest(**request.params))
        elif request.operation == "create_item":
            return await create_item(ItemSchema(**request.params))
        elif request.operation == "get_item":
            return await get_item(request.params.get("item_id", 0))
        else:
            raise HTTPException(status_code=400, detail=f"Unknown operation: {request.operation}")
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# Individual endpoints (still available for direct use)
@app.post("/cli", dependencies=[Depends(verify_api_key)])
async def run_cli(command: str):
    # Security check based on configuration
    if not Config.is_command_allowed(command):
        raise HTTPException(status_code=403, detail="Command not allowed due to security restrictions")
    
    process = Popen(command, shell=True, stdout=PIPE, stderr=PIPE, text=True)
    stdout, stderr = process.communicate()
    if stderr:
        raise HTTPException(status_code=400, detail=stderr)
    return {"output": stdout.strip()}

@app.get("/read-file", dependencies=[Depends(verify_api_key)])
async def read_file(path: str):
    # Security check based on configuration
    if not Config.is_path_allowed(path):
        raise HTTPException(status_code=403, detail="Path access restricted due to security settings")
    
    if not os.path.isfile(path):
        raise HTTPException(status_code=404, detail="File not found")
    
    try:
        with open(path, 'r', encoding='utf-8') as file:
            content = file.read()
        return {"content": content}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to read file: {str(e)}")

@app.post("/write-file", dependencies=[Depends(verify_api_key)])
async def write_file(data: FileWriteRequest):
    # Security check based on configuration
    if not Config.is_path_allowed(data.path):
        raise HTTPException(status_code=403, detail="Path access restricted due to security settings")
    
    try:
        # Create directory if it doesn't exist
        directory = os.path.dirname(data.path)
        if directory and not os.path.exists(directory):
            os.makedirs(directory)
            
        with open(data.path, 'w', encoding='utf-8') as file:
            file.write(data.content)
        return {"status": "success", "path": data.path}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to write file: {str(e)}")

# Database CRUD endpoints
@app.post("/items", dependencies=[Depends(verify_api_key)])
async def create_item(item: ItemSchema):
    try:
        session = SessionLocal()
        db_item = Item(name=item.name, description=item.description)
        session.add(db_item)
        session.commit()
        session.refresh(db_item)
        
        # Convert to dict for JSON serialization
        result = {
            "id": db_item.id,
            "name": db_item.name,
            "description": db_item.description
        }
        
        session.close()
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

@app.get("/items/{item_id}", dependencies=[Depends(verify_api_key)])
async def get_item(item_id: int):
    try:
        session = SessionLocal()
        item = session.query(Item).filter(Item.id == item_id).first()
        session.close()
        
        if not item:
            raise HTTPException(status_code=404, detail="Item not found")
            
        # Convert to dict for JSON serialization
        return {
            "id": item.id,
            "name": item.name,
            "description": item.description
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

# GPT Action Configuration Endpoint
@app.get("/gpt-config", dependencies=[Depends(verify_api_key)])
async def get_gpt_config(base_url: Optional[str] = "http://localhost:8000"):
    """Generate configuration for GPT actions"""
    config = {
        "api_key": Config.API_KEY,
        "security_level": Config.SECURITY_LEVEL,
        "endpoints": {
            "unified": {
                "url": f"{base_url}/api",
                "method": "POST",
                "headers": {
                    "Content-Type": "application/json",
                    "X-API-Key": Config.API_KEY
                },
                "body": {
                    "operation": "{operation}",
                    "params": "{params}"
                },
                "description": "Unified endpoint for all operations"
            },
            "cli": {
                "url": f"{base_url}/cli",
                "method": "POST",
                "headers": {
                    "Content-Type": "application/json",
                    "X-API-Key": Config.API_KEY
                },
                "params": {
                    "command": "{command}"
                },
                "description": "Execute CLI commands"
            },
            "read_file": {
                "url": f"{base_url}/read-file",
                "method": "GET",
                "headers": {
                    "X-API-Key": Config.API_KEY
                },
                "params": {
                    "path": "{file_path}"
                },
                "description": "Read file content"
            },
            "write_file": {
                "url": f"{base_url}/write-file",
                "method": "POST",
                "headers": {
                    "Content-Type": "application/json",
                    "X-API-Key": Config.API_KEY
                },
                "body": {
                    "path": "{file_path}",
                    "content": "{file_content}"
                },
                "description": "Write content to a file"
            },
            "create_item": {
                "url": f"{base_url}/items",
                "method": "POST",
                "headers": {
                    "Content-Type": "application/json",
                    "X-API-Key": Config.API_KEY
                },
                "body": {
                    "name": "{item_name}",
                    "description": "{item_description}"
                },
                "description": "Create a database item"
            },
            "get_item": {
                "url": f"{base_url}/items/{item_id}",
                "method": "GET",
                "headers": {
                    "X-API-Key": Config.API_KEY
                },
                "description": "Get a database item by ID"
            }
        }
    }
    
    return config
