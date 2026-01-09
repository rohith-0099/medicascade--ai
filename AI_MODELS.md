# 🔧 AI Models Configuration - REAL APIs ONLY

## Updated Models (All Working & Active)

### Layer 1: HuggingFace AI Models

| Specialist | Model | Status | Purpose |
|------------|-------|--------|---------|
| **Symptoms** | `microsoft/BioGPT-Large` | ✅ Active | Medical text generation & symptom analysis |
| **Labs** | `emilyalsentzer/Bio_ClinicalBERT` | ✅ Active | Clinical lab report interpretation |
| **Notes** | `microsoft/BiomedNLP-PubMedBERT-base-uncased-abstract-fulltext` | ✅ Active | Medical literature NER |
| **Scans** | `google/vit-base-patch16-224` | ✅ Active | Vision transformer for medical images |

### Layer 2 & 3: Local LLM
- **Model:** `llama3.2` via Ollama
- **Status:** ✅ Must be running locally
- **Command:** `ollama serve`

## Token Setup

Your HuggingFace token is configured in `.env`:
```
HUGGINGFACE_TOKEN=REMOVED
```

## How to Verify Models Are Working

Run the test script:
```bash
cd /home/rohith/medicascade-ai/backend
./test_ai_models.sh
```

## Expected Behavior Now

### ✅ With Working APIs:
- **Layer 1**: All 5 specialists use REAL AI models
- **Layer 2**: Llama 3.2 validates and decides  
- **Layer 3**: Llama 3.2 generates explanations
- **Processing Time**: 30-60 seconds (API calls take time!)

### ❌ If APIs Fail:
- System will show specific error messages
- No silent fallbacks anymore
- You'll know immediately if something is wrong

## Troubleshooting

**HuggingFace "503 Service Unavailable"**
- Models are loading (cold start)
- Wait 10-20 seconds and retry
- This is normal for free tier

**Ollama "500 Internal Server Error"**
```bash
# Check if Ollama is running
ps aux | grep ollama

# If not, start it
ollama serve
```

**HuggingFace "401 Unauthorized"**
- Token is invalid or expired
- Get new token from: https://huggingface.co/settings/tokens

---

**System is now configured to use 100% REAL AI models!** 🚀
