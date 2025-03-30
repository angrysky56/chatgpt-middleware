# Setting Up ChatGPT Custom GPT Actions

This guide provides step-by-step instructions for configuring a Custom GPT to work with the ChatGPT Middleware.

## Prerequisites

1. A running ChatGPT Middleware server (local or internet-accessible)
2. Access to ChatGPT with Custom GPT creation capabilities
3. Your API key from the middleware server

## Quick Setup

The fastest way to get all the necessary configuration is to use the built-in configuration endpoint:

1. Start your middleware server:
   ```bash
   cd /path/to/chatgpt-middleware
   source venv/bin/activate
   uvicorn main:app --reload
   ```

2. Get the configuration:
   ```bash
   curl http://localhost:8000/gpt-config -H "X-API-Key: your_api_key"
   ```
   
   This will output a complete JSON configuration for all available endpoints.

3. Use this configuration when setting up your Custom GPT actions.

## Detailed Setup Guide

### 1. Make your server accessible

If using with ChatGPT, your server needs to be accessible from the internet:

#### Option A: Using ngrok (easiest for testing)
```bash
# Install ngrok if needed
npm install ngrok -g

# Start a tunnel to your local server
ngrok http 8000
```

Note the URL provided by ngrok (like `https://abc123.ngrok.io`).

#### Option B: Port forwarding on your router
Configure your router to forward port 8000 to your computer's local IP address.

#### Option C: Cloud deployment
Deploy the middleware to a cloud provider like AWS, Digital Ocean, etc.

### 2. Create a new Custom GPT

1. Go to ChatGPT and click "Create a GPT"
2. Give it a name and description
3. Under "Configure," go to "Actions"
4. Click "Add action" for each endpoint you want to add

### 3. Configure Individual Actions

For a clean setup, add each action separately:

#### CLI Command Action
```
Name: Execute Command
Description: Run a system command on the server
Endpoint: https://your-server-url/cli
Method: POST
Authentication:
  Type: API Key
  API Key Name: X-API-Key
  API Key Value: your_api_key
Parameters:
  command:
    Description: The command to execute
    Type: String
    Required: Yes
```

#### Read File Action
```
Name: Read File
Description: Read a file from the server
Endpoint: https://your-server-url/read-file
Method: GET
Authentication:
  Type: API Key
  API Key Name: X-API-Key
  API Key Value: your_api_key
Parameters:
  path:
    Description: Path to the file
    Type: String
    Required: Yes
```

#### Write File Action
```
Name: Write File
Description: Write content to a file on the server
Endpoint: https://your-server-url/write-file
Method: POST
Authentication:
  Type: API Key
  API Key Name: X-API-Key
  API Key Value: your_api_key
Request Body:
  {
    "path": "{file_path}",
    "content": "{file_content}"
  }
```

#### Create Database Item Action
```
Name: Create Item
Description: Add an item to the database
Endpoint: https://your-server-url/items
Method: POST
Authentication:
  Type: API Key
  API Key Name: X-API-Key
  API Key Value: your_api_key
Request Body:
  {
    "name": "{item_name}",
    "description": "{item_description}"
  }
```

#### Get Database Item Action
```
Name: Get Item
Description: Get an item from the database by ID
Endpoint: https://your-server-url/items/{item_id}
Method: GET
Authentication:
  Type: API Key
  API Key Name: X-API-Key
  API Key Value: your_api_key
Parameters:
  item_id:
    Description: ID of the item to retrieve
    Type: Integer
    Required: Yes
```

### 4. Alternative: Unified API Action (Advanced)

Instead of individual actions, you can use the unified API endpoint:

```
Name: Unified API
Description: Execute any operation through a single endpoint
Endpoint: https://your-server-url/api
Method: POST
Authentication:
  Type: API Key
  API Key Name: X-API-Key
  API Key Value: your_api_key
Request Body:
  {
    "operation": "{operation}",
    "params": {
      // Parameters specific to each operation
    }
  }
```

### 5. Testing Your Actions

After configuring your Custom GPT, test it with simple commands:

- **CLI**: "Run the command 'echo hello world'"
- **Read File**: "Read the file at /path/to/some/file.txt"
- **Write File**: "Create a file called test.txt with the content 'This is a test'"
- **Database**: "Create a new item with name 'Test Item' and description 'This is a test item'"

### 6. Troubleshooting

If your actions aren't working:

1. **URL Issues**: Ensure your server URL is correct and accessible
2. **API Key**: Check that your API key matches the one in the server's .env file
3. **Headers**: Make sure X-API-Key is added as a header (not a parameter)
4. **Request Format**: Verify the request body has the correct structure
5. **Server Logs**: Check your server logs for detailed error information

### 7. Security Considerations

For production use:

1. Use HTTPS URLs only (not HTTP)
2. Set security level to "high" in your server's .env file
3. Use a long, random API key
4. Consider IP restrictions or additional authentication
5. Regularly audit command and file access logs

### 8. OpenAPI Specification

For advanced setups, you can use the OpenAPI schema:

```json
{
  "openapi": "3.1.0",
  "info": {
    "title": "ChatGPT Middleware API",
    "description": "API for system access via ChatGPT",
    "version": "v1"
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
  ],
  "paths": {
    "/cli": {
      "post": {
        "summary": "Execute a CLI command",
        "parameters": [
          {
            "name": "command",
            "in": "query",
            "required": true,
            "schema": {
              "type": "string"
            }
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
        "parameters": [
          {
            "name": "path",
            "in": "query",
            "required": true,
            "schema": {
              "type": "string"
            }
          }
        ],
        "responses": {
          "200": {
            "description": "File content returned successfully"
          }
        }
      }
    }
    // Additional endpoints...
  }
}
```
