import pytest
from unittest.mock import patch
from PIL import Image

from SecurityEngine import SecurityEngine


@pytest.fixture
def dummy_image():
    return Image.new("RGB", (50, 50), color="white")


@pytest.fixture(autouse=True)
def set_real_mode():
    SecurityEngine.demo_scenario = "REAL"
    yield
    SecurityEngine.demo_scenario = "LOW RISK"


@patch("SecurityEngine.validate_document")
def test_real_pipeline_valid_document(mock_validate, dummy_image):
    """
    Verify that SecurityEngine correctly maps the ACTUAL
    Person 1 document-validator output into the shared contract.
    """

    mock_validate.return_value = {
        "status": "PASS",

        "passport_data": {
            "document_type": "Passport",
            "country_code": "IND",
            "passport_number": "J1234567",
            "name": "KUMAR AMIT",
            "nationality": "INDIAN",
            "sex": "M",
            "date_of_birth": "12/05/1995",
            "date_of_issue": "12/05/2025",
            "date_of_expiry": "11/05/2030",
            "mrz": [
                "P<INDKUMAR<<AMIT<<<<<<<<<<<<<<<<<<<<<<<<",
                "J1234567<8IND9505124M3005118<<<<<<<<<<<<04"
            ]
        },

        "mrz_data": {
            "valid": True,
            "document_type": "P",
            "issuing_country": "IND",
            "surname": "KUMAR",
            "given_names": "AMIT",
            "passport_number": "J1234567",
            "nationality": "IND",
            "date_of_birth": "950512",
            "sex": "M",
            "expiry_date": "300511",
            "checks": {
                "passport_number": True,
                "date_of_birth": True,
                "expiry_date": True,
                "overall": True
            },
            "raw_mrz": [
                "P<INDKUMAR<<AMIT<<<<<<<<<<<<<<<<<<<<<<<<",
                "J1234567<8IND9505124M3005118<<<<<<<<<<<<04"
            ]
        },

        "cross_validation": {
            "matches": 5,
            "total": 5,
            "all_match": True,
            "results": [
                {
                    "field": "passport_number",
                    "visual_value": "J1234567",
                    "mrz_value": "J1234567",
                    "match": True
                },
                {
                    "field": "nationality",
                    "visual_value": "IND",
                    "mrz_value": "IND",
                    "match": True
                },
                {
                    "field": "sex",
                    "visual_value": "M",
                    "mrz_value": "M",
                    "match": True
                },
                {
                    "field": "date_of_birth",
                    "visual_value": "950512",
                    "mrz_value": "950512",
                    "match": True
                },
                {
                    "field": "date_of_expiry",
                    "visual_value": "300511",
                    "mrz_value": "300511",
                    "match": True
                }
            ]
        },

        "tamper": {
            "tamper_suspected": False,
            "tamper_score": 12.0,
            "forensic_status": "CLEAN",
            "failed_checks": [],
            "checks": {},
            "reasons": []
        },

        "ocr_texts": [
            "P<INDKUMAR<<AMIT<<<<<<<<<<<<<<<<<<<<<<<<",
            "J1234567<8IND9505124M3005118<<<<<<<<<<<<04"
        ]
    }

    result = SecurityEngine.analyze_document(dummy_image, None)

    # Processing
    assert result["processing"]["status"] == "SUCCESS"

    # Document information
    assert result["document_info"]["document_type"] == "Passport"
    assert result["document_info"]["issuing_country"] == "IND"
    assert result["document_info"]["document_number"] == "J1234567"
    assert result["document_info"]["surname"] == "KUMAR"
    assert result["document_info"]["given_names"] == "AMIT"
    assert result["document_info"]["date_of_birth"] == "12/05/1995"
    assert result["document_info"]["expiry_date"] == "11/05/2030"

    # MRZ
    assert result["mrz"]["is_valid"] is True
    assert result["mrz"]["dob_match"] is True
    assert result["mrz"]["expiry_match"] is True
    assert result["mrz"]["checksums_passed"] == 4
    assert result["mrz"]["total_checksums"] == 4

    # Tampering
    assert result["tampering"]["tampering_detected"] is False
    assert result["tampering"]["tamper_score"] == 0.12
    assert result["tampering"]["anomalies"] == []

    # OCR
    assert result["ocr"]["status"] == "SUCCESS"
    assert result["ocr"]["confidence_score"] == 0.0
    assert "P<INDKUMAR<<AMIT" in result["ocr"]["extracted_text"]

    # Risk
    assert result["risk_assessment"]["risk_level"] == "LOW RISK"

    # Face verification is not integrated into this branch yet
    assert result["face_verification"]["status"] == "NOT_PROVIDED"


