#!/bin/bash

# Define colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BOLD='\033[1m'
NC='\033[0m' # No Color

clear
echo -e "${BOLD}🚀 ChatGPT System Access Toolkit - Automated Setup${NC}"
echo -e "--------------------------------------------------------"
echo -e "This script will set up your middleware that connects ChatGPT to your system."
echo ""

# Check if network connectivity exists
echo -e "${BLUE}Checking network connectivity...${NC}"
if ping -c 1 google.com &> /dev/null; then
    echo -e "✅ Internet connection detected"
else
    echo -e "${RED}⚠️ Warning: Internet connectivity issues detected${NC}"
    echo -e "The setup will continue, but you may experience problems downloading dependencies."
    echo ""
fi

# Create virtual environment
echo -e "\n${BLUE}Creating Python virtual environment...${NC}"
if [ -d "venv" ]; then
    echo -e "✅ Virtual environment already exists"
else
    python -m venv venv
    echo -e "✅ Created new virtual environment"
fi

source venv/bin/activate
echo -e "✅ Activated virtual environment"

# Install dependencies
echo -e "\n${BLUE}Installing dependencies...${NC}"
pip install --upgrade pip > /dev/null
pip install -r requirements.txt > /dev/null
echo -e "✅ All dependencies installed successfully"

# Default security choices if running in non-interactive mode
SECURITY_LEVEL="medium"
AUTO_KEY=true
CUSTOM_KEY=""
ALLOWED_DIRS="$PWD"

# Determine if this is running interactively
if [ -t 0 ]; then
    INTERACTIVE=true
else
    INTERACTIVE=false
    echo -e "\n${YELLOW}Running in non-interactive mode. Using default settings:${NC}"
    echo -e "• Security Level: Medium"
    echo -e "• API Key: Auto-generated"
    echo -e "• Allowed Paths: Current directory ($PWD)"
fi

# Configure security if interactive
if [ "$INTERACTIVE" = true ]; then
    echo -e "\n${YELLOW}${BOLD}SECURITY CONFIGURATION${NC}"
    echo -e "----------------------"
    echo -e "Choose security level:"
    echo -e "1) High   - Only whitelisted commands and paths allowed (recommended for production)"
    echo -e "2) Medium - Dangerous commands blocked, path restrictions (default)"
    echo -e "3) Low    - Minimal restrictions (development only)"
    
    read -p "Enter choice [2]: " SECURITY_CHOICE
    
    case $SECURITY_CHOICE in
        1) SECURITY_LEVEL="high";;
        3) SECURITY_LEVEL="low";;
        *) SECURITY_LEVEL="medium";;
    esac
    
    # Configure allowed paths
    echo -e "\n${YELLOW}${BOLD}ALLOWED PATHS CONFIGURATION${NC}"
    echo -e "----------------------"
    echo -e "Enter directories that ChatGPT should be allowed to access (comma-separated)."
    echo -e "Example: /home/user/documents,/home/user/downloads"
    echo -e "Leave blank for default (current directory)."
    
    read -p "Allowed directories: " ALLOWED_DIRS
    
    if [ -z "$ALLOWED_DIRS" ]; then
        ALLOWED_DIRS="$PWD"
    fi
    
    # Configure API key if running interactively
    echo -e "\n${YELLOW}${BOLD}API KEY CONFIGURATION${NC}"
    echo -e "----------------------"
    echo -e "Your API key is used to authenticate requests to your server."
    echo -e "1) Generate a random secure API key (recommended)"
    echo -e "2) Enter a custom API key"
    
    read -p "Enter choice [1]: " KEY_CHOICE
    
    if [ "$KEY_CHOICE" = "2" ]; then
        AUTO_KEY=false
        read -p "Enter your custom API key: " CUSTOM_KEY
        if [ -z "$CUSTOM_KEY" ]; then
            echo -e "${RED}No key entered. Generating random key instead.${NC}"
            AUTO_KEY=true
        fi
    fi
fi

# Generate or set API key
if [ "$AUTO_KEY" = true ]; then
    NEW_KEY=$(python -c "import secrets; print(secrets.token_hex(16))")
else
    NEW_KEY=$CUSTOM_KEY
