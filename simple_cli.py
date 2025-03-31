#!/usr/bin/env python3
"""
Simplified CLI Endpoint for ChatGPT Middleware

This script provides a standalone, minimal CLI endpoint with
anti-hallucination protections to prevent directory listing issues.
"""

import os
import json
import sys
from subprocess import Popen, PIPE
from flask import Flask, request, jsonify
from dotenv import load_dotenv
from response_instruction_injector import ResponseInjector

# Load environment variables
load_dotenv()

app = Flask(__name__)

# Get API key from environment
API_KEY = os.getenv("API_KEY", "default_middleware_key")

# Security settings
ALLOWED_COMMANDS = ["ls", "dir", "cat", "head", "tail", "grep", "pwd", "echo"]
ALLOWED_PATHS = os.getenv("ALLOWED_PATHS", os.getcwd())
if isinstance(ALLOWED_PATHS, str) and "," in ALLOWED_PATHS:
    ALLOWED_PATHS = [p.strip() for p in ALLOWED_PATHS.split(",")]
else:
    ALLOWED_PATHS = [ALLOWED_PATHS]

@app.route("/cli", methods=["GET", "POST"])
def cli_endpoint():
    """Execute CLI command with anti-hallucination protection"""
    # Check API key
    api_key = request.headers.get("X-API-Key") or request.args.get("apiKey")
    if api_key != API_KEY:
        return jsonify({"error": "Invalid API key"}), 403
    
    # Get command from query parameters or JSON body
    command = None
    if request.method == "GET":
        command = request.args.get("command")
    else:
        if request.is_json:
            command = request.json.get("command")
        else:
            command = request.form.get("command")
    
    if not command:
        return jsonify({"error": "Missing 'command' parameter"}), 400
    
    # Basic security check
    cmd_parts = command.strip().split()
    base_cmd = cmd_parts[0] if cmd_parts else ""
    
    if base_cmd not in ALLOWED_COMMANDS:
        return jsonify({"error": f"Command '{base_cmd}' not allowed"}), 403
    
    # Path security check for directory listing
    has_path = False
    for part in cmd_parts[1:]:
        if part.startswith("/") or part.startswith("~"):
            has_path = True
            path_allowed = False
            for allowed in ALLOWED_PATHS:
                if part.startswith(allowed):
                    path_allowed = True
                    break
            if not path_allowed:
                return jsonify({"error": f"Path '{part}' not allowed"}), 403
    
    # Execute command
    try:
        process = Popen(command, shell=True, stdout=PIPE, stderr=PIPE, text=True)
        stdout, stderr = process.communicate()
        
        if process.returncode != 0:
            return jsonify({"error": f"Command failed: {stderr}"}), 500
        
        # Create response with anti-hallucination instructions
        response = ResponseInjector.inject_cli_instructions(command, stdout)
        return jsonify(response)
        
    except Exception as e:
        return jsonify({"error": f"Error executing command: {str(e)}"}), 500

# Add other endpoints here as needed

if __name__ == "__main__":
    # Default port
    port = 8080
    
    # Check if port specified in command line
    if len(sys.argv) > 1:
        try:
            port = int(sys.argv[1])
        except ValueError:
            print(f"Invalid port: {sys.argv[1]}, using default port 8080")
    
    # Start the server
    print(f"Starting simple CLI server on port {port}")
    print(f"Allowed commands: {', '.join(ALLOWED_COMMANDS)}")
    print(f"Allowed paths: {ALLOWED_PATHS}")
    
    app.run(host="0.0.0.0", port=port, debug=True)
