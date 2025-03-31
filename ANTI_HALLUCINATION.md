# Anti-Hallucination Features for ChatGPT Custom GPT

This document explains the anti-hallucination protections added to the middleware to prevent directory and file hallucinations in ChatGPT responses.

## The Problem

When ChatGPT receives file listings or reads files through the middleware, it may:

1. **Location Hallucination**: Present files from a subdirectory as if they exist in the parent directory
2. **Content Hallucination**: Make up file content or misattribute content from one file to another
3. **Path Hallucination**: Incorrectly describe file paths or directory structures

This is particularly problematic for directory listings, where ChatGPT might list files in a completely wrong location.

## Solution Components

### 1. Response Instruction Injector

The `response_instruction_injector.py` module adds explicit instructions to API responses that tell ChatGPT exactly how to present file and directory information:

- **For Directory Listings**: Includes clear warnings to specify the exact directory location and not to report files as being in parent directories
- **For File Reading**: Includes instructions to specify the exact file path and not attribute content to other files

### 2. Simplified Standalone Endpoints

Two simplified endpoints have been created for better stability:

- `simple_cli.py`: A standalone CLI endpoint with anti-hallucination protections
- `simple_file_reader.py`: A standalone file reading endpoint with anti-hallucination protections

### 3. Testing Interface

A web-based testing interface at `/test` allows you to execute commands and view the structured responses that should reduce hallucinations.

## Usage

1. Start the server with anti-hallucination protections:
   ```bash
   ./start_simple_server.sh
   ```

2. Test a directory listing:
   ```bash
   curl "http://localhost:8000/cli?command=ls%20-la%20/path/to/directory&apiKey=your_api_key"
   ```

3. View the structured response with anti-hallucination instructions and warnings.

## Technical Details

The anti-hallucination system adds these elements to responses:

1. **Explicit Path Information**: Full absolute paths to avoid ambiguity
2. **Structured Output**: Clearly formatted data that separates files from directories
3. **Warning Instructions**: Clear instructions for the LLM on how to present the information
4. **Example Correct/Incorrect Responses**: Shows the LLM what good and bad responses look like

## Example

When listing a directory `/home/user/docs/subfolder`, the response includes:

```json
{
  "output": "... raw output ...",
  "command": "ls -la /home/user/docs/subfolder",
  "target_directory": "/home/user/docs/subfolder",
  "instructions": "... explicit instructions ...",
  "_warning": "Any response suggesting files exist elsewhere than the exact target directory is incorrect"
}
```

The instructions explain that files should only be presented as existing in that exact directory, not elsewhere.

## Best Practices

1. Always check ChatGPT's responses for location accuracy
2. If you see hallucination, point it out to ChatGPT and ask it to correct itself
3. Use the `/test` interface to see how responses are formatted with anti-hallucination guidance
