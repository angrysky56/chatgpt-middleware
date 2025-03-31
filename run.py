#!/usr/bin/env python3
"""
ChatGPT Middleware - All-in-One Runner

This script handles the complete setup and execution of the ChatGPT middleware,
including virtual environment setup, dependency installation, and server start
with ngrok integration.

Usage:
    python run.py [--no-ngrok]

Options:
    --no-ngrok    Start the server without attempting to use ngrok
"""

import os
import sys
import subprocess
import platform
import json
import socket
import time
import argparse
import secrets
import shutil
from pathlib import Path
import re

# ANSI colors for terminal output (works on most platforms)
class Colors:
    GREEN = '\033[0;32m'
    BLUE = '\033[0;34m'
    YELLOW = '\033[1;33m'
    RED = '\033[0;31m'
    BOLD = '\033[1m'
    END = '\033[0m'


def print_header(title):
    """Print a formatted header"""
    print(f"\n{Colors.BOLD}{title}{Colors.END}")
    print("=" * (len(title) + 5))


def run_command(command, shell=True, check=False, capture_output=True):
    """Run a shell command and return the result"""
    try:
        result = subprocess.run(
            command,
            shell=shell,
            check=check,
            stdout=subprocess.PIPE if capture_output else None,
            stderr=subprocess.PIPE if capture_output else None,
            text=True
        )
        if result.returncode != 0 and capture_output:
            print(f"{Colors.RED}Command failed: {command}{Colors.END}")
            if result.stderr:
                print(f"Error output: {result.stderr}")
        return result
    except Exception as e:
        print(f"{Colors.RED}Error executing command: {e}{Colors.END}")
        return None


def get_python_command():
    """Get the correct python command for the platform"""
    # Try python3 first
    try:
        subprocess.run(["python3", "--version"], capture_output=True, text=True, check=True)
        return "python3"
    except (subprocess.CalledProcessError, FileNotFoundError):
        # Fall back to python
        try:
            version = subprocess.run(["python", "--version"], capture_output=True, text=True, check=True)
            if "Python 3" in version.stdout:
                return "python"
            else:
                print(f"{Colors.RED}Python 3 is required but not found{Colors.END}")
                sys.exit(1)
        except (subprocess.CalledProcessError, FileNotFoundError):
            print(f"{Colors.RED}Python 3 is required but not found{Colors.END}")
            sys.exit(1)


def setup_virtual_env(python_cmd):
    """Set up the virtual environment"""
    print_header("🔧 Setting up virtual environment")
    
    venv_dir = "venv"
    
    # Check if venv already exists
    if os.path.exists(venv_dir):
        print(f"{Colors.GREEN}✓ Virtual environment already exists{Colors.END}")
    else:
        print(f"Creating virtual environment using {python_cmd}...")
        run_command(f"{python_cmd} -m venv {venv_dir}", check=True)
        print(f"{Colors.GREEN}✓ Created virtual environment{Colors.END}")

    # Return paths to python and pip in the virtual environment
    if platform.system() == "Windows":
        venv_python = os.path.join(venv_dir, "Scripts", "python.exe")
        venv_pip = os.path.join(venv_dir, "Scripts", "pip.exe")
    else:
        venv_python = os.path.join(venv_dir, "bin", "python")
        venv_pip = os.path.join(venv_dir, "bin", "pip")
    
    return venv_python, venv_pip


def install_dependencies(venv_pip):
    """Install required dependencies"""
    print_header("📦 Installing dependencies")
    
    # Upgrade pip first
    print("Upgrading pip...")
    result = run_command(f"{venv_pip} install --upgrade pip")
    if result.returncode == 0:
        print(f"{Colors.GREEN}✓ Pip upgraded successfully{Colors.END}")
    
    # Install requirements
    requirements_file = "requirements.txt"
    if os.path.exists(requirements_file):
        print(f"Installing packages from {requirements_file}...")
        result = run_command(f"{venv_pip} install -r {requirements_file}")
        if result.returncode == 0:
            print(f"{Colors.GREEN}✓ Dependencies installed successfully{Colors.END}")
        else:
            print(f"{Colors.RED}Failed to install dependencies{Colors.END}")
            sys.exit(1)
    else:
        print(f"{Colors.RED}Error: {requirements_file} not found{Colors.END}")
        sys.exit(1)


