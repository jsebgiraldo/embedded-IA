#!/bin/bash
#
# Quick setup script for local LLM with Ollama
# 
# Usage:
#   ./scripts/setup_local_llm.sh              # Install Ollama + recommended model
#   ./scripts/setup_local_llm.sh best         # Install best model (DeepSeek 16B)
#   ./scripts/setup_local_llm.sh lightweight  # Install lightweight model (CodeLlama 7B)
#

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Detect OS
OS=$(uname -s)

echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}  ESP32 Multi-Agent System - Local LLM Setup${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}\n"

# Model selection
TIER="${1:-balanced}"

case $TIER in
    best)
        MODEL="deepseek-coder-v2:16b"
        RAM_REQUIRED="20GB"
        ;;
    balanced)
        MODEL="qwen2.5-coder:14b"
        RAM_REQUIRED="18GB"
        ;;
    fast)
        MODEL="codellama:13b"
        RAM_REQUIRED="16GB"
        ;;
    lightweight)
        MODEL="codellama:7b"
        RAM_REQUIRED="8GB"
        ;;
    *)
        echo -e "${RED}Invalid tier: $TIER${NC}"
        echo "Valid options: best, balanced, fast, lightweight"
        exit 1
        ;;
esac

echo -e "${GREEN}Selected tier: $TIER${NC}"
echo -e "Model: ${YELLOW}$MODEL${NC}"
echo -e "RAM required: ${YELLOW}$RAM_REQUIRED${NC}\n"

# Check system RAM
if [[ "$OS" == "Darwin" ]]; then
    TOTAL_RAM=$(sysctl hw.memsize | awk '{print int($2/1024/1024/1024)}')
    echo -e "System RAM: ${GREEN}${TOTAL_RAM}GB${NC}"
elif [[ "$OS" == "Linux" ]]; then
    TOTAL_RAM=$(free -g | awk '/^Mem:/{print $2}')
    echo -e "System RAM: ${GREEN}${TOTAL_RAM}GB${NC}"
fi

echo ""

# Step 1: Check if Ollama is installed
echo -e "${BLUE}[1/4]${NC} Checking Ollama installation..."

if command -v ollama &> /dev/null; then
    echo -e "${GREEN}✅ Ollama is already installed${NC}"
    OLLAMA_VERSION=$(ollama --version | head -n1)
    echo -e "   Version: $OLLAMA_VERSION"
else
    echo -e "${YELLOW}⚠️  Ollama not found. Installing...${NC}"
    
    if [[ "$OS" == "Darwin" ]]; then
        # macOS
        if command -v brew &> /dev/null; then
            echo "   Using Homebrew..."
            brew install ollama
        else
            echo -e "${RED}❌ Homebrew not found. Install from: https://brew.sh/${NC}"
            echo "   Or download Ollama from: https://ollama.com/download"
            exit 1
        fi
    elif [[ "$OS" == "Linux" ]]; then
        # Linux
        echo "   Downloading installer..."
        curl -fsSL https://ollama.com/install.sh | sh
    else
        echo -e "${RED}❌ Unsupported OS: $OS${NC}"
        echo "   Please install Ollama manually from: https://ollama.com/download"
        exit 1
    fi
    
    echo -e "${GREEN}✅ Ollama installed successfully${NC}"
fi

echo ""

# Step 2: Start Ollama server
echo -e "${BLUE}[2/4]${NC} Starting Ollama server..."

if pgrep -x "ollama" > /dev/null; then
    echo -e "${GREEN}✅ Ollama server is already running${NC}"
else
    echo "   Starting server in background..."
    ollama serve > /dev/null 2>&1 &
    sleep 2
    
    if pgrep -x "ollama" > /dev/null; then
        echo -e "${GREEN}✅ Ollama server started${NC}"
    else
        echo -e "${RED}❌ Failed to start Ollama server${NC}"
        echo "   Try manually: ollama serve"
        exit 1
    fi
fi

echo ""

# Step 3: Download model
echo -e "${BLUE}[3/4]${NC} Downloading model: $MODEL"
echo -e "${YELLOW}   This may take a while depending on your internet speed...${NC}"

# Check if model already exists
if ollama list | grep -q "$MODEL"; then
    echo -e "${GREEN}✅ Model $MODEL is already downloaded${NC}"
else
    echo "   Pulling model..."
    if ollama pull "$MODEL"; then
        echo -e "${GREEN}✅ Model downloaded successfully${NC}"
    else
        echo -e "${RED}❌ Failed to download model${NC}"
        exit 1
    fi
fi

echo ""

# Step 4: Test model
echo -e "${BLUE}[4/4]${NC} Testing model..."

TEST_PROMPT="What is the purpose of the ESP32 microcontroller? Reply in one short sentence."

echo "   Sending test prompt..."
RESPONSE=$(ollama run "$MODEL" "$TEST_PROMPT" 2>&1)

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Model is working!${NC}"
    echo -e "\n   ${YELLOW}Test response:${NC}"
    echo "   $RESPONSE"
else
    echo -e "${RED}❌ Model test failed${NC}"
    exit 1
fi

echo ""
echo -e "${GREEN}═══════════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}  ✨ Local LLM Setup Complete!${NC}"
echo -e "${GREEN}═══════════════════════════════════════════════════════════${NC}"
echo ""
echo -e "${BLUE}Next steps:${NC}"
echo ""
echo "1. Update your .env file:"
echo -e "   ${YELLOW}LLM_PROVIDER=ollama${NC}"
echo -e "   ${YELLOW}LLM_MODEL=$MODEL${NC}"
echo ""
echo "2. Test the integration:"
echo -e "   ${YELLOW}python3 agent/llm_provider.py${NC}"
echo ""
echo "3. Try the Developer Agent:"
echo -e "   ${YELLOW}python3 examples/test_developer_agent.py${NC}"
echo ""
echo -e "${BLUE}Useful commands:${NC}"
echo ""
echo "  List models:      ollama list"
echo "  Interactive chat: ollama run $MODEL"
echo "  Stop server:      pkill ollama"
echo "  Server logs:      tail -f ~/.ollama/logs/server.log"
echo ""
echo -e "${BLUE}Model recommendations:${NC}"
echo ""
echo "  • lightweight (7B):  Fast, 8GB RAM needed"
echo "  • fast (13B):        Balanced, 16GB RAM needed"
echo "  • balanced (14B):    Recommended, 18GB RAM needed ⭐"
echo "  • best (16B):        Highest quality, 20GB RAM needed"
echo ""
echo "To switch models, run:"
echo -e "  ${YELLOW}./scripts/setup_local_llm.sh <tier>${NC}"
echo ""
echo -e "${GREEN}Happy coding with AI! 🚀${NC}"
echo ""
