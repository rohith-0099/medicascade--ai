# 🔑 HuggingFace API Authentication Required

## The Error:
```
❌ API Error: 401 Client Error: Unauthorized
```

## What This Means:
The HuggingFace AI models need an authentication token to work. Without it, you get "Parse error" because the API refuses the requests.

## Quick Fix (1 Minute):

### Step 1: Get a FREE HuggingFace Token
1. Go to: https://huggingface.co/settings/tokens
2. Click "New token"
3. Name it: "medicascade"
4. Select: "Read" permissions (enough for our use)
5. Click "Generate"
6. **Copy the token** (starts with `hf_...`)

### Step 2: Add Token to .env File

**Option A: Edit file directly**
```bash
nano ~/medicascade-ai/backend/.env
```

Find the line:
```
HF_API_TOKEN=your_huggingface_api_key_here
```

Replace with your actual token:
```
HF_API_TOKEN=hf_YourActualTokenHere
```

Save and exit (Ctrl+X, then Y, then Enter)

**Option B: Use sed command**
```bash
cd ~/medicascade-ai/backend
sed -i 's/HF_API_TOKEN=.*/HF_API_TOKEN=hf_YourActualTokenHere/' .env
```
(Replace `hf_YourActualTokenHere` with your real token)

### Step 3: Restart Backend
The backend will auto-reload and pick up the new token!

## After Adding Token:
✅ All AI specialists will work properly
✅ Real diagnoses instead of "Parse error"  
✅ Different results for different patients
✅ Proper confidence scores

## Test It:
Upload a PDF again and you should see:
```
[symptom_analyzer] AI diagnosis: Migraine (85%)
[risk_analyzer] AI assessment: HIGH risk for Diabetes (72%)
```

Instead of:
```
❌ API Error: 401 Client Error: Unauthorized
Parse error (30%)
```
