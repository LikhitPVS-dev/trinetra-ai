import pytest
from unittest.mock import patch, MagicMock
from PIL import Image
from SecurityEngine import SecurityEngine


@pytest.fixture
def dummy_image():
    return Image.new('RGB', (50, 50), color='white')


@pytest.fixture(autouse=True)
def set_real_mode():
    SecurityEngine.demo_scenario = "REAL"
    yield
    SecurityEngine.demo_scenario = "LOW RISK"


@patch("SecurityEngine.validate_document")
def test_real_pipeline_valid_document(mock_validate, dummy_image):
    mock_validate.return_value = {
        "status": "SUCCESS",
        "passport_data": {
            "type": "P",
            "country": "IND",
            "document_number": "J1234567",
            "surname": "KUMAR",
            "given_names": "AMIT",
            "date_of_birth": "1995-05-12",
            "expiry_date": "2030-05-11"
        },
        "mrz_data": {
            "valid": True,
            "document_number": "J1234567",
            "date_of_birth": "1995-05-12",
            "expiry_date": "2030-05-11",
            "checksums_passed": 3,
            "total_checksums": 3
        },
        "cross_validation": {
            "matches": 2,
            "total": 2,
            "all_match": True,
            "results": [
                {"field": "date_of_birth", "match": True},
                {"field": "expiry_date", "match": True}
            ]
        },
        "tamper": {
            "tamper_suspected": False,
            "tamper_score": 12.0,  # 0-100 scale from P1
            "reasons": []
        },
        "ocr_texts": ["P<INDKUMAR<<AMIT<<<<<<<<<<<<<<<<<<<<<<<", "J1234567<8IND9505124M3005118<<<<<<<<<<<<<<04"]
    }

    result = SecurityEngine.analyze_document(dummy_image, None)

    assert result["processing"]["status"] == "SUCCESS"
    assert result["document_info"]["surname"] == "KUMAR"
    assert result["document_info"]["document_number"] == "J1234567"
    assert result["mrz"]["is_valid"] is True
    assert result["mrz"]["dob_match"] is True
    assert result["mrz"]["expiry_match"] is True
    assert result["mrz"]["checksums_passed"] == 3
    assert result["tampering"]["tampering_detected"] is False
    assert result["tampering"]["tamper_score"] == 0.12  # Normalized to 0-1
    assert result["risk_assessment"]["risk_level"] == "LOW RISK"
    assert result["face_verification"]["status"] == "NOT_PROVIDED"


@patch("SecurityEngine.validate_document")
def test_real_pipeline_tampering_and_mrz_failure(mock_validate, dummy_image):
    mock_validate.return_value = {
        "status": "SUCCESS",
        "passport_data": {"surname": "DOE"},
        "mrz_data": {
            "valid": False,
            "checksums_passed": 1,
            "total_checksums": 3
        },
        "cross_validation": {
            "matches": 0,
            "total": 2,
            "all_match": False,
            "results": [{"field": "date_of_birth", "match": False}]
        },
        "tamper": {
            "tamper_suspected": True,
            "tamper_score": 85.0,
            "reasons": ["ELA compression anomaly near photo"]
        },
        "ocr_texts": "SAMPLE TEXT"
    }

    result = SecurityEngine.analyze_document(dummy_image, None)

    assert result["mrz"]["is_valid"] is False
    assert result["tampering"]["tampering_detected"] is True
    assert result["tampering"]["tamper_score"] == 0.85
    assert result["risk_assessment"]["risk_level"] == "HIGH RISK"
    assert result["risk_assessment"]["overall_score"] >= 70
    assert any("tampering" in ev.lower() for ev in result["risk_assessment"]["evidence"])


@patch("SecurityEngine.validate_document")
def test_real_pipeline_p1_error_handling(mock_validate, dummy_image):
    mock_validate.return_value = {
        "status": "ERROR",
        "reason": "Image blur exceeds threshold"
    }

    result = SecurityEngine.analyze_document(dummy_image, None)

    assert result["processing"]["status"] == "INSUFFICIENT_EVIDENCE"
    assert result["document_info"]["surname"] == "UNKNOWN"  # No fabricated data
    assert result["risk_assessment"]["risk_level"] == "INSUFFICIENT EVIDENCE"
    assert "blur exceeds threshold" in result["risk_assessment"]["evidence"][0]


def test_real_pipeline_missing_passport_image():
    result = SecurityEngine.analyze_document(None, None)
    assert result["processing"]["status"] == "INSUFFICIENT_EVIDENCE"
    assert result["risk_assessment"]["risk_level"] == "INSUFFICIENT EVIDENCE"