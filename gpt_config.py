#!/usr/bin/env python3
"""
ChatGPT Custom GPT Configuration Generator

This tool automatically generates the configuration needed for ChatGPT Custom GPTs
to connect to your middleware server, with all endpoints and your API key pre-configured.
"""

import os
import sys
import json
import socket
import argparse
import requests
import subprocess
from pathlib import Path
from dotenv import load_dotenv
from urllib.parse import urlparse

# ANSI colors for terminal output
class Colors:
    BLUE = '\033[94m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
    END = '\033[0m'

def print_header():
    """Print a nice formatted header"""
    print(f"\n{Colors.BOLD}🔧 ChatGPT System Access Toolkit - Configuration Generator{Colors.END}")
    print("===========================================================")

def get_api_key():
    """Get API key from environment file"""
    load_dotenv()
    api_key = os.getenv("API_KEY", "default_middleware_key")
    
    # Check if this looks like the default key
    if api_key == "default_middleware_key":
        print(f"{Colors.YELLOW}⚠️ Warning: Using default API key. Run setup.sh for better security.{Colors.END}\n")
        
    return api_key

def get_security_level():
    """Get security level from environment file"""
    load_dotenv()
    return os.getenv("SECURITY_LEVEL", "medium")

def detect_server_url(specified_url=None):
    """Auto-detect the best server URL to use"""
    if specified_url:
        return specified_url
        
    # Check if server is running locally
    try:
        response = requests.get("http://localhost:8000/api", timeout=1)
        return "http://localhost:8000"
    except requests.exceptions.ConnectionError:
        pass
        
    # Try to find local IP for network access
    try:
        hostname = socket.gethostname()
        local_ip = socket.gethostbyname(hostname)
        return f"http://{local_ip}:8000"
    except:
        pass
    
    # Check if ngrok is running
    try:
        ngrok_output = subprocess.check_output(['curl', '-s', 'http://localhost:4040/api/tunnels']).decode('utf-8')
        ngrok_data = json.loads(ngrok_output)
        for tunnel in ngrok_data.get('tunnels', []):
            if tunnel.get('proto') == 'https':
                return tunnel.get('public_url')
    except:
        pass
        
    # Default fallback
    return "http://localhost:8000"

def validate_url(url):
    """Validate that the URL is properly formatted"""
    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc])
    except:
        return False

