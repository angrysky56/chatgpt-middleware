#!/usr/bin/env python3
"""
Simplified File Reader Endpoint for ChatGPT Middleware

This script provides a standalone, minimal file reading endpoint with
anti-hallucination protections.
"""

import os
import json
import sys
from flask import Flask, request, jsonify
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = Flask(__name__)

# Get API key from environment
API_KEY = os.getenv("API_KEY", "default_middleware_key")

# Security settings
ALLOWED_PATHS = os.getenv("ALLOWED_PATHS", os.getcwd())
if isinstance(ALLOWED_PATHS, str) and "," in ALLOWED_PATHS:
    ALLOWED_PATHS = [p.strip() for p in ALLOWED_PATHS.split(",")]
else:
    ALLOWED_PATHS = [ALLOWED_PATHS]

@app.route("/read-file", methods=["GET"])
def read_file_endpoint():
    """Read file with anti-hallucination protection"""
    # Check API key
    api_key = request.headers.get("X-API-Key") or request.args.get("apiKey")
    if api_key != API_KEY:
        return jsonify({"error": "Invalid API key"}), 403
    
    # Get file path
    path = request.args.get("path")
    if not path:
        return jsonify({"error": "Missing 'path' parameter"}), 400
    
    # Path security check
    path_allowed = False
    for allowed in ALLOWED_PATHS:
        if path.startswith(allowed):
            path_allowed = True
            break
    
    if not path_allowed:
        return jsonify({"error": f"Path '{path}' not allowed"}), 403
    
    # Check if file exists
    if not os.path.isfile(path):
        return jsonify({"error": f"File '{path}' not found"}), 404
    
    # Read file
    try:
        with open(path, 'r', encoding='utf-8') as file:
            content = file.read()
        
        # Create response with anti-hallucination instructions
        response = {
            "content": content,
            "file_path": path,
            "file_name": os.path.basename(path),
            "directory": os.path.dirname(path),
            "instructions": f"""
IMPORTANT - FILE CONTENT WARNING:
When reporting the content of this file:

1. Always explicitly state the EXACT file path: `{path}`
2. This content exists ONLY in the file `{path}`
3. DO NOT claim this content exists in any other file
4. Present file content without modifications or additions
5. If referring to this file later, always use the complete file path

Example correct response:
"The content of file `{path}` is:
(content here)"

Example INCORRECT response (hallucination):
"The content of file `{os.path.basename(path)}` in a different directory is:
(content here)"
            """,
            "_warning": "Any response suggesting this content exists in a different file is incorrect"
        }
        
        return jsonify(response)
        
    except Exception as e:
        return jsonify({"error": f"Error reading file: {str(e)}"}), 500

# Add other endpoints here as needed

if __name__ == "__main__":
    # Default port
    port = 8090
    
    # Check if port specified in command line
    if len(sys.argv) > 1:
        try:
            port = int(sys.argv[1])
        except ValueError:
            print(f"Invalid port: {sys.argv[1]}, using default port 8090")
    
    # Start the server
    print(f"Starting simple file reader server on port {port}")
    print(f"Allowed paths: {ALLOWED_PATHS}")
    
    app.run(host="0.0.0.0", port=port, debug=True)