fi

# Update .env file
echo -e "\n${BLUE}Updating configuration...${NC}"
if [ -f .env ]; then
    # Update existing .env file
    sed -i "s/^API_KEY=.*$/API_KEY=$NEW_KEY/" .env
    sed -i "s/^SECURITY_LEVEL=.*$/SECURITY_LEVEL=$SECURITY_LEVEL/" .env
    
    # Update or add allowed paths
    if grep -q "^ALLOWED_PATHS=" .env; then
        sed -i "s|^ALLOWED_PATHS=.*$|ALLOWED_PATHS=$ALLOWED_DIRS|" .env
    else
        echo "ALLOWED_PATHS=$ALLOWED_DIRS" >> .env
    fi
else
    # Create new .env file
    echo "API_KEY=$NEW_KEY" > .env
    echo "SECURITY_LEVEL=$SECURITY_LEVEL" >> .env
    echo "ALLOWED_PATHS=$ALLOWED_DIRS" >> .env
fi

echo -e "✅ Configuration updated:"
echo -e "• Security level: ${BOLD}$SECURITY_LEVEL${NC}"
echo -e "• API Key: ${BOLD}$NEW_KEY${NC}"
echo -e "• Allowed paths: ${BOLD}$ALLOWED_DIRS${NC}"

# Make helper scripts executable
chmod +x gpt_config.py 2>/dev/null || true
chmod +x example_client.py 2>/dev/null || true

# Find available port
PORT=8000
while netstat -tuln | grep -q ":$PORT "; do
    PORT=$((PORT+1))
done

# Detect IP for local network access
IP_ADDR=$(hostname -I | awk '{print $1}')
if [ -z "$IP_ADDR" ]; then
    IP_ADDR="localhost"
fi

# Check for ngrok
NGROK_AVAILABLE=false
if command -v ngrok &> /dev/null; then
    NGROK_AVAILABLE=true
fi

# Print next steps
echo -e "\n${GREEN}${BOLD}✅ SETUP COMPLETE!${NC}"
echo -e "========================================================================"
echo -e "${BOLD}Next Steps:${NC}"
echo -e ""
echo -e "${BOLD}1. Start your server:${NC}"
echo -e "   ${YELLOW}source venv/bin/activate${NC}"
echo -e "   ${YELLOW}uvicorn main:app --reload --port $PORT${NC}"
echo -e ""
echo -e "${BOLD}2. Get your ChatGPT configuration:${NC}"
echo -e "   ${YELLOW}./gpt_config.py${NC}"
echo -e ""
echo -e "${BOLD}3. Access Options:${NC}"
echo -e "   • Local Access:      ${YELLOW}http://localhost:$PORT${NC}"
echo -e "   • Network Access:    ${YELLOW}http://$IP_ADDR:$PORT${NC}"

if [ "$NGROK_AVAILABLE" = true ]; then
    echo -e "   • Internet Access:   ${YELLOW}ngrok http $PORT${NC} (Run this in a separate terminal)"
else
    echo -e "   • Internet Access:   ${YELLOW}Install ngrok for public access${NC} (npm install -g ngrok)"
fi

echo -e ""
echo -e "${BOLD}Important:${NC} Your API key and security settings are stored in the .env file."
echo -e "Keep this file secure and don't commit it to public repositories."
echo -e "========================================================================"

# Offer to start the server immediately if interactive
if [ "$INTERACTIVE" = true ]; then
    read -p "Would you like to start the server now? (y/n) [y]: " START_SERVER
    case $START_SERVER in
        [Nn]* ) 
            echo -e "\n${YELLOW}Server not started. You can start it later with:${NC}"
            echo -e "${YELLOW}source venv/bin/activate${NC}"
            echo -e "${YELLOW}uvicorn main:app --reload --port $PORT${NC}"
            ;;
        * ) 
            echo -e "\n${GREEN}Starting server on port $PORT...${NC}"
            echo -e "Press Ctrl+C to stop the server when you're done."
            echo -e "You can access the configuration tool in another terminal with: ${YELLOW}./gpt_config.py${NC}"
            sleep 2
            uvicorn main:app --reload --port $PORT
            ;;
    esac
fi
