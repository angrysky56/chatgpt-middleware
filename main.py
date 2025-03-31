import os
import sys
import json
import socket
import datetime
import requests
import shutil
from enum import Enum
from typing import Dict, Any, List, Optional
from fastapi import FastAPI, HTTPException, Request, Depends, Header, Body, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.security import APIKeyHeader
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, RedirectResponse
from subprocess import Popen, PIPE
from dotenv import load_dotenv
from pydantic import BaseModel, Field
from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.orm import sessionmaker, declarative_base

# Import custom modules
from middleware_output_wrapper import OutputWrapper
from llm_prompt_formatter import LLMPromptFormatter

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
        os.getcwd()  # Default to current working directory
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

app = FastAPI(
    title="ChatGPT System Access Toolkit",
    description="API for system access via CLI, filesystem, and database operations",
    version="1.0.0"
)

# Custom exception handler for method not allowed
@app.exception_handler(405)
async def method_not_allowed_handler(request, exc):
    """Custom handler for method not allowed errors to help debugging"""
    print(f"METHOD NOT ALLOWED: {request.method} {request.url}")
    print(f"Allowed methods: {exc.headers.get('allow', 'NONE')}")
    return JSONResponse(
        status_code=405,
        content={
            "detail": f"Method {request.method} not allowed for {request.url.path}. Allowed methods: {exc.headers.get('allow', 'NONE')}",
            "allowed_methods": exc.headers.get("allow", "").split(", ")
        }
    )

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

# Add basic routes for health checks and info
@app.get("/")
async def root():
    """Root endpoint with basic information"""
    return {
        "name": "ChatGPT System Access Toolkit",
        "version": "1.0.0",
        "status": "online",
        "documentation": "/docs",
        "setup_custom_gpt": "/setup-gpt",
        "test_interface": "/test"
    }

@app.get("/test", response_class=HTMLResponse)
async def test_interface(request: Request):
    """Provide a user-friendly web page for testing the middleware"""
    return templates.TemplateResponse(
        "test_form.html", 
        {
            "request": request,
            "api_key": Config.API_KEY
        }
    )

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "ok", "timestamp": datetime.datetime.now().isoformat()}