def generate_openapi_schema(base_url, api_key):
    """Generate an OpenAPI schema for Custom GPT actions"""
    schema = {
        "openapi": "3.1.0",
        "info": {
            "title": "System Access API",
            "description": "API for system access via CLI, Filesystem, and Database",
            "version": "v1"
        },
        "servers": [
            {
                "url": base_url
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

def generate_gpt_config(base_url):
    """Generate configuration for ChatGPT Custom GPT actions"""
    api_key = get_api_key()
    security_level = get_security_level()
    
    openapi_schema = generate_openapi_schema(base_url, api_key)
    
    config = {
        "api_key": api_key,
        "security_level": security_level,
        "base_url": base_url,
        "openapi_schema": openapi_schema,
        "actions": {
            "System Commander": {
                "auth": {
                    "type": "service_http",
                    "authorization_type": "bearer",
                    "verification_tokens": {
                        "openai": "YOUR_OPENAI_VERIFICATION_TOKEN"
                    }
                },
                "api": {
                    "type": "openapi",
                    "url": f"{base_url}/openapi.json",
                    "has_user_authentication": False
                },
                "privacy_policy": {
                    "url": ""
                },
                "oauth": {
                    "client_id": "",
                    "client_secret": "",
                    "authorization_url": "",
                    "scope": "",
                    "token_exchange_method": {
                        "method": "POST",
                        "url": ""
                    }
                }
            }
        },
        "individual_endpoints": {
            "cli": {
                "url": f"{base_url}/cli",
                "method": "POST",
                "headers": {
                    "Content-Type": "application/json",
                    "X-API-Key": api_key
                },
                "params": {
                    "command": "{command}"
                },
                "description": "Run system commands"
            },
            "read_file": {
                "url": f"{base_url}/read-file",
                "method": "GET",
                "headers": {
                    "X-API-Key": api_key
                },
                "params": {
                    "path": "{path}"
                },
                "description": "Read file content"
            },
            "write_file": {
                "url": f"{base_url}/write-file",
                "method": "POST",
                "headers": {
                    "Content-Type": "application/json",
                    "X-API-Key": api_key
                },
                "body": {
                    "path": "{path}",
                    "content": "{content}"
                },
                "description": "Write content to a file"
            },
            "create_item": {
                "url": f"{base_url}/items",
                "method": "POST",
                "headers": {
                    "Content-Type": "application/json",
                    "X-API-Key": api_key
                },
                "body": {
                    "name": "{name}",
                    "description": "{description}"
                },
                "description": "Create a database item"
            },
            "get_item": {
                "url": f"{base_url}/items/{{item_id}}",
                "method": "GET",
                "headers": {
                    "X-API-Key": api_key
                },
                "description": "Get a database item"
            }
        }
    }
    
    return config

def test_server_connection(url):
    """Test if the server is accessible"""
    try:
        response = requests.get(f"{url}/cli", params={"command": "echo test"}, 
                               headers={"X-API-Key": get_api_key()}, timeout=3)
        if response.status_code == 200:
            return True, "Connection successful!"
        else:
            return False, f"Server returned status code: {response.status_code}"
    except Exception as e:
        return False, f"Connection failed: {str(e)}"

def is_server_running():
    """Check if the server is currently running"""
    try:
        response = requests.get("http://localhost:8000/cli", 
                               params={"command": "echo test"},
                               headers={"X-API-Key": get_api_key()}, 
                               timeout=1)
        return True
    except:
        return False

def create_gpt_instruction_text(base_url, api_key):
    """Generate user-friendly instructions for setting up the GPT"""
    security_level = get_security_level()
    
    instructions = f"""
{Colors.BOLD}HOW TO SET UP YOUR CUSTOM GPT{Colors.END}

1. Go to ChatGPT and select "Create a GPT" or "Customize"
2. Give your GPT a name (e.g., "System Commander")
3. In the "Configure" tab, go to "Actions"
4. Click "Add action"
5. Copy and paste this information:

{Colors.BOLD}Name:{Colors.END} System Commander
{Colors.BOLD}Description:{Colors.END} Access your system through CLI, files, and database

{Colors.BOLD}Authentication:{Colors.END}
Type: "API Key"
API Key Name: "X-API-Key" 
API Key Value: "{api_key}"

{Colors.BOLD}Schema:{Colors.END}
(Copy the OpenAPI schema below)

{Colors.YELLOW}Your server URL is: {base_url}{Colors.END}
{Colors.YELLOW}Your API Key is: {api_key}{Colors.END}
{Colors.YELLOW}Security level: {security_level}{Colors.END}

{Colors.BOLD}Important:{Colors.END} Make sure your server is running and accessible when using the GPT.
"""
    return instructions

def print_openapi_schema(schema):
    """Print the OpenAPI schema in a user-friendly format"""
    print(f"\n{Colors.BOLD}📝 OpenAPI Schema (Copy this into your Custom GPT){Colors.END}")
    print(f"{Colors.YELLOW}```json{Colors.END}")
    print(json.dumps(schema, indent=2))
    print(f"{Colors.YELLOW}```{Colors.END}")

def get_ngrok_url():
    """Try to get the ngrok URL if it's running"""
    try:
        response = requests.get("http://localhost:4040/api/tunnels", timeout=1)
        data = response.json()
        for tunnel in data.get('tunnels', []):
            if tunnel.get('proto') == 'https':
                return tunnel.get('public_url')
    except:
        return None
    return None

def main():
    parser = argparse.ArgumentParser(
        description="Generate configuration for ChatGPT Custom GPT actions",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  ./gpt_config.py                           # Auto-detect server URL
  ./gpt_config.py --url https://example.com # Use specific URL
  ./gpt_config.py --check                   # Test server connection
  ./gpt_config.py --format openapi          # Get OpenAPI schema only
        """
    )
    parser.add_argument("--url", help="Base URL for the API server")
    parser.add_argument("--format", choices=["full", "openapi", "actions"], default="full", 
                      help="Output format: full=all, openapi=schema only, actions=endpoints only")
    parser.add_argument("--output", help="Output file path (optional)")
    parser.add_argument("--check", action="store_true", help="Test connection to the server")
    
    args = parser.parse_args()
    
    print_header()
    
    # Check if server is running
    server_running = is_server_running()
    if not server_running and not args.url:
        print(f"{Colors.YELLOW}⚠️ Local server doesn't seem to be running.{Colors.END}")
        print(f"   Start your server with: {Colors.BOLD}uvicorn main:app --reload{Colors.END}")
        print(f"   Or specify a URL with: {Colors.BOLD}./gpt_config.py --url https://your-server-url{Colors.END}\n")
    
    # Auto-detect URL or use provided one
    base_url = detect_server_url(args.url)
    
    # Show server status
    if args.check:
        print(f"{Colors.BLUE}🔍 Testing connection to {base_url}...{Colors.END}")
        success, message = test_server_connection(base_url)
        if success:
            print(f"{Colors.GREEN}✅ {message}{Colors.END}")
        else:
            print(f"{Colors.RED}❌ {message}{Colors.END}")
            print(f"\nTroubleshooting tips:")
            print(f"1. Make sure your server is running: {Colors.BOLD}uvicorn main:app --reload{Colors.END}")
            print(f"2. Check that your API key matches the one in the .env file")
            print(f"3. If using a remote URL, ensure it's accessible and correctly formatted")
            sys.exit(1)
    
    # Check if URL is valid
    if not validate_url(base_url):
        print(f"{Colors.RED}❌ Invalid URL format: {base_url}{Colors.END}")
        print(f"Please provide a valid URL (e.g., http://localhost:8000)")
        sys.exit(1)
    
    # Get API key
    api_key = get_api_key()
    
    # Generate configuration
    config = generate_gpt_config(base_url)
    openapi_schema = config["openapi_schema"]
    
    # Show server info
    print(f"{Colors.GREEN}✅ Server Configuration{Colors.END}")
    print(f"• Server URL: {Colors.BOLD}{base_url}{Colors.END}")
    print(f"• API Key: {Colors.BOLD}{api_key}{Colors.END}")
    print(f"• Security Level: {Colors.BOLD}{config['security_level']}{Colors.END}")
    
    # Output based on format
    if args.format == "openapi":
        print_openapi_schema(openapi_schema)
    elif args.format == "actions":
        print(f"\n{Colors.BOLD}📝 API Endpoints{Colors.END}")
        for name, endpoint in config["individual_endpoints"].items():
            print(f"\n{Colors.BOLD}{name.upper()}{Colors.END}")
            print(f"URL: {endpoint['url']}")
            print(f"Method: {endpoint['method']}")
            print(f"API Key: {api_key}")
    else:
        # Print full setup instructions
        print(create_gpt_instruction_text(base_url, api_key))
        print_openapi_schema(openapi_schema)
    
    # Save to file if specified
    if args.output:
        with open(args.output, 'w') as f:
            if args.format == "openapi":
                json.dump(openapi_schema, f, indent=2)
            elif args.format == "actions":
                json.dump(config["individual_endpoints"], f, indent=2)
            else:
                json.dump(config, f, indent=2)
        print(f"\n{Colors.GREEN}✅ Configuration saved to {args.output}{Colors.END}")
    
    # Print server access options
    print(f"\n{Colors.BOLD}🌐 Server Access Options{Colors.END}")
    
    # Local
    print(f"• Local: {Colors.BOLD}http://localhost:8000{Colors.END}")
    
    # Network
    try:
        hostname = socket.gethostname()
        local_ip = socket.gethostbyname(hostname)
        print(f"• Network: {Colors.BOLD}http://{local_ip}:8000{Colors.END}")
    except:
        pass
    
    # Ngrok
    ngrok_url = get_ngrok_url()
    if ngrok_url:
        print(f"• Internet (ngrok): {Colors.BOLD}{ngrok_url}{Colors.END}")
    else:
        print(f"• Internet: Run {Colors.BOLD}ngrok http 8000{Colors.END} in a separate terminal")
    
    # Final note
    print(f"\n{Colors.BOLD}💡 Tip:{Colors.END} For ChatGPT to access your server, it needs to be publicly accessible.")
    print(f"If testing locally, run ngrok: {Colors.BOLD}ngrok http 8000{Colors.END}")

if __name__ == "__main__":
    main()
