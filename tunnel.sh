#!/bin/bash

# Colors for terminal output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BOLD='\033[1m'
NC='\033[0m' # No Color

clear
echo -e "${BOLD}🌐 ChatGPT System Access Toolkit - Public Tunnel${NC}"
echo -e "--------------------------------------------------------"
echo -e "This script sets up a public URL for your middleware server."
echo ""

# Check if ngrok is installed
if ! command -v ngrok &> /dev/null; then
    echo -e "${RED}❌ Ngrok is not installed.${NC}"
    echo -e "You need to install ngrok to create a public tunnel:"
    
    # Check which package manager is available
    if command -v npm &> /dev/null; then
        echo -e "${BLUE}Install with npm:${NC}"
        echo -e "npm install ngrok -g"
    elif command -v brew &> /dev/null; then
        echo -e "${BLUE}Install with Homebrew:${NC}"
        echo -e "brew install ngrok/ngrok/ngrok"
    else
        echo -e "${BLUE}Download from:${NC} https://ngrok.com/download"
    fi
    
    read -p "Do you want to try installing with npm? (y/n): " install_choice
    if [[ $install_choice == "y" || $install_choice == "Y" ]]; then
        echo -e "Installing ngrok..."
        npm install -g ngrok
        
        if [ $? -ne 0 ]; then
            echo -e "${RED}Installation failed. Please install ngrok manually.${NC}"
            exit 1
        fi
    else
        echo -e "Please install ngrok and run this script again."
        exit 1
    fi
fi

# Check if server is running
if ! curl -s http://localhost:8000 > /dev/null; then
    echo -e "${YELLOW}⚠️ Warning: Your middleware server doesn't seem to be running.${NC}"
    echo -e "Start your server first with:"
    echo -e "${BOLD}source venv/bin/activate${NC}"
    echo -e "${BOLD}uvicorn main:app --reload${NC}"
    
    read -p "Do you want to start the server now? (y/n): " start_server
    if [[ $start_server == "y" || $start_server == "Y" ]]; then
        echo -e "Starting server in the background..."
        source venv/bin/activate
        nohup uvicorn main:app --reload > server.log 2>&1 &
        SERVER_PID=$!
        echo -e "Server started with PID: $SERVER_PID"
        sleep 3
    else
        echo -e "Please start the server before creating a tunnel."
        exit 1
    fi
fi

# Start ngrok
echo -e "${BLUE}Starting ngrok tunnel...${NC}"

# Check if port is specified
PORT=8000
if [ ! -z "$1" ]; then
    PORT=$1
fi

# Start ngrok with basic auth disabled
echo -e "Creating tunnel to port $PORT..."
ngrok http $PORT --log=stdout > /dev/null &
NGROK_PID=$!

# Wait for ngrok to start
sleep 3

# Get the public URL
NGROK_URL=$(curl -s http://localhost:4040/api/tunnels | grep -o '"public_url":"[^"]*' | grep -o 'http[^"]*')

if [ -z "$NGROK_URL" ]; then
    echo -e "${RED}❌ Failed to get ngrok URL. Please check if ngrok is running correctly.${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Tunnel created successfully!${NC}"
echo -e "Your server is now accessible at: ${BOLD}$NGROK_URL${NC}"
echo ""

# Generate GPT configuration with the ngrok URL
echo -e "${BLUE}Generating GPT configuration with the public URL...${NC}"
./gpt_config.py --url $NGROK_URL

echo -e "\n${YELLOW}Keep this terminal window open to maintain the tunnel.${NC}"
echo -e "Press Ctrl+C to stop the tunnel when you're done."

# Keep the script running to maintain the tunnel
trap "kill $NGROK_PID 2>/dev/null" EXIT
while true; do
    sleep 1
done
