# 🎯 HOW TO RUN THE PROJECT

## ✅ Issues Fixed
- ✓ PostCSS config converted to ES modules
- ✓ Python dependencies installed in virtual environment
- ✓ Ollama Llama 3.2 model downloaded

## 🚀 Running the Application

### Backend (Terminal 1)
```bash
cd /home/rohith/medicascade-ai/backend
./start.sh
```

**OR manually:**
```bash
cd /home/rohith/medicascade-ai/backend
source venv/bin/activate
python main.py
```

### Frontend (Terminal 2)
```bash
cd /home/rohith/medicascade-ai/frontend
npm run dev
```

## 📝 Important Notes

1. **HuggingFace Token**: Add your token to `.env` file:
   ```bash
   cd /home/rohith/medicascade-ai
   echo "HUGGINGFACE_TOKEN=hf_your_token_here" > .env
   ```
   Get token from: https://huggingface.co/settings/tokens

2. **First Run**: HuggingFace models may take 10-20 seconds to "wake up"

3. **Open Browser**: http://localhost:5173

## 🧪 Testing
- Upload the sample PDF (will be created on first backend run)
- Or create your own patient PDF with symptoms, labs, etc.

## ❓ Troubleshooting

**Backend won't start:**
```bash
cd /home/rohith/medicascade-ai/backend
source venv/bin/activate
pip install -r requirements.txt
```

**Frontend PostCSS error (FIXED):**
- We converted `postcss.config.js` to ES module syntax ✓

**Ollama not responding:**
```bash
ollama serve  # In a separate terminal
```
