import time
from typing import Optional
import cv2
import numpy as np
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


def validate_image_bytes(image_bytes: bytes) -> bool:
    """Verifies that the byte stream can be decoded into a valid image matrix."""
    if not image_bytes:
        return False
    np_arr = np.frombuffer(image_bytes, np.uint8)
    img = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
    return img is not None and img.size > 0


def build_mock_analysis(scenario: str = "LOW RISK", has_face: bool = False) -> dict:
    """Constructs a compliant schema response matching TRINETRA API contracts."""
    scenario = (scenario or "LOW RISK").upper()

    score_map = {
        "LOW RISK": (12, "Document and identity verified. Cleared for standard entry."),
        "REVIEW": (58, "Minor anomalies detected. Recommend secondary officer review."),
        "HIGH RISK": (89, "Critical tampering/checksum failure detected. Flag document."),
        "INSUFFICIENT EVIDENCE": (0, "Image quality below threshold. Recapture document."),
    }
    score, rec = score_map.get(scenario, (15, "Standard clearance."))

    if has_face:
        face_verification = {
            "status": "SUCCESS",
            "is_match": scenario != "HIGH RISK",
            "match_score": 24 if scenario == "HIGH RISK" else 94,
        }
    else:
        face_verification = {
            "status": "NOT_PROVIDED",
            "is_match": False,
            "match_score": 0,
        }

    return {
        "processing": {
            "status": (
                "INSUFFICIENT_EVIDENCE"
                if scenario == "INSUFFICIENT EVIDENCE"
                else "SUCCESS"
            ),
            "processing_time": 0.42,
            "pipeline_version": "v0.1",
        },
        "document_info": {
            "document_type": "P<IND",
            "issuing_country": "IND",
            "document_number": "Z8921473",
            "surname": "SHARMA",
            "given_names": "VIKRAM",
            "date_of_birth": "1994-08-22",
            "expiry_date": "2031-08-21",
        },
        "ocr": {
            "status": "SUCCESS",
            "extracted_text": (
                "P<INDSHARMA<<VIKRAM<<<<<<<<<<<<<<<<<<<<<<<<<<\n"
                "Z8921473<4IND9408221M3108218<<<<<<<<<<<<<<<4"
            ),
            "confidence_score": 0.96,
        },
        "mrz": {
            "status": "SUCCESS",
            "is_valid": scenario != "HIGH RISK",
            "checksums_passed": 2 if scenario == "HIGH RISK" else 5,
            "total_checksums": 5,
            "dob_match": True,
            "expiry_match": scenario != "HIGH RISK",
        },
        "tampering": {
            "status": "SUCCESS",
            "tampering_detected": scenario in ["HIGH RISK", "REVIEW"],
            "tamper_score": 0.84 if scenario == "HIGH RISK" else 0.12,
            "anomalies": (
                ["ELA compression discontinuity in MRZ zone"]
                if scenario == "HIGH RISK"
                else []
            ),
            "regions": [],
        },
        "face_verification": face_verification,
        "risk_assessment": {
            "risk_level": scenario,
            "overall_score": score,
            "recommendation": rec,
            "evidence": [
                (
                    "ICAO Doc 9303 line checksums validated"
                    if scenario != "HIGH RISK"
                    else "MRZ check digit mismatch"
                ),
                (
                    "Facial biometric cosine similarity acceptable"
                    if scenario != "HIGH RISK"
                    else "Facial embedding distance exceeds threshold"
                ),
                (
                    "No digital splicing or clone tool artifacts found"
                    if scenario != "HIGH RISK"
                    else "High frequency noise discrepancy on photo region"
                ),
            ],
        },
    }


@app.get("/")
@app.get("/health")
def health_check():
    return {"status": "TRINETRA API is running"}


@app.post("/analyze")
async def analyze_document(
    passport: UploadFile = File(...),
    face: Optional[UploadFile] = File(None),
    scenario: Optional[str] = Form("LOW RISK"),
):
    allowed_types = ["image/jpeg", "image/png", "image/jpg"]
    if passport.content_type not in allowed_types:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported passport file type: {passport.content_type}. Only JPEG/PNG are accepted.",
        )

    passport_bytes = await passport.read()
    if not validate_image_bytes(passport_bytes):
        raise HTTPException(
            status_code=400,
            detail="Invalid or corrupted passport image.",
        )
    passport_array = cv2.imdecode(
        np.frombuffer(passport_bytes, np.uint8),
        cv2.IMREAD_COLOR
    )

    face_bytes = None
    face_array = None

    if face:
        face_bytes = await face.read()

    if face_bytes and validate_image_bytes(face_bytes):
        face_array = cv2.imdecode(
            np.frombuffer(face_bytes, np.uint8),
            cv2.IMREAD_COLOR
        )
    from SecurityEngine import SecurityEngine

    SecurityEngine.demo_scenario = scenario or "LOW RISK"

    return SecurityEngine.analyze_document(
        passport_array,
        face_array
    )