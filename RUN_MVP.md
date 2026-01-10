# 🚀 MedicaScade AI - Quick Start Guide

## Prerequisites Check
```bash
# 1. Check Ollama is running
ollama list
# Should show: llama3.2:3b

# 2. Check you have HuggingFace token (optional but recommended)
cat backend/.env | grep HF_API_TOKEN
```

---

## 🎯 Start the MVP (3 Simple Steps)

### Step 1: Start Backend
```bash
cd ~/medicascade-ai/backend
source venv/bin/activate
uvicorn main:app --reload
```

**Expected Output:**
```
INFO:     Uvicorn running on http://127.0.0.1:8000
INFO:     Application startup complete.
```

**Keep this terminal open!**

---

### Step 2: Start Frontend (New Terminal)
```bash
cd ~/medicascade-ai/frontend
npm run dev
```

**Expected Output:**
```
VITE ready in XXX ms
Local: http://localhost:5173/
```

**Keep this terminal open!**

---

### Step 3: Access Application
Open your browser and go to:
**http://localhost:5173**

---

## 📤 Upload Patient PDF

1. Click "Upload PDF" button
2. Select a patient medical PDF file
3. Wait for AI analysis (20-60 seconds)
4. View results:
   - **Layer 0**: PDF extraction
   - **Layer 1**: AI specialist diagnoses (now using real AI!)
   - **Layer 2**: Cross-validated reasoning
   - **Layer 3**: Final medical report

---

## 🔍 Testing with Sample Data

If you don't have a PDF, you can manually enter:

**Patient Info:**
- Name: John Doe
- Age: 58
- Gender: Male

**Symptoms:**
```
Severe headache for 3 months
Blurred vision in left eye
Nausea and vomiting
Sensitivity to light
```

**Lab Results (paste as text):**
```
Hemoglobin: 9.5 g/dL
WBC: 15000 cells/μL
Glucose: 180 mg/dL
Intracranial Pressure: 22 mmHg
```

---

## 🛑 Stop the MVP

**Terminal 1 (Backend):**
Press `Ctrl + C`

**Terminal 2 (Frontend):**
Press `Ctrl + C`

---

## ⚡ Quick Restart Script

Create this file for easy restart:
```bash
# Save as: ~/medicascade-ai/start_mvp.sh
#!/bin/bash

echo "🚀 Starting MedicaScade AI MVP..."

# Start backend in background
cd ~/medicascade-ai/backend
source venv/bin/activate
uvicorn main:app --reload &
BACKEND_PID=$!

# Wait for backend
sleep 3

# Start frontend
cd ~/medicascade-ai/frontend
npm run dev &
FRONTEND_PID=$!

echo "✅ Backend running (PID: $BACKEND_PID)"
echo "✅ Frontend running (PID: $FRONTEND_PID)"
echo ""
echo "🌐 Open: http://localhost:5173"
echo ""
echo "Press Ctrl+C to stop both services"

# Wait for user interrupt
wait
```

Make it executable:
```bash
chmod +x ~/medicascade-ai/start_mvp.sh
```

Then run:
```bash
~/medicascade-ai/start_mvp.sh
```

---

## 🐛 Troubleshooting

### Backend won't start
```bash
# Check if venv exists
ls ~/medicascade-ai/backend/venv/

# Recreate if needed
cd ~/medicascade-ai/backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### "HuggingFace API error"
- AI models might be loading (wait 30 seconds)
- Add your HF token to `backend/.env`:
  ```
  HF_API_TOKEN=hf_your_token_here
  ```

### Frontend build errors
```bash
cd ~/medicascade-ai/frontend
rm -rf node_modules
npm install
```

---

## 📊 What You'll See

**With the new AI-powered specialists:**
- Each patient gets **unique diagnoses** based on AI analysis
- Different symptoms = different results (no more repetitive outputs!)
- Confidence scores reflect actual AI assessment
- Reasoning explains the AI's diagnostic logic

**The system now uses:**
- ✅ HuggingFace Gemma-2 AI for symptoms
- ✅ AI-powered lab interpretation
- ✅ AI entity extraction from clinical notes
- ✅ Ollama LLM for Layer 2 cross-validation
