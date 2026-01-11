#!/bin/bash
# Start backend with AI verification

# Determine project root and backend dir
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" \u0026\u0026 pwd )"
cd "$SCRIPT_DIR"

echo "🚀 Starting Universal AI Disease Prediction Engine"
echo "=================================================="
echo ""

# Check Ollama
echo "Checking Ollama..."
if ! curl -s http://localhost:11434/api/tags > /dev/null 2>&1; then
    echo "⚠️  Ollama not running!"
    echo "   Please run in another terminal: ollama serve"
    echo ""
    read -p "Press Enter when Ollama is running..."
fi

# Check HuggingFace token
echo "Checking HuggingFace token..."
if grep -q "HUGGINGFACE_TOKEN=your_" ../.env || grep -q "HUGGINGFACE_TOKEN=hf_" ../.env; then
    echo "✅ Token configured"
else
    echo "⚠️  Token not found or default placeholder in .env"
fi

echo ""
echo "Starting backend with REAL AI models..."
echo "========================================"
echo ""

# Activate venv and run
source venv/bin/activate
python main.py
