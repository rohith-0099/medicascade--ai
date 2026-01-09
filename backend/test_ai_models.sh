#!/bin/bash
# Test script to verify all AI models are working

echo "🧪 Testing AI Model Connections..."
echo "=================================="
echo ""

# Test 1: Ollama
echo "1️⃣ Testing Ollama (Layer 2 & 3)..."
if curl -s http://localhost:11434/api/generate -d '{"model":"llama3.2","prompt":"test","stream":false}' > /dev/null 2>&1; then
    echo "   ✅ Ollama is working!"
else
    echo "   ❌ Ollama not responding. Run: ollama serve"
fi
echo ""

# Test 2: HuggingFace Token
echo "2️⃣ Testing HuggingFace Token..."
if [ -f "../.env" ]; then
    TOKEN=$(grep HUGGINGFACE_TOKEN ../.env | cut -d '=' -f2)
    if [ ! -z "$TOKEN" ]; then
        echo "   ✅ Token found: ${TOKEN:0:10}..."
    else
        echo "   ❌ Token not set in .env"
    fi
else
    echo "   ❌ .env file not found"
fi
echo ""

# Test 3: Python Environment
echo "3️⃣ Testing Python Dependencies..."
source venv/bin/activate
if python -c "import fastapi, ollama" 2>/dev/null; then
    echo "   ✅ Core dependencies installed"
else
    echo "   ⚠️  Some dependencies missing (this is OK if fastapi works)"
fi
echo ""

echo "=================================="
echo "Ready to test! Run:"
echo "  ./start.sh"
echo "=================================="