def read_env_file():
    """Read the .env file and return settings as a dictionary"""
    env_file = ".env"
    settings = {
        "API_KEY": "",
        "SECURITY_LEVEL": "medium",
        "ALLOWED_PATHS": ""
    }
    
    if os.path.exists(env_file):
        with open(env_file, "r") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#"):
                    if "=" in line:
                        key, value = line.split("=", 1)
                        settings[key] = value
    
    return settings


def display_allowed_paths(paths):
    """Display the current allowed paths in a formatted way"""
    if not paths:
        print(f"{Colors.YELLOW}No directories are currently allowed for access.{Colors.END}")
        return
    
    paths_list = paths.split(",")
    
    if len(paths_list) == 1:
        print(f"Currently allowed directory: {Colors.BOLD}{paths_list[0]}{Colors.END}")
    else:
        print(f"Currently allowed directories:")
        for i, path in enumerate(paths_list, 1):
            print(f"  {i}. {Colors.BOLD}{path}{Colors.END}")


def manage_allowed_paths(current_paths=""):
    """Interactive function to manage allowed directory paths"""
    print(f"\n{Colors.BLUE}Directory Access Configuration{Colors.END}")
    print("For security, ChatGPT middleware limits file access to specific directories.")
    
    paths_list = []
    if current_paths:
        paths_list = current_paths.split(",")
        display_allowed_paths(current_paths)
    else:
        print(f"{Colors.YELLOW}No directories are currently configured for access.{Colors.END}")
    
    # Ensure current directory is in the list or add it
    cwd = os.getcwd()
    if not paths_list or cwd not in paths_list:
        if not paths_list:
            print(f"Adding current directory: {Colors.BOLD}{cwd}{Colors.END}")
            paths_list.append(cwd)
        else:
            print(f"\nCurrent directory {Colors.BOLD}{cwd}{Colors.END} is not in the allowed list.")
            add_cwd = input("Would you like to add it? (y/n): ").strip().lower()
            if add_cwd in ('y', 'yes'):
                paths_list.append(cwd)
                print(f"Added current directory to allowed paths.")
    
    # Ask if user wants to modify paths
    if paths_list:
        modify = input("\nWould you like to modify the allowed directories? (y/n): ").strip().lower()
        if modify in ('y', 'yes'):
            while True:
                print("\nWhat would you like to do?")
                print("1. Add a directory")
                print("2. Remove a directory")
                print("3. Finished - Save changes")
                
                choice = input("\nEnter your choice (1-3): ").strip()
                
                if choice == '1':  # Add directory
                    new_path = input("Enter the directory path to add: ").strip()
                    
                    # Expand user home directory if needed
                    if new_path.startswith("~"):
                        new_path = os.path.expanduser(new_path)
                    
                    # Convert to absolute path
                    new_path = os.path.abspath(new_path)
                    
                    # Check if path exists
                    if not os.path.exists(new_path):
                        print(f"{Colors.YELLOW}Warning: Directory {new_path} does not exist.{Colors.END}")
                        confirm = input("Add it anyway? (y/n): ").strip().lower()
                        if confirm not in ('y', 'yes'):
                            continue
                    
                    # Check if already in list
                    if new_path in paths_list:
                        print(f"{Colors.YELLOW}This directory is already in the allowed list.{Colors.END}")
                    else:
                        paths_list.append(new_path)
                        print(f"{Colors.GREEN}✓ Added: {new_path}{Colors.END}")
                
                elif choice == '2':  # Remove directory
                    if len(paths_list) == 1:
                        print(f"{Colors.RED}Cannot remove the last directory. At least one must be allowed.{Colors.END}")
                        continue
                    
                    print("\nSelect a directory to remove:")
                    for i, path in enumerate(paths_list, 1):
                        print(f"{i}. {path}")
                    
                    try:
                        index = int(input("\nEnter number to remove (or 0 to cancel): ").strip())
                        if index == 0:
                            continue
                        if 1 <= index <= len(paths_list):
                            removed_path = paths_list.pop(index - 1)
                            print(f"{Colors.GREEN}✓ Removed: {removed_path}{Colors.END}")
                        else:
                            print(f"{Colors.RED}Invalid selection. Please try again.{Colors.END}")
                    except ValueError:
                        print(f"{Colors.RED}Please enter a valid number.{Colors.END}")
                
                elif choice == '3':  # Finished
                    break
                
                else:
                    print(f"{Colors.RED}Invalid choice. Please enter 1, 2, or 3.{Colors.END}")
                
                # Display current list after each action
                print("\nCurrent allowed directories:")
                for i, path in enumerate(paths_list, 1):
                    print(f"{i}. {Colors.BOLD}{path}{Colors.END}")
    
    # Return the final comma-separated list
    return ",".join(paths_list)


