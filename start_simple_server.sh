#!/bin/bash

# Colors for terminal output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BOLD='\033[1m'
NC='\033[0m' # No Color

echo -e "${BOLD}🔒 Anti-Hallucination ChatGPT Middleware${NC}"
echo -e "----------------------------------------"

# Activate the virtual environment if it exists
if [ -d "venv" ]; then
    # For bash
    if [ -f "venv/bin/activate" ]; then
        source venv/bin/activate
        echo -e "${GREEN}✓ Activated virtual environment${NC}"
    # For fish shell
    elif [ -f "venv/bin/activate.fish" ]; then
        source venv/bin/activate.fish
        echo -e "${GREEN}✓ Activated virtual environment (fish)${NC}"
    else
        echo -e "${YELLOW}⚠ Could not find activation script for virtual environment${NC}"
    fi
else
    echo -e "${YELLOW}⚠ No virtual environment found${NC}"
fi

# Install dependencies if required
pip install -q flask python-dotenv markdown requests > /dev/null

# Check for ngrok
NGROK_AVAILABLE=false
PUBLIC_URL=""
if command -v ngrok &> /dev/null; then
    NGROK_AVAILABLE=true
    
    # Check if ngrok is already running
    if curl -s http://localhost:4040/api/tunnels > /dev/null; then
        NGROK_RESPONSE=$(curl -s http://localhost:4040/api/tunnels)
        PUBLIC_URL=$(echo $NGROK_RESPONSE | grep -o '"public_url":"[^"]*' | head -1 | cut -d'"' -f4)
        echo -e "${GREEN}✓ Ngrok is already running with URL: ${BOLD}$PUBLIC_URL${NC}"
    else
        echo -e "${YELLOW}⚠ Ngrok is installed but not running.${NC}"
        echo -e "Run 'ngrok http 8000' in a separate terminal to expose your server publicly."
    fi
else
    echo -e "${YELLOW}⚠ Ngrok is not installed. ChatGPT will not be able to access your server from the internet.${NC}"
    echo -e "Install ngrok from https://ngrok.com/download"
fi

# Start the server
echo -e "\n${BLUE}Starting anti-hallucination middleware server...${NC}"

# Define port
PORT=8000

# Copy the current .env to make sure permissions are set properly
if [ -f ".env" ]; then
    API_KEY=$(grep API_KEY .env | cut -d'=' -f2)
    echo -e "${GREEN}✓ Using API Key: ${BOLD}$API_KEY${NC}"
else
    API_KEY="default_middleware_key"
    echo "API_KEY=$API_KEY" > .env
    echo -e "${YELLOW}⚠ Created new .env file with default API key${NC}"
fi

echo -e "\n${BOLD}Server Information:${NC}"
echo -e "• Local URL: http://localhost:$PORT"
if [ ! -z "$PUBLIC_URL" ]; then
    echo -e "• Public URL: $PUBLIC_URL"
fi
echo -e "• API Key: $API_KEY"

echo -e "\n${BOLD}Testing:${NC}"
echo -e "• Visit http://localhost:$PORT/test to test via web interface"
echo -e "• Or use curl: curl \"http://localhost:$PORT/cli?command=ls&apiKey=$API_KEY\""

echo -e "\n${YELLOW}Press Ctrl+C to stop the server${NC}"
echo -e "----------------------------------------"

# Run the server (prefer Flask for simplicity)
export FLASK_APP=simple_cli.py
flask run --host=0.0.0.0 --port=$PORT
