#!/usr/bin/env python3
"""
Response Instruction Injector for ChatGPT Middleware

This module specifically targets directory listing hallucinations by adding
explicit instructions and guidance to API responses.
"""

import os
import json
from typing import Dict, Any, List, Optional, Union

class ResponseInjector:
    """
    Injects anti-hallucination instructions into API responses
    """
    
    @staticmethod
    def inject_cli_instructions(command: str, output: str) -> Dict[str, Any]:
        """
        Add clear instructions to CLI responses to prevent hallucinations
        
        Args:
            command: The command that was executed
            output: The raw output text
            
        Returns:
            Response dict with anti-hallucination guidance
        """
        # Check if it's an 'ls' or 'dir' command
        tokens = command.strip().split()
        base_cmd = tokens[0] if tokens else ""
        
        if base_cmd in ["ls", "dir"]:
            return ResponseInjector._inject_directory_listing_instructions(command, output)
        elif base_cmd in ["cat", "more", "less", "type"]:
            return ResponseInjector._inject_file_content_instructions(command, output)
        else:
            # Default instruction injection
            return {
                "output": output,
                "instructions": f"""
When reporting the results of this command, please:
1. Show the exact command executed: `{command}`
2. Present the output exactly as shown, without alteration
3. Do not make assumptions about file or directory structures not present in the output
                """
            }
    
    @staticmethod
    def _inject_directory_listing_instructions(command: str, output: str) -> Dict[str, Any]:
        """Add instructions specific to directory listings"""
        # Find target directory in the command
        tokens = command.strip().split()
        target_dir = None
        
        # Look for a directory path in the command
        for token in tokens:
            if token.startswith("/") or token.startswith("~") or token.startswith("./"):
                target_dir = token
                break
                
        # If no dir found, check the last token without dash
        if not target_dir and len(tokens) > 1:
            last_token = tokens[-1]
            if not last_token.startswith("-"):
                target_dir = last_token
                
        # Default to current directory if still not found
        if not target_dir:
            target_dir = "current directory"
        
        return {
            "output": output,
            "command": command,
            "target_directory": target_dir,
            "instructions": f"""
IMPORTANT - DIRECTORY LISTING WARNING:
When reporting the results of this directory listing:

1. Always explicitly state that these files are in EXACTLY this directory: `{target_dir}`
2. If the output shows files, these exist ONLY in `{target_dir}` - NOT in parent directories
3. DO NOT state or imply that these files exist anywhere else
4. DO NOT expand or extrapolate beyond what is shown in the output
5. If referring to these files later, always include the full directory path

Example correct response format:
"Here are the files in the EXACT directory `{target_dir}` (not in parent or other directories):
- file1.txt
- file2.txt"

Example INCORRECT response (hallucination):
"Here are the files in {os.path.dirname(target_dir)}:
- file1.txt
- file2.txt"
            """,
            "_warning": "Any response suggesting files exist elsewhere than the exact target directory is incorrect"
        }
    
    @staticmethod
    def _inject_file_content_instructions(command: str, output: str) -> Dict[str, Any]:
        """Add instructions specific to file content display"""
        # Extract filename from command
        tokens = command.strip().split()
        file_path = None
        
        # Look for a file path in the command (naively taking the last token)
        if len(tokens) > 1:
            file_path = tokens[-1]
        
        return {
            "output": output,
            "command": command,
            "file_path": file_path,
            "instructions": f"""
IMPORTANT - FILE CONTENT WARNING:
When reporting the content of this file:

1. Always explicitly state the EXACT file path: `{file_path}`
2. This content exists ONLY in the file `{file_path}`
3. DO NOT claim this content exists in any other file
4. Present file content without modifications or additions
5. If referring to this file later, always use the complete file path

Example correct response:
"The content of file `{file_path}` is:
(content here)"

Example INCORRECT response (hallucination):
"The content of file `{os.path.basename(file_path)}` in the parent directory is:
(content here)"
            """,
            "_warning": "Any response suggesting this content exists in a different file is incorrect"
        }
