# ChatGPT System Access Toolkit

A simple middleware solution that gives ChatGPT access to your system through three powerful tools:

1. **Command Line Interface (CLI)** - Run system commands
2. **Filesystem Access** - Read and write files
3. **SQLite Database** - Store and retrieve data

## 🚀 Quick Start Guide

### Setup

```bash
# Clone the repository
git clone https://github.com/angrysky56/chatgpt-middleware.git
cd chatgpt-middleware

# Run the automated setup script
./setup.sh
```

The setup script handles everything automatically:
- Creates a virtual environment
- Installs dependencies
- Configures security settings
- Generates an API key for you

### Starting the Server

```bash
# After running setup.sh
source venv/bin/activate
uvicorn main:app --reload
```

Your middleware server is now running at: http://localhost:8000

## 🔌 Connecting to ChatGPT

### Step 1: Generate the OpenAPI Schema

```bash
./gpt_config.py --format openapi
```

This creates an `openapi.json` file with all endpoints properly configured.

### Step 2: Make Your Schema Available Online

For ChatGPT to access your schema, you need to expose it online:

```bash
# Install ngrok if you don't have it already

[NGROK, free for developers](https://ngrok.com/pricing)

# Create a tunnel to your server
ngrok http 8000
```

This will give you a public URL like: `https://12ab34cd.ngrok.io`

### Step 3: Set Up Custom GPT

1. Go to ChatGPT and create a new Custom GPT or edit an existing one
2. In the "Configure" tab, go to "Actions"
3. Click "Import from URL" and enter: `https://your-ngrok-url/openapi.json`
4. For authentication, select "API Key" and enter:
   - **Name**: X-API-Key
   - **Value**: Your API key (shown during setup)

## 💡 Example Usage

Once connected, you can ask your Custom GPT to:

- "Run the command 'ls -la' to list files"
- "Read the file at /path/to/notes.txt"
- "Create a file called ideas.txt with this content: [content]"
- "Save this to the database: Name: Project X, Description: AI initiative"
- "Get item #3 from the database"

## 🔧 Troubleshooting

### Common Issues

- **Server Issues**: Make sure your server is running with `uvicorn main:app --reload`
- **Connection Issues**: Ensure ngrok is running and your URL is correct
- **Schema Errors**: Run `./gpt_config.py --format openapi` to regenerate a fixed schema
- **API Key Issues**: Check that the API key in your GPT matches the one in your `.env` file

### Testing Your Setup

You can test your API with curl:

```bash
# Get your API key
grep API_KEY .env

# Test a command
curl http://localhost:8000/cli?command=echo+hello -H "X-API-Key: your_api_key"
```

## 🔐 Security Settings

Your middleware has configurable security settings in the `.env` file:

```
API_KEY=your_generated_key
SECURITY_LEVEL=medium  # Options: high, medium, low
ALLOWED_PATHS=/path/to/dir1,/path/to/dir2
```

### Security Levels

- **High**: Only whitelisted commands and paths allowed
- **Medium**: Dangerous commands blocked, but allowed paths accessible
- **Low**: Minimal restrictions (for development only)

### Allowed Paths

You can specify which directories ChatGPT can access by setting the `ALLOWED_PATHS` variable. 
Multiple directories should be comma-separated:

```
ALLOWED_PATHS=/home/user/documents,/home/user/projects,/tmp
```

During setup, you'll be prompted to configure these paths, or you can edit the `.env` file later.

To change any settings, edit the `.env` file or run `./setup.sh` again.
