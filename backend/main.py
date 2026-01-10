
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

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # For development
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

if os.path.exists(settings.OUTPUT_DIR):
    app.mount("/outputs", StaticFiles(directory=settings.OUTPUT_DIR), name="outputs")

@app.get("/")
async def root():
    
    return {
        "message": "Universal AI Disease Prediction Engine API",
        "version": "1.0.0",
        "status": "running"
    }

@app.get("/health")
async def health_check():
    
    try:
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
async def diagnose(file: UploadFile = File(...), scan: UploadFile = File(None)):
    
    print(f"\n{'='*60}")
    print(f"[API] New diagnosis request: {file.filename}")
    if scan:
        print(f"[API] Dedicated scan provided: {scan.filename}")
    print(f"{'='*60}\n")
    
    start_time = time.time()
    
    if not file.filename.endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Only PDF files are accepted")
    
    upload_path = os.path.join(settings.UPLOAD_DIR, f"patient_{int(time.time())}.pdf")
    scan_path = None
    
    try:
        with open(upload_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        print(f"[API] PDF file saved: {upload_path}")
        
        if scan:
            from pathlib import Path
            ext = Path(scan.filename).suffix
            scan_path = os.path.join(settings.UPLOAD_DIR, f"scan_{int(time.time())}{ext}")
            with open(scan_path, "wb") as buffer:
                shutil.copyfileobj(scan.file, buffer)
            print(f"[API] Scan file saved: {scan_path}")
        
        print(f"\n{'-'*60}")
        patient_data = layer0_processor.process(upload_path, scan_path)
        print(f"{'-'*60}\n")
        
        print(f"\n{'-'*60}")
        layer1_output = layer1_specialists.process(patient_data)
        print(f"{'-'*60}\n")
        
        print(f"\n{'-'*60}")
        layer2_diagnosis = layer2_validator.process(layer1_output)
        print(f"{'-'*60}\n")
        
        print(f"\n{'-'*60}")
        layer3_report = layer3_annotator.process(layer2_diagnosis, patient_data, layer1_output)
        print(f"{'-'*60}\n")
        
        total_elapsed = time.time() - start_time
        
        print(f"\n{'='*60}")
        print(f"[API] DIAGNOSIS COMPLETE")
        print(f"[API] Total processing time: {total_elapsed:.2f}s")
        print(f"[API] Primary diagnosis: {layer2_diagnosis.primary_diagnosis}")
        print(f"[API] Confidence: {layer2_diagnosis.confidence:.0%}")
        print(f"{'='*60}\n")
        
        response_dict = {
            "success": True,
            "primary_diagnosis": layer2_diagnosis.primary_diagnosis,
            "confidence": layer2_diagnosis.confidence,
            "reasoning": layer2_diagnosis.reasoning,
            "secondary_diagnoses": layer2_diagnosis.secondary_diagnoses,
            "cross_validation_score": layer2_diagnosis.cross_validation_score,
            "anomaly_detected": layer2_diagnosis.anomaly_detected,
            "explanation_text": layer3_report.explanation_text,
            "annotated_pdf_path": layer3_report.annotated_pdf_path,
            "total_processing_time": total_elapsed
        }
        
        return response_dict
    
    except Exception as e:
        print(f"\n[API ERROR] {str(e)}\n")
        raise HTTPException(status_code=500, detail=f"Processing error: {str(e)}")
    
    finally:
        if os.path.exists(upload_path):
            try:
                os.remove(upload_path)
            except:
                pass
        
        if scan_path and os.path.exists(scan_path):
            try:
                os.remove(scan_path)
            except:
                pass

@app.get("/api/report/{filename}")
async def get_report(filename: str):
    
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
    
    file_path = os.path.join(settings.OUTPUT_DIR, filename)
    
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Image not found")
    
    return FileResponse(file_path, media_type="image/png")

if __name__ == "__main__":
    print()
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