@app.get("/chatgpt-guide", include_in_schema=False)
async def get_chatgpt_guide():
    """Serve the ChatGPT import guide"""
    try:
        guide_path = os.path.join(os.path.dirname(__file__), "chatgpt_import_guide.md")
        with open(guide_path, "r") as f:
            content = f.read()
            
        # Replace placeholders with actual values
        public_url = None
        try:
            response = requests.get("http://localhost:4040/api/tunnels", timeout=1)
            data = response.json()
            for tunnel in data.get('tunnels', []):
                if tunnel.get('proto') == 'https':
                    public_url = tunnel.get('public_url')
                    break
        except:
            pass
            
        if public_url:
            content = content.replace("YOUR-NGROK-URL", public_url.replace("https://", ""))
            
        # Convert markdown to HTML
        from markdown import markdown
        html_content = markdown(content)
        
        # Add some basic styling
        styled_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>ChatGPT Custom GPT Import Guide</title>
            <style>
                body {{
                    font-family: system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
                    line-height: 1.6;
                    color: #333;
                    max-width: 800px;
                    margin: 0 auto;
                    padding: 20px;
                }}
                pre {{
                    background-color: #f5f5f5;
                    padding: 15px;
                    border-radius: 5px;
                    overflow-x: auto;
                }}
                code {{
                    background-color: #f5f5f5;
                    padding: 2px 6px;
                    border-radius: 3px;
                }}
                h1, h2, h3 {{
                    color: #0066cc;
                }}
                .warning {{
                    background-color: #fffaed;
                    border-left: 4px solid #e8b339;
                    padding: 15px;
                    margin: 15px 0;
                    border-radius: 4px;
                }}
            </style>
        </head>
        <body>
            {html_content}
        </body>
        </html>
        """
        
        return HTMLResponse(content=styled_content)
    except Exception as e:
        print(f"Error serving guide: {str(e)}")
        raise HTTPException(status_code=500, detail="Error serving guide")

@app.get("/openapi.json", include_in_schema=False, response_class=JSONResponse)
async def get_openapi_schema():
    """Serve the OpenAPI schema with correct content-type headers"""
    # Try to detect if ngrok is running for public URL
    public_url = None
    try:
        response = requests.get("http://localhost:4040/api/tunnels", timeout=1)
        data = response.json()
        for tunnel in data.get('tunnels', []):
            if tunnel.get('proto') == 'https':
                public_url = tunnel.get('public_url')
                # Ensure URL is properly formatted with no trailing whitespace
                public_url = public_url.strip()
                break
    except:
        pass
        
    # Get local network URL
    local_url = "http://localhost:8000"
    network_url = local_url
    
    try:
        hostname = socket.gethostname()
        local_ip = socket.gethostbyname(hostname)
        network_url = f"http://{local_ip}:8000"
    except:
        pass
    
    # Generate a fresh schema with the current server URL
    server_url = public_url if public_url else network_url
    
    # Ensure server_url has proper format for RFC3986
    if server_url and not server_url.startswith(("http://", "https://")):
        server_url = f"https://{server_url}"
    
    # Read the base schema structure
    schema_path = os.path.join(os.path.dirname(__file__), "openapi.json")
    
    try:
        # Read the existing schema but update the server URL
        with open(schema_path, "r") as f:
            schema = json.load(f)
            
        # Update the server URL
        if "servers" in schema and len(schema["servers"]) > 0:
            schema["servers"][0]["url"] = server_url
            schema["servers"][0]["description"] = "Dynamic server endpoint"
        else:
            schema["servers"] = [{"url": server_url, "description": "Dynamic server endpoint"}]
        
        # Make sure security schemes are properly defined
        if "components" not in schema:
            schema["components"] = {}
        
        if "securitySchemes" not in schema["components"]:
            schema["components"]["securitySchemes"] = {
                "ApiKeyAuth": {
                    "type": "apiKey",
                    "in": "header",
                    "name": "X-API-Key"
                }
            }
        
        if "security" not in schema:
            schema["security"] = [{"ApiKeyAuth": []}]
        
        # Create backup before writing
        try:
            if os.path.exists(schema_path):
                backup_path = f"{schema_path}.bak"
                shutil.copy2(schema_path, backup_path)
        except Exception as backup_error:
            print(f"Warning: Could not create backup: {str(backup_error)}")
            
        # Write updated schema back to file for future use
        with open(schema_path, "w") as f:
            json.dump(schema, f, indent=2)
            
        # Also update schema.json to be in sync
        schema_json_path = os.path.join(os.path.dirname(__file__), "schema.json")
        try:
            if os.path.exists(schema_json_path):
                backup_path = f"{schema_json_path}.bak"
                shutil.copy2(schema_json_path, backup_path)
        except Exception as backup_error:
            print(f"Warning: Could not create backup: {str(backup_error)}")
            
        with open(schema_json_path, "w") as f:
            json.dump(schema, f, indent=2)
            
        return schema
    except Exception as e:
        print(f"Error updating schema: {str(e)}")
        # Generate a new schema as fallback
        import subprocess
        try:
            print("Generating new OpenAPI schema...")
            subprocess.run([sys.executable, "gpt_config.py"])
            
            # Now try to read it again
            with open(schema_path, "r") as f:
                return json.load(f)
        except Exception as e:
            print(f"Error generating schema: {str(e)}")
            # Fall back to app.openapi() as last resort
            return app.openapi()

@app.get("/schema.json", include_in_schema=False, response_class=JSONResponse)
async def get_schema_json():
    """Serve the schema.json file (identical to openapi.json) with correct content-type headers"""
    # This endpoint ensures that both openapi.json and schema.json 
    # are available and in sync with the same content
    
    schema_path = os.path.join(os.path.dirname(__file__), "schema.json")
    openapi_path = os.path.join(os.path.dirname(__file__), "openapi.json")
    
    # Try to detect if ngrok is running for public URL
    public_url = None
    try:
        response = requests.get("http://localhost:4040/api/tunnels", timeout=1)
        data = response.json()
        for tunnel in data.get('tunnels', []):
            if tunnel.get('proto') == 'https':
                public_url = tunnel.get('public_url')
                # Ensure URL is properly formatted with no trailing whitespace
                public_url = public_url.strip()
                break
    except:
        pass
        
    # Get local network URL
    local_url = "http://localhost:8000"
    network_url = local_url
    
    try:
        hostname = socket.gethostname()
        local_ip = socket.gethostbyname(hostname)
        network_url = f"http://{local_ip}:8000"
    except:
        pass
    
    # Determine the URL to use
    server_url = public_url if public_url else network_url
    
    # Ensure server_url has proper format for RFC3986
    if server_url and not server_url.startswith(("http://", "https://")):
        server_url = f"https://{server_url}"
    
    try:
        # Check if schema.json exists, if not create it from openapi.json
        if not os.path.exists(schema_path) and os.path.exists(openapi_path):
            with open(openapi_path, "r") as f:
                schema = json.load(f)
                
            # Update the server URL
            if "servers" in schema and len(schema["servers"]) > 0:
                schema["servers"][0]["url"] = server_url
                schema["servers"][0]["description"] = "Dynamic server endpoint"
            else:
                schema["servers"] = [{"url": server_url, "description": "Dynamic server endpoint"}]
            
            # Make sure security schemes are properly defined
            if "components" not in schema:
                schema["components"] = {}
            
            if "securitySchemes" not in schema["components"]:
                schema["components"]["securitySchemes"] = {
                    "ApiKeyAuth": {
                        "type": "apiKey",
                        "in": "header",
                        "name": "X-API-Key"
                    }
                }
            
            if "security" not in schema:
                schema["security"] = [{"ApiKeyAuth": []}]
            
            with open(schema_path, "w") as f:
                json.dump(schema, f, indent=2)
        else:
            # If schema.json exists, update it with the current server URL
            with open(schema_path, "r") as f:
                schema = json.load(f)
                
            # Update the server URL
            if "servers" in schema and len(schema["servers"]) > 0:
                schema["servers"][0]["url"] = server_url
            else:
                schema["servers"] = [{"url": server_url, "description": "Dynamic server endpoint"}]
                
            # Write the updated schema
            with open(schema_path, "w") as f:
                json.dump(schema, f, indent=2)
        
        # Read and return the schema
        with open(schema_path, "r") as f:
            return json.load(f)
    except Exception as e:
        # If schema.json doesn't exist or can't be read, redirect to openapi.json
        print(f"Error serving schema.json: {str(e)}")
        return RedirectResponse(url="/openapi.json")

@app.get("/simple-schema.json", include_in_schema=False)
async def get_simple_schema():
    """Serve a barebones OpenAPI schema that works reliably with ChatGPT"""
    # Try to detect if ngrok is running for public URL
    public_url = None
    try:
        response = requests.get("http://localhost:4040/api/tunnels", timeout=1)
        data = response.json()
        for tunnel in data.get('tunnels', []):
            if tunnel.get('proto') == 'https':
                public_url = tunnel.get('public_url')
                break
    except:
        pass
        
    # Use ngrok URL if available, otherwise use local URL
    server_url = public_url if public_url else "http://localhost:8000"
    
    # Read the simplified schema template
    schema_path = os.path.join(os.path.dirname(__file__), "simple_schema.json")
    
    try:
        with open(schema_path, "r") as f:
            schema = json.load(f)
            
        # Update the server URL
        schema["servers"][0]["url"] = server_url
        
        return schema
    except Exception as e:
        print(f"Error serving simple schema: {str(e)}")
        raise HTTPException(status_code=500, detail="Error serving schema")

@app.get("/schema-for-gpt", include_in_schema=False)
async def get_gpt_specific_schema():
    """Serve a specially formatted OpenAPI schema optimized for ChatGPT Custom GPT"""
    # Try to detect if ngrok is running for public URL
    public_url = None
    try:
        response = requests.get("http://localhost:4040/api/tunnels", timeout=1)
        data = response.json()
        for tunnel in data.get('tunnels', []):
            if tunnel.get('proto') == 'https':
                public_url = tunnel.get('public_url')
                break
    except:
        pass
        
    # Get local network URL as fallback
    local_url = "http://localhost:8000"
    network_url = local_url
    try:
        hostname = socket.gethostname()
        local_ip = socket.gethostbyname(hostname)
        network_url = f"http://{local_ip}:8000"
    except:
        pass
    
    # Use ngrok URL if available, otherwise use local URL
    server_url = public_url if public_url else network_url
    
    # This is a simplified schema that works reliably with Custom GPT
    schema = {
        "openapi": "3.1.0",
        "info": {
            "title": "System Access API",
            "description": "API for system access via CLI, Filesystem, and Database",
            "version": "v1"
        },
        "servers": [
            {
                "url": server_url
            }
        ],
        "paths": {
            "/cli": {
                "post": {
                    "summary": "Execute a CLI command",
                    "operationId": "executeCommand",
                    "parameters": [
                        {
                            "name": "command",
                            "in": "query",
                            "required": True,
                            "schema": {
                                "type": "string"
                            },
                            "description": "Command to execute"
                        }
                    ],
                    "responses": {
                        "200": {
                            "description": "Command executed successfully"
                        }
                    }
                }
            },
            "/read-file": {
                "get": {
                    "summary": "Read a file",
                    "operationId": "readFile",
                    "parameters": [
                        {
                            "name": "path",
                            "in": "query",
                            "required": True,
                            "schema": {
                                "type": "string"
                            },
                            "description": "Path to the file"
                        }
                    ],
                    "responses": {
                        "200": {
                            "description": "File content"
                        }
                    }
                }
            },
            "/write-file": {
                "post": {
                    "summary": "Write to a file",
                    "operationId": "writeFile",
                    "requestBody": {
                        "required": True,
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "properties": {
                                        "path": {
                                            "type": "string",
                                            "description": "Path to the file"
                                        },
                                        "content": {
                                            "type": "string",
                                            "description": "Content to write"
                                        }
                                    },
                                    "required": ["path", "content"]
                                }
                            }
                        }
                    },
                    "responses": {
                        "200": {
                            "description": "File written successfully"
                        }
                    }
                }
            },
            "/items": {
                "post": {
                    "summary": "Create a database item",
                    "operationId": "createItem",
                    "requestBody": {
                        "required": True,
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "properties": {
                                        "name": {
                                            "type": "string",
                                            "description": "Item name"
                                        },
                                        "description": {
                                            "type": "string",
                                            "description": "Item description"
                                        }
                                    },
                                    "required": ["name", "description"]
                                }
                            }
                        }
                    },
                    "responses": {
                        "200": {
                            "description": "Item created successfully"
                        }
                    }
                }
            },
            "/items/{item_id}": {
                "get": {
                    "summary": "Get a database item",
                    "operationId": "getItem",
                    "parameters": [
                        {
                            "name": "item_id",
                            "in": "path",
                            "required": True,
                            "schema": {
                                "type": "integer"
                            },
                            "description": "Item ID"
                        }
                    ],
                    "responses": {
                        "200": {
                            "description": "Item details"
                        }
                    }
                }
            }
        },
        "components": {
            "schemas": {},
            "securitySchemes": {
                "ApiKeyAuth": {
                    "type": "apiKey",
                    "in": "header",
                    "name": "X-API-Key"
                }
            }
        },
        "security": [
            {
                "ApiKeyAuth": []
            }
        ]
    }
    
    return schema

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
    
    # Log the request for debugging
    print(f"API REQUEST: Operation={request.operation}, Params={request.params}")
        
    try:
        # Route to appropriate handler based on operation
        if request.operation == "cli":
            # Ensure command parameter exists
            if "command" not in request.params:
                raise HTTPException(status_code=400, detail="Missing 'command' parameter for CLI operation")
            return await run_cli(request.params.get("command", ""))
        elif request.operation == "read_file":
            if "path" not in request.params:
                raise HTTPException(status_code=400, detail="Missing 'path' parameter for read_file operation")
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
        # More detailed error logging
        print(f"API ERROR: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))

# Individual endpoints (still available for direct use)
# Support both GET and POST for CLI commands for better compatibility
@app.post("/cli")
@app.get("/cli")
async def run_cli(
    command: str, 
    format: str = "json", 
    request: Request = None,
    api_key: str = Header(None, alias="X-API-Key"),
    apiKey: str = None  # For query parameter from form
):
    # Handle API key from either header or query param
    key = api_key or apiKey
    if not key or key != Config.API_KEY:
        raise HTTPException(status_code=403, detail="Invalid API Key")
    # Security check based on configuration
    if not Config.is_command_allowed(command):
        raise HTTPException(status_code=403, detail="Command not allowed due to security restrictions")
    
    process = Popen(command, shell=True, stdout=PIPE, stderr=PIPE, text=True)
    stdout, stderr = process.communicate()
    
    # Log output for debugging
    print(f"COMMAND: {command}")
    print(f"STDOUT: {stdout}")
    print(f"STDERR: {stderr}")
    
    # Handle case where command executes but produces no output
    if not stdout and not stderr:
        return {
            "output": f"Command executed successfully, but produced no output. This might mean the directory is empty or there's a permission issue.",
            "command": command,
            "structured_output": {
                "command": command,
                "status": "SUCCESS_NO_OUTPUT",
                "note": "This command executed successfully but produced no output."
            },
            "suggested_response": f"""
