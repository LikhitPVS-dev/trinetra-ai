import pytest
from pydantic import ValidationError
from models.screening import (
    ScreeningResult, OCRResult, MRZResult, 
    TamperingResult, FaceVerificationResult, RiskAssessment
)
from SecurityEngine import SecurityEngine

def test_valid_engine_output():
    """Ensure the mock engine generates a completely valid schema."""
    result_dict = SecurityEngine.analyze_document(passport_img=None, face_img=None)
    # If this fails, the dict structure is broken
    validated = ScreeningResult(**result_dict)
    assert validated.risk_assessment.risk_level == "LOW RISK"

def test_invalid_ocr_confidence():
    with pytest.raises(ValidationError):
        OCRResult(status="SUCCESS", extracted_text="TEXT", confidence_score=1.5)

def test_invalid_tamper_score():
    with pytest.raises(ValidationError):
        TamperingResult(status="SUCCESS", tampering_detected=False, tamper_score=-0.1, anomalies=[], regions=[])

def test_invalid_face_match_score():
    with pytest.raises(ValidationError):
        FaceVerificationResult(status="SUCCESS", provided=True, match_score=105.0, is_match=True)

def test_invalid_risk_score():
    with pytest.raises(ValidationError):
        RiskAssessment(overall_score=105, risk_level="LOW RISK", evidence=[], recommendation="")

def test_invalid_risk_level():
    with pytest.raises(ValidationError):
        # "CLEARED" is forbidden by Literal type
        RiskAssessment(overall_score=10, risk_level="CLEARED", evidence=[], recommendation="")

def test_inconsistent_mrz_checksums():
    with pytest.raises(ValidationError) as excinfo:
        MRZResult(
            status="SUCCESS", is_valid=False, dob_match=True, expiry_match=True,
            checksums_passed=3, total_checksums=2
        )
    assert "cannot exceed total_checksums" in str(excinfo.value)