import time
import tempfile
import os
from typing import Optional

from PIL import Image, ImageOps
import cv2
import numpy as np
from face_verification import FaceVerifier
from models.screening import ScreeningResult



# Import P1 document validator
try:
    from src.document_validator import validate_document
except ImportError:
    validate_document = None


class SecurityEngine:
    """
    Central TRINETRA orchestration layer.

    REAL mode:
        Uses Person 1's document-analysis pipeline.

    Demo modes:
        Provide deterministic UI/demo results.

    Face verification is intentionally left as NOT_PROVIDED
    until the face-verification module is integrated.
    """

    demo_scenario: str = "REAL"
    face_verifier = None

    @staticmethod
    def _save_temp_image(img: Image.Image) -> str:
        """Save a PIL image to a temporary JPEG file."""
        fd, path = tempfile.mkstemp(suffix=".jpg")

        try:
            with os.fdopen(fd, "wb") as f:
                if img.mode in ("RGBA", "P"):
                    img = img.convert("RGB")

                img.save(f, format="JPEG")

            return path

        except Exception:
            if os.path.exists(path):
                os.remove(path)
            raise
    @staticmethod
    def _pil_to_cv2(
        img: Optional[Image.Image]
    ) -> Optional[np.ndarray]:
        """
        Convert a PIL image to an OpenCV BGR NumPy array.
        Returns None when no image is provided.
        """
        if img is None:
            return None

        if img.mode != "RGB":
            img = img.convert("RGB")

        rgb_array = np.array(img)

        return cv2.cvtColor(
            rgb_array,
            cv2.COLOR_RGB2BGR
        )
    @staticmethod
    def _normalize_document_orientation(
        img: Optional[Image.Image],
        ) -> Optional[Image.Image]:
        """
        Normalize a document image before screening.

        - Applies EXIF orientation if present.
        - Rotates portrait-oriented document images 90 degrees
        so the document is presented in landscape orientation.
        """
        if img is None:
            return None

        # Correct orientation metadata from phone/camera images.
        img = ImageOps.exif_transpose(img)

    # Passport/document pages are normally landscape.
    # Rotate images that are clearly taller than they are wide.
        if img.height > img.width:
            img = img.rotate(90, expand=True)

        return img
    @staticmethod
    def _basic_document_check(
        img: Optional[Image.Image]
    ) -> tuple[bool, str]:
        """
        Fast sanity check before expensive OCR processing.

        This is intentionally conservative:
        it rejects only obviously unsuitable images and
        does not attempt to prove that an image is a passport.
        """
        if img is None:
            return False, "No document image was provided."

        try:
            width, height = img.size

            # Reject extremely small images.
            if width < 300 or height < 200:
                return False, "Image resolution is too low for document screening."

        # Reject extreme aspect ratios.
            aspect_ratio = max(width, height) / min(width, height)

            if aspect_ratio > 3.0:
                return False, "Image dimensions are unsuitable for a passport document."

            return True, ""

        except Exception:
            return False, "Unable to inspect the uploaded document image."

    @staticmethod
    def analyze_document(
        passport_img: Optional[Image.Image],
        face_img: Optional[Image.Image] = None
    ) -> dict:
        """
        Main interface for the TRINETRA screening pipeline.
        """
        if SecurityEngine.demo_scenario != "REAL":
            return SecurityEngine._get_demo_result(face_img)

        passport_img = SecurityEngine._normalize_document_orientation(passport_img)

        return SecurityEngine._process_real(passport_img, face_img)
    @staticmethod
    def _normalize_date(date_value):
        """
        Convert MRZ date format YYMMDD to DD/MM/YYYY.

        Human-readable dates are returned unchanged.
       """
        if date_value is None:
            return None

        value = str(date_value).strip()

    # Already human-readable
        if len(value) == 10 and value[2] == "/" and value[5] == "/":
            return value

    # MRZ format: YYMMDD
        if len(value) == 6 and value.isdigit():
            yy = int(value[0:2])
            mm = value[2:4]
            dd = value[4:6]

        # Practical century rule for current passport data.
            current_year = time.localtime().tm_year % 100

            if yy <= current_year:
                year = 2000 + yy
            else:
                year = 1900 + yy

            return f"{dd}/{mm}/{year}"

        return value
    @staticmethod
    def _process_real(
        passport_img: Optional[Image.Image],
        face_img: Optional[Image.Image] = None
    ) -> dict:

        start_time = time.time()
        pass_path: Optional[str] = None
        stage_start = time.time()

        if passport_img is None:
            return SecurityEngine._create_insufficient_evidence_result(
                start_time,
                "Passport image was not provided."
            )
                # --------------------------------------------------
        # Fast document sanity check
        # --------------------------------------------------
        valid_image, check_reason = SecurityEngine._basic_document_check(
            passport_img
        )

        if not valid_image:
            return SecurityEngine._create_insufficient_evidence_result(
                start_time,
                check_reason
            )

        try:
            # --------------------------------------------------
            # 1. Save passport image for P1 disk-based pipeline
            # --------------------------------------------------

            pass_path = SecurityEngine._save_temp_image(
                passport_img
            )
            print(f"[PERF] Save image: {time.time() - stage_start:.2f}s")
            stage_start = time.time()

            # --------------------------------------------------
            # 2. Run Person 1 document pipeline
            # --------------------------------------------------

            if validate_document is None:
                raise ImportError(
                    "src.document_validator module is unavailable."
                )

            p1_result = validate_document(pass_path)
            print(f"[PERF] P1 document pipeline: {time.time() - stage_start:.2f}s")
            stage_start = time.time()

            if not isinstance(p1_result, dict):
                return SecurityEngine._create_insufficient_evidence_result(
                    start_time,
                    "Invalid output from document validator."
                )

            if p1_result.get("status") == "ERROR":
                reason = p1_result.get(
                    "reason",
                    "Document validation pipeline failed."
                )

                return SecurityEngine._create_insufficient_evidence_result(
                    start_time,
                    reason
                )
            # --------------------------------------------------
            # 3. Face verification
            # --------------------------------------------------

            if face_img is None:
                face_res = {
                    "status": "NOT_PROVIDED",
                    "provided": False,
                    "match_score": None,
                    "is_match": None
                }

            else:
                try:
                # Convert PIL images to OpenCV/NumPy arrays.
                    passport_array = SecurityEngine._pil_to_cv2(
                        passport_img
                    )
                    face_array = SecurityEngine._pil_to_cv2(
                        face_img
                    )

                # Lazily initialize FaceVerifier only when
                # a presented face has actually been provided.
                    if SecurityEngine.face_verifier is None:
                        SecurityEngine.face_verifier = FaceVerifier()

                    face_res = SecurityEngine.face_verifier.verify(
                        passport_array,
                        face_array
                    )

                except Exception as e:
                    print(
                        f"[FACE] Verification failed: {e}"
                    )

                    face_res = {
                        "status": "FAILED",
                        "provided": True,
                        "match_score": None,
                        "is_match": None
                    }

            # --------------------------------------------------
            # 4. Extract P1 results
            # --------------------------------------------------

            doc_data = p1_result.get("passport_data") or {}
            mrz_data = p1_result.get("mrz_data") or {}
            cross_val = p1_result.get("cross_validation") or {}
            tamper_data = p1_result.get("tamper") or {}

            # --------------------------------------------------
            # 5. Cross-validation results
            # --------------------------------------------------

            dob_match = False
            expiry_match = False

            cv_results = cross_val.get("results") or []

            if isinstance(cv_results, list):
                for item in cv_results:
                    if not isinstance(item, dict):
                        continue

                    field_name = str(
                        item.get("field", "")
                    ).lower()

                    match_value = bool(
                        item.get("match", False)
                    )

                    if field_name in {
                        "date_of_birth",
                        "dob"
                    }:
                        dob_match = match_value

                    elif field_name in {
                        "date_of_expiry",
                        "expiry_date",
                        "expiry"
                    }:
                        expiry_match = match_value

            # --------------------------------------------------
            # 6. MRZ validity + checksum information
            # --------------------------------------------------

            mrz_valid = bool(
                mrz_data.get("valid", False)
            )

            checks = mrz_data.get("checks")

            if isinstance(checks, dict):
                checksum_values = [
                    bool(value)
                    for value in checks.values()
                ]

                chk_total = len(checksum_values)
                chk_passed = sum(checksum_values)

            elif (
                "checksums_passed" in mrz_data
                and "total_checksums" in mrz_data
            ):
                chk_passed = int(
                    mrz_data["checksums_passed"]
                )

                chk_total = int(
                    mrz_data["total_checksums"]
                )

            else:
                chk_total = 1 if mrz_data else 0
                chk_passed = (
                    1
                    if mrz_valid
                    else 0
                )

            # Safety check for shared schema
            chk_passed = max(
                0,
                min(chk_passed, chk_total)
            )

            # --------------------------------------------------
            # 7. Tampering
            # --------------------------------------------------

            raw_tamper_score = float(
                tamper_data.get(
                    "tamper_score",
                    0.0
                )
            )

            # P1 score is 0-100.
            tamper_score_normalized = max(
                0.0,
                min(
                    1.0,
                    raw_tamper_score / 100.0
                )
            )

            tamper_detected = bool(
                tamper_data.get(
                    "tamper_suspected",
                    False
                )
            )

            anomalies = (
                tamper_data.get("reasons")
                or tamper_data.get("failed_checks")
                or []
            )

            if not isinstance(anomalies, list):
                anomalies = [str(anomalies)]

            # --------------------------------------------------
            # 8. OCR
            # --------------------------------------------------

            raw_ocr = p1_result.get(
                "ocr_texts",
                ""
            )

            if isinstance(raw_ocr, list):
                extracted_ocr_text = "\n".join(
                    str(text)
                    for text in raw_ocr
                )
            else:
                extracted_ocr_text = str(
                    raw_ocr
                )

            # P1 currently does not expose OCR confidence.
            # Do not invent a confidence value.
            raw_conf = p1_result.get(
                "ocr_confidence"
            )

            if raw_conf is None:
                ocr_conf = 0.0
            else:
                ocr_conf = max(
                    0.0,
                    min(
                        1.0,
                        float(raw_conf)
                    )
                )

            # --------------------------------------------------
            # 9. Deterministic risk assessment
            # --------------------------------------------------

            risk_score = 0
            evidence = []

            if not mrz_valid:
                risk_score += 35

                evidence.append(
                    "MRZ validation failed or checksum mismatch detected"
                )
            else:
                evidence.append(
                    "MRZ syntax and checksums verified"
                )

            if tamper_detected:
                risk_score += 40

                evidence.append(
                    "Image tampering suspected: "
                    + (
                        ", ".join(
                            str(a)
                            for a in anomalies
                        )
                        if anomalies
                        else "Forensic anomaly"
                    )
                )
            else:
                evidence.append(
                    "No tampering anomalies detected"
                )

            if (
                cross_val
                and not cross_val.get(
                    "all_match",
                    True
                )
            ):
                risk_score += 20

                evidence.append(
                    "Inconsistency detected between "
                    "document visual zone and MRZ"
                )

            # --------------------------------------------------
            # Risk level
            # --------------------------------------------------

            if risk_score >= 70:
                risk_level = "HIGH RISK"

                recommendation = (
                    "Secondary review recommended "
                    "before further processing"
                )

            elif risk_score >= 30:
                risk_level = "REVIEW"

                recommendation = (
                    "Additional verification recommended"
                )

            else:
                risk_level = "LOW RISK"

                recommendation = (
                    "Continue normal screening"
                )

            # --------------------------------------------------
            # 10. Build shared ScreeningResult
            # --------------------------------------------------

            result_dict = {
                "processing": {
                    "status": "SUCCESS",
                    "processing_time": round(
                        time.time() - start_time,
                        2
                    ),
                    "pipeline_version": "1.0"
                },

                "document_info": {
                    "document_type": str(
                        doc_data.get("document_type")
                        or doc_data.get("type")
                        or mrz_data.get("document_type")
                        or "PASSPORT"
                    ),

                    "issuing_country": str(
                        doc_data.get("country_code")
                        or doc_data.get("country")
                        or doc_data.get("issuing_country")
                        or mrz_data.get("issuing_country")
                        or "UNKNOWN"
                    ),

                    "document_number": str(
                        doc_data.get("passport_number")
                        or doc_data.get("document_number")
                        or mrz_data.get("passport_number")
                        or mrz_data.get("document_number")
                        or "UNKNOWN"
                    ),

                    "surname": str(
                        mrz_data.get("surname")
                        or doc_data.get("surname")
                        or "UNKNOWN"
                    ),

                    "given_names": str(
                        mrz_data.get("given_names")
                        or doc_data.get("given_names")
                        or doc_data.get("names")
                        or "UNKNOWN"
                    ),
                    "date_of_birth": SecurityEngine._normalize_date(
                        doc_data.get("date_of_birth")
                        or doc_data.get("dob")
                        or mrz_data.get("date_of_birth")
                    ),

                    "expiry_date": SecurityEngine._normalize_date(
                        doc_data.get("date_of_expiry")
                        or doc_data.get("expiry_date")
                        or mrz_data.get("expiry_date")
                    )
                },

                "ocr": {
                    "status": (
                        "SUCCESS"
                        if extracted_ocr_text.strip()
                        else "FAILED"
                    ),

                    "extracted_text": extracted_ocr_text,

                    "confidence_score": ocr_conf
                },

                "mrz": {
                    "status": (
                        "SUCCESS"
                        if mrz_data
                        else "FAILED"
                    ),

                    "is_valid": mrz_valid,

                    "dob_match": dob_match,

                    "expiry_match": expiry_match,

                    "checksums_passed": chk_passed,

                    "total_checksums": chk_total
                },

                "tampering": {
                    "status": (
                        "SUCCESS"
                        if tamper_data
                        else "FAILED"
                    ),

                    "tampering_detected": tamper_detected,

                    "tamper_score": tamper_score_normalized,

                    "anomalies": [
                        str(a)
                        for a in anomalies
                    ],

                    "regions": (
                        tamper_data.get("regions")
                        or []
                    )
                },

                "face_verification": face_res,

                "risk_assessment": {
                    "overall_score": min(
                        100,
                        risk_score
                    ),

                    "risk_level": risk_level,

                    "evidence": evidence,

                    "recommendation": recommendation
                }
            }
            print(f"[PERF] Result preparation: {time.time() - stage_start:.2f}s")
            # --------------------------------------------------
            # 11. Validate against shared Pydantic contract
            # --------------------------------------------------

            validated = ScreeningResult(
                **result_dict
            )
            print(f"[PERF] TOTAL: {time.time() - start_time:.2f}s")


            return validated.model_dump()

        except Exception as e:
            return SecurityEngine._create_insufficient_evidence_result(
                start_time,
                f"System error during analysis: {str(e)}"
            )

        finally:
            if (
                pass_path
                and os.path.exists(pass_path)
            ):
                os.remove(pass_path)

    @staticmethod
    def _create_insufficient_evidence_result(
        start_time: float,
        reason: str
    ) -> dict:

        result = {
            "processing": {
                "status": "INSUFFICIENT_EVIDENCE",
                "processing_time": round(
                    time.time() - start_time,
                    2
                ),
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
                "recommendation": (
                    "Recapture document image "
                    "for further analysis"
                )
            }
        }

        validated = ScreeningResult(**result)

        return validated.model_dump()

    @staticmethod
    def _get_demo_result(
        face_img: Optional[Image.Image] = None
    ) -> dict:

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
                "extracted_text": (
                    "P<INDSHARMA<<ROHAN<<<<<<<<<<<<<<<<<<<<<<<\n"
                    "Z9876543<8IND9001015M2812316<<<<<<<<<<<<<<02"
                ),
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
                "evidence": [
                    "No significant anomalies detected",
                    "MRZ checks passed",
                    "Document fields are consistent"
                ],
                "recommendation": "Continue normal screening"
            }
        }

        if SecurityEngine.demo_scenario == "HIGH RISK":

            result["tampering"].update({
                "tampering_detected": True,
                "tamper_score": 0.88,
                "anomalies": [
                    "Digital splicing detected near photo",
                    "Inconsistent compression"
                ]
            })

            result["risk_assessment"].update({
                "overall_score": 95,
                "risk_level": "HIGH RISK",
                "evidence": [
                    "Severe tampering anomalies detected "
                    "in photo region"
                ],
                "recommendation": (
                    "Secondary review recommended "
                    "before further processing"
                )
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
                "evidence": [
                    "MRZ checksum mismatch",
                    "Expiry date validation failed"
                ],
                "recommendation": (
                    "Additional verification recommended"
                )
            })

        elif SecurityEngine.demo_scenario == "INSUFFICIENT EVIDENCE":

            return SecurityEngine._create_insufficient_evidence_result(
                start_time,
                "Image quality too low for automated processing"
            )

        validated = ScreeningResult(**result)

        return validated.model_dump()