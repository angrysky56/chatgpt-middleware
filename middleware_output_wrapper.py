#!/usr/bin/env python3
"""
Middleware Output Wrapper - Anti-Hallucination Protection

This module adds contextual information to CLI and file operation outputs
to help LLMs avoid hallucinations or misrepresentations.
"""

import os
import re
from typing import Dict, Any, Optional

class OutputWrapper:
    """
    Wraps API output with additional context to reduce LLM hallucinations
    """
    
    @staticmethod
    def wrap_cli_output(command: str, output: str) -> Dict[str, Any]:
        """
        Enhance CLI command output with useful context to prevent hallucinations
        
        Args:
            command: The CLI command that was executed
            output: The raw output from the command
            
        Returns:
            Dict with enhanced output including context
        """
        # Extract key information from the command
        cmd_parts = command.strip().split()
        base_cmd = cmd_parts[0] if cmd_parts else ""
        
        # Add special handling for common commands
        if base_cmd == "ls":
            return OutputWrapper._enhance_ls_output(command, output)
        elif base_cmd in ["cat", "head", "tail"]:
            return OutputWrapper._enhance_file_read_output(command, output)
        elif base_cmd == "find":
            return OutputWrapper._enhance_find_output(command, output)
        else:
            # Default enhancement for other commands
            return {
                "output": output,
                "context": {
                    "command_executed": command,
                    "command_type": base_cmd,
                    "note": "This is the raw output of the command. Interpret with care."
                }
            }
    
    @staticmethod
    def _enhance_ls_output(command: str, output: str) -> Dict[str, Any]:
        """Enhance ls command output with directory context"""
        # Determine target directory from the command
        cmd_parts = command.strip().split()
        target_dir = None
        
        # Look for a path in the command (simple approach)
        for part in cmd_parts:
            if part.startswith("/") or part.startswith("./") or part.startswith("../"):
                target_dir = part
                break
        
        # If no explicit path, assume current directory
        if not target_dir:
            if len(cmd_parts) > 1 and not cmd_parts[1].startswith("-"):
                target_dir = cmd_parts[1]
            else:
                target_dir = "Current directory"
                
        # Parse output to distinguish files from directories
        lines = output.strip().split("\n")
        files = []
        dirs = []
        other_entries = []
        
        for line in lines:
            if not line.strip():
                continue
                
            # Most ls -l output formats have permissions at the start
            if re.search(r'^d\S+', line):  # Directory
                parts = line.split()
                if len(parts) >= 9:
                    name = " ".join(parts[8:])
                    dirs.append(name)
            elif re.search(r'^-\S+', line):  # File
                parts = line.split()
                if len(parts) >= 9:
                    name = " ".join(parts[8:])
                    files.append(name)
            else:
                other_entries.append(line)
        
        # Create structured file list for clarity
        file_list_str = "\n".join([f"- {file}" for file in files])
        dir_list_str = "\n".join([f"- {d}" for d in dirs])
        
        # Create a very explicit, structured response that's harder to misrepresent
        return {
            "output": output,
            "context": {
                "command_executed": command,
                "directory_path": os.path.abspath(target_dir) if target_dir != "Current directory" else os.getcwd(),
                "file_count": len(files),
                "directory_count": len(dirs),
                "is_empty": len(files) == 0 and len(dirs) == 0,
            },
            "structured_output": {
                "directory": target_dir,
                "files_in_this_directory": files,
                "subdirectories_in_this_directory": dirs
            },
            "warning": "IMPORTANT: The files and directories listed above exist ONLY in the exact directory path specified, not in parent or other directories. Any output suggesting these files exist elsewhere is incorrect.",
            "suggested_response": f"""
Directory listing for: {target_dir}

Files found directly in this directory ({len(files)}):
{file_list_str if files else "None"}

Subdirectories found directly in this directory ({len(dirs)}):
{dir_list_str if dirs else "None"}

Note: These files and directories exist ONLY in the specific path shown above, not in parent directories.
"""
        }
    
    @staticmethod
    def _enhance_file_read_output(command: str, output: str) -> Dict[str, Any]:
        """Enhance file reading command output with file context"""
        # Extract filename from command
        cmd_parts = command.strip().split()
        filename = None
        
        for part in cmd_parts:
            if part.startswith("/") or part.startswith("./") or part.startswith("../") or "." in part:
                filename = part
                break
        
        if not filename and len(cmd_parts) > 1:
            filename = cmd_parts[-1]
        
        return {
            "output": output,
            "context": {
                "command_executed": command,
                "file_read": filename,
                "content_length": len(output),
                "note": f"This output shows the content of the file {filename}."
            }
        }
    
    @staticmethod
    def _enhance_find_output(command: str, output: str) -> Dict[str, Any]:
        """Enhance find command output with search context"""
        # Extract search path and pattern
        cmd_parts = command.strip().split()
        search_path = "Current directory"
        search_pattern = None
        
        if len(cmd_parts) > 1:
            for i, part in enumerate(cmd_parts[1:], 1):
                if part.startswith("/") or part.startswith("./") or part.startswith("../"):
                    search_path = part
                elif part == "-name" and i+1 < len(cmd_parts):
                    search_pattern = cmd_parts[i+1]
        
        # Count items found
        items = [line for line in output.strip().split("\n") if line.strip()]
        
        return {
            "output": output,
            "context": {
                "command_executed": command,
                "search_path": search_path,
                "search_pattern": search_pattern,
                "items_found": len(items),
                "note": f"This output shows files/directories found in {search_path} matching the specified criteria."
            }
        }
    
    @staticmethod
    def wrap_file_read_output(path: str, content: str) -> Dict[str, Any]:
        """
        Enhance file read output with useful context
        
        Args:
            path: The path of the file that was read
            content: The content of the file
            
        Returns:
            Dict with enhanced output including context
        """
        file_size = len(content)
        file_ext = os.path.splitext(path)[1].lower() if "." in os.path.basename(path) else "none"
        
        # Special handling for different file types
        file_type = "text"
        if file_ext in [".json", ".js"]:
            file_type = "json/javascript"
        elif file_ext in [".py"]:
            file_type = "python"
        elif file_ext in [".md"]:
            file_type = "markdown"
        elif file_ext in [".csv", ".tsv"]:
            file_type = "csv/tabular data"
        elif file_ext in [".html", ".htm"]:
            file_type = "html"
            
        # Get the first few lines for quick preview
        preview_lines = content.split('\n')[:5]
        preview = '\n'.join(preview_lines)
        if len(preview_lines) < content.count('\n'):
            preview += "\n[...]"
        
        return {
            "content": content,
            "context": {
                "file_path": os.path.abspath(path),
                "file_name": os.path.basename(path),
                "file_size_bytes": file_size,
                "line_count": content.count('\n') + 1,
                "file_type": file_type
            },
            "structured_output": {
                "file": os.path.basename(path),
                "exact_location": os.path.abspath(path),
                "directory": os.path.dirname(os.path.abspath(path)),
                "preview": preview
            },
            "warning": "IMPORTANT: This file exists ONLY at the exact path specified. The content shown is from that specific file. Any output suggesting this content exists in a different file is incorrect.",
            "suggested_response": f"""
File: {os.path.basename(path)}
Location: {os.path.abspath(path)}
Type: {file_type}
Size: {file_size} bytes
Lines: {content.count('\n') + 1}

Content of {os.path.basename(path)}:
```
{content[:1000]}{'...' if len(content) > 1000 else ''}
```
"""
        }

# Example usage:
# wrapped_output = OutputWrapper.wrap_cli_output("ls -la /home/user", "drwxr-xr-x 2 user user 4096 Jan 1 12:00 file.txt")
