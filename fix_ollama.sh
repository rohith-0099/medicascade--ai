#!/bin/bash
# Fix Ollama Installation

echo "🔧 Fixing Ollama Installation"
echo "=============================="
echo ""

# Step 1: Stop broken Ollama
echo "1. Stopping broken Ollama service..."
sudo systemctl stop ollama 2>/dev/null || true
sudo pkill -9 ollama 2>/dev/null || true
sleep 2

# Step 2: Reinstall Ollama
echo ""
echo "2. Reinstalling Ollama..."
curl -fsSL https://ollama.com/install.sh | sh

# Step 3: Start Ollama
echo ""
echo "3. Starting Ollama service..."
sudo systemctl start ollama 2>/dev/null || ollama serve &
sleep 3

# Step 4: Pull model
echo ""
echo "4. Pulling llama3.2 model..."
ollama pull llama3.2

# Step 5: Test
echo ""
echo "5. Testing Ollama..."
ollama run llama3.2 "Say hello" --verbose

echo ""
echo "=============================="
echo "✅ Ollama should now be working!"
echo ""
echo "Test with: ollama run llama3.2 'What is diabetes?'"
echo "=============================="
