"""
FastAPI Main Application
Universal AI Disease Prediction Engine Backend
"""
from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from layers.layer0_pdf_processor import layer0_processor
from layers.layer1_specialists import layer1_specialists
from layers.layer2_validator import layer2_validator
from layers.layer3_annotator import layer3_annotator
from schemas import DiagnosisResponse
from config import settings
import uvicorn
import os
import time
import shutil
from datetime import datetime

app = FastAPI(
    title="Universal AI Disease Prediction Engine",
    description="Multi-layer AI system for medical diagnosis with explainability",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # For development
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve output files
if os.path.exists(settings.OUTPUT_DIR):
    app.mount("/outputs", StaticFiles(directory=settings.OUTPUT_DIR), name="outputs")


@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "message": "Universal AI Disease Prediction Engine API",
        "version": "1.0.0",
        "status": "running"
    }


@app.get("/health")
async def health_check():
    """Check if all systems are operational"""
    try:
        # Check Ollama connectivity
        from utils.ollama_client import ollama_client
        test_response = ollama_client.generate("Test", temperature=0.1)
        ollama_status = "connected" if test_response else "disconnected"
    except:
        ollama_status = "error"
    
    return {
        "status": "healthy",
        "ollama": ollama_status,
        "timestamp": datetime.now().isoformat()
    }


@app.post("/api/diagnose")
async def diagnose(file: UploadFile = File(...)):
    """
    Main diagnosis endpoint - processes PDF through all 4 layers
    
    Args:
        file: Uploaded PDF file containing patient data
        
    Returns:
        Complete diagnosis with annotations
    """
    print(f"\n{'='*60}")
    print(f"[API] New diagnosis request: {file.filename}")
    print(f"{'='*60}\n")
    
    start_time = time.time()
    
    # Validate file
    if not file.filename.endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Only PDF files are accepted")
    
    # Save uploaded file
    upload_path = os.path.join(settings.UPLOAD_DIR, f"patient_{int(time.time())}.pdf")
    
    try:
        with open(upload_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        print(f"[API] File saved: {upload_path}")
        
        # LAYER 0: PDF Processing
        print(f"\n{'-'*60}")
        patient_data = layer0_processor.process(upload_path)
        print(f"{'-'*60}\n")
        
        # LAYER 1: Multiple AI Specialists
        print(f"\n{'-'*60}")
        layer1_output = layer1_specialists.process(patient_data)
        print(f"{'-'*60}\n")
        
        # LAYER 2: Major AI Validator
        print(f"\n{'-'*60}")
        layer2_diagnosis = layer2_validator.process(layer1_output)
        print(f"{'-'*60}\n")
        
        # LAYER 3: Explanation Generator
        print(f"\n{'-'*60}")
        layer3_report = layer3_annotator.process(layer2_diagnosis, patient_data)
        print(f"{'-'*60}\n")
        
        total_elapsed = time.time() - start_time
        
        print(f"\n{'='*60}")
        print(f"[API] DIAGNOSIS COMPLETE")
        print(f"[API] Total processing time: {total_elapsed:.2f}s")
        print(f"[API] Primary diagnosis: {layer2_diagnosis.primary_diagnosis}")
        print(f"[API] Confidence: {layer2_diagnosis.confidence:.0%}")
        print(f"{'='*60}\n")
        
        # Build response
        response = DiagnosisResponse(
            success=True,
            patient_data=patient_data,
            layer1_output=layer1_output,
            layer2_diagnosis=layer2_diagnosis,
            layer3_report=layer3_report,
            total_processing_time=total_elapsed
        )
        
        return response
    
    except Exception as e:
        print(f"\n[API ERROR] {str(e)}\n")
        raise HTTPException(status_code=500, detail=f"Processing error: {str(e)}")
    
    finally:
        # Cleanup uploaded file
        if os.path.exists(upload_path):
            try:
                os.remove(upload_path)
            except:
                pass


@app.get("/api/report/{filename}")
async def get_report(filename: str):
    """Download generated report PDF"""
    file_path = os.path.join(settings.OUTPUT_DIR, filename)
    
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Report not found")
    
    return FileResponse(
        file_path,
        media_type="application/pdf",
        filename=filename
    )


@app.get("/api/image/{filename}")
async def get_image(filename: str):
    """Get annotated image"""
    file_path = os.path.join(settings.OUTPUT_DIR, filename)
    
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Image not found")
    
    return FileResponse(file_path, media_type="image/png")


if __name__ == "__main__":
    print("""
    ╔══════════════════════════════════════════════════════════╗
    ║  Universal AI Disease Prediction Engine                  ║
    ║  Multi-Layer AI Medical Diagnostic System                ║
    ╚══════════════════════════════════════════════════════════╝
    
    Starting server on http://localhost:8000
    API Documentation: http://localhost:8000/docs
    """)
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