def write_env_file(settings):
    """Write settings to the .env file"""
    env_file = ".env"
    
    with open(env_file, "w") as f:
        for key, value in settings.items():
            f.write(f"{key}={value}\n")


def setup_env_file():
    """Set up the .env file with default settings"""
    print_header("⚙️ Setting up configuration")
    
    env_file = ".env"
    settings = read_env_file()
    
    # Check if .env file exists
    if not os.path.exists(env_file):
        # Generate a new API key
        settings["API_KEY"] = secrets.token_hex(16)
        settings["SECURITY_LEVEL"] = "medium"
        
        # Manage allowed paths
        settings["ALLOWED_PATHS"] = manage_allowed_paths()
        
        # Write the .env file with new values
        write_env_file(settings)
        
        print(f"{Colors.GREEN}✓ Created new .env file with:{Colors.END}")
        print(f"  - API Key: {Colors.BOLD}{settings['API_KEY']}{Colors.END}")
        print(f"  - Security level: {Colors.BOLD}{settings['SECURITY_LEVEL']}{Colors.END}")
    else:
        # Check and update allowed paths if needed
        settings["ALLOWED_PATHS"] = manage_allowed_paths(settings.get("ALLOWED_PATHS", ""))
        write_env_file(settings)
        
        print(f"{Colors.GREEN}✓ Configuration updated{Colors.END}")
        print(f"  Note: You can modify settings anytime by editing the {env_file} file")


def check_ngrok():
    """Check if ngrok is installed and available"""
    try:
        result = run_command("ngrok --version", check=False)
        if result and result.returncode == 0:
            ngrok_version = result.stdout.strip()
            print(f"{Colors.GREEN}✓ Ngrok found: {ngrok_version}{Colors.END}")
            return True
        else:
            print(f"{Colors.YELLOW}⚠ Ngrok not found in PATH{Colors.END}")
            print("  For ChatGPT to access this server, please install ngrok:")
            print("  https://ngrok.com/download")
            return False
    except Exception as e:
        print(f"{Colors.YELLOW}⚠ Ngrok not found or not working: {str(e)}{Colors.END}")
        return False


def get_available_port(start_port=8000):
    """Find an available port starting from start_port"""
    port = start_port
    max_port = start_port + 100  # Limit search to 100 ports
    
    while port < max_port:
        try:
            # Try to create a socket at the port
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(1)
            sock.bind(('127.0.0.1', port))
            sock.close()
            return port
        except OSError:
            port += 1
    
    # If we get here, no ports were available
    print(f"{Colors.YELLOW}⚠ No available ports found. Using default port {start_port}{Colors.END}")
    return start_port