@patch("SecurityEngine.validate_document")
def test_real_pipeline_tampering_and_mrz_failure(
    mock_validate,
    dummy_image
):
    """
    Verify that MRZ failure + tampering correctly produces
    a high-risk assessment.
    """

    mock_validate.return_value = {
        "status": "REVIEW",

        "passport_data": {
            "document_type": "Passport",
            "country_code": "IND",
            "passport_number": "J1234567",
            "name": "DOE JOHN",
            "nationality": "INDIAN",
            "sex": "M",
            "date_of_birth": "12/05/1995",
            "date_of_issue": "12/05/2025",
            "date_of_expiry": "11/05/2030",
            "mrz": []
        },

        "mrz_data": {
            "valid": False,
            "document_type": "P",
            "issuing_country": "IND",
            "surname": "DOE",
            "given_names": "JOHN",
            "passport_number": "J1234567",
            "nationality": "IND",
            "date_of_birth": "950512",
            "sex": "M",
            "expiry_date": "300511",
            "checks": {
                "passport_number": True,
                "date_of_birth": False,
                "expiry_date": False,
                "overall": False
            },
            "raw_mrz": []
        },

        "cross_validation": {
            "matches": 0,
            "total": 5,
            "all_match": False,
            "results": [
                {
                    "field": "passport_number",
                    "visual_value": "J1234567",
                    "mrz_value": "J1234567",
                    "match": False
                },
                {
                    "field": "nationality",
                    "visual_value": "IND",
                    "mrz_value": "XXX",
                    "match": False
                },
                {
                    "field": "sex",
                    "visual_value": "M",
                    "mrz_value": "F",
                    "match": False
                },
                {
                    "field": "date_of_birth",
                    "visual_value": "950512",
                    "mrz_value": "000000",
                    "match": False
                },
                {
                    "field": "date_of_expiry",
                    "visual_value": "300511",
                    "mrz_value": "000000",
                    "match": False
                }
            ]
        },

        "tamper": {
            "tamper_suspected": True,
            "tamper_score": 85.0,
            "forensic_status": "SUSPICIOUS",
            "failed_checks": [
                "compression_analysis"
            ],
            "checks": {
                "compression_analysis": False
            },
            "reasons": [
                "ELA compression anomaly near photo"
            ]
        },

        "ocr_texts": [
            "SAMPLE TEXT"
        ]
    }

    result = SecurityEngine.analyze_document(dummy_image, None)

    # MRZ failure
    assert result["mrz"]["is_valid"] is False

    # Tampering
    assert result["tampering"]["tampering_detected"] is True
    assert result["tampering"]["tamper_score"] == 0.85

    # Risk
    assert result["risk_assessment"]["risk_level"] == "HIGH RISK"
    assert result["risk_assessment"]["overall_score"] >= 70

    # Evidence should mention tampering
    assert any(
        "tampering" in evidence.lower()
        for evidence in result["risk_assessment"]["evidence"]
    )


@patch("SecurityEngine.validate_document")
def test_real_pipeline_p1_error_handling(
    mock_validate,
    dummy_image
):
    """
    Verify safe handling when Person 1's document pipeline
    returns an ERROR.
    """

    mock_validate.return_value = {
        "status": "ERROR",
        "reason": "Image blur exceeds threshold"
    }

    result = SecurityEngine.analyze_document(dummy_image, None)

    assert result["processing"]["status"] == "INSUFFICIENT_EVIDENCE"

    assert result["document_info"]["surname"] == "UNKNOWN"

    assert (
        result["risk_assessment"]["risk_level"]
        == "INSUFFICIENT EVIDENCE"
    )

    assert (
        "blur exceeds threshold"
        in result["risk_assessment"]["evidence"][0]
    )


def test_real_pipeline_missing_passport_image():
    """
    Verify safe handling when no passport image is supplied.
    """

    result = SecurityEngine.analyze_document(None, None)

    assert result["processing"]["status"] == "INSUFFICIENT_EVIDENCE"

    assert (
        result["risk_assessment"]["risk_level"]
        == "INSUFFICIENT EVIDENCE"
    )