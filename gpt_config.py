#!/usr/bin/env python3
"""
ChatGPT Custom GPT Configuration Generator - Simple Version

This script generates the OpenAPI schema required for setting up
a Custom GPT with access to your system through CLI, filesystem, and database.
"""

import os
import json
import socket
import requests
from dotenv import load_dotenv

# ANSI colors for terminal output
class Colors:
    BLUE = '\033[94m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BOLD = '\033[1m'
    END = '\033[0m'

def main():
    print(f"\n{Colors.BOLD}🔧 ChatGPT System Access - Schema Generator{Colors.END}")
    print("================================================")

    # Load API key
    load_dotenv()
    api_key = os.getenv("API_KEY", "default_middleware_key")
    
    # Check if server is running
    server_running = False
    try:
        requests.get("http://localhost:8000/health", timeout=1)
        server_running = True
    except:
        print(f"{Colors.RED}❌ Server not running! Start it with: ./setup.sh{Colors.END}")
        return

    # Detect publicly accessible URL (ngrok)
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

    # Get local network IP
    try:
        hostname = socket.gethostname()
        local_ip = socket.gethostbyname(hostname)
        local_network = f"http://{local_ip}:8000"
    except:
        local_network = "http://localhost:8000"

    # Generate schema
    schema = {
        "openapi": "3.1.0",
        "info": {
            "title": "System Access API",
            "description": "API for system access via CLI, Filesystem, and Database",
            "version": "v1"
        },
        "servers": [
            {
                "url": public_url if public_url else local_network,
                "description": "Server endpoint"
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
            "schemas": {},  # Required for browser compatibility
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
    
    # Save schema file
    with open("openapi.json", "w") as f:
        json.dump(schema, f, indent=2)
    
    # Print setup instructions
    print(f"\n{Colors.GREEN}✅ OpenAPI schema generated!{Colors.END}")
    print(f"\n{Colors.BOLD}Server Status:{Colors.END}")
    print(f"• Local URL: http://localhost:8000")
    
    if public_url:
        print(f"• Public URL: {Colors.GREEN}{public_url}{Colors.END} (via ngrok)")
    else:
        print(f"• Network URL: {local_network}")
        print(f"• {Colors.YELLOW}No public URL detected. Run 'ngrok http 8000' for internet access.{Colors.END}")
    
    print(f"\n{Colors.BOLD}Custom GPT Setup Instructions:{Colors.END}")
    print(f"1. Visit http://localhost:8000/setup-gpt for detailed instructions")
    print(f"2. Your API Key: {Colors.YELLOW}{api_key}{Colors.END}")
    
    # Print a note about the web interface
    print(f"\n{Colors.BOLD}💡 Tip:{Colors.END} Access the web setup guide at {Colors.BOLD}http://localhost:8000/setup-gpt{Colors.END}")

if __name__ == "__main__":
    main()