def start_server(venv_python, port):
    """Start the FastAPI server"""
    print_header(f"🚀 Starting server on port {port}")
    
    # Start the server as a background process
    if platform.system() == "Windows":
        # Windows uses different syntax for background processes
        server_process = subprocess.Popen(
            f"start cmd /c {venv_python} -m uvicorn main:app --host 0.0.0.0 --port {port}",
            shell=True
        )
    else:
        # Unix-like systems
        server_process = subprocess.Popen(
            [venv_python, "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", str(port)],
            stdout=open("server.log", "w"),
            stderr=subprocess.STDOUT
        )
    
    # Give the server a moment to start
    print(f"Starting server (PID: {server_process.pid})...")
    time.sleep(3)
    
    # Check if server is running
    try:
        import requests
        response = requests.get(f"http://localhost:{port}/health", timeout=2)
        if response.status_code == 200:
            print(f"{Colors.GREEN}✓ Server is running{Colors.END}")
            print(f"  - Local URL: {Colors.BOLD}http://localhost:{port}{Colors.END}")
            print(f"  - Setup page: {Colors.BOLD}http://localhost:{port}/setup-gpt{Colors.END}")
            return server_process
        else:
            print(f"{Colors.YELLOW}⚠ Server response code: {response.status_code}{Colors.END}")
            return server_process
    except Exception as e:
        print(f"{Colors.YELLOW}⚠ Server may not be running properly: {str(e)}{Colors.END}")
        print("  Check server.log for details")
        return server_process


