import time
import tempfile
import os
from typing import Optional, Any
from PIL import Image
from models.screening import ScreeningResult

# Import P1 document validator
try:
    from src.document_validator import validate_document
except ImportError:
    validate_document = None


class SecurityEngine:
    # "REAL" routes to P1 pipeline. Demo scenarios remain available for UI testing.
    demo_scenario: str = "REAL"

    @staticmethod
    def _save_temp_image(img: Image.Image) -> str:
        """Saves a PIL image to a temporary file on disk."""
        fd, path = tempfile.mkstemp(suffix=".jpg")
        with os.fdopen(fd, 'wb') as f:
            if img.mode in ("RGBA", "P"):
                img = img.convert("RGB")
            img.save(f, format="JPEG")
        return path

    @staticmethod
    def analyze_document(passport_img: Optional[Image.Image], face_img: Optional[Image.Image] = None) -> dict:
        """
        Main interface for the TRINETRA screening pipeline.
        Routes to demo mock generator or REAL document processing.
        """
        if SecurityEngine.demo_scenario != "REAL":
            return SecurityEngine._get_demo_result(face_img)

        return SecurityEngine._process_real(passport_img, face_img)

    @staticmethod
    def _process_real(passport_img: Optional[Image.Image], face_img: Optional[Image.Image] = None) -> dict:
        start_time = time.time()
        pass_path: Optional[str] = None
        face_path: Optional[str] = None

        if passport_img is None:
            return SecurityEngine._create_insufficient_evidence_result(
                start_time, "Passport image was not provided."
            )

        try:
            # 1. Save temporary images for disk-based processing
            pass_path = SecurityEngine._save_temp_image(passport_img)
            if face_img is not None:
                face_path = SecurityEngine._save_temp_image(face_img)

            # 2. Invoke P1 Pipeline
            if validate_document is None:
                raise ImportError("src.document_validator module is unavailable.")

            p1_result = validate_document(pass_path)
            if not isinstance(p1_result, dict) or p1_result.get("status") == "ERROR":
                reason = p1_result.get("reason", "Document validation pipeline failed.") if isinstance(p1_result, dict) else "Invalid output from document validator."
                return SecurityEngine._create_insufficient_evidence_result(start_time, reason)

            # 3. Face Verification (Disabled for this integration stage)
            face_res = {
                "status": "NOT_PROVIDED",
                "provided": False,
                "match_score": None,
                "is_match": None
            }

            # 4. Extract and Map P1 Sub-structures
            doc_data = p1_result.get("passport_data") or {}
            mrz_data = p1_result.get("mrz_data") or {}
            cross_val = p1_result.get("cross_validation") or {}
            tamper_data = p1_result.get("tamper") or {}

            # Parse Cross-Validation fields
            dob_match = False
            expiry_match = False
            cv_results = cross_val.get("results") or []
            if isinstance(cv_results, list):
                for item in cv_results:
                    if isinstance(item, dict):
                        field_name = str(item.get("field", "")).lower()
                        match_val = bool(item.get("match", False))
                        if field_name in ("date_of_birth", "dob"):
                            dob_match = match_val
                        elif field_name in ("expiry_date", "expiry", "date_of_expiry"):
                            expiry_match = match_val

            # Parse MRZ Checksums without fabricating counts
            mrz_valid = bool(mrz_data.get("valid", False))
            if "checksums_passed" in mrz_data and "total_checksums" in mrz_data:
                chk_passed = int(mrz_data["checksums_passed"])
                chk_total = int(mrz_data["total_checksums"])
            elif isinstance(mrz_data.get("checksums"), dict):
                chk_dict = mrz_data["checksums"]
                chk_total = len(chk_dict)
                chk_passed = sum(1 for v in chk_dict.values() if bool(v))
            else:
                chk_total = 1 if mrz_data else 0
                chk_passed = 1 if mrz_valid else 0

            # Parse Tampering Score
            raw_tamper_score = float(tamper_data.get("tamper_score", 0.0))
            tamper_score_normalized = max(0.0, min(1.0, raw_tamper_score / 100.0 if raw_tamper_score > 1.0 else raw_tamper_score))
            tamper_detected = bool(tamper_data.get("tamper_suspected", False))
            anomalies = tamper_data.get("reasons") or tamper_data.get("failed_checks") or []

            # Parse OCR Text and Confidence
            raw_ocr = p1_result.get("ocr_texts", "")
            if isinstance(raw_ocr, list):
                extracted_ocr_text = "\n".join(str(t) for t in raw_ocr)
            else:
                extracted_ocr_text = str(raw_ocr)
            
            raw_conf = p1_result.get("ocr_confidence")
            ocr_conf = float(raw_conf) if raw_conf is not None else 0.0
            ocr_conf = max(0.0, min(1.0, ocr_conf))

            # 5. Deterministic Risk Assessment
            risk_score = 0
            evidence = []

            if not mrz_valid:
                risk_score += 35
                evidence.append("MRZ validation failed or checksum mismatch detected")
            else:
                evidence.append("MRZ syntax and checksums verified")

            if tamper_detected:
                risk_score += 40
                evidence.append(f"Image tampering suspected: {', '.join(anomalies) if anomalies else 'Forensic anomaly'}")
            else:
                evidence.append("No tampering anomalies detected")

            if cross_val and not cross_val.get("all_match", True):
                risk_score += 20
                evidence.append("Inconsistency detected between document visual zone and MRZ")

            # Risk Assessment Levels
            if risk_score >= 70:
                risk_level = "HIGH RISK"
                recommendation = "Secondary review recommended before further processing"
            elif risk_score >= 30:
                risk_level = "REVIEW"
                recommendation = "Additional verification recommended"
            else:
                risk_level = "LOW RISK"
                recommendation = "Continue normal screening"

            # 6. Build Final Response Dictionary
            result_dict = {
                "processing": {
                    "status": "SUCCESS",
                    "processing_time": round(time.time() - start_time, 2),
                    "pipeline_version": "1.0"
                },
                "document_info": {
                    "document_type": str(doc_data.get("document_type") or doc_data.get("type") or "PASSPORT"),
                    "issuing_country": str(doc_data.get("country") or doc_data.get("issuing_country") or "UNKNOWN"),
                    "document_number": str(doc_data.get("document_number") or mrz_data.get("document_number") or "UNKNOWN"),
                    "surname": str(doc_data.get("surname") or "UNKNOWN"),
                    "given_names": str(doc_data.get("given_names") or doc_data.get("names") or "UNKNOWN"),
                    "date_of_birth": doc_data.get("date_of_birth") or doc_data.get("dob") or mrz_data.get("date_of_birth"),
                    "expiry_date": doc_data.get("expiry_date") or mrz_data.get("expiry_date")
                },
                "ocr": {
                    "status": "SUCCESS" if extracted_ocr_text.strip() else "FAILED",
                    "extracted_text": extracted_ocr_text,
                    "confidence_score": ocr_conf
                },
                "mrz": {
                    "status": "SUCCESS" if mrz_data else "FAILED",
                    "is_valid": mrz_valid,
                    "dob_match": dob_match,
                    "expiry_match": expiry_match,
                    "checksums_passed": chk_passed,
                    "total_checksums": chk_total
                },
                "tampering": {
                    "status": "SUCCESS" if tamper_data else "FAILED",
                    "tampering_detected": tamper_detected,
                    "tamper_score": tamper_score_normalized,
                    "anomalies": [str(a) for a in anomalies],
                    "regions": tamper_data.get("regions") or []
                },
                "face_verification": face_res,
                "risk_assessment": {
                    "overall_score": min(100, risk_score),
                    "risk_level": risk_level,
                    "evidence": evidence,
                    "recommendation": recommendation
                }
            }

            validated = ScreeningResult(**result_dict)
            return validated.model_dump()

        except Exception as e:
            return SecurityEngine._create_insufficient_evidence_result(start_time, f"System error during analysis: {str(e)}")

        finally:
            if pass_path and os.path.exists(pass_path):
                os.remove(pass_path)
            if face_path and os.path.exists(face_path):
                os.remove(face_path)

    @staticmethod
    def _create_insufficient_evidence_result(start_time: float, reason: str) -> dict:
        result = {
            "processing": {
                "status": "INSUFFICIENT_EVIDENCE",
                "processing_time": round(time.time() - start_time, 2),
                "pipeline_version": "1.0"
            },
            "document_info": {
                "document_type": "PASSPORT",
                "issuing_country": "UNKNOWN",
                "document_number": "UNKNOWN",
                "surname": "UNKNOWN",
                "given_names": "UNKNOWN",
                "date_of_birth": None,
                "expiry_date": None
            },
            "ocr": {
                "status": "FAILED",
                "extracted_text": "",
                "confidence_score": 0.0
            },
            "mrz": {
                "status": "FAILED",
                "is_valid": False,
                "dob_match": False,
                "expiry_match": False,
                "checksums_passed": 0,
                "total_checksums": 0
            },
            "tampering": {
                "status": "INSUFFICIENT_EVIDENCE",
                "tampering_detected": False,
                "tamper_score": 0.0,
                "anomalies": [],
                "regions": []
            },
            "face_verification": {
                "status": "NOT_PROVIDED",
                "provided": False,
                "match_score": None,
                "is_match": None
            },
            "risk_assessment": {
                "overall_score": 0,
                "risk_level": "INSUFFICIENT EVIDENCE",
                "evidence": [reason],
                "recommendation": "Recapture document image for further analysis"
            }
        }
        validated = ScreeningResult(**result)
        return validated.model_dump()

    @staticmethod
    def _get_demo_result(face_img: Optional[Image.Image] = None) -> dict:
        start_time = time.time()
        result = {
            "processing": {
                "status": "SUCCESS",
                "processing_time": 0.1,
                "pipeline_version": "0.1"
            },
            "document_info": {
                "document_type": "PASSPORT",
                "issuing_country": "IND",
                "document_number": "Z9876543",
                "surname": "SHARMA",
                "given_names": "ROHAN",
                "date_of_birth": "1990-01-01",
                "expiry_date": "2031-12-28"
            },
            "ocr": {
                "status": "SUCCESS",
                "extracted_text": "P<INDSHARMA<<ROHAN<<<<<<<<<<<<<<<<<<<<<<<\nZ9876543<8IND9001015M2812316<<<<<<<<<<<<<<02",
                "confidence_score": 0.985
            },
            "mrz": {
                "status": "SUCCESS",
                "is_valid": True,
                "dob_match": True,
                "expiry_match": True,
                "checksums_passed": 2,
                "total_checksums": 2
            },
            "tampering": {
                "status": "SUCCESS",
                "tampering_detected": False,
                "tamper_score": 0.12,
                "anomalies": [],
                "regions": []
            },
            "face_verification": {
                "status": "NOT_PROVIDED",
                "provided": False,
                "match_score": None,
                "is_match": None
            },
            "risk_assessment": {
                "overall_score": 12,
                "risk_level": "LOW RISK",
                "evidence": ["No significant anomalies detected", "MRZ checks passed", "Document fields are consistent"],
                "recommendation": "Continue normal screening"
            }
        }

        # Face behavior is disabled for Demo Mode to stay consistent with REAL mode for now
        
        if SecurityEngine.demo_scenario == "HIGH RISK":
            result["tampering"].update({
                "tampering_detected": True,
                "tamper_score": 0.88,
                "anomalies": ["Digital splicing detected near photo", "Inconsistent compression"]
            })
            result["risk_assessment"].update({
                "overall_score": 95,
                "risk_level": "HIGH RISK",
                "evidence": ["Severe tampering anomalies detected in photo region"],
                "recommendation": "Secondary review recommended before further processing"
            })

        elif SecurityEngine.demo_scenario == "REVIEW":
            result["mrz"].update({
                "is_valid": False,
                "checksums_passed": 1,
                "expiry_match": False
            })
            result["risk_assessment"].update({
                "overall_score": 65,
                "risk_level": "REVIEW",
                "evidence": ["MRZ checksum mismatch", "Expiry date validation failed"],
                "recommendation": "Additional verification recommended"
            })

        elif SecurityEngine.demo_scenario == "INSUFFICIENT EVIDENCE":
            return SecurityEngine._create_insufficient_evidence_result(start_time, "Image quality too low for automated processing")

        validated = ScreeningResult(**result)
        return validated.model_dump()