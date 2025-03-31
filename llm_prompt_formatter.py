#!/usr/bin/env python3
"""
LLM Prompt Formatter - Generates prompts that help prevent hallucinations

This module contains helper functions to create middleware responses that
encourage LLMs to accurately represent directory structures and file locations.
"""

import json
from typing import Dict, Any, List

class LLMPromptFormatter:
    """
    Formats API responses to guide LLM interpretation
    """
    
    @staticmethod
    def enhance_api_response(response: Dict[str, Any], operation_type: str) -> Dict[str, Any]:
        """
        Add LLM-specific guidance to API responses
        
        Args:
            response: The API response to enhance
            operation_type: The type of operation (cli, file_read, etc.)
            
        Returns:
            Enhanced response with LLM guidance
        """
        # Add metadata about structured response
        response["_meta"] = {
            "wrapper_version": "1.0.0",
            "anti_hallucination": True,
            "response_format": "structured"
        }
        
        # Add explicit LLM instructions based on operation type
        if operation_type == "cli":
            response = LLMPromptFormatter._enhance_cli_response(response)
        elif operation_type == "file_read":
            response = LLMPromptFormatter._enhance_file_read_response(response)
            
        return response
    
    @staticmethod
    def _enhance_cli_response(response: Dict[str, Any]) -> Dict[str, Any]:
        """
        Add LLM-specific instructions for CLI responses
        """
        if "suggested_response" not in response:
            response["suggested_response"] = "Please provide a response using the structured data format shown above to prevent hallucinations."
            
        # Add LLM instruction preamble
        response["_llm_instructions"] = """
IMPORTANT INSTRUCTION FOR LLM PROCESSING:
1. Use ONLY the information provided in this API response
2. DO NOT extrapolate or assume existence of files/directories not explicitly listed
3. Present information using the exact paths shown in the response
4. If possible, use the 'suggested_response' field as a template
5. Clearly state the exact directory path being listed to prevent confusion
"""
        return response
    
    @staticmethod
    def _enhance_file_read_response(response: Dict[str, Any]) -> Dict[str, Any]:
        """
        Add LLM-specific instructions for file read responses
        """
        if "suggested_response" not in response:
            response["suggested_response"] = "Please provide a response using the structured data format shown above to prevent hallucinations."
            
        # Add LLM instruction preamble
        response["_llm_instructions"] = """
IMPORTANT INSTRUCTION FOR LLM PROCESSING:
1. Use ONLY the content provided in this API response
2. DO NOT extrapolate or assume existence of other files or additional content
3. Present the file content using the exact path shown in the response
4. If possible, use the 'suggested_response' field as a template
5. Always specify the exact file path to prevent confusion
"""
        return response

# Example usage:
# enhanced_response = LLMPromptFormatter.enhance_api_response(response, "cli")