The command `{command}` executed successfully but didn't produce any output.
This often happens when:
- A directory is empty (for listing commands)
- An operation completed without errors (for file operations)
- The command doesn't normally produce output
"""
        }
    
    # Return stderr as part of output if it exists but wasn't fatal
    if stderr and not stdout:
        wrapped_output = {
            "output": f"Warning: {stderr}",
            "command": command,
            "structured_output": {
                "command": command,
                "status": "WARNING",
                "error_message": stderr
            },
            "suggested_response": f"""
The command `{command}` produced a warning:
```
{stderr}
```
"""
        }
        return wrapped_output
    
    # Normal case - return the enhanced command output with context
    wrapped_output = OutputWrapper.wrap_cli_output(command, stdout.strip())
    
    # Add LLM guidance to prevent hallucinations
    enhanced_output = LLMPromptFormatter.enhance_api_response(wrapped_output, "cli")
    
    # Return as HTML if requested
    if format.lower() == "html" and request is not None:
        suggested = enhanced_output.get("suggested_response", "")
        structured = json.dumps(enhanced_output.get("structured_output", {}), indent=2)
        
        return templates.TemplateResponse(
            "middleware_response.html",
            {
                "request": request,
                "command": command,
                "raw_output": stdout.strip(),
                "structured_output": structured,
                "suggested_response": suggested
            }
        )
    
    return enhanced_output

@app.get("/read-file")
async def read_file(
    path: str, 
    format: str = "json", 
    request: Request = None,
    api_key: str = Header(None, alias="X-API-Key"),
    apiKey: str = None  # For query parameter from form
):
    # Handle API key from either header or query param
    key = api_key or apiKey
    if not key or key != Config.API_KEY:
        raise HTTPException(status_code=403, detail="Invalid API Key")
    # Security check based on configuration
    if not Config.is_path_allowed(path):
        raise HTTPException(status_code=403, detail="Path access restricted due to security settings")
    
    if not os.path.isfile(path):
        raise HTTPException(status_code=404, detail="File not found")
    
    try:
        with open(path, 'r', encoding='utf-8') as file:
            content = file.read()
        
        # Return enhanced file content with context
        wrapped_content = OutputWrapper.wrap_file_read_output(path, content)
        
        # Add LLM guidance to prevent hallucinations
        enhanced_content = LLMPromptFormatter.enhance_api_response(wrapped_content, "file_read")
        
        # Return as HTML if requested
        if format.lower() == "html" and request is not None:
            suggested = enhanced_content.get("suggested_response", "")
            structured = json.dumps(enhanced_content.get("structured_output", {}), indent=2)
            
            return templates.TemplateResponse(
                "middleware_response.html",
                {
                    "request": request,
                    "command": f"read-file {path}",
                    "raw_output": content,
                    "structured_output": structured,
                    "suggested_response": suggested
                }
            )
        
        return enhanced_content
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
# Set up Jinja2 templates
templates = Jinja2Templates(directory="templates")

@app.get("/setup-gpt", response_class=HTMLResponse)
async def setup_gpt(request: Request):
    """Provide a user-friendly web page for setting up a Custom GPT"""
    # Try to detect if ngrok is running for public URL
    public_url = None
    try:
        response = requests.get("http://localhost:4040/api/tunnels", timeout=1)
        data = response.json()
        for tunnel in data.get('tunnels', []):
            if tunnel.get('proto') == 'https':
                public_url = tunnel.get('public_url')
                # Ensure URL is properly formatted with no trailing whitespace
                public_url = public_url.strip()
                break
    except:
        pass
        
    # Get local network URL
    local_url = "http://localhost:8000"
    network_url = local_url
    hostname = socket.gethostname()
    try:
        local_ip = socket.gethostbyname(hostname)
        network_url = f"http://{local_ip}:8000"
    except:
        pass
    
    # Ensure URLs have proper format for RFC3986
    if public_url and not public_url.startswith(("http://", "https://")):
        public_url = f"https://{public_url}"
    
    # Get OpenAPI schema
    schema_path = os.path.join(os.path.dirname(__file__), "openapi.json")
    try:
        with open(schema_path, "r") as f:
            schema = json.load(f)
            
        # Ensure schema has proper server URL
        if "servers" in schema and len(schema["servers"]) > 0:
            if public_url:
                schema["servers"][0]["url"] = public_url
            else:
                schema["servers"][0]["url"] = network_url
                
        # Convert to JSON string for template
        schema_json = json.dumps(schema, indent=2)
    except:
        # Generate schema if it doesn't exist
        openapi_schema = app.openapi()
        # Add proper server URL
        if "servers" not in openapi_schema or not openapi_schema["servers"]:
            server_url = public_url if public_url else network_url
            openapi_schema["servers"] = [{"url": server_url, "description": "Dynamic server endpoint"}]
            
        schema_json = json.dumps(openapi_schema, indent=2)
        # Save for future use
        with open("openapi.json", "w") as f:
            f.write(schema_json)
    
    # Render the HTML template
    return templates.TemplateResponse(
        "setup.html", 
        {
            "request": request,
            "local_url": local_url,
            "network_url": network_url,
            "public_url": public_url,
            "api_key": Config.API_KEY,
            "schema_json": schema_json
        }
    )
