#!/bin/bash

# Universal AI Disease Prediction Engine - Setup Script
# This script automates the setup process

echo "╔══════════════════════════════════════════════════════════╗"
echo "║  Universal AI Disease Prediction Engine - Setup          ║"
echo "╚══════════════════════════════════════════════════════════╝"
echo ""

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Step 1: Check System Dependencies
echo -e "${YELLOW}[1/7] Checking system dependencies...${NC}"
if ! command -v tesseract &> /dev/null; then
    echo -e "${RED}Tesseract OCR not found. Installing...${NC}"
    sudo apt-get update
    sudo apt-get install -y tesseract-ocr poppler-utils
else
    echo -e "${GREEN}✓ Tesseract OCR found${NC}"
fi

if ! command -v ollama &> /dev/null; then
    echo -e "${RED}Ollama not found. Please install from https://ollama.ai${NC}"
    exit 1
else
    echo -e "${GREEN}✓ Ollama found${NC}"
fi

# Step 2: Setup Python Backend
echo -e "\n${YELLOW}[2/7] Setting up Python backend...${NC}"
cd /home/rohith/medicascade-ai/backend
pip install -r requirements.txt
echo -e "${GREEN}✓ Python dependencies installed${NC}"

# Step 3: Check Ollama Model
echo -e "\n${YELLOW}[3/7] Checking Ollama model...${NC}"
if ! ollama list | grep -q "llama3.2"; then
    echo "Pulling Llama 3.2 model..."
    ollama pull llama3.2
else
    echo -e "${GREEN}✓ Llama 3.2 model available${NC}"
fi

# Step 4: Setup Environment
echo -e "\n${YELLOW}[4/7] Setting up environment...${NC}"
cd /home/rohith/medicascade-ai
if [ ! -f .env ]; then
    cp .env.example .env
    echo -e "${YELLOW}⚠ Please add your HuggingFace token to .env${NC}"
    echo "   Get it from: https://huggingface.co/settings/tokens"
else
    echo -e "${GREEN}✓ .env file exists${NC}"
fi

# Step 5: Setup Frontend
echo -e "\n${YELLOW}[5/7] Setting up frontend...${NC}"
cd /home/rohith/medicascade-ai/frontend
npm install
echo -e "${GREEN}✓ Frontend dependencies installed${NC}"

# Step 6: Create Sample PDF
echo -e "\n${YELLOW}[6/7] Creating sample patient PDF...${NC}"
cd /home/rohith/medicascade-ai
python demo/create_sample_pdf.py
echo -e "${GREEN}✓ Sample PDF created${NC}"

# Step 7: Create directories
echo -e "\n${YELLOW}[7/7] Creating required directories...${NC}"
mkdir -p uploads outputs
echo -e "${GREEN}✓ Directories created${NC}"

# Final Instructions
echo ""
echo "╔══════════════════════════════════════════════════════════╗"
echo "║  Setup Complete! ✓                                        ║"
echo "╚══════════════════════════════════════════════════════════╝"
echo ""
echo -e "${GREEN}To start the system:${NC}"
echo ""
echo "1. Start Ollama (if not running):"
echo "   ollama serve"
echo ""
echo "2. Start Backend (in one terminal):"
echo "   cd /home/rohith/medicascade-ai/backend"
echo "   python main.py"
echo ""
echo "3. Start Frontend (in another terminal):"
echo "   cd /home/rohith/medicascade-ai/frontend"
echo "   npm run dev"
echo ""
echo "4. Open browser:"
echo "   http://localhost:5173"
echo ""
echo -e "${YELLOW}Sample PDF for testing:${NC}"
echo "   /home/rohith/medicascade-ai/demo/sample_patient.pdf"
echo ""