def start_ngrok(port):
    """Start ngrok tunnel to the specified port"""
    print_header("🔄 Starting ngrok tunnel")
    
    # Start ngrok as a background process
    if platform.system() == "Windows":
        ngrok_process = subprocess.Popen(
            f"start cmd /c ngrok http {port}",
            shell=True
        )
    else:
        ngrok_process = subprocess.Popen(
            ["ngrok", "http", str(port)],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
    
    # Give ngrok a moment to start
    print(f"Starting ngrok (PID: {ngrok_process.pid})...")
    time.sleep(5)
    
    # Get the ngrok URL
    try:
        import requests
        response = requests.get("http://localhost:4040/api/tunnels", timeout=2)
        data = response.json()
        
        for tunnel in data.get('tunnels', []):
            if tunnel.get('proto') == 'https':
                public_url = tunnel.get('public_url')
                print(f"{Colors.GREEN}✓ Ngrok tunnel established{Colors.END}")
                print(f"  - Public URL: {Colors.BOLD}{public_url}{Colors.END}")
                return public_url, ngrok_process
        
        print(f"{Colors.YELLOW}⚠ Ngrok tunnel started but no HTTPS URL found{Colors.END}")
        return None, ngrok_process
    except Exception as e:
        print(f"{Colors.YELLOW}⚠ Error getting ngrok URL: {str(e)}{Colors.END}")
        return None, ngrok_process


def update_schema(public_url, port):
    """Update the OpenAPI schema with the correct URL"""
    print_header("📝 Updating OpenAPI schema")
    
    # Define schema file paths
    openapi_path = "openapi.json"
    schema_path = "schema.json"
    
    try:
        # Check if the OpenAPI schema file exists
        if not os.path.exists(openapi_path):
            print(f"{Colors.YELLOW}⚠ OpenAPI schema file not found. Will be generated by the server.{Colors.END}")
            return
        
        # Read the existing OpenAPI schema
        with open(openapi_path, "r") as f:
            schema = json.load(f)
        
        # Determine the URL to use - ensure proper RFC3986 formatting
        if public_url:
            # Sanitize the ngrok URL to ensure it's RFC3986 compliant
            # Strip any potential whitespace and ensure proper formatting
            server_url = public_url.strip()
            
            # Ensure URL has proper scheme (https://)
            if not server_url.startswith(("http://", "https://")):
                server_url = f"https://{server_url}"
        else:
            # Use local URL which should be properly formatted
            try:
                hostname = socket.gethostname()
                local_ip = socket.gethostbyname(hostname)
                server_url = f"http://{local_ip}:{port}"
            except:
                server_url = f"http://localhost:{port}"
        
        # Update the server URL in the schema
        if "servers" in schema and len(schema["servers"]) > 0:
            schema["servers"][0]["url"] = server_url
            schema["servers"][0]["description"] = "Dynamic server endpoint"
        else:
            schema["servers"] = [{"url": server_url, "description": "Dynamic server endpoint"}]
        
        # Add security schemes if they don't exist
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
        
        # Create a backup of schema files before modifying
        if os.path.exists(openapi_path):
            shutil.copy2(openapi_path, f"{openapi_path}.bak")
        if os.path.exists(schema_path):
            shutil.copy2(schema_path, f"{schema_path}.bak")
            
        # Write the updated OpenAPI schema
        with open(openapi_path, "w") as f:
            json.dump(schema, f, indent=2)
        
        # Write the same content to schema.json to ensure they're in sync
        with open(schema_path, "w") as f:
            json.dump(schema, f, indent=2)
        
        print(f"{Colors.GREEN}✓ Schema files updated with URL: {server_url}{Colors.END}")
        print(f"  - Updated openapi.json and schema.json")
        print(f"  - Created backups of original files (.bak)")
    except Exception as e:
        print(f"{Colors.RED}Error updating schema: {str(e)}{Colors.END}")


def print_final_instructions(public_url, port):
    """Print final instructions for the user"""
    print_header("✅ Setup Complete")
    
    print("Your ChatGPT middleware is now running!\n")
    
    if public_url:
        print(f"To set up your Custom GPT:")
        print(f"1. Go to {Colors.BOLD}http://localhost:{port}/setup-gpt{Colors.END}")
        print(f"2. Follow the instructions to create your Custom GPT")
        print(f"3. Import the OpenAPI schema from: {Colors.BOLD}{public_url}/openapi.json{Colors.END}")
        print(f"   (You can also use: {Colors.BOLD}{public_url}/schema.json{Colors.END})")
    else:
        print(f"To set up your Custom GPT:")
        print(f"1. Visit {Colors.BOLD}http://localhost:{port}/setup-gpt{Colors.END} in your browser")
        print(f"2. Follow the instructions to create your Custom GPT")
        print(f"{Colors.YELLOW}Note: ChatGPT requires a publicly accessible URL.{Colors.END}")
        print(f"To make this accessible from the internet, install ngrok: https://ngrok.com/download")
    
    print(f"\n{Colors.BOLD}Local Access:{Colors.END}")
    print(f"- Server: {Colors.BOLD}http://localhost:{port}{Colors.END}")
    print(f"- Setup: {Colors.BOLD}http://localhost:{port}/setup-gpt{Colors.END}")
    print(f"- Docs: {Colors.BOLD}http://localhost:{port}/docs{Colors.END}")
    
    print(f"\n{Colors.YELLOW}Press Ctrl+C to stop the server when finished{Colors.END}")


def main():
    """Main function to run the setup and server"""
    # Set up command line arguments
    parser = argparse.ArgumentParser(description="ChatGPT Middleware Runner")
    parser.add_argument("--no-ngrok", action="store_true", help="Skip ngrok tunnel setup")
    args = parser.parse_args()
    
    # Clear screen and print welcome message
    os.system('cls' if platform.system() == "Windows" else 'clear')
    print(f"{Colors.BOLD}🚀 ChatGPT System Access - All-in-One Runner{Colors.END}")
    print("=" * 50)
    
    # Get the correct Python command
    python_cmd = get_python_command()
    
    # Set up virtual environment
    venv_python, venv_pip = setup_virtual_env(python_cmd)
    
    # Install dependencies
    install_dependencies(venv_pip)
    
    # Set up .env file
    setup_env_file()
    
    # Check if ngrok is available (if needed)
    ngrok_available = True
    if not args.no_ngrok:
        ngrok_available = check_ngrok()
    
    # Find an available port
    port = get_available_port()
    
    # Start the server
    server_process = start_server(venv_python, port)
    if not server_process:
        print(f"{Colors.RED}Failed to start server.{Colors.END}")
        sys.exit(1)
    
    # Start ngrok if available and requested
    public_url = None
    ngrok_process = None
    if ngrok_available and not args.no_ngrok:
        public_url, ngrok_process = start_ngrok(port)
    
    # Update the OpenAPI schema
    update_schema(public_url, port)
    
    # Print final instructions
    print_final_instructions(public_url, port)
    
    # Keep the script running to maintain the processes
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print(f"\n{Colors.YELLOW}Shutting down...{Colors.END}")
        if server_process:
            server_process.terminate()
        if ngrok_process:
            ngrok_process.terminate()
        sys.exit(0)


if __name__ == "__main__":
    main()
