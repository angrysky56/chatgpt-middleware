#!/bin/bash

# Colors for terminal output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BOLD='\033[1m'
NC='\033[0m' # No Color

clear
echo -e "${BOLD}🚀 ChatGPT System Access Toolkit - Quick Start${NC}"
echo -e "--------------------------------------------------------"

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo -e "${YELLOW}Virtual environment not found. Running setup first...${NC}"
    ./setup.sh
    # If setup.sh exits with an error, stop
    if [ $? -ne 0 ]; then
        exit 1
    fi
else
    source venv/bin/activate
    echo -e "${GREEN}✅ Activated virtual environment${NC}"
fi

# Check if we are in a virtual environment
if [ -z "$VIRTUAL_ENV" ]; then
    echo -e "${RED}❌ Not in a virtual environment. Try running:${NC}"
    echo -e "${BOLD}source venv/bin/activate${NC}"
    exit 1
fi

# Check if we need to upgrade
if [ "$1" == "--upgrade" ]; then
    echo -e "${BLUE}Upgrading dependencies...${NC}"
    pip install --upgrade -r requirements.txt
    echo -e "${GREEN}✅ Dependencies upgraded${NC}"
fi

# Ask user if they want local or public access
echo -e "\n${BOLD}How do you want to access your middleware?${NC}"
echo -e "1) Local only (http://localhost:8000)"
echo -e "2) Public access via ngrok (for ChatGPT)"

read -p "Enter choice [2]: " ACCESS_CHOICE
ACCESS_CHOICE=${ACCESS_CHOICE:-2}

# Find an available port
PORT=8000
while netstat -tuln | grep -q ":$PORT "; do
    PORT=$((PORT+1))
done

echo -e "\n${BLUE}Starting server on port $PORT...${NC}"
if [ "$ACCESS_CHOICE" == "1" ]; then
    # Start server only
    echo -e "${GREEN}Server will be available at:${NC} ${BOLD}http://localhost:$PORT${NC}"
    echo -e "To generate GPT configuration, run: ${BOLD}./gpt_config.py${NC}"
    echo -e "Press Ctrl+C to stop the server."
    uvicorn main:app --reload --port $PORT
else
    # Start server and create tunnel in one go
    echo -e "${GREEN}Starting server and creating public tunnel...${NC}"
    echo -e "A new window will open for the tunnel. Keep both windows open."
    
    # Start the server
    uvicorn main:app --reload --port $PORT &
    SERVER_PID=$!
    
    # Give the server time to start
    sleep 2
    
    # Start tunnel in a new terminal window if possible
    if command -v gnome-terminal &> /dev/null; then
        gnome-terminal -- ./tunnel.sh $PORT
    elif command -v xterm &> /dev/null; then
        xterm -e "./tunnel.sh $PORT" &
    elif command -v terminal &> /dev/null; then
        terminal -e "./tunnel.sh $PORT" &
    else
        # Fall back to starting in the same window
        ./tunnel.sh $PORT
    fi
    
    # If we get here, we're in a GUI environment and have opened a new window
    echo -e "${GREEN}✅ Server started at:${NC} ${BOLD}http://localhost:$PORT${NC}"
    echo -e "${YELLOW}Check the other terminal window for your public URL${NC}"
    echo -e "Press Ctrl+C to stop the server."
    
    # Wait for the server process to complete
    wait $SERVER_PID
fi
