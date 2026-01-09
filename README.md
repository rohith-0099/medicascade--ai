# Universal AI Disease Prediction Engine - Setup Instructions

## Prerequisites

### 1. Install System Dependencies
```bash
# Install Tesseract OCR
sudo apt-get update
sudo apt-get install -y tesseract-ocr poppler-utils

# Verify installation
tesseract --version
```

### 2. Install Python Dependencies
```bash
cd /home/rohith/medicascade-ai/backend
pip install -r requirements.txt
```

### 3. Setup Ollama (Already Installed)
```bash
# Verify Ollama is running
ollama serve

# In another terminal, pull Llama model
ollama pull llama3.2
```

### 4. Get HuggingFace API Token
1. Go to https://huggingface.co/settings/tokens
2. Create a new token (read access)
3. Copy the token

### 5. Configure Environment
```bash
cd /home/rohith/medicascade-ai
cp .env.example .env
nano .env  # Add your HuggingFace token
```

## Running the Backend

```bash
cd /home/rohith/medicascade-ai/backend
python main.py
```

The API will be available at:
- Main API: http://localhost:8000
- Documentation: http://localhost:8000/docs
- Health Check: http://localhost:8000/health

## Testing the System

### Using cURL:
```bash
curl -X POST "http://localhost:8000/api/diagnose" \
  -H "accept: application/json" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@/path/to/patient.pdf"
```

### Using Python:
```python
import requests

with open("patient.pdf", "rb") as f:
    response = requests.post(
        "http://localhost:8000/api/diagnose",
        files={"file": f}
    )
    
result = response.json()
print(f"Diagnosis: {result['layer2_diagnosis']['primary_diagnosis']}")
print(f"Confidence: {result['layer2_diagnosis']['confidence']}")
```

## Frontend Setup (Next Steps)

```bash
cd /home/rohith/medicascade-ai/frontend
npm install
npm run dev
```

Frontend will be available at http://localhost:5173

## Troubleshooting

### Ollama not responding
```bash
# Check if Ollama is running
ps aux | grep ollama

# Restart Ollama
pkill ollama
ollama serve
```

### HuggingFace rate limiting
- Free tier has rate limits
- Models may take 10-20s to "wake up" from cold state
- System has automatic retry logic

### PDF extraction issues
- Make sure poppler-utils is installed for pdf2image
- Tesseract must be installed for OCR
- Test with: `tesseract --version`

## Project Structure
```
medicascade-ai/
├── backend/
│   ├── layers/              # 4-layer architecture
│   ├── specialists/         # Layer 1 specialist models
│   ├── utils/               # Helper modules
│   ├── main.py             # FastAPI app
│   ├── config.py           # Configuration
│   └── schemas.py          # Data models
├── frontend/               # React app (to be created)
├── demo/                   # Test files
├── uploads/                # Temporary uploads
└── outputs/                # Generated reports
```
