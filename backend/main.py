from fastapi import FastAPI, UploadFile, File, Form, HTTPException
import io
from PIL import Image
import sys
import os

# Ensure the backend can import from the root project directory
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from SecurityEngine import SecurityEngine
from models.screening import ScreeningResult
from pydantic import ValidationError

app = FastAPI(
    title="TRINETRA API",
    description="Backend API for AI-assisted passport screening",
    version="0.1"
)

ALLOWED_TYPES = ["image/jpeg", "image/jpg", "image/png"]

@app.get("/")
def read_root():
    """Health check endpoint"""
    return {"status": "TRINETRA API is running"}

@app.post("/analyze", response_model=ScreeningResult)
async def analyze_document(
    passport: UploadFile = File(...),
    face: UploadFile = File(None),
    scenario: str = Form("LOW RISK")
):
    """
    Accepts passport and optional face image, runs SecurityEngine,
    and returns Pydantic-validated JSON.
    """
    # 1. Validate file types
    if passport.content_type not in ALLOWED_TYPES:
        raise HTTPException(status_code=400, detail=f"Unsupported passport file type: {passport.content_type}")
    
    if face and face.content_type not in ALLOWED_TYPES:
        raise HTTPException(status_code=400, detail=f"Unsupported face file type: {face.content_type}")

    # 2. Process Passport Image
    try:
        pass_bytes = await passport.read()
        passport_img = Image.open(io.BytesIO(pass_bytes))
        passport_img.verify() # Verify it's a valid image
        passport_img = Image.open(io.BytesIO(pass_bytes)) # Reopen after verify
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid or corrupted passport image")

    # 3. Process Face Image
    face_img = None
    if face:
        try:
            face_bytes = await face.read()
            face_img = Image.open(io.BytesIO(face_bytes))
            face_img.verify()
            face_img = Image.open(io.BytesIO(face_bytes))
        except Exception:
            raise HTTPException(status_code=400, detail="Invalid or corrupted face image")

    # 4. Handle Demo Scenario safely across HTTP
    # (Sets the static mock variable just before execution)
    SecurityEngine.demo_scenario = scenario

    # 5. Execute AI Pipeline & Validate
    try:
        # Engine internally calls Pydantic and returns dict
        result_dict = SecurityEngine.analyze_document(passport_img, face_img)
        
        # FastAPI's response_model will re-verify against ScreeningResult automatically
        return result_dict
        
    except ValidationError as ve:
        raise HTTPException(status_code=500, detail="System fault: Backend generated invalid data structure.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"SecurityEngine fault: {str(e)}")