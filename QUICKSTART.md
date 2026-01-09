# 🚀 Quick Start Guide

## Prerequisites Check
- [ ] Ollama installed and running
- [ ] Node.js installed (v18+)
- [ ] Python 3.8+ installed
- [ ] HuggingFace account (free)

## Installation Steps

### 1. Install Backend Dependencies
```bash
cd /home/rohith/medicascade-ai/backend
pip install -r requirements.txt
```

### 2. Setup Ollama Model
```bash
ollama pull llama3.2
```

### 3. Get HuggingFace Token
1. Go to https://huggingface.co/settings/tokens
2. Click "New token"
3. Give it a name (e.g., "medicascade")
4. Select "Read" access
5. Copy the token

### 4. Configure Environment
```bash
cd /home/rohith/medicascade-ai
cp .env.example .env
echo "HUGGINGFACE_TOKEN=YOUR_TOKEN_HERE" >> .env
```

### 5. Install Frontend Dependencies
```bash
cd /home/rohith/medicascade-ai/frontend
npm install
```

## Running the Application

### Terminal 1: Start Backend
```bash
cd /home/rohith/medicascade-ai/backend
python main.py
```
💡 Backend will run on http://localhost:8000

### Terminal 2: Start Frontend
```bash
cd /home/rohith/medicascade-ai/frontend
npm run dev
```
💡 Frontend will run on http://localhost:5173

## Testing with Sample Data

1. Open http://localhost:5173 in your browser
2. You'll see the upload interface
3. Sample patient PDF for testing will be created when you run the backend
4. Upload any patient PDF containing:
   - Patient demographics
   - Symptoms
   - Lab results
   - Clinical notes

## Expected Flow

1. **Upload** → PDF is sent to backend
2. **Layer 0** → ~5s - Extracts text, images, tables
3. **Layer 1** → ~15s - 5 AI specialists analyze in parallel
4. **Layer 2** → ~10s - Major AI validates and decides
5. **Layer 3** → ~10s - Generates annotated report
6. **Results** → View diagnosis with evidence!

## Troubleshooting

**"Ollama connection error"**
```bash
ollama serve  # Start Ollama server
```

**"Module not found" errors**
```bash
# Backend
cd backend && pip install -r requirements.txt

# Frontend
cd frontend && npm install
```

**"HuggingFace API rate limit"**
- Wait 10-20 seconds for model to wake up
- System has automatic retry logic
- Fallback to rule-based analysis if APIs unavailable

**"Cannot find sample PDF"**
```bash
cd /home/rohith/medicascade-ai
# Install reportlab first if needed
pip install reportlab
python demo/create_sample_pdf.py
```

## What to Expect

✅ **Working Features:**
- PDF upload with drag & drop
- Real-time progress tracking
- 5 AI specialist opinions
- Cross-validated diagnosis
- Evidence highlighting
- Confidence scores
- Downloadable PDF reports

⚠️ **Known Limitations:**
- HuggingFace free tier has rate limits (may take 10-20s)
- First API call may be slow (model loading)
- Vision models may not work for all image types
- This is a demo - not for actual medical use!

## Next Steps

After verification:
1. Test with your own patient PDF samples
2. Customize AI prompts in specialist modules
3. Add more specialist models
4. Enhance UI with additional visualizations
5. Deploy to production (Docker recommended)

---

**Need Help?** Check the full README.md and walkthrough.md for detailed documentation.
