# Quick Start Guide

## One-Command Setup & Start

```bash
# Clone the repository
git clone https://github.com/yourusername/chatgpt-middleware.git
cd chatgpt-middleware

# Run the all-in-one starter script
./start.sh
```

That's it! The script will:
1. Set up the environment
2. Generate an API key
3. Start the server
4. Create a public tunnel (if requested)
5. Generate the GPT configuration

## Using with ChatGPT

1. Go to ChatGPT
2. Create a new Custom GPT
3. In the "Configure" tab, go to "Actions"
4. Copy the OpenAPI configuration from your terminal output
5. Set the API key as shown in the terminal

## Common Commands

```bash
# Start everything with one command
./start.sh

# Get configuration for ChatGPT
./gpt_config.py

# Create a public tunnel separately
./tunnel.sh

# Reconfigure settings
./setup.sh
```

## Need More Help?

See the full [README.md](README.md) for detailed instructions and troubleshooting.
