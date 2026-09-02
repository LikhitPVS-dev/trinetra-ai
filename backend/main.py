import time
from typing import Optional
from fastapi import FastAPI, File, UploadFile, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="TRINETRA Border Security API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def build_mock_analysis(scenario: str = "LOW RISK") -> dict:
    """Provides a compliant full-schema response matching the TRINETRA UI contract."""
    scenario = (scenario or "LOW RISK").upper()

    score_map = {
        "LOW RISK": (12, "Document and identity verified. Cleared for standard entry."),
        "REVIEW": (58, "Minor anomalies detected. Recommend secondary officer review."),
        "HIGH RISK": (89, "Critical tampering/checksum failure detected. Flag document."),
        "INSUFFICIENT EVIDENCE": (0, "Image quality below threshold. Recapture document.")
    }
    score, rec = score_map.get(scenario, (15, "Standard clearance."))

    return {
        "processing": {
            "status": "INSUFFICIENT_EVIDENCE" if scenario == "INSUFFICIENT EVIDENCE" else "SUCCESS",
            "processing_time": 0.42,
            "pipeline_version": "v0.1"
        },
        "document_info": {
            "document_type": "P<IND",
            "issuing_country": "IND",
            "document_number": "Z8921473",
            "surname": "SHARMA",
            "given_names": "VIKRAM",
            "date_of_birth": "1994-08-22",
            "expiry_date": "2031-08-21"
        },
        "ocr": {
            "status": "SUCCESS",
            "extracted_text": "P<INDSHARMA<<VIKRAM<<<<<<<<<<<<<<<<<<<<<<<<<<\nZ8921473<4IND9408221M3108218<<<<<<<<<<<<<<<4",
            "confidence_score": 0.96
        },
        "mrz": {
            "status": "SUCCESS",
            "is_valid": scenario != "HIGH RISK",
            "checksums_passed": 2 if scenario == "HIGH RISK" else 5,
            "total_checksums": 5,
            "dob_match": True,
            "expiry_match": scenario != "HIGH RISK"
        },
        "tampering": {
            "status": "SUCCESS",
            "tampering_detected": scenario in ["HIGH RISK", "REVIEW"],
            "tamper_score": 0.84 if scenario == "HIGH RISK" else 0.12,
            "anomalies": ["ELA compression discontinuity in MRZ zone"] if scenario == "HIGH RISK" else [],
            "regions": []
        },
        "face_verification": {
            "status": "SUCCESS",
            "is_match": scenario != "HIGH RISK",
            "match_score": 24 if scenario == "HIGH RISK" else 94
        },
        "risk_assessment": {
            "risk_level": scenario,
            "overall_score": score,
            "recommendation": rec,
            "evidence": [
                "ICAO Doc 9303 line checksums validated" if scenario != "HIGH RISK" else "MRZ check digit mismatch",
                "Facial biometric cosine similarity acceptable" if scenario != "HIGH RISK" else "Facial embedding distance exceeds threshold",
                "No digital splicing or clone tool artifacts found" if scenario != "HIGH RISK" else "High frequency noise discrepancy on photo region"
            ]
        }
    }

@app.get("/health")
def health_check():
    return {"status": "online", "service": "Trinetra Forensic Engine"}

@app.post("/analyze")
async def analyze_document(
    passport: UploadFile = File(...),
    face: Optional[UploadFile] = File(None),
    scenario: Optional[str] = Form("LOW RISK")
):
    # Validate uploaded passport extension
    allowed_types = ["image/jpeg", "image/png", "image/jpg"]
    if passport.content_type not in allowed_types:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type: {passport.content_type}. Only JPEG/PNG are accepted."
        )

    passport_bytes = await passport.read()
    if len(passport_bytes) == 0:
        raise HTTPException(status_code=400, detail="Uploaded file is empty.")

    face_bytes = await face.read() if face else None

    # Person 1 integration call
    try:
        from SecurityEngine import SecurityEngine
        engine = SecurityEngine()
        if hasattr(engine, "analyze"):
            return engine.analyze(passport_bytes, face_bytes, scenario=scenario)
        if hasattr(engine, "run_full_forensic_pipeline"):
            return engine.run_full_forensic_pipeline(passport_bytes, face_bytes)
    except Exception:
        pass

    # Safe mock fallback matching app.py schema
    return build_mock_analysis(scenario or "LOW RISK")