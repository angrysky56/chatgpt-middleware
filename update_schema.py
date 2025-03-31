#!/usr/bin/env python3
"""
ChatGPT Middleware - Schema Updater

This utility script checks for a running ngrok tunnel and updates the OpenAPI schema
with the correct public URL. This ensures Custom GPT can connect to your middleware.
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
    print(f"\n{Colors.BOLD}🔄 ChatGPT Middleware - Schema URL Updater{Colors.END}")
    print("================================================")

    # Load API key
    load_dotenv()
    api_key = os.getenv("API_KEY", "default_middleware_key")
    
    # Check if server is running
    server_running = False
    try:
        response = requests.get("http://localhost:8000/health", timeout=1)
        if response.status_code == 200:
            server_running = True
            print(f"{Colors.GREEN}✓ Server is running{Colors.END}")
        else:
            print(f"{Colors.YELLOW}⚠ Server returned status {response.status_code}{Colors.END}")
    except:
        print(f"{Colors.RED}✗ Server not running! Start it with: ./start.sh{Colors.END}")
        return

    # Detect publicly accessible URL (ngrok)
    public_url = None
    try:
        response = requests.get("http://localhost:4040/api/tunnels", timeout=1)
        data = response.json()
        for tunnel in data.get('tunnels', []):
            if tunnel.get('proto') == 'https':
                public_url = tunnel.get('public_url')
                print(f"{Colors.GREEN}✓ Ngrok is running with URL: {public_url}{Colors.END}")
                break
    except:
        print(f"{Colors.YELLOW}⚠ Ngrok not detected. Run 'ngrok http 8000' in a separate terminal.{Colors.END}")
        print(f"{Colors.YELLOW}⚠ ChatGPT requires a public URL to access your middleware.{Colors.END}")
        
    # Get local network IP
    try:
        hostname = socket.gethostname()
        local_ip = socket.gethostbyname(hostname)
        local_network = f"http://{local_ip}:8000"
        print(f"{Colors.BLUE}ℹ Local network URL: {local_network}{Colors.END}")
    except:
        local_network = "http://localhost:8000"
        print(f"{Colors.BLUE}ℹ Local URL: {local_network}{Colors.END}")

    # Load and update the schema
    schema_path = os.path.join(os.path.dirname(__file__), "openapi.json")
    
    try:
        with open(schema_path, "r") as f:
            schema = json.load(f)
            
        current_url = schema.get("servers", [{}])[0].get("url", "")
        print(f"{Colors.BLUE}ℹ Current schema URL: {current_url}{Colors.END}")
        
        server_url = public_url if public_url else local_network
        
        # Update the server URL
        if "servers" in schema and len(schema["servers"]) > 0:
            schema["servers"][0]["url"] = server_url
            schema["servers"][0]["description"] = "Dynamic server endpoint"
        else:
            schema["servers"] = [{"url": server_url, "description": "Dynamic server endpoint"}]
            
        # Write updated schema back
        with open(schema_path, "w") as f:
            json.dump(schema, f, indent=2)
            
        print(f"{Colors.GREEN}✓ Schema updated with URL: {server_url}{Colors.END}")
        
        # Print next steps
        print(f"\n{Colors.BOLD}Next Steps:{Colors.END}")
        
        if public_url:
            print(f"1. Go to your Custom GPT and update the schema with URL: {public_url}/openapi.json")
            print(f"2. Or import from URL directly: {public_url}/openapi.json")
        else:
            print(f"1. Start ngrok with: ngrok http 8000")
            print(f"2. Run this script again to update the schema with the public URL")
            
    except Exception as e:
        print(f"{Colors.RED}✗ Error updating schema: {str(e)}{Colors.END}")

if __name__ == "__main__":
    main()
