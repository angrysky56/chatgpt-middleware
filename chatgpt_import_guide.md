# Troubleshooting ChatGPT Custom GPT Setup

If you're having issues setting up your Custom GPT with the middleware, follow these steps:

## Step 1: Ensure ngrok is running

Make sure ngrok is running and your middleware server is accessible via a public URL:

```bash
./start_with_ngrok.sh
```

## Step 2: Import with the simplified schema

1. In your ChatGPT Custom GPT editor, go to "Configure" and "Actions"
2. Set Authentication to "None" initially (we'll add it back later)
3. Click "Import from URL" and use this URL: 
   ```
   https://YOUR-NGROK-URL/simple-schema.json
   ```
   Replace YOUR-NGROK-URL with your actual ngrok domain

## Step 3: Verify the import worked

You should see no errors after import. The actions should appear in the available actions list.

## Step 4: Add API Key authentication

1. After successful import, change Authentication from "None" to "API Key"
2. Set API Key Name: `X-API-Key`
3. Set API Key Value: your key from the `.env` file
4. Click "Save"

## Step 5: Test the actions

1. Go to the "Preview" tab
2. Try a simple command: "List files in the current directory"
3. Check that it executes properly

## Common Issues and Solutions

### Error: "Could not find a valid URL in servers"

This usually happens when:
- The schema can't be fetched from the URL
- The server URL in the schema isn't in the correct format

**Solutions:**
- Make sure your ngrok URL is correct
- Try using HTTP instead of HTTPS in the schema
- Try manually pasting the schema

### Error when executing commands

If your commands aren't executing:
- Make sure you've added the API Key
- Check that your middleware server is running
- Verify your ngrok URL is still active (they expire)

### Actions defined but not working

If your GPT says it can perform actions but fails:
- The API key might be incorrect
- There might be CORS issues
- Your middleware server might be blocking the requests

Run the diagnostics endpoint to check:
```
https://YOUR-NGROK-URL/health
```

## Understanding and Preventing LLM Hallucinations

When using the middleware with ChatGPT, be aware that the LLM might occasionally:

1. **Misrepresent Directory Structure**: It might list files from a subdirectory but present them as if they're in the parent directory.

2. **Create Fictional Content**: It might fabricate file names, file content, or command outputs that don't exist.

3. **Mix Real with Imaginary**: Most dangerously, it might combine real files/data with fabricated information.

The middleware now includes context with each response to help reduce these issues. When interpreting ChatGPT's responses:

- Always verify critical information from multiple sources
- Be skeptical of very specific file paths or content that seems too perfectly aligned with your expectations
- Check the "context" field in responses which provides metadata about the actual commands executed

## Need more help?

Check the OpenAI forums or GitHub issues for the repository for more solutions.
