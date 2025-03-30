# ChatGPT System Access Toolkit

A single integrated middleware solution that provides system access to ChatGPT Custom GPTs through three powerful tools:

1. **Command Line Interface (CLI)** - Run system commands
2. **Filesystem Access** - Read and write files
3. **SQLite Database** - Store and retrieve data

## 🚀 Quick Start Guide

### One-Command Setup

```bash
# Clone the repository
git clone https://github.com/angrysky56/chatgpt-middleware.git
cd chatgpt-middleware

# Run the automated setup script
./setup.sh
```

The setup script handles everything:
- Creates a Python virtual environment
- Installs dependencies
- Configures security settings
- Generates an API key for you
- Provides instructions for the next steps

### Starting the Server

```bash
# After running setup.sh
source venv/bin/activate
uvicorn main:app --reload
```

**Your server will be running at: http://localhost:8000**

### Getting Your Custom GPT Configuration

After starting the server, run:

```bash
# Get your GPT configuration automatically
./gpt_config.py
```

This will output a complete configuration that you can copy directly into your Custom GPT.

## 📦 What's in the Box

This toolkit provides ChatGPT with access to your system through a secure API:

- **Run Commands**: Execute CLI commands on your system
- **Read Files**: Access file contents
- **Write Files**: Create or modify files
- **Store Data**: Save and retrieve information in a SQLite database

All functions use the same API key and security settings, so you only need to configure them once.

## 🛠️ Setting Up Your Custom GPT

### Automated Setup (Recommended)

1. Start your server as shown above
2. Run `./gpt_config.py`
3. Copy the output
4. Paste it into your Custom GPT's "Actions" section

The configuration includes:
- The correct URLs for all endpoints
- Your API key pre-filled
- Proper parameters for each function

### What About Server URLs?

Don't worry about server URLs - the configuration tool automatically detects the correct URL based on how you're running the server:

- **Local testing**: Uses `http://localhost:8000`
- **Network access**: Can use your computer's IP address
- **Public access**: Can use ngrok or other tunneling services

To use a public URL (for accessing from ChatGPT), run:

```bash
./gpt_config.py --url https://your-public-url.com
```

## 🔐 Security

Your server uses:

- **API Key Authentication**: Secure access with a randomly generated key
- **Configurable Security Levels**: Choose high/medium/low security based on your needs
- **Path Restrictions**: Limit filesystem access to safe directories
- **Command Filtering**: Block dangerous commands

All these settings are configured in the `.env` file and can be changed through the setup script.

## 🌐 Making Your Server Accessible to ChatGPT

For ChatGPT to access your server, it needs to be available on the internet. You have three options:

### Option 1: Ngrok (Easiest for Testing)

```bash
# Install ngrok if you don't have it
npm install ngrok -g

# Start a tunnel to your local server
ngrok http 8000

# Then use the ngrok URL with the config tool
./gpt_config.py --url https://your-ngrok-url.com
```

### Option 2: Port Forwarding (Home Networks)

1. Configure your router to forward port 8000 to your computer
2. Find your public IP address (search "what's my IP" online)
3. Use `./gpt_config.py --url http://your-public-ip:8000`

### Option 3: Cloud Deployment (Most Reliable)

Deploy to a cloud provider like AWS, Digital Ocean, or Heroku.

## 📚 Example Usage in ChatGPT

Once configured, you can ask your Custom GPT to:

- "Run the command 'ls -la' to list files"
- "Read the file at /path/to/important-notes.txt"
- "Create a file called project-ideas.txt with the following content: [your content]"
- "Save this information to the database: Name: Project Alpha, Description: New AI initiative"
- "Retrieve item #5 from the database"

## 🔧 Troubleshooting

### Server Won't Start
- Check if another process is using port 8000
- Ensure you've activated the virtual environment: `source venv/bin/activate`

### ChatGPT Can't Connect
- Verify your server is accessible from the internet
- Check that the API key in your GPT matches the one in your `.env` file
- Test your API locally: `curl http://localhost:8000/cli?command=echo+hello -H "X-API-Key: your_api_key"`

### Security Restrictions
- If commands are being blocked, check your security level in `.env`
- For filesystem operations, ensure paths are within allowed directories

### Need More Help?
Run `./gpt_config.py --help` for additional configuration options.

## 🛡️ Advanced Configuration

For advanced users who need more control:

```bash
# Edit your .env file to customize settings
nano .env

# Contents:
API_KEY=your_secure_key
SECURITY_LEVEL=medium  # Options: high, medium, low
```

You can edit this file directly or run `./setup.sh` again to reconfigure.
